"""Private, crash-recoverable workspace controller for ce-work external units.

The generic peer-job runner owns process supervision. This controller owns the
repository-specific transaction: one private run manifest, detached sibling
JJ workspaces, complete-tree transport changes, canonical integration evidence,
exact restoration, retention, and explicit cleanup. It never launches a model
CLI and never commits a worker's output in the canonical checkout.

Every successful command prints a status word and one compact JSON document.
Trust failures print only ``UNREADABLE`` and an error on stderr.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path


SCHEMA_VERSION = 1
PLAN_CHECKPOINT_MESSAGE = "Checkpoint selected implementation plan"
_uid_getter = getattr(os, "geteuid", None) or getattr(os, "getuid", None)
_EFFECTIVE_UID = _uid_getter() if _uid_getter is not None else None
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_PACKET_BYTES = 200_000
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
TERMINAL_PROCESS = {"done", "failed", "timeout", "died-without-result"}
INTEGRATABLE_STATES = {"integration-pending", "integrated", "verified"}
UNIT_STATES = {
    "queued", "authoring", "authored", "integration-pending", "integrated",
    "restoring", "verified", "committed", "preserved", "cleaned", "native-completed",
}
GIT_LOCAL_ENV_VARS = frozenset({
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CONFIG",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS",
    "GIT_DIR",
    "GIT_GRAFT_FILE",
    "GIT_IMPLICIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_INTERNAL_SUPER_PREFIX",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_OBJECT_DIRECTORY",
    "GIT_PREFIX",
    "GIT_REPLACE_REF_BASE",
    "GIT_SHALLOW_FILE",
    "GIT_WORK_TREE",
})


class Operational(Exception):
    def __init__(self, word: str, message: str, detail: dict | None = None):
        super().__init__(message)
        self.word = word
        self.detail = detail or {}


class TrustFailure(Operational):
    def __init__(self, message: str):
        super().__init__("UNREADABLE", message)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def test_fault(point: str) -> None:
    """Deterministic crash-window injection for the repository test suite."""
    configured = {value.strip() for value in os.environ.get("CE_WORK_TEST_FAULT", "").split(",") if value.strip()}
    if point in configured:
        raise Operational("INTERRUPTED", f"injected test interruption at {point}")


def _jj_workspace_root_from_cwd(cwd: str | None = None) -> str | None:
    try:
        proc = subprocess.run(
            ["jj", "--no-pager", "--color=never", "workspace", "root"],
            cwd=cwd or os.getcwd(),
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    root = proc.stdout.decode("utf-8", "replace").strip()
    return root or None


def _private_root_usable(path: str) -> bool:
    """True when `path` is (or can now be) a directory we own and can write into."""
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        pass
    except OSError:
        return False
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if not stat.S_ISDIR(st.st_mode):
        return False
    if _EFFECTIVE_UID is not None and st.st_uid != _EFFECTIVE_UID:
        return False
    return os.access(path, os.W_OK)


def owner_scratch_root() -> str:
    """Workspace `.tmp`, or cwd `.tmp` when not in a Jujutsu repository."""
    workspace = _jj_workspace_root_from_cwd()
    path = os.path.join(workspace, ".tmp") if workspace else os.path.abspath(".tmp")
    if not _private_root_usable(path):
        os.makedirs(path, mode=0o700, exist_ok=True)
        if not _private_root_usable(path):
            raise TrustFailure(f"cannot create owner-private scratch root: {path}")
    return path


def runs_root() -> str:
    configured = os.environ.get("CE_WORK_RUNS_ROOT")
    if configured:
        return os.path.abspath(configured)
    peer_root = os.environ.get("CE_PEER_JOBS_ROOT")
    if peer_root:
        return os.path.join(os.path.abspath(peer_root), "ce-work")
    return os.path.join(owner_scratch_root(), "ce-work")


def safe_id(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value) or not value.strip("."):
        raise Operational("REFUSED", f"unsafe {label}: {value!r}")
    return value


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _valid_git_object_id(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        raw = bytes.fromhex(value)
    except ValueError:
        return False
    return len(raw) in {20, 32} and raw.hex() == value


def _native_completion_commit(unit: dict) -> str | None:
    attempts = unit.get("attempts")
    if not isinstance(attempts, list) or not attempts or not isinstance(attempts[-1], dict):
        return None
    fallback = attempts[-1].get("fallback")
    if not isinstance(fallback, dict):
        return None
    claim = fallback.get("claimed")
    completion = fallback.get("completed")
    if not isinstance(claim, dict) or not isinstance(completion, dict) or completion.get("claim") != claim:
        return None
    claim_mode = claim.get("mode")
    if claim_mode not in {"prefer", "require"}:
        return None
    accepted_head = completion.get("accepted_head")
    base = unit.get("workspace", {}).get("base")
    snapshot = completion.get("snapshot")
    wave = unit.get("wave", {})
    changed_paths = completion.get("changed_paths")
    if not (
        _valid_git_object_id(accepted_head)
        and _valid_git_object_id(base)
        and completion.get("base") == base
        and isinstance(completion.get("at"), str)
        and bool(completion["at"])
        and isinstance(completion.get("summary"), str)
        and bool(completion["summary"])
        and isinstance(completion.get("evidence_digest"), str)
        and len(completion["evidence_digest"]) == 64
        and _valid_git_object_id(completion["evidence_digest"])
        and isinstance(snapshot, dict)
        and snapshot.get("head") == accepted_head
        and snapshot.get("status_empty") is True
        and snapshot.get("worktree_index_empty") is True
        and _valid_git_object_id(snapshot.get("head_tree"))
        and snapshot.get("head_tree") == snapshot.get("index_tree")
        and snapshot.get("status_sha256") == digest_bytes(b"")
        and (
            not wave.get("id")
            or (
                _valid_git_object_id(claim.get("canonical_head"))
                and isinstance(changed_paths, list)
                and all(isinstance(path, str) for path in changed_paths)
            )
        )
    ):
        return None
    return accepted_head


def unit_accepted_commit(unit: dict) -> str | None:
    if unit.get("state") == "native-completed":
        return _native_completion_commit(unit)
    if unit.get("state") != "cleaned":
        return None
    integration = unit.get("integration")
    if not isinstance(integration, dict):
        return None
    canonical = integration.get("canonical_commit")
    if not (
        isinstance(canonical, dict)
        and all(_valid_git_object_id(canonical.get(field)) for field in ("commit", "parent", "tree"))
        and isinstance(canonical.get("at"), str)
        and bool(canonical["at"])
    ):
        return None
    return canonical["commit"]


def unit_ready_for_run_verification(unit: object) -> bool:
    return isinstance(unit, dict) and unit_accepted_commit(unit) is not None


def accepted_unit_commit_snapshot(units: object) -> dict[str, str] | None:
    if not isinstance(units, dict):
        return None
    snapshot: dict[str, str] = {}
    for unit_id in sorted(units):
        if not isinstance(unit_id, str) or not SAFE_ID.fullmatch(unit_id):
            return None
        unit = units[unit_id]
        if not isinstance(unit, dict):
            return None
        commit = unit_accepted_commit(unit)
        if commit is None:
            return None
        snapshot[unit_id] = commit
    return snapshot


def _mode(st: os.stat_result) -> int:
    return stat.S_IMODE(st.st_mode)


def _euid() -> int | None:
    return _EFFECTIVE_UID


def validate_private_dir(path: str) -> None:
    try:
        fd = os.open(path, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open directory {path}: {exc}") from exc
    try:
        st = os.fstat(fd)
        if not stat.S_ISDIR(st.st_mode):
            raise TrustFailure(f"not a real directory: {path}")
        if _euid() is not None and st.st_uid != _euid():
            raise TrustFailure(f"directory is not owned by current user: {path}")
        if _mode(st) != 0o700:
            raise TrustFailure(f"directory mode is {_mode(st):04o}, expected 0700: {path}")
    finally:
        os.close(fd)


def ensure_private_dir(path: str) -> None:
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        pass
    validate_private_dir(path)


def _owner_root_for_runs(root: str) -> str | None:
    try:
        owner_root = os.path.abspath(owner_scratch_root())
    except TrustFailure:
        return None
    try:
        if os.path.commonpath([owner_root, os.path.abspath(root)]) == owner_root:
            return owner_root
    except ValueError:  # different drives on Windows: not under this candidate
        return None
    return None


def _ensure_owner_scratch_root(path: str) -> None:
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        pass
    try:
        fd = os.open(path, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open owner scratch root {path}: {exc}") from exc
    try:
        current = os.fstat(fd)
        if not stat.S_ISDIR(current.st_mode):
            raise TrustFailure(f"owner scratch root is not a real directory: {path}")
        if _euid() is not None and current.st_uid != _euid():
            raise TrustFailure(f"owner scratch root is not owned by current user: {path}")
        if _mode(current) != 0o700:
            os.fchmod(fd, 0o700)
            repaired = os.fstat(fd)
            if repaired.st_uid != current.st_uid or _mode(repaired) != 0o700:
                raise TrustFailure(f"could not repair owner scratch root mode to 0700: {path}")
    finally:
        os.close(fd)


def ensure_root() -> str:
    return ensure_runs_root(runs_root())


def ensure_runs_root(root: str) -> str:
    """Create or verify one runs root (the creation root, or the other candidate
    root an existing run was found under) and its private lock directory."""
    owner_root = _owner_root_for_runs(root)
    if owner_root is not None:
        _ensure_owner_scratch_root(owner_root)
    parent = os.path.dirname(root)
    # The configured root's ancestors are caller-controlled; the private root
    # itself and everything below it are the durable confidentiality boundary.
    os.makedirs(parent, mode=0o700, exist_ok=True)
    ensure_private_dir(root)
    ensure_private_dir(os.path.join(root, ".locks"))
    return root


def read_private(path: str, cap: int = MAX_JSON_BYTES) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open state file {path}: {exc}") from exc
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise TrustFailure(f"state is not a regular file: {path}")
        if _euid() is not None and st.st_uid != _euid():
            raise TrustFailure(f"state is not owned by current user: {path}")
        if _mode(st) != 0o600:
            raise TrustFailure(f"state mode is {_mode(st):04o}, expected 0600: {path}")
        if st.st_size > cap:
            raise TrustFailure(f"state exceeds {cap}-byte limit: {path}")
        out = bytearray()
        while len(out) <= cap:
            part = os.read(fd, min(65536, cap + 1 - len(out)))
            if not part:
                break
            out.extend(part)
        if len(out) > cap:
            raise TrustFailure(f"state grew beyond {cap}-byte limit: {path}")
        return bytes(out)
    finally:
        os.close(fd)


def stat_private_file(path: str) -> os.stat_result:
    """Validate a private file by descriptor without consuming its content."""
    try:
        fd = os.open(path, os.O_RDONLY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open state file {path}: {exc}") from exc
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise TrustFailure(f"state is not a regular file: {path}")
        if _euid() is not None and st.st_uid != _euid():
            raise TrustFailure(f"state is not owned by current user: {path}")
        if _mode(st) != 0o600:
            raise TrustFailure(f"state mode is {_mode(st):04o}, expected 0600: {path}")
        return st
    finally:
        os.close(fd)


def read_private_json(path: str) -> dict:
    try:
        value = json.loads(read_private(path))
    except TrustFailure:
        raise
    except (ValueError, UnicodeDecodeError) as exc:
        raise TrustFailure(f"malformed JSON state: {path}") from exc
    if not isinstance(value, dict):
        raise TrustFailure(f"JSON state is not an object: {path}")
    return value


def create_private(path: str, data: bytes) -> None:
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
    except OSError as exc:
        raise Operational("BLOCKED", f"cannot exclusively create {path}: {exc}") from exc
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_private_json(path: str, doc: dict) -> None:
    data = (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_JSON_BYTES:
        raise Operational("BLOCKED", "manifest exceeds bounded state size")
    parent = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix=".manifest-", dir=parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb", closefd=True) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        dfd = os.open(parent, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def candidate_runs_roots() -> list:
    """Every root an existing run may live under. Creation uses runs_root();
    lookup must not depend on which root this invocation would create under."""
    configured = os.environ.get("CE_WORK_RUNS_ROOT")
    if configured:
        return [os.path.abspath(configured)]
    peer_root = os.environ.get("CE_PEER_JOBS_ROOT")
    if peer_root:
        return [os.path.join(os.path.abspath(peer_root), "ce-work")]
    return [os.path.join(os.path.abspath(owner_scratch_root()), "ce-work")]


def run_dir(run_id: str) -> str:
    rid = safe_id(run_id, "run id")
    for root in candidate_runs_roots():
        existing = os.path.join(root, rid)
        if os.path.isdir(existing) and not os.path.islink(existing):
            return existing
    return os.path.join(runs_root(), rid)


@contextlib.contextmanager
def locked_manifest(run_id: str, write: bool = False):
    run_id = safe_id(run_id, "run id")
    rd = run_dir(run_id)
    ensure_runs_root(os.path.dirname(rd))
    validate_private_dir(rd)
    lock_path = os.path.join(rd, "manifest.lock")
    try:
        fd = os.open(lock_path, os.O_RDWR | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open manifest lock: {exc}") from exc
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or (_euid() is not None and st.st_uid != _euid()) or _mode(st) != 0o600:
            raise TrustFailure("manifest lock owner/type/mode validation failed")
        fcntl.flock(fd, fcntl.LOCK_EX if write else fcntl.LOCK_SH)
        doc = read_private_json(os.path.join(rd, "manifest.json"))
        if doc.get("schema_version") != SCHEMA_VERSION or doc.get("run_id") != run_id:
            raise TrustFailure("manifest schema or run identity mismatch")
        before = json.dumps(doc, sort_keys=True, separators=(",", ":"))
        yield doc
        after = json.dumps(doc, sort_keys=True, separators=(",", ":"))
        if write and after != before:
            doc["revision"] = int(doc.get("revision", 0)) + 1
            doc["updated_at"] = now_iso()
            atomic_private_json(os.path.join(rd, "manifest.json"), doc)
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def sanitized_git_environment(overrides: dict | None = None) -> dict[str, str]:
    process_env = {key: value for key, value in os.environ.items() if key not in GIT_LOCAL_ENV_VARS}
    process_env.update(overrides or {})
    return process_env


def jj(workspace: str, *args: str, input_data: bytes | None = None, check: bool = True, env: dict | None = None) -> bytes:
    """Run a public jj command with cwd=workspace so file lists stay repo-relative."""
    process_env = dict(os.environ)
    process_env.update(env or {})
    proc = subprocess.run(
        ["jj", "--no-pager", "--color=never", *args],
        cwd=workspace,
        input=input_data,
        capture_output=True,
        env=process_env,
        check=False,
    )
    if check and proc.returncode != 0:
        message = proc.stderr.decode("utf-8", "replace").strip()
        raise Operational("BLOCKED", f"jj {' '.join(args)} failed: {message}")
    return proc.stdout


def jj_text(workspace: str, *args: str, check: bool = True) -> str:
    return jj(workspace, *args, check=check).decode("utf-8", "surrogateescape").strip()


def current_commit(workspace: str, rev: str = "@") -> str:
    return jj_text(workspace, "log", "-r", rev, "--no-graph", "-T", "commit_id")


def current_empty(workspace: str, rev: str = "@") -> bool:
    return jj_text(workspace, "log", "-r", rev, "--no-graph", "-T", "empty") == "true"


def current_conflict(workspace: str, rev: str = "@") -> bool:
    return jj_text(workspace, "log", "-r", rev, "--no-graph", "-T", "conflict") == "true"


def parent_commits(workspace: str, rev: str = "@") -> list[str]:
    raw = jj_text(
        workspace,
        "log", "-r", rev, "--no-graph", "-T",
        'parents.map(|c| c.commit_id()).join(" ")',
    )
    return [part for part in raw.split() if part]


def is_ancestor(workspace: str, ancestor: str, descendant: str) -> bool:
    out = jj_text(
        workspace, "log", "-r", f"{ancestor} & ::{descendant}",
        "--no-graph", "-T", "commit_id", check=False,
    )
    return out == ancestor


def bookmark_names(workspace: str, rev: str) -> list[str]:
    raw = jj_text(workspace, "bookmark", "list", "-r", rev, "-T", 'name ++ "\n"', check=False)
    return [line for line in raw.splitlines() if line.strip()]


def workspace_rows(workspace: str) -> list[dict]:
    raw = jj_text(
        workspace, "workspace", "list", "-T",
        'name ++ "\t" ++ try(root.absolute(), "") ++ "\n"',
    )
    rows: list[dict] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        name, _, root = line.partition("\t")
        rows.append({"name": name, "root": root, "workspace": root})
    return rows


def current_workspace_name(workspace: str) -> str:
    wanted = os.path.realpath(workspace)
    for row in workspace_rows(workspace):
        root = row.get("root") or ""
        if root and os.path.realpath(root) == wanted:
            return row["name"]
    raise Operational("BLOCKED", "workspace is not registered in jj workspace list")


def workspace_root_for_name(workspace: str, name: str) -> str:
    return os.path.realpath(jj_text(workspace, "workspace", "root", "--name", name))


def resolve_commit(workspace: str, rev: str) -> str:
    return current_commit(workspace, rev)


def file_in_revision(workspace: str, rev: str, rel: str) -> bool:
    raw = jj_text(workspace, "file", "list", "-r", rev, rel, check=False)
    return any(line == rel or line.startswith(rel.rstrip("/") + "/") for line in raw.splitlines() if line)


def parse_summary_paths(raw: str) -> list[str]:
    paths: list[str] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        _, _, path = line.partition(" ")
        if path:
            paths.append(path)
    return paths


def add_unit_workspace(repo: str, workspace: str, base: str, name: str) -> None:
    jj(repo, "workspace", "add", "--name", name, "-r", base, "--sparse-patterns", "full", workspace)


def forget_unit_workspace(repo: str, name: str) -> None:
    jj(repo, "workspace", "forget", name, check=False)


def restore_to_revision(workspace: str, rev: str) -> None:
    jj(workspace, "restore", "--from", rev, "--into", "@")


def apply_transport_change(workspace: str, transport: str, pre_head: str, base: str) -> None:
    if base == pre_head:
        restore_to_revision(workspace, transport)
        return
    before = set(filter(None, jj_text(workspace, "log", "-r", "all()", "--no-graph", "-T", "commit_id").splitlines()))
    jj(workspace, "duplicate", transport, "-o", pre_head)
    after = set(filter(None, jj_text(workspace, "log", "-r", "all()", "--no-graph", "-T", "commit_id").splitlines()))
    created = after - before
    if len(created) != 1:
        raise Operational("BLOCKED", "could not isolate duplicated transport change")
    jj(workspace, "edit", created.pop())


def bookmark_create(workspace: str, name: str, rev: str) -> None:
    jj(workspace, "bookmark", "create", name, "-r", rev)


def bookmark_delete(workspace: str, name: str) -> None:
    jj(workspace, "bookmark", "delete", name, check=False)


def bookmark_target(workspace: str, name: str) -> str:
    return jj_text(workspace, "log", "-r", name, "--no-graph", "-T", "commit_id", check=False)


def commit_index_tree(repo: str, message: str, paths: list[str] | None = None) -> str:
    """Finish the working-copy change with the host-composed message."""
    if not message.strip() or "\0" in message:
        raise Operational("REFUSED", "commit message must be non-empty and contain no NUL")
    args = ["commit", "-m", message.rstrip()]
    if paths:
        args.append("--")
        args.extend(paths)
    jj(repo, *args)
    return current_commit(repo, "@-")


def repo_info(repo: str) -> dict:
    repo = os.path.realpath(repo)
    top = os.path.realpath(jj_text(repo, "workspace", "root"))
    if top != repo:
        repo = top
    bookmarks = bookmark_names(repo, "@") or bookmark_names(repo, "@-")
    if not bookmarks:
        raise Operational("REFUSED", "canonical checkout must have a bookmark at the working copy")
    name = current_workspace_name(repo)
    membership = "\n".join(
        f"{row['name']}\t{row.get('root') or ''}" for row in workspace_rows(repo)
    )
    identity = digest_bytes((top + f"\0{name}\0" + membership).encode())
    head = current_commit(repo)
    return {
        "toplevel": repo,
        "workspace_name": name,
        "identity_digest": identity,
        "branch_ref": bookmarks[0],
        "head": head,
        "head_tree": head,
    }


def validate_source(doc: dict) -> None:
    source = doc.get("source")
    if source is not None:
        if not isinstance(source, dict):
            raise TrustFailure("manifest source record is malformed")
        kind = source.get("kind")
        if kind == "prompt":
            if source.get("storage") != "run" or source.get("path") != "source/bare-prompt.md":
                raise TrustFailure("prompt source location is malformed")
            if not isinstance(source.get("digest"), str) or not re.fullmatch(r"[0-9a-f]{64}", source["digest"]):
                raise TrustFailure("prompt source digest is malformed")
            data = read_private(os.path.join(run_dir(doc["run_id"]), source["path"]), MAX_PACKET_BYTES)
            if digest_bytes(data) != source.get("digest"):
                raise TrustFailure("prompt source digest does not match private content")
        elif kind == "plan":
            if source.get("storage") != "repository" or not isinstance(source.get("path"), str):
                raise TrustFailure("plan source location is malformed")
            if not isinstance(source.get("digest"), str) or not re.fullmatch(r"[0-9a-f]{64}", source["digest"]):
                raise TrustFailure("plan source digest is malformed")
        else:
            raise TrustFailure("manifest source kind is invalid")


def validate_repo(doc: dict) -> dict:
    validate_source(doc)
    recorded = doc["repository"]
    current = repo_info(recorded["toplevel"])
    for key in ("toplevel", "workspace_name", "identity_digest"):
        if current[key] != recorded[key]:
            raise Operational("BLOCKED", f"canonical repository identity changed ({key})")
    if current["branch_ref"] != doc["branch"]["ref"]:
        raise Operational("BLOCKED", "canonical bookmark changed")
    return current


def resolve_plan(repo: str, plan: str) -> tuple[str, str]:
    supplied = os.path.abspath(plan if os.path.isabs(plan) else os.path.join(repo, plan))
    try:
        st = os.lstat(supplied)
    except OSError as exc:
        raise Operational("REFUSED", f"selected plan is missing: {exc}") from exc
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise Operational("REFUSED", "selected plan must be one regular non-symlink file")
    # OS temp roots may themselves be compatibility symlinks (macOS /var ->
    # /private/var). Reject a symlink at the selected file, then compare the
    # resolved file against the already-resolved canonical repository.
    absolute = os.path.realpath(supplied)
    if os.path.commonpath([repo, absolute]) != repo:
        raise Operational("REFUSED", "plan must be inside the canonical repository")
    return absolute, os.path.relpath(absolute, repo)


def parse_json_arg(raw: str, label: str) -> dict:
    try:
        value = json.loads(raw)
    except ValueError as exc:
        raise Operational("REFUSED", f"invalid {label} JSON") from exc
    if not isinstance(value, dict):
        raise Operational("REFUSED", f"{label} must be a JSON object")
    return value


ROUTE_CONTRACTS = {
    "codex": {"target": "codex", "harness": "codex", "intermediaries": [], "default_model": "auto", "restriction_posture": "adapter-enforced"},
    "claude": {"target": "claude", "harness": "claude", "intermediaries": [], "default_model": "auto", "restriction_posture": "cooperative"},
    "grok-cli": {"target": "grok", "harness": "grok", "intermediaries": [], "default_model": "auto", "restriction_posture": "cooperative"},
    "cursor": {"target": "cursor", "harness": "cursor-agent", "intermediaries": [], "default_model": "auto", "restriction_posture": "adapter-enforced"},
    "composer": {"target": "composer", "harness": "cursor-agent", "intermediaries": ["cursor"], "default_model": "composer-2.5-fast", "restriction_posture": "adapter-enforced"},
    "grok-cursor": {"target": "grok", "harness": "cursor-agent", "intermediaries": ["cursor"], "default_model": "cursor-grok-4.6-high", "restriction_posture": "adapter-enforced"},
    "opencode": {"target": "opencode", "harness": "opencode", "intermediaries": [], "default_model": "auto", "restriction_posture": "cooperative"},
    "opencode2": {"target": "opencode2", "harness": "opencode2", "intermediaries": [], "default_model": "auto", "restriction_posture": "cooperative"},
}


def route_model_allowed(route: str, model: str) -> bool:
    if route == "opencode2":
        return model == "auto" or bool(re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9._-]+(?:#[A-Za-z0-9._-]+)?",
            model,
        ))
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]*", model):
        return False
    lowered = model.lower()
    if route == "codex":
        return model == "auto" or bool(re.fullmatch(r"(?:gpt-[A-Za-z0-9._-]+|o[0-9][A-Za-z0-9._-]*)", model))
    if route == "claude":
        return model in {"auto", "fable", "opus", "sonnet", "haiku"} or bool(re.fullmatch(r"claude-[A-Za-z0-9._-]+", model))
    if route == "grok-cli":
        return model == "auto" or bool(re.fullmatch(r"grok-[A-Za-z0-9._-]+", model))
    if route == "cursor":
        reserved = lowered in {"composer", "grok"} or lowered.startswith(("composer-", "grok-", "cursor-grok-"))
        return not reserved
    if route == "composer":
        return bool(re.fullmatch(r"composer-[A-Za-z0-9._-]+", model))
    if route == "grok-cursor":
        return bool(re.fullmatch(r"cursor-grok-[A-Za-z0-9._-]+", model))
    if route == "opencode":
        return model == "auto" or bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9._-]+", model))
    if route == "opencode2":
        return model == "auto" or bool(re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9._-]+(?:#[A-Za-z0-9._-]+)?",
            model,
        ))
    return False


def fixed_route_contract(binding: dict, egress: dict, word: str = "BLOCKED") -> dict:
    if not isinstance(binding, dict) or not isinstance(egress, dict):
        raise Operational(word, "run binding or egress sanction is malformed")
    expected_binding_fields = {"mode", "target", "model", "source"}
    if set(binding) != expected_binding_fields:
        raise Operational(word, "binding must contain exactly mode, target, model, and source")
    if binding.get("mode") not in {"prefer", "require"}:
        raise Operational(word, "binding mode must be 'prefer' or 'require'")
    source = binding.get("source")
    if not isinstance(source, str) or not source or "\0" in source or len(source.encode()) > 256:
        raise Operational(word, "binding source must be a non-empty string of at most 256 bytes")
    route = egress.get("route")
    contract = ROUTE_CONTRACTS.get(route)
    if not contract:
        allowed = ", ".join(ROUTE_CONTRACTS)
        raise Operational(word, f"unsupported egress route {route!r}; expected one of: {allowed}")
    if binding.get("target") != contract["target"]:
        raise Operational(word, "binding target does not match the sanctioned fixed route")
    intermediaries = egress.get("intermediaries")
    if intermediaries != contract["intermediaries"]:
        raise Operational(word, "egress intermediaries do not match the fixed route")
    model = binding.get("model")
    if model is not None and (not isinstance(model, str) or not model):
        raise Operational(word, "binding model must be null or a non-empty string")
    requested_model = model or contract["default_model"]
    if not route_model_allowed(route, requested_model):
        raise Operational(word, "binding model is not compatible with the sanctioned fixed route")
    restrictions = egress.get("restrictions", [])
    if not isinstance(restrictions, list) or not all(isinstance(item, str) for item in restrictions):
        raise Operational(word, "egress restrictions must be a string list")
    return contract


def attempt_authorization(
    doc: dict,
    activity_posture: str,
    unit_id: str,
    attempt_id: str,
    packet_digest: str,
) -> dict:
    binding = doc.get("binding")
    egress = doc.get("egress")
    contract = fixed_route_contract(binding, egress)
    route = egress.get("route")
    intermediaries = egress.get("intermediaries")
    model = binding.get("model")
    restrictions = egress.get("restrictions", [])
    return {
        "schema_version": 1,
        "run_id": doc["run_id"],
        "unit_id": unit_id,
        "attempt_id": attempt_id,
        "route": route,
        "target": contract["target"],
        "harness": contract["harness"],
        "intermediaries": list(contract["intermediaries"]),
        "model_requested": model or contract["default_model"],
        "restriction_posture": contract["restriction_posture"],
        "restrictions": list(restrictions),
        "activity_posture": activity_posture,
        "packet_digest": packet_digest,
    }


def read_external_packet(path: str, label: str = "unit packet") -> bytes:
    supplied = os.path.abspath(path)
    try:
        fd = os.open(supplied, os.O_RDONLY | O_NOFOLLOW)
    except OSError as exc:
        raise Operational("REFUSED", f"cannot safely open {label}: {exc}") from exc
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise Operational("REFUSED", f"{label} must be one regular non-symlink file")
        if st.st_size > MAX_PACKET_BYTES:
            raise Operational("REFUSED", f"{label} exceeds {MAX_PACKET_BYTES}-byte limit")
        data = bytearray()
        while len(data) <= MAX_PACKET_BYTES:
            part = os.read(fd, min(65536, MAX_PACKET_BYTES + 1 - len(data)))
            if not part:
                break
            data.extend(part)
        if len(data) > MAX_PACKET_BYTES:
            raise Operational("REFUSED", f"{label} exceeds {MAX_PACKET_BYTES}-byte limit")
        return bytes(data)
    finally:
        os.close(fd)


def event(doc: dict, kind: str, unit_id: str | None = None, detail: dict | None = None) -> None:
    row = {"at": now_iso(), "kind": kind}
    if unit_id is not None:
        row["unit_id"] = unit_id
    if detail:
        row["detail"] = detail
    doc.setdefault("events", []).append(row)


def cmd_init(args) -> tuple[str, dict]:
    ensure_root()
    rid = safe_id(args.run_id, "run id")
    info = repo_info(args.repo)
    if args.plan:
        if not args.plan_digest or args.prompt_digest:
            raise Operational("REFUSED", "plan source requires only --plan-digest")
        plan_abs, plan_rel = resolve_plan(info["toplevel"], args.plan)
        source_bytes = Path(plan_abs).read_bytes()
        source_kind = "plan"
        supplied_digest = args.plan_digest
        source_record = {
            "kind": source_kind,
            "storage": "repository",
            "path": plan_rel,
            "digest": digest_bytes(source_bytes),
        }
    else:
        if not args.prompt_digest or args.plan_digest:
            raise Operational("REFUSED", "prompt source requires only --prompt-digest")
        prompt_abs = os.path.realpath(os.path.abspath(args.prompt_brief))
        if os.path.commonpath([info["toplevel"], prompt_abs]) == info["toplevel"]:
            raise Operational("REFUSED", "prompt brief must be outside the canonical repository")
        source_bytes = read_external_packet(args.prompt_brief, "prompt brief")
        source_kind = "prompt"
        supplied_digest = args.prompt_digest
        source_record = {
            "kind": source_kind,
            "storage": "run",
            "path": "source/bare-prompt.md",
            "digest": digest_bytes(source_bytes),
        }
    actual_digest = source_record["digest"]
    if actual_digest != supplied_digest:
        raise Operational("REFUSED", f"selected {source_kind} digest does not match content")
    binding = parse_json_arg(args.binding_json, "binding")
    egress = parse_json_arg(args.egress_json, "egress")
    fixed_route_contract(binding, egress, "REFUSED")
    rd = run_dir(rid)
    try:
        os.mkdir(rd, 0o700)
    except FileExistsError:
        try:
            existing = os.lstat(rd)
        except OSError as exc:
            raise TrustFailure(f"cannot safely inspect run directory {rd}: {exc}") from exc
        if stat.S_ISDIR(existing.st_mode) and not os.path.lexists(os.path.join(rd, "manifest.json")):
            raise Operational(
                "BLOCKED",
                "run directory exists without a controller manifest; choose a new run id or remove the directory after confirming no initialization is active",
            )
        validate_private_dir(rd)
        with locked_manifest(rid) as existing:
            validate_repo(existing)
            existing_source = existing.get("source")
            if not isinstance(existing_source, dict):
                plan = existing.get("plan")
                existing_source = {
                    "kind": "plan",
                    "storage": "repository",
                    "path": plan.get("path") if isinstance(plan, dict) else None,
                    "digest": plan.get("digest") if isinstance(plan, dict) else None,
                }
            if (
                existing["repository"]["identity_digest"] != info["identity_digest"]
                or existing_source.get("kind") != source_kind
                or existing_source.get("digest") != actual_digest
            ):
                raise Operational("BLOCKED", "run id already belongs to another repository or source")
            if existing.get("binding") != binding or existing.get("egress") != egress:
                raise Operational(
                    "BLOCKED",
                    "run id binding or egress sanction differs from the recorded fixed contract; resume with the recorded contract or choose a new run id",
                )
            return "READY", {
                "run_id": rid,
                "revision": existing["revision"],
                "resumed": True,
                "source_kind": source_kind,
                "source_digest": actual_digest,
                "recovery_path": rd,
            }
    validate_private_dir(rd)
    for child in ("units", "jobs", "packets", "source"):
        ensure_private_dir(os.path.join(rd, child))
    if source_kind == "prompt":
        create_private(os.path.join(rd, source_record["path"]), source_bytes)
    create_private(os.path.join(rd, "manifest.lock"), b"")
    created = now_iso()
    doc = {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "run_id": rid,
        "created_at": created,
        "updated_at": created,
        "repository": {k: info[k] for k in ("toplevel", "workspace_name", "identity_digest")},
        "branch": {"ref": info["branch_ref"], "initial_head": info["head"]},
        "source": source_record,
        "plan": {
            "kind": source_kind,
            "path": plan_rel if source_kind == "plan" else None,
            "digest": actual_digest,
            "checkpoint": None,
        },
        "binding": binding,
        "egress": egress,
        "integration_lock": None,
        "units": {},
        "verification_attempts": [],
        "verifications": [],
        "blockers": [],
        "events": [{"at": created, "kind": "run-created"}],
    }
    create_private(os.path.join(rd, "manifest.json"), (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode())
    return "READY", {
        "run_id": rid,
        "revision": 0,
        "resumed": False,
        "source_kind": source_kind,
        "source_digest": actual_digest,
        "recovery_path": rd,
    }


def status_paths(repo: str) -> set[str]:
    raw = jj_text(repo, "diff", "--name-only")
    return {line for line in raw.splitlines() if line}


def status_paths_between(repo: str, frm: str, to: str) -> set[str]:
    raw = jj_text(repo, "diff", "--from", frm, "--to", to, "--name-only")
    return {line for line in raw.splitlines() if line}


def diff_summary(repo: str, frm: str, to: str) -> str:
    return jj_text(repo, "diff", "--from", frm, "--to", to, "--summary")


def reconcile_plan_checkpoint(repo: str, doc: dict, info: dict, plan_rel: str) -> dict | None:
    """Recover the controller's plan commit when its manifest receipt was interrupted."""
    prior = doc.get("branch", {}).get("initial_head")
    commit = info["head"]
    if commit == prior:
        return None
    lineage = [commit, *parent_commits(repo, commit)]
    changed = status_paths_between(repo, f"{commit}-", commit)
    message = jj_text(repo, "log", "-r", commit, "--no-graph", "-T", "description").rstrip("\n")
    plan_bytes = jj(repo, "file", "show", "-r", commit, plan_rel, check=False)
    if (
        not _valid_git_object_id(prior)
        or lineage != [commit, prior]
        or changed != {plan_rel}
        or message != PLAN_CHECKPOINT_MESSAGE
        or digest_bytes(plan_bytes) != doc["plan"]["digest"]
    ):
        raise Operational(
            "BLOCKED",
            "canonical HEAD advanced without a recorded matching plan checkpoint",
            {"expected_prior_head": prior, "head": commit},
        )
    committed_at = int(jj_text(repo, "log", "-r", commit, "--no-graph", "-T", 'committer.timestamp().format("%s")'))
    return {
        "prior_head": prior,
        "commit": commit,
        "tree": info["head_tree"],
        "path": plan_rel,
        "digest": doc["plan"]["digest"],
        "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(committed_at)),
    }


