"""Private, crash-recoverable workspace controller for ce-work external units.

The generic peer-job runner owns process supervision. This controller owns the
repository-specific transaction: one private run manifest, isolated sibling
workspaces, pinned revisions, canonical integration evidence, exact restoration,
retention, and explicit cleanup. It never launches an external authoring CLI or
publishes a worker's output directly.

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


SCHEMA_VERSION = 2
_uid_getter = getattr(os, "geteuid", None) or getattr(os, "getuid", None)
_EFFECTIVE_UID = _uid_getter() if _uid_getter is not None else None
OWNER_SCRATCH_ROOT = None
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_PACKET_BYTES = 200_000
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
TERMINAL_PROCESS = {"done", "failed", "timeout", "died-without-result"}
TERMINAL_FAILURE = TERMINAL_PROCESS - {"done"}
INTEGRATABLE_STATES = {"integration-pending", "integrated", "verified"}
UNIT_STATES = {
    "queued", "authoring", "authored", "integration-pending", "integrated",
    "restoring", "verified", "accepted", "preserved", "cleaned", "native-completed",
}
VCS_LOCAL_ENV_VARS = frozenset({
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CONFIG",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS",
    "GIT_DIR",
    "GIT_GRAFT_FILE",
    "GIT_IMPLICIT_WORK_TREE",
    "GIT_INDEX_FILE",
    # Older backing-repository clients exported this local variable. Scrub it
    # so an inherited value cannot leak into unit verification.
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


def _private_root_usable(path: str) -> bool:
    """True when `path` is (or can now be) a directory we own and can write into.

    Creation is the probe; a pre-existing root must still pass ownership and
    writability checks.
    """
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


def _workspace_scratch_root() -> str:
    probe = subprocess.run(["jj", "workspace", "root"], capture_output=True, text=True, check=False)
    root = probe.stdout.strip() if probe.returncode == 0 else os.getcwd()
    return os.path.join(os.path.realpath(root), ".tmp", "rocketclaw")


def owner_scratch_root() -> str:
    """The owner-private scratch root, in the same candidate order as the skills' shell preamble."""
    root = _workspace_scratch_root()
    os.makedirs(root, mode=0o700, exist_ok=True)
    return root


def workspace_tmp_path(path: str, label: str) -> str:
    absolute = os.path.abspath(path)
    allowed = os.path.join(os.path.realpath(jj_workspace_root()), ".tmp", "rocketclaw")
    if os.path.commonpath([allowed, absolute]) != allowed:
        raise Operational("REFUSED", f"{label} must stay under the active workspace's .tmp/rocketclaw directory")
    return absolute


def jj_workspace_root() -> str:
    probe = subprocess.run(["jj", "workspace", "root"], capture_output=True, text=True, check=False)
    return probe.stdout.strip() if probe.returncode == 0 and probe.stdout.strip() else os.getcwd()


def runs_root() -> str:
    configured = os.environ.get("CE_WORK_RUNS_ROOT")
    if configured:
        return workspace_tmp_path(configured, "CE_WORK_RUNS_ROOT")
    peer_root = os.environ.get("CE_PEER_JOBS_ROOT")
    if peer_root:
        return os.path.join(workspace_tmp_path(peer_root, "CE_PEER_JOBS_ROOT"), "ce-work")
    return os.path.join(owner_scratch_root(), "ce-work")


