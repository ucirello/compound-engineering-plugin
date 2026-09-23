"""Private, crash-recoverable workspace controller for ce-work external units.

The generic peer-job runner owns process supervision. This controller owns the
repository-specific transaction: one private run manifest, linked sibling
workspaces, transport changes, canonical integration evidence, exact
restoration, retention, and explicit cleanup. It never launches a model CLI
and never finishes a worker's output in the canonical workspace except through
the host-owned integrate path.

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
import time
from pathlib import Path


SCHEMA_VERSION = 1
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
# Scrub inherited Git local-environment variables so they cannot redirect the
# workspace jj discovers from cwd, and so verification commands do not inherit
# a leaked directory pointer.
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


def workspace_scratch_root(start: str | None = None) -> str:
    """Workspace-local scratch, with a local directory fallback outside JJ."""
    origin = os.path.abspath(start or os.getcwd())
    try:
        proc = subprocess.run(
            ["jj", "--color=never", "--no-pager", "workspace", "root"],
            cwd=origin,
            capture_output=True,
            check=False,
        )
        reported = proc.stdout.decode("utf-8", "replace").strip() if proc.returncode == 0 else ""
    except FileNotFoundError:
        reported = ""
    root = reported or origin
    return os.path.join(root, ".tmp", "rocketclaw")


def owner_scratch_root() -> str:
    return workspace_scratch_root()


def runs_root() -> str:
    configured = os.environ.get("CE_WORK_RUNS_ROOT")
    if configured:
        return os.path.abspath(configured)
    peer_root = os.environ.get("CE_PEER_JOBS_ROOT")
    if peer_root:
        return os.path.join(os.path.abspath(peer_root), "ce-work")
    return os.path.join(workspace_scratch_root(), "ce-work")


def safe_id(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value) or not value.strip("."):
        raise Operational("REFUSED", f"unsafe {label}: {value!r}")
    return value


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _valid_commit_id(value: object) -> bool:
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
        _valid_commit_id(accepted_head)
        and _valid_commit_id(base)
        and completion.get("base") == base
        and isinstance(completion.get("at"), str)
        and bool(completion["at"])
        and isinstance(completion.get("summary"), str)
        and bool(completion["summary"])
        and isinstance(completion.get("evidence_digest"), str)
        and len(completion["evidence_digest"]) == 64
        and _valid_commit_id(completion["evidence_digest"])
        and isinstance(snapshot, dict)
        and snapshot.get("head") == accepted_head
        and snapshot.get("status_empty") is True
        and snapshot.get("diff_empty") is True
        and snapshot.get("status_sha256") == digest_bytes(b"")
        and (
            not wave.get("id")
            or (
                _valid_commit_id(claim.get("canonical_head"))
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
        and all(_valid_commit_id(canonical.get(field)) for field in ("commit", "parent"))
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
    owner_root = os.path.abspath(workspace_scratch_root())
    try:
        if os.path.commonpath([owner_root, os.path.abspath(root)]) == owner_root:
            return owner_root
    except ValueError:
        return None
    return None


def _ensure_owner_scratch_root(path: str) -> None:
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
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
    tmp = os.path.join(parent, f".manifest-{secrets.token_hex(8)}")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
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
    """The workspace scratch root this invocation resolves, or an explicit override."""
    configured = os.environ.get("CE_WORK_RUNS_ROOT")
    if configured:
        return [os.path.abspath(configured)]
    peer_root = os.environ.get("CE_PEER_JOBS_ROOT")
    if peer_root:
        return [os.path.join(os.path.abspath(peer_root), "ce-work")]
    return [os.path.join(workspace_scratch_root(), "ce-work")]


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


def sanitized_process_environment(overrides: dict | None = None) -> dict[str, str]:
    process_env = {key: value for key, value in os.environ.items() if key not in GIT_LOCAL_ENV_VARS}
    process_env.update(overrides or {})
    return process_env


def jj(workspace_root: str, *args: str, input_data: bytes | None = None, check: bool = True, env: dict | None = None) -> bytes:
    """Run jj with cwd set to the workspace root. Do not pass -R; paths come back repo-relative."""
    root = os.path.abspath(workspace_root)
    proc = subprocess.run(
        ["jj", "--color=never", "--no-pager", *args],
        cwd=root,
        input=input_data,
        capture_output=True,
        env=sanitized_process_environment(env),
        check=False,
    )
    if check and proc.returncode != 0:
        message = proc.stderr.decode("utf-8", "replace").strip()
        raise Operational("BLOCKED", f"jj {' '.join(args)} failed: {message}")
    return proc.stdout


def jj_text(workspace_root: str, *args: str, check: bool = True) -> str:
    return jj(workspace_root, *args, check=check).decode("utf-8", "surrogateescape").strip()


def log_template(workspace_root: str, rev: str, template: str, check: bool = True) -> str:
    return jj_text(workspace_root, "log", "-r", rev, "--no-graph", "-T", template, check=check)


def working_copy(workspace_root: str) -> dict:
    raw = log_template(
        workspace_root,
        "@",
        'commit_id ++ "\n" ++ change_id ++ "\n" ++ parents.map(|c| c.commit_id()).join(" ") ++ "\n" ++ empty ++ "\n" ++ conflict',
    )
    lines = raw.splitlines()
    if len(lines) < 5:
        raise Operational("BLOCKED", "working-copy template output was incomplete")
    parents = lines[2].split() if lines[2] else []
    return {
        "commit_id": lines[0],
        "change_id": lines[1],
        "parents": parents,
        "parent": parents[0] if len(parents) == 1 else "",
        "empty": lines[3] == "true",
        "conflict": lines[4] == "true",
    }


def summary_paths(text: str) -> list[str]:
    """Repo-relative paths from `jj diff --summary`. Rename braces are jj syntax, not a path prefix."""
    paths: list[str] = []
    for line in text.splitlines():
        if not line or " " not in line:
            continue
        _status, rest = line.split(" ", 1)
        if " => " in rest and ("{" in rest or rest.count(" => ") == 1):
            if "{" in rest and "}" in rest:
                prefix, _, tail = rest.partition("{")
                inner, _, suffix = tail.partition("}")
                old, _, new = inner.partition(" => ")
                paths.append(f"{prefix}{old}{suffix}")
                paths.append(f"{prefix}{new}{suffix}")
            else:
                old, _, new = rest.partition(" => ")
                paths.append(old)
                paths.append(new)
        else:
            paths.append(rest)
    return paths


def changed_name_only(workspace_root: str, rev: str | None = None, from_rev: str | None = None, to_rev: str | None = None) -> list[str]:
    # JSON preserves whitespace and both sides of a rename, unlike display paths.
    args = ["diff", "-T", 'json(source.path()) ++ "\n" ++ json(target.path()) ++ "\n"']
    if from_rev is not None or to_rev is not None:
        if from_rev is not None:
            args.extend(["--from", from_rev])
        if to_rev is not None:
            args.extend(["--to", to_rev])
    elif rev is not None:
        args.extend(["-r", rev])
    raw = jj(workspace_root, *args).decode("utf-8", "surrogateescape")
    try:
        paths = [json.loads(line) for line in raw.splitlines() if line]
    except ValueError as exc:
        raise Operational("BLOCKED", "JJ changed-path inventory was malformed") from exc
    if any(
        not isinstance(path, str) or not path or "\0" in path
        or os.path.isabs(path) or ".." in path.split("/")
        for path in paths
    ):
        raise Operational("BLOCKED", "JJ changed-path inventory was malformed")
    return list(dict.fromkeys(paths))


def diff_summary_paths(workspace_root: str, from_rev: str | None = None, to_rev: str | None = None, rev: str | None = None) -> list[str]:
    return changed_name_only(workspace_root, rev=rev, from_rev=from_rev, to_rev=to_rev)


def diff_has_submodule(workspace_root: str, from_rev: str, to_rev: str) -> bool:
    raw = jj_text(workspace_root, "diff", "--from", from_rev, "--to", to_rev, "--types")
    for line in raw.splitlines():
        letters = line.split(" ", 1)[0] if line else ""
        if "G" in letters:
            return True
    return False


def is_ancestor(workspace_root: str, ancestor: str, descendant: str) -> bool:
    if not _valid_commit_id(ancestor) or not _valid_commit_id(descendant):
        return False
    out = jj(
        workspace_root,
        "log", "-r", f"{ancestor} & ::{descendant}", "--no-graph", "-T", "commit_id",
        check=False,
    )
    return out.decode("utf-8", "replace").strip() == ancestor


def resolve_commit(workspace_root: str, rev: str, check: bool = True) -> str:
    return log_template(workspace_root, rev, "commit_id", check=check)


def bookmark_names_at(workspace_root: str, rev: str) -> list[str]:
    raw = log_template(workspace_root, rev, 'local_bookmarks.map(|b| b.name()).join("\n")', check=False)
    return [line for line in raw.splitlines() if line]


def bookmark_name(workspace_root: str) -> str:
    names = bookmark_names_at(workspace_root, "@")
    if len(names) == 1:
        return names[0]
    wc = working_copy(workspace_root)
    if not names and wc["empty"] and not changed_name_only(workspace_root):
        names = bookmark_names_at(workspace_root, "@-")
        if len(names) == 1:
            return names[0]
    raise Operational("REFUSED", "canonical workspace must have exactly one local bookmark")


def content_commit_id(workspace_root: str) -> str:
    wc = working_copy(workspace_root)
    if wc["empty"] and len(wc["parents"]) == 1 and not changed_name_only(workspace_root):
        return wc["parent"]
    return wc["commit_id"]


def recorded_bookmark(workspace_root: str) -> str:
    names = bookmark_names_at(workspace_root, "@")
    if len(names) == 1:
        return names[0]
    names = bookmark_names_at(workspace_root, "@-")
    if len(names) == 1:
        return names[0]
    return ""


def semantic_snapshot(repo: str) -> dict:
    wc = working_copy(repo)
    names = changed_name_only(repo)
    raw = "\n".join(names).encode()
    empty = not names
    return {
        "head": content_commit_id(repo) if empty else wc["commit_id"],
        "commit_id": wc["commit_id"],
        "change_id": wc["change_id"],
        "parent_commit_id": wc["parent"],
        "bookmark": recorded_bookmark(repo),
        "diff_empty": empty,
        "status_empty": empty,
        "status_sha256": digest_bytes(raw),
        "operation_id": current_operation_id(repo),
    }


def snapshots_equal(left: dict, right: dict) -> bool:
    ignore = {"operation_id"}
    return {k: v for k, v in left.items() if k not in ignore} == {k: v for k, v in right.items() if k not in ignore}


def current_operation_id(workspace_root: str) -> str:
    return jj_text(workspace_root, "op", "log", "-n", "1", "--no-graph", "-T", "id")


def workspace_rows(workspace_root: str) -> list[dict]:
    raw = jj_text(workspace_root, "workspace", "list", "-T", 'json(name) ++ "\n"')
    try:
        names = [json.loads(line) for line in raw.splitlines() if line]
    except ValueError as exc:
        raise Operational("BLOCKED", "JJ workspace list was malformed") from exc
    if any(not isinstance(name, str) or not name for name in names) or len(set(names)) != len(names):
        raise Operational("BLOCKED", "JJ workspace list was malformed")
    return [{"name": name} for name in names]


def workspace_name_for_root(workspace_root: str) -> str:
    top = os.path.realpath(jj_text(workspace_root, "workspace", "root"))
    for row in workspace_rows(workspace_root):
        named = jj_text(top, "workspace", "root", "--name", row["name"], check=False)
        if named and os.path.realpath(named) == top:
            return row["name"]
    raise Operational("BLOCKED", "workspace is not listed by jj workspace list")


def workspace_root_named(workspace_root: str, name: str) -> str:
    return jj_text(workspace_root, "workspace", "root", "--name", name)


def path_exists_at(workspace_root: str, rev: str, rel: str) -> bool:
    out = jj(workspace_root, "file", "list", "-r", rev, "--", rel, check=False)
    return bool(out.decode("utf-8", "surrogateescape").strip())


def file_bytes_at(workspace_root: str, rev: str, rel: str) -> bytes:
    return jj(workspace_root, "file", "show", "-r", rev, "--", rel, check=False)


def child_commit_ids(workspace_root: str, rev: str = "@") -> set[str]:
    raw = log_template(workspace_root, f"children({rev})", 'commit_id ++ "\n"', check=False)
    return {line for line in raw.splitlines() if line}


def finish_working_copy(workspace_root: str, message: str, bookmark: str | None = None) -> str:
    """Finish the working-copy change and start a new one.

    Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
    The host reads that history with jj log; runtime project instructions and
    history syntax override Go guidance. The supplied message is never templated.
    """
    if not message.strip() or "\0" in message:
        raise Operational("REFUSED", "commit message must be non-empty and contain no NUL")
    jj(workspace_root, "commit", "-m", message)
    commit = log_template(workspace_root, "@-", "commit_id")
    if bookmark:
        jj(workspace_root, "bookmark", "set", bookmark, "-r", "@-")
    return commit


def restore_operation(workspace_root: str, operation_id: str) -> None:
    jj(workspace_root, "op", "restore", operation_id)


def apply_transport(workspace_root: str, transport_commit: str) -> list[str]:
    """Replay a transport change into the working copy. The working-copy change id stays put."""
    before = working_copy(workspace_root)
    if before["conflict"]:
        raise Operational("BLOCKED", "canonical working copy is already conflicted")
    prior_children = child_commit_ids(workspace_root)
    jj(workspace_root, "duplicate", transport_commit, "--onto", "@")
    created = child_commit_ids(workspace_root) - prior_children
    if len(created) != 1:
        for commit in created:
            jj(workspace_root, "abandon", commit, check=False)
        raise Operational("BLOCKED", "transport duplicate did not create exactly one child change")
    dup = next(iter(created))
    if log_template(workspace_root, dup, "conflict") == "true":
        jj(workspace_root, "abandon", dup)
        raise Operational("BLOCKED", "transport apply conflicted")
    paths = changed_name_only(workspace_root, rev=dup)
    jj(workspace_root, "squash", "--from", dup, "--into", "@")
    after = working_copy(workspace_root)
    if after["change_id"] != before["change_id"] or after["parent"] != before["parent"]:
        raise Operational("BLOCKED", "transport apply moved the working-copy change")
    if after["conflict"]:
        jj(workspace_root, "restore")
        raise Operational("BLOCKED", "transport apply conflicted")
    return paths


def preview_apply_paths(workspace_root: str, transport_commit: str) -> dict:
    operation = current_operation_id(workspace_root)
    try:
        prior_children = child_commit_ids(workspace_root)
        jj(workspace_root, "duplicate", transport_commit, "--onto", "@")
        created = child_commit_ids(workspace_root) - prior_children
        if len(created) != 1:
            raise Operational("BLOCKED", "could not preview transport apply")
        dup = next(iter(created))
        if log_template(workspace_root, dup, "conflict") == "true":
            raise Operational("BLOCKED", "transport apply would conflict")
        return {"changed_paths": changed_name_only(workspace_root, rev=dup), "tree_commit": dup}
    finally:
        restore_operation(workspace_root, operation)


def repo_info(repo: str) -> dict:
    start = os.path.abspath(repo)
    top = os.path.realpath(jj_text(start, "workspace", "root"))
    name = workspace_name_for_root(top)
    named = os.path.realpath(workspace_root_named(top, name))
    if named != top:
        raise Operational("BLOCKED", "jj workspace root --name does not match the workspace root")
    bookmark = bookmark_name(top)
    wc = working_copy(top)
    return {
        "toplevel": top,
        "workspace_name": name,
        "bookmark": bookmark,
        "head": content_commit_id(top),
        "commit_id": wc["commit_id"],
        "change_id": wc["change_id"],
        "parent_commit_id": wc["parent"],
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
    if current["toplevel"] != recorded.get("toplevel") or current["workspace_name"] != recorded.get("workspace_name"):
        raise Operational("BLOCKED", "canonical workspace membership changed")
    named = os.path.realpath(workspace_root_named(current["toplevel"], recorded["workspace_name"]))
    if named != current["toplevel"]:
        raise Operational("BLOCKED", "canonical workspace is not a member of this repo")
    bookmark = doc.get("bookmark", {})
    if not isinstance(bookmark, dict) or current["bookmark"] != bookmark.get("name"):
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
    # Workspace roots may themselves be compatibility symlinks (macOS /var ->
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
    "grok-cursor": {"target": "grok", "harness": "cursor-agent", "intermediaries": ["cursor"], "default_model": "grok-4.7-xhigh", "restriction_posture": "adapter-enforced"},
    "opencode": {"target": "opencode", "harness": "opencode", "intermediaries": [], "default_model": "auto", "restriction_posture": "cooperative"},
}


def route_model_allowed(route: str, model: str) -> bool:
    if route == "opencode":
        return bool(re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*(?:#[A-Za-z0-9][A-Za-z0-9._-]*)?",
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
        return bool(re.fullmatch(r"(?:cursor-grok-[A-Za-z0-9._-]+|grok-4\.7-[A-Za-z0-9._-]+)", model))
    return False


EFFORT_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,31}")


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
    effort = egress.get("effort")
    if effort is not None and (not isinstance(effort, str) or not EFFORT_TOKEN.fullmatch(effort)):
        raise Operational(word, "egress effort must be a short plain token")
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
    authorization = {
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
    # Present only when requested, so an unset run keeps the original key set.
    if egress.get("effort") is not None:
        authorization["effort_requested"] = egress["effort"]
    return authorization


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
        scratch = os.path.realpath(os.path.join(info["toplevel"], ".tmp"))
        inside = os.path.commonpath([info["toplevel"], prompt_abs]) == info["toplevel"]
        in_scratch = inside and os.path.commonpath([scratch, prompt_abs]) == scratch
        if inside and not in_scratch:
            raise Operational("REFUSED", "prompt brief must be under the workspace .tmp scratch or outside the workspace")
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
                existing["repository"].get("workspace_name") != info["workspace_name"]
                or existing["repository"].get("toplevel") != info["toplevel"]
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
        "repository": {"toplevel": info["toplevel"], "workspace_name": info["workspace_name"]},
        "bookmark": {"name": info["bookmark"], "initial_commit_id": info["head"]},
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
    return set(changed_name_only(repo))


def reconcile_plan_checkpoint(repo: str, doc: dict, info: dict, plan_rel: str) -> dict | None:
    """Recover the controller's plan change when its manifest receipt was interrupted."""
    prior = doc.get("bookmark", {}).get("initial_commit_id")
    commit = info["head"]
    if commit == prior:
        return None
    parents = log_template(repo, commit, 'parents.map(|c| c.commit_id()).join(" ")').split()
    changed = set(changed_name_only(repo, rev=commit))
    message = log_template(repo, commit, "description").rstrip("\n")
    plan_bytes = file_bytes_at(repo, commit, plan_rel)
    if (
        not _valid_commit_id(prior)
        or parents != [prior]
        or changed != {plan_rel}
        or message != doc["plan"].get("checkpoint_message")
        or digest_bytes(plan_bytes) != doc["plan"]["digest"]
    ):
        raise Operational(
            "BLOCKED",
            "canonical working copy advanced without a recorded matching plan checkpoint",
            {"expected_prior_head": prior, "head": commit},
        )
    return {
        "prior_head": prior,
        "commit": commit,
        "change_id": log_template(repo, commit, "change_id"),
        "path": plan_rel,
        "digest": doc["plan"]["digest"],
        "at": now_iso(),
    }