def cmd_checkpoint_plan(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        repo = info["toplevel"]
        plan = doc.get("plan")
        if not isinstance(plan, dict) or plan.get("kind", "plan") != "plan" or not plan.get("path"):
            dirty = status_paths(repo)
            if dirty:
                raise Operational("BLOCKED", "prompt-backed external execution requires a clean canonical checkout", {"dirty_paths": sorted(dirty)})
            return "NOOP", {"checkpoint": None, "head": info["head"], "source_kind": "prompt"}
        plan_rel = plan["path"]
        plan_abs, _ = resolve_plan(repo, plan_rel)
        if digest_bytes(Path(plan_abs).read_bytes()) != doc["plan"]["digest"]:
            raise Operational("BLOCKED", "selected plan content no longer matches recorded digest")
        dirty = status_paths(repo)
        if not dirty:
            checkpoint = doc["plan"].get("checkpoint")
            if checkpoint is not None:
                return "NOOP", {"checkpoint": checkpoint, "head": info["head"]}
            checkpoint = reconcile_plan_checkpoint(repo, doc, info, plan_rel)
            if checkpoint is None:
                return "NOOP", {"checkpoint": None, "head": info["head"]}
            doc["plan"]["checkpoint"] = checkpoint
            event(doc, "plan-checkpoint", detail={"commit": checkpoint["commit"], "path": plan_rel})
            return "CHECKPOINTED", {"checkpoint": checkpoint}
        if dirty != {plan_rel}:
            raise Operational("BLOCKED", "canonical dirt is not exactly the selected plan", {"dirty_paths": sorted(dirty)})
        prior = info["head"]
    try:
        commit = commit_index_tree(repo, PLAN_CHECKPOINT_MESSAGE, [plan_rel])
    except Operational:
        jj(repo, "restore", "--from", prior, check=False)
        raise
    test_fault("checkpoint-plan-after-commit")
    if status_paths(repo):
        raise Operational("BLOCKED", "checkpoint committed but canonical checkout is not clean")
    cp = {"prior_head": prior, "commit": commit, "tree": current_commit(repo, commit), "path": plan_rel, "digest": doc["plan"]["digest"], "at": now_iso()}
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        doc["plan"]["checkpoint"] = cp
        event(doc, "plan-checkpoint", detail={"commit": commit, "path": plan_rel})
    return "CHECKPOINTED", {"checkpoint": cp}


@contextlib.contextmanager
def admin_lock(lock_key: str):
    root = ensure_root()
    key = digest_bytes(os.path.realpath(lock_key).encode())
    path = os.path.join(root, ".locks", f"workspace-{key}.lock")
    try:
        create_private(path, b"")
    except Operational:
        pass
    data = read_private(path, 64)
    del data
    fd = os.open(path, os.O_RDWR | O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def worktree_rows(repo: str) -> list[dict]:
    return workspace_rows(repo)


def validate_workspace(doc: dict, unit: dict) -> dict:
    repo = doc["repository"]["toplevel"]
    workspace = unit["workspace"]["path"]
    owned = os.path.join(run_dir(doc["run_id"]), "units", unit["unit_id"])
    if os.path.commonpath([os.path.realpath(workspace), os.path.realpath(owned)]) != os.path.realpath(owned):
        raise Operational("BLOCKED", "workspace escaped its owned unit directory")
    validate_private_dir(workspace)
    matches = [
        r for r in workspace_rows(repo)
        if r.get("root") and os.path.realpath(str(r.get("root"))) == os.path.realpath(workspace)
    ]
    if len(matches) != 1:
        raise Operational("BLOCKED", "workspace is not registered exactly once")
    recorded_name = unit["workspace"].get("name") or matches[0]["name"]
    if workspace_root_for_name(repo, recorded_name) != os.path.realpath(workspace):
        raise Operational("BLOCKED", "unit workspace belongs to another repository")
    canonical_names = {row["name"] for row in workspace_rows(repo)}
    if recorded_name not in canonical_names:
        raise Operational("BLOCKED", "unit workspace belongs to another repository")
    return matches[0]


def validate_pristine_unit_base(doc: dict, unit: dict) -> dict:
    row = validate_workspace(doc, unit)
    workspace = unit["workspace"]["path"]
    base = unit["workspace"]["base"]
    parents = parent_commits(workspace, "@")
    if current_commit(workspace) != base and parents != [base]:
        raise Operational("BLOCKED", "unit workspace working copy no longer equals the recorded base")
    dirty = status_paths(workspace)
    if dirty:
        raise Operational(
            "BLOCKED",
            "unit workspace is dirty before dispatch authorization",
            {"dirty_paths": sorted(dirty)},
        )
    return row