def safe_id(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value) or not value.strip("."):
        raise Operational("REFUSED", f"unsafe {label}: {value!r}")
    return value


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def valid_commit_id(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        raw = bytes.fromhex(value)
    except ValueError:
        return False
    return len(raw) in {20, 32} and raw.hex() == value


def _native_completion_revision(unit: dict) -> str | None:
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
    accepted_revision = completion.get("accepted_revision")
    base = unit.get("workspace", {}).get("base")
    snapshot = completion.get("snapshot")
    wave = unit.get("wave", {})
    changed_paths = completion.get("changed_paths")
    if not (
        valid_commit_id(accepted_revision)
        and valid_commit_id(base)
        and completion.get("base") == base
        and isinstance(completion.get("at"), str)
        and bool(completion["at"])
        and isinstance(completion.get("summary"), str)
        and bool(completion["summary"])
        and isinstance(completion.get("evidence_digest"), str)
        and len(completion["evidence_digest"]) == 64
        and valid_commit_id(completion["evidence_digest"])
        and isinstance(snapshot, dict)
        and snapshot.get("commit_id") == accepted_revision
        and snapshot.get("empty") is True
        and (
            not wave.get("id")
            or (
                valid_commit_id(claim.get("canonical_revision"))
                and isinstance(changed_paths, list)
                and all(isinstance(path, str) for path in changed_paths)
            )
        )
    ):
        return None
    return accepted_revision


def unit_accepted_revision(unit: dict) -> str | None:
    if unit.get("state") == "native-completed":
        return _native_completion_revision(unit)
    if unit.get("state") not in {"accepted", "cleaned"}:
        return None
    integration = unit.get("integration")
    if not isinstance(integration, dict):
        return None
    canonical = integration.get("canonical_revision")
    if not (
        isinstance(canonical, dict)
        and valid_commit_id(canonical.get("commit_id"))
        and isinstance(canonical.get("parent_commit_ids"), list)
        and all(valid_commit_id(parent) for parent in canonical["parent_commit_ids"])
        and isinstance(canonical.get("change_id"), str)
        and bool(canonical["change_id"])
        and isinstance(canonical.get("at"), str)
        and bool(canonical["at"])
    ):
        return None
    return canonical["commit_id"]


def unit_ready_for_run_verification(unit: object) -> bool:
    return isinstance(unit, dict) and unit_accepted_revision(unit) is not None


def accepted_unit_revision_snapshot(units: object) -> dict[str, str] | None:
    if not isinstance(units, dict):
        return None
    snapshot: dict[str, str] = {}
    for unit_id in sorted(units):
        if not isinstance(unit_id, str) or not SAFE_ID.fullmatch(unit_id):
            return None
        unit = units[unit_id]
        if not isinstance(unit, dict):
            return None
        revision = unit_accepted_revision(unit)
        if revision is None:
            return None
        snapshot[unit_id] = revision
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
    for candidate in (_workspace_scratch_root(),):
        owner_root = os.path.abspath(candidate)
        try:
            if os.path.commonpath([owner_root, os.path.abspath(root)]) == owner_root:
                return owner_root
        except ValueError:  # different drives on Windows: not under this candidate
            continue
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
    tmp = os.path.join(parent, f".manifest-{secrets.token_hex(12)}")
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
    """Every workspace-local root an existing run may live under."""
    configured = os.environ.get("CE_WORK_RUNS_ROOT")
    if configured:
        return [workspace_tmp_path(configured, "CE_WORK_RUNS_ROOT")]
    peer_root = os.environ.get("CE_PEER_JOBS_ROOT")
    if peer_root:
        return [os.path.join(workspace_tmp_path(peer_root, "CE_PEER_JOBS_ROOT"), "ce-work")]
    return [os.path.join(os.path.abspath(_workspace_scratch_root()), "ce-work")]


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


def sanitized_vcs_environment(overrides: dict | None = None) -> dict[str, str]:
    process_env = {key: value for key, value in os.environ.items() if key not in VCS_LOCAL_ENV_VARS}
    process_env.update(overrides or {})
    return process_env


def jj(repo: str, *args: str, input_data: bytes | None = None, check: bool = True, env: dict | None = None) -> bytes:
    proc = subprocess.run(
        ["jj", "-R", repo, *args], input=input_data, capture_output=True,
        env=sanitized_vcs_environment(env), check=False,
    )
    if check and proc.returncode != 0:
        message = proc.stderr.decode("utf-8", "replace").strip()
        raise Operational("BLOCKED", f"jj {' '.join(args)} failed: {message}")
    return proc.stdout


def jj_text(repo: str, *args: str, check: bool = True) -> str:
    return jj(repo, *args, check=check).decode("utf-8", "surrogateescape").strip()


def revision_info(repo: str, revision: str = "@") -> dict:
    template = 'change_id ++ "\\t" ++ commit_id ++ "\\t" ++ parents.map(|p| p.commit_id()).join(",") ++ "\\t" ++ conflict ++ "\\t" ++ description.escape_json() ++ "\\n"'
    rows = jj_text(repo, "log", "-r", revision, "--no-graph", "-T", template).splitlines()
    if len(rows) != 1:
        raise Operational("BLOCKED", f"revision {revision!r} did not resolve to exactly one change")
    fields = rows[0].split("\t")
    if len(fields) != 5:
        raise TrustFailure("Jujutsu revision metadata has an unexpected shape")
    change_id, commit_id, parents, conflict, description_json = fields
    return {
        "change_id": change_id,
        "commit_id": commit_id,
        "parent_commit_ids": list(filter(None, parents.split(","))),
        "conflicted": conflict == "true",
        "description": json.loads(description_json),
    }


def revision_is_ancestor(repo: str, ancestor: str, descendant: str) -> bool:
    resolved = jj_text(repo, "log", "-r", f"({ancestor}) & ::({descendant})", "--no-graph", "-T", 'commit_id ++ "\\n"', check=False)
    return resolved == revision_info(repo, ancestor)["commit_id"]


def describe_change(repo: str, description: str, revision: str = "@") -> dict:
    if not description.strip() or "\0" in description or len(description.encode()) > 65536:
        raise Operational("REFUSED", "change description must be non-empty, contain no NUL, and be at most 65536 bytes. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Use the repository's current local syntax; do not impose a fixed type, scope, prefix, footer, or body template.")
    jj(repo, "describe", "-r", revision, "-m", description.rstrip())
    return revision_info(repo, revision)


def repo_info(repo: str) -> dict:
    repo = os.path.realpath(repo)
    top = os.path.realpath(jj_text(repo, "workspace", "root"))
    if top != repo:
        repo = top
    workspace_rows = jj_text(repo, "workspace", "list", "-T", 'name ++ "\\t" ++ target.change_id() ++ "\\n"').splitlines()
    current_revision = revision_info(repo)
    matches = [row.split("\t", 1)[0] for row in workspace_rows if row.endswith("\t" + current_revision["change_id"])]
    if len(matches) != 1:
        raise Operational("BLOCKED", "current Jujutsu workspace could not be identified uniquely")
    workspace = matches[0]
    common = os.path.realpath(os.path.join(top, ".jj", "repo"))
    if not os.path.isdir(common):
        raise Operational("BLOCKED", "shared Jujutsu repository store is unavailable")
    st = os.stat(common)
    roots = [jj_text(repo, "log", "-r", "root()", "--no-graph", "-T", "commit_id")]
    identity = digest_bytes((common + f"\0{st.st_dev}\0{st.st_ino}\0" + "\n".join(roots)).encode())
    return {
        "toplevel": repo,
        "common_dir": common,
        "common_dev": st.st_dev,
        "common_ino": st.st_ino,
        "identity_digest": identity,
        "workspace_name": workspace,
        **current_revision,
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
    for key in ("toplevel", "common_dir", "common_dev", "common_ino", "identity_digest"):
        if current[key] != recorded[key]:
            raise Operational("BLOCKED", f"canonical repository identity changed ({key})")
    if current["workspace_name"] != doc["workspace"]["name"]:
        raise Operational("BLOCKED", "canonical workspace changed")
    return current


def resolve_plan(repo: str, plan: str) -> tuple[str, str]:
    supplied = os.path.abspath(plan if os.path.isabs(plan) else os.path.join(repo, plan))
    try:
        st = os.lstat(supplied)
    except OSError as exc:
        raise Operational("REFUSED", f"selected plan is missing: {exc}") from exc
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise Operational("REFUSED", "selected plan must be one regular non-symlink file")
    # Reject a symlink at the selected file, then compare its resolved path
    # against the already-resolved canonical repository.
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
        return model == "auto" or bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9._-]+(#[A-Za-z0-9._-]+)?", model))
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
        "repository": {k: info[k] for k in ("toplevel", "common_dir", "common_dev", "common_ino", "identity_digest")},
        "workspace": {
            "name": info["workspace_name"],
            "initial_change_id": info["change_id"],
            "initial_commit_id": info["commit_id"],
        },
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
    raw = jj(repo, "diff", "-r", "@", "--name-only")
    return set(filter(None, raw.decode("utf-8", "surrogateescape").splitlines()))


def root_file_filesets(paths: list[str] | set[str]) -> list[str]:
    filesets = []
    for path in paths:
        if not isinstance(path, str) or not path or "\0" in path:
            raise TrustFailure("recorded changed path is malformed")
        filesets.append("root-file:" + json.dumps(path, ensure_ascii=False))
    return filesets


def reconcile_plan_checkpoint(repo: str, doc: dict, info: dict, plan_rel: str) -> dict | None:
    return None


def cmd_checkpoint_plan(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        repo = info["toplevel"]
        plan = doc.get("plan")
        if not isinstance(plan, dict) or plan.get("kind", "plan") != "plan" or not plan.get("path"):
            dirty = status_paths(repo)
            if dirty:
                raise Operational("BLOCKED", "prompt-backed external execution requires a clean canonical checkout", {"dirty_paths": sorted(dirty)})
            return "NOOP", {"checkpoint": None, "revision": info["commit_id"], "source_kind": "prompt"}
        plan_rel = plan["path"]
        plan_abs, _ = resolve_plan(repo, plan_rel)
        if digest_bytes(Path(plan_abs).read_bytes()) != doc["plan"]["digest"]:
            raise Operational("BLOCKED", "selected plan content no longer matches recorded digest")
        dirty = status_paths(repo)
        if not dirty:
            checkpoint = doc["plan"].get("checkpoint")
            if checkpoint is not None:
                return "NOOP", {"checkpoint": checkpoint, "revision": info["commit_id"]}
            checkpoint = reconcile_plan_checkpoint(repo, doc, info, plan_rel)
            if checkpoint is None:
                return "NOOP", {"checkpoint": None, "revision": info["commit_id"]}
            doc["plan"]["checkpoint"] = checkpoint
            event(doc, "plan-checkpoint", detail={"revision": checkpoint["commit_id"], "path": plan_rel})
            return "CHECKPOINTED", {"checkpoint": checkpoint}
        if dirty != {plan_rel}:
            raise Operational("BLOCKED", "canonical dirt is not exactly the selected plan", {"dirty_paths": sorted(dirty)})
        prior = info["parent_commit_ids"]
    completed = describe_change(repo, args.description)
    test_fault("checkpoint-plan-after-describe")
    jj(repo, "new", completed["commit_id"])
    if status_paths(repo):
        raise Operational("BLOCKED", "plan checkpoint completed but the new canonical change is not empty")
    cp = {
        "prior_commit_ids": prior,
        "change_id": completed["change_id"],
        "commit_id": completed["commit_id"],
        "path": plan_rel,
        "digest": doc["plan"]["digest"],
        "at": now_iso(),
    }
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        doc["plan"]["checkpoint"] = cp
        event(doc, "plan-checkpoint", detail={"revision": completed["commit_id"], "path": plan_rel})
    return "CHECKPOINTED", {"checkpoint": cp}


@contextlib.contextmanager
def admin_lock(common_dir: str):
    root = ensure_root()
    key = digest_bytes(os.path.realpath(common_dir).encode())
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


def workspace_rows(repo: str) -> list[dict]:
    raw = jj_text(repo, "workspace", "list", "-T", 'name ++ "\\t" ++ target.change_id() ++ "\\t" ++ target.commit_id() ++ "\\n"')
    rows = []
    for line in raw.splitlines():
        name, change_id, commit_id = line.split("\t")
        rows.append({"name": name, "change_id": change_id, "commit_id": commit_id})
    return rows


def validate_workspace(doc: dict, unit: dict) -> dict:
    repo = doc["repository"]["toplevel"]
    workspace = unit["workspace"]["path"]
    owned = os.path.join(run_dir(doc["run_id"]), "units", unit["unit_id"])
    if os.path.commonpath([os.path.realpath(workspace), os.path.realpath(owned)]) != os.path.realpath(owned):
        raise Operational("BLOCKED", "workspace escaped its owned unit directory")
    validate_private_dir(workspace)
    matches = [r for r in workspace_rows(repo) if r["name"] == unit["workspace"]["name"]]
    if len(matches) != 1:
        raise Operational("BLOCKED", "workspace is not registered exactly once")
    current = revision_info(workspace)
    if current["change_id"] != matches[0]["change_id"] or current["commit_id"] != matches[0]["commit_id"]:
        raise Operational("BLOCKED", "recorded workspace path does not match its registered working-copy change")
    common = os.path.realpath(os.path.join(jj_text(workspace, "workspace", "root"), ".jj", "repo"))
    if common != doc["repository"]["common_dir"]:
        raise Operational("BLOCKED", "unit workspace belongs to another repository")
    return matches[0]


def validate_pristine_unit_base(doc: dict, unit: dict) -> dict:
    row = validate_workspace(doc, unit)
    workspace = unit["workspace"]["path"]
    base = unit["workspace"]["base"]
    current = revision_info(workspace)
    if current["parent_commit_ids"] != [base]:
        raise Operational("BLOCKED", "unit workspace no longer has the recorded base as its sole parent")
    dirty = status_paths(workspace)
    if dirty:
        raise Operational(
            "BLOCKED",
            "unit workspace is dirty before dispatch authorization",
            {"dirty_paths": sorted(dirty)},
        )
    return row