def cmd_checkpoint_plan(args) -> tuple[str, dict]:
    # Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
    # The host inspects history with jj log; runtime project instructions and
    # history syntax override Go guidance. This command accepts that message.
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
        message = getattr(args, "commit_message", None)
        if not isinstance(message, str) or not message.strip() or "\0" in message:
            raise Operational("REFUSED", "plan checkpoint requires --commit-message composed from runtime project standards")
        prior = working_copy(repo)["parent"]
        if not prior:
            raise Operational("BLOCKED", "plan checkpoint requires a single working-copy parent")
        bookmark = info["bookmark"]
    with locked_manifest(args.run_id, write=True) as doc:
        doc["plan"]["checkpoint_message"] = message
        doc["bookmark"]["initial_commit_id"] = prior
    if status_paths(repo) != {plan_rel}:
        raise Operational("BLOCKED", "working-copy paths are not exactly the selected plan")
    # A failed checkpoint must preserve the selected plan, including its edits.
    commit = finish_working_copy(repo, message, bookmark)
    test_fault("checkpoint-plan-after-commit")
    if status_paths(repo):
        raise Operational("BLOCKED", "checkpoint committed but canonical workspace is not clean")
    cp = {
        "prior_head": prior,
        "commit": commit,
        "change_id": log_template(repo, commit, "change_id"),
        "path": plan_rel,
        "digest": doc["plan"]["digest"],
        "at": now_iso(),
    }
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        doc["plan"]["checkpoint"] = cp
        event(doc, "plan-checkpoint", detail={"commit": commit, "path": plan_rel})
    return "CHECKPOINTED", {"checkpoint": cp}


@contextlib.contextmanager
def admin_lock(workspace_root: str):
    root = ensure_root()
    key = digest_bytes(os.path.realpath(workspace_root).encode())
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


def validate_canonical_membership(doc: dict, workspace: str) -> None:
    """Prove the workspace resolves the canonical member, even after forget."""
    repo = doc["repository"]["toplevel"]
    if os.path.realpath(jj_text(workspace, "workspace", "root")) != os.path.realpath(workspace):
        raise Operational("BLOCKED", "unit path is not a workspace root")
    canonical_name = doc["repository"]["workspace_name"]
    if not any(row["name"] == canonical_name for row in workspace_rows(workspace)):
        raise Operational("BLOCKED", "unit workspace does not list the canonical workspace")
    if os.path.realpath(workspace_root_named(workspace, canonical_name)) != os.path.realpath(repo):
        raise Operational("BLOCKED", "unit workspace does not resolve the canonical workspace")


def validate_workspace(doc: dict, unit: dict) -> dict:
    repo = doc["repository"]["toplevel"]
    workspace = unit["workspace"]["path"]
    name = unit["workspace"].get("name")
    owned = os.path.join(run_dir(doc["run_id"]), "units", unit["unit_id"])
    if os.path.commonpath([os.path.realpath(workspace), os.path.realpath(owned)]) != os.path.realpath(owned):
        raise Operational("BLOCKED", "workspace escaped its owned unit directory")
    validate_private_dir(workspace)
    if not isinstance(name, str) or not name:
        raise Operational("BLOCKED", "unit workspace has no recorded name")
    listed = [row for row in workspace_rows(repo) if row["name"] == name]
    if len(listed) != 1:
        raise Operational("BLOCKED", "workspace is not registered exactly once")
    named = os.path.realpath(workspace_root_named(repo, name))
    if named != os.path.realpath(workspace):
        raise Operational("BLOCKED", "unit workspace is not a member of the canonical repo")
    # A registered path can have been replaced by another workspace. Prove
    # membership from both ends through the public CLI, not admin-file identity.
    if workspace_name_for_root(workspace) != name:
        raise Operational("BLOCKED", "unit workspace membership changed")
    validate_canonical_membership(doc, workspace)
    return listed[0]


def validate_pristine_unit_base(doc: dict, unit: dict) -> dict:
    row = validate_workspace(doc, unit)
    workspace = unit["workspace"]["path"]
    base = unit["workspace"]["base"]
    wc = working_copy(workspace)
    if wc["parent"] != base or not wc["empty"] or status_paths(workspace):
        raise Operational("BLOCKED", "unit workspace is not an empty change on the recorded base")
    return row
