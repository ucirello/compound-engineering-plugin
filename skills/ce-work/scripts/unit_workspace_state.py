"""Private, crash-recoverable Jujutsu workspace controller state.

The detached runner owns process supervision. This module owns durable manifests,
workspace identity, route authorization, private workspace-local storage, and
Jujutsu revision evidence. Every successful command prints one status word and
one compact JSON document through the CLI entrypoint.
"""

from __future__ import annotations

import argparse
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
import time
from pathlib import Path


SCHEMA_VERSION = 2
DESCRIPTION_GUIDANCE = (
    "The exact sentence 'Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, "
    "compose commit messages adherent to the present standards.' is non-operational compatibility wording, not an instruction to "
    "inspect Git history. For Jujutsu descriptions, the user's current instruction wins, followed by active project instructions "
    "and syntax observed in the current `jj log`. Compatible Go guidance may improve only quality, clarity, and structure; it "
    "does not impose a fixed prefix, type, scope, subject, body, layout, template, or example."
)
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
_uid_getter = getattr(os, "geteuid", None) or getattr(os, "getuid", None)
_EFFECTIVE_UID = _uid_getter() if _uid_getter is not None else None


def _environment(name: str) -> str | None:
    value = os.environ.get(name)
    if value is not None or not name.startswith("ROCKETCLAW_"):
        return value
    legacy = f"{chr(67)}{chr(69)}_{name[len('ROCKETCLAW_'):]}"
    return os.environ.get(legacy)


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
    configured = {value.strip() for value in (_environment("ROCKETCLAW_WORK_TEST_FAULT") or "").split(",") if value.strip()}
    if point in configured:
        raise Operational("INTERRUPTED", f"injected interruption at {point}")


def safe_id(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value) or not value.strip("."):
        raise Operational("REFUSED", f"unsafe {label}: {value!r}")
    return value


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
        current = os.fstat(fd)
        if not stat.S_ISDIR(current.st_mode):
            raise TrustFailure(f"not a real directory: {path}")
        if _euid() is not None and current.st_uid != _euid():
            raise TrustFailure(f"directory is not owned by current user: {path}")
        if os.name != "nt" and _mode(current) != 0o700:
            raise TrustFailure(f"directory mode is {_mode(current):04o}, expected 0700: {path}")
    finally:
        os.close(fd)


def ensure_private_dir(path: str) -> None:
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        pass
    validate_private_dir(path)


def read_private(path: str, cap: int = MAX_JSON_BYTES) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open state file {path}: {exc}") from exc
    try:
        current = os.fstat(fd)
        if not stat.S_ISREG(current.st_mode):
            raise TrustFailure(f"state is not a regular file: {path}")
        if _euid() is not None and current.st_uid != _euid():
            raise TrustFailure(f"state is not owned by current user: {path}")
        if os.name != "nt" and _mode(current) != 0o600:
            raise TrustFailure(f"state mode is {_mode(current):04o}, expected 0600: {path}")
        if current.st_size > cap:
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
    try:
        fd = os.open(path, os.O_RDONLY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open state file {path}: {exc}") from exc
    try:
        current = os.fstat(fd)
        if not stat.S_ISREG(current.st_mode):
            raise TrustFailure(f"state is not a regular file: {path}")
        if _euid() is not None and current.st_uid != _euid():
            raise TrustFailure(f"state is not owned by current user: {path}")
        if os.name != "nt" and _mode(current) != 0o600:
            raise TrustFailure(f"state mode is {_mode(current):04o}, expected 0600: {path}")
        return current
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


def _reserve_atomic(parent: str, prefix: str) -> tuple[int, str]:
    for _ in range(128):
        path = os.path.join(parent, f".{prefix}-{os.getpid()}-{secrets.token_hex(8)}")
        try:
            return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600), path
        except FileExistsError:
            continue
    raise Operational("BLOCKED", "could not reserve an atomic workspace-local state file")


def atomic_private_json(path: str, doc: dict) -> None:
    data = (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_JSON_BYTES:
        raise Operational("BLOCKED", "manifest exceeds bounded state size")
    parent = os.path.dirname(path)
    fd, temporary = _reserve_atomic(parent, "manifest")
    try:
        with os.fdopen(fd, "wb", closefd=True) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(parent, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temporary)
        raise


def sanitized_process_environment(overrides: dict | None = None) -> dict[str, str]:
    process_env = dict(os.environ)
    process_env.update(overrides or {})
    return process_env


def jj(repo: str, *args: str, input_data: bytes | None = None, check: bool = True, env: dict | None = None) -> bytes:
    proc = subprocess.run(
        ["jj", "--config", "snapshot.auto-track='all() ~ glob:\".tmp/**\"'", "-R", repo, *args], input=input_data, capture_output=True,
        env=sanitized_process_environment(env), check=False,
    )
    if check and proc.returncode != 0:
        message = proc.stderr.decode("utf-8", "replace").strip()
        raise Operational("BLOCKED", f"jj {' '.join(args)} failed: {message}")
    return proc.stdout


def jj_text(repo: str, *args: str, check: bool = True) -> str:
    return jj(repo, *args, check=check).decode("utf-8", "surrogateescape").strip()


def workspace_root(path: str, check: bool = True) -> str:
    try:
        out = jj_text(path, "workspace", "root", check=check)
    except Operational:
        if check:
            raise
        return ""
    return os.path.realpath(out) if out else ""


def storage_boundary(repo: str | None = None) -> str:
    probe = os.path.realpath(repo or os.getcwd())
    base = workspace_root(probe, check=False) or os.path.realpath(os.getcwd())
    boundary = os.path.join(base, ".tmp")
    if os.path.lexists(boundary):
        current = os.lstat(boundary)
        if not stat.S_ISDIR(current.st_mode) or stat.S_ISLNK(current.st_mode):
            raise TrustFailure("workspace-local .tmp must be a real directory")
        if _euid() is not None and current.st_uid != _euid():
            raise TrustFailure("workspace-local .tmp is not owned by the current user")
    return boundary


def validated_storage_override(path: str, label: str, repo: str | None = None) -> str:
    boundary = storage_boundary(repo)
    resolved = os.path.realpath(os.path.abspath(path))
    try:
        inside = os.path.commonpath([boundary, resolved]) == boundary and resolved != boundary
    except ValueError:
        inside = False
    if not inside:
        raise Operational("BLOCKED", f"{label} must resolve inside {boundary}")
    return resolved


def require_path_within(path: str, boundary: str, label: str) -> str:
    resolved = os.path.realpath(os.path.abspath(path))
    boundary = os.path.realpath(boundary)
    try:
        inside = os.path.commonpath([boundary, resolved]) == boundary and resolved != boundary
    except ValueError:
        inside = False
    if not inside:
        raise Operational("REFUSED", f"{label} must resolve inside {boundary}")
    return resolved


def local_storage_root(repo: str | None = None) -> str:
    configured = os.environ.get("ROCKETCLAW_WORK_RUNS_ROOT") or os.environ.get("CE_WORK_RUNS_ROOT")
    if configured:
        return validated_storage_override(configured, "work runs root", repo)
    peer_root = os.environ.get("ROCKETCLAW_PEER_JOBS_ROOT") or os.environ.get("CE_PEER_JOBS_ROOT")
    if peer_root:
        root = validated_storage_override(peer_root, "peer jobs root", repo)
        return os.path.join(root, "ce-work")
    local_tmp = storage_boundary(repo)
    try:
        os.mkdir(local_tmp, 0o700)
    except FileExistsError:
        pass
    current = os.lstat(local_tmp)
    if not stat.S_ISDIR(current.st_mode) or stat.S_ISLNK(current.st_mode) or (_euid() is not None and current.st_uid != _euid()):
        raise TrustFailure("workspace-local .tmp is not an owner-controlled directory")
    private_root = os.path.join(local_tmp, "rocketclaw")
    ensure_private_dir(private_root)
    return os.path.join(private_root, "ce-work")


def runs_root(repo: str | None = None) -> str:
    return local_storage_root(repo)


def candidate_runs_roots(repo: str | None = None) -> list[str]:
    return [runs_root(repo)]


def ensure_runs_root(root: str) -> str:
    parent = os.path.dirname(root)
    os.makedirs(parent, mode=0o700, exist_ok=True)
    if os.name != "nt":
        with contextlib.suppress(OSError):
            os.chmod(parent, 0o700)
    ensure_private_dir(root)
    ensure_private_dir(os.path.join(root, ".locks"))
    return root


def ensure_root(repo: str | None = None) -> str:
    return ensure_runs_root(runs_root(repo))


def run_dir(run_id: str, repo: str | None = None) -> str:
    rid = safe_id(run_id, "run id")
    root = runs_root(repo)
    return os.path.join(root, rid)


def _v1_migration_blocker(message: str) -> Operational:
    return Operational(
        "BLOCKED",
        f"v1 manifest cannot be proven equivalent to Jujutsu state: {message}; preserved without migration or redispatch",
    )


def _migrate_v1_manifest(doc: dict, rd: str) -> dict:
    """Migrate only a pristine v1 run with an exact current Jujutsu projection."""
    if doc.get("schema_version") != 1:
        raise TrustFailure("manifest schema is unsupported")
    revision = doc.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise _v1_migration_blocker("the manifest revision is malformed")
    if doc.get("units") != {}:
        raise _v1_migration_blocker("the run contains unit state")
    for key in ("integration_lock",):
        if doc.get(key) is not None:
            raise _v1_migration_blocker(f"{key} is active")
    for key in ("verification_attempts", "verifications"):
        if doc.get(key, []) != []:
            raise _v1_migration_blocker(f"{key} is not empty")
    plan = doc.get("plan")
    if not isinstance(plan, dict) or plan.get("checkpoint") is not None:
        raise _v1_migration_blocker("the plan checkpoint is absent or already mutated")
    for child in ("units", "jobs"):
        path = os.path.join(rd, child)
        validate_private_dir(path)
        with os.scandir(path) as entries:
            if next(entries, None) is not None:
                raise _v1_migration_blocker(f"the {child} directory is not empty")

    recorded = doc.get("repository")
    branch = doc.get("branch")
    if not isinstance(recorded, dict) or not isinstance(branch, dict):
        raise _v1_migration_blocker("repository identity is malformed")
    top = recorded.get("toplevel")
    initial_head = branch.get("initial_head")
    if not isinstance(top, str) or not isinstance(initial_head, str) or not re.fullmatch(r"[0-9a-f]{40,128}", initial_head):
        raise _v1_migration_blocker("the recorded Git root or initial revision is malformed")
    top = os.path.realpath(top)
    common = recorded.get("common_dir")
    try:
        common_stat = os.stat(common) if isinstance(common, str) else None
    except OSError as exc:
        raise _v1_migration_blocker(f"the recorded Git identity is unavailable ({exc})") from exc
    if (
        common_stat is None
        or common_stat.st_dev != recorded.get("common_dev")
        or common_stat.st_ino != recorded.get("common_ino")
    ):
        raise _v1_migration_blocker("the recorded Git identity changed")

    try:
        info = repo_info(top)
        initial_commit = resolve_revision(top, initial_head)
        current = revision_snapshot(top)
        current_paths = changed_paths(top)
        conflicted = has_conflicts(top)
    except Operational as exc:
        raise _v1_migration_blocker(str(exc)) from exc
    if initial_commit != initial_head or current_paths or conflicted:
        raise _v1_migration_blocker("the canonical Jujutsu working copy is not pristine")
    if current["commit"] != initial_head and current["parents"] != [initial_head]:
        raise _v1_migration_blocker("the current Jujutsu revision does not project the recorded Git HEAD")

    source = doc.get("source")
    if source is None:
        source = {
            "kind": plan.get("kind", "plan"),
            "storage": "repository",
            "path": plan.get("path"),
            "digest": plan.get("digest"),
        }
    if not isinstance(source, dict) or source.get("kind") not in {"plan", "prompt"}:
        raise _v1_migration_blocker("the source record is malformed")
    if not isinstance(source.get("digest"), str) or not re.fullmatch(r"[0-9a-f]{64}", source["digest"]):
        raise _v1_migration_blocker("the source digest is malformed")
    if source.get("kind") == "prompt":
        if source.get("storage") != "run" or source.get("path") != "source/bare-prompt.md":
            raise _v1_migration_blocker("the prompt source location is malformed")
        if digest_bytes(read_private(os.path.join(rd, source["path"]), MAX_PACKET_BYTES)) != source["digest"]:
            raise _v1_migration_blocker("the prompt source digest changed")
    elif source.get("storage") != "repository" or not isinstance(source.get("path"), str):
        raise _v1_migration_blocker("the plan source location is malformed")
    else:
        try:
            source_path, _ = resolve_plan(top, source["path"])
            source_digest = digest_bytes(Path(source_path).read_bytes())
        except (OSError, Operational) as exc:
            raise _v1_migration_blocker(f"the plan source cannot be verified ({exc})") from exc
        if source_digest != source["digest"]:
            raise _v1_migration_blocker("the plan source digest changed")
    try:
        fixed_route_contract(doc.get("binding"), doc.get("egress"))
    except Operational as exc:
        raise _v1_migration_blocker(str(exc)) from exc

    migrated = json.loads(json.dumps(doc))
    migrated["schema_version"] = SCHEMA_VERSION
    migrated["revision"] = revision + 1
    migrated["updated_at"] = now_iso()
    migrated["repository"] = {
        key: info[key] for key in ("toplevel", "workspace", "jj_dir", "jj_dev", "jj_ino", "identity_digest")
    }
    migrated["canonical"] = {
        "initial_change": current["change_id"],
        "initial_commit": current["commit"],
        "initial_operation": info["operation"],
    }
    migrated["source"] = source
    migrated["plan"] = {
        "kind": source["kind"],
        "path": source.get("path") if source["kind"] == "plan" else None,
        "digest": source["digest"],
        "checkpoint": None,
    }
    migrated.pop("branch", None)
    event(migrated, "manifest-migrated", detail={"from_schema": 1, "to_schema": SCHEMA_VERSION, "storage_root": rd})
    return migrated


@contextlib.contextmanager
def locked_manifest(run_id: str, write: bool = False, directory: str | None = None):
    run_id = safe_id(run_id, "run id")
    rd = os.path.abspath(directory) if directory else locate_run_dir(run_id)
    ensure_runs_root(os.path.dirname(rd))
    validate_private_dir(rd)
    lock_path = os.path.join(rd, "manifest.lock")
    try:
        fd = os.open(lock_path, os.O_RDWR | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open manifest lock: {exc}") from exc
    try:
        current = os.fstat(fd)
        if not stat.S_ISREG(current.st_mode) or (_euid() is not None and current.st_uid != _euid()):
            raise TrustFailure("manifest lock owner or type validation failed")
        # An exclusive lock lets a first v2 reader migrate one provably pristine
        # v1 manifest atomically before exposing it to any command.
        fcntl.flock(fd, fcntl.LOCK_EX)
        manifest_path = os.path.join(rd, "manifest.json")
        doc = read_private_json(manifest_path)
        if doc.get("run_id") != run_id:
            raise TrustFailure("manifest run identity mismatch")
        if doc.get("schema_version") == 1:
            try:
                doc = _migrate_v1_manifest(doc, rd)
            except TrustFailure as exc:
                raise _v1_migration_blocker(str(exc)) from exc
            atomic_private_json(manifest_path, doc)
        elif doc.get("schema_version") != SCHEMA_VERSION:
            raise TrustFailure("manifest schema is unsupported")
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


def locate_run_dir(run_id: str, repo: str | None = None) -> str:
    rid = safe_id(run_id, "run id")
    return os.path.join(runs_root(repo), rid)


def _single_revision_value(repo: str, revision: str, template: str) -> str:
    return jj_text(repo, "log", "-r", revision, "--no-graph", "-T", template)


def resolve_revision(repo: str, revision: str) -> str:
    value = _single_revision_value(repo, revision, 'commit_id ++ "\\n"')
    rows = [row for row in value.splitlines() if row]
    if len(rows) != 1:
        raise Operational("BLOCKED", f"revision must resolve to one commit: {revision}")
    return rows[0]


def revision_snapshot(repo: str, revision: str = "@") -> dict:
    raw = _single_revision_value(
        repo,
        revision,
        'change_id ++ "\\0" ++ commit_id ++ "\\0" ++ parents.map(|p| p.commit_id()).join(" ") ++ "\\0" ++ description ++ "\\0"',
    )
    parts = raw.split("\0")
    if len(parts) < 4 or not parts[0] or not parts[1]:
        raise Operational("BLOCKED", f"could not read revision snapshot: {revision}")
    return {
        "change_id": parts[0],
        "commit": parts[1],
        "parents": [value for value in parts[2].split() if value],
        "description": parts[3].rstrip("\n"),
    }


def operation_id(repo: str) -> str:
    return jj_text(repo, "op", "log", "-n", "1", "--no-graph", "-T", 'id ++ "\\n"')


def changed_paths(repo: str, revision: str = "@") -> list[str]:
    raw = jj(repo, "diff", "-r", revision, "-T", 'path ++ "\\0"')
    return sorted({part.decode("utf-8", "surrogateescape") for part in raw.split(b"\0") if part})


def status_paths(repo: str) -> set[str]:
    jj(repo, "status")
    return set(changed_paths(repo, "@"))


def has_conflicts(repo: str, revision: str = "@") -> bool:
    return jj_text(repo, "log", "-r", f"{revision} & conflicts()", "--count") != "0"


def is_ancestor(repo: str, ancestor: str, descendant: str) -> bool:
    return jj_text(repo, "log", "-r", f"{ancestor} & ::{descendant}", "--count", check=False) == "1"


def all_commit_ids(repo: str) -> set[str]:
    raw = jj_text(repo, "log", "-r", "all()", "--no-graph", "-T", 'commit_id ++ "\\n"')
    return {row for row in raw.splitlines() if row}


def workspace_rows(repo: str) -> list[dict]:
    raw = jj(repo, "workspace", "list", "-T", 'name ++ "\\0" ++ root ++ "\\0" ++ target.commit_id() ++ "\\0"')
    values = [part.decode("utf-8", "surrogateescape") for part in raw.split(b"\0") if part]
    if len(values) % 3:
        raise Operational("BLOCKED", "workspace list returned an unexpected shape")
    return [
        {"name": values[index], "path": os.path.realpath(values[index + 1]), "identity": values[index + 2]}
        for index in range(0, len(values), 3)
    ]


def current_workspace_name(repo: str) -> str:
    root = workspace_root(repo)
    matches = [row["name"] for row in workspace_rows(repo) if row["path"] == root]
    if len(matches) != 1:
        raise Operational("BLOCKED", "current Jujutsu workspace identity is ambiguous")
    return matches[0]


def repo_info(repo: str) -> dict:
    root = workspace_root(repo)
    jj_dir = os.path.join(root, ".jj")
    current = os.stat(jj_dir)
    snapshot = revision_snapshot(root)
    identity = digest_bytes(f"{root}\0{current.st_dev}\0{current.st_ino}".encode())
    return {
        "toplevel": root,
        "workspace": current_workspace_name(root),
        "jj_dir": os.path.realpath(jj_dir),
        "jj_dev": current.st_dev,
        "jj_ino": current.st_ino,
        "identity_digest": identity,
        "change_id": snapshot["change_id"],
        "commit": snapshot["commit"],
        "parents": snapshot["parents"],
        "operation": operation_id(root),
    }


def validate_source(doc: dict) -> None:
    source = doc.get("source")
    if not isinstance(source, dict):
        raise TrustFailure("manifest source record is malformed")
    kind = source.get("kind")
    if kind == "prompt":
        if source.get("storage") != "run" or source.get("path") != "source/bare-prompt.md":
            raise TrustFailure("prompt source location is malformed")
        data = read_private(os.path.join(locate_run_dir(doc["run_id"]), source["path"]), MAX_PACKET_BYTES)
        if digest_bytes(data) != source.get("digest"):
            raise TrustFailure("prompt source digest does not match private content")
    elif kind == "plan":
        if source.get("storage") != "repository" or not isinstance(source.get("path"), str):
            raise TrustFailure("plan source location is malformed")
    else:
        raise TrustFailure("manifest source kind is invalid")
    if not isinstance(source.get("digest"), str) or not re.fullmatch(r"[0-9a-f]{64}", source["digest"]):
        raise TrustFailure("source digest is malformed")


def validate_repo(doc: dict) -> dict:
    validate_source(doc)
    recorded = doc["repository"]
    current = repo_info(recorded["toplevel"])
    for key in ("toplevel", "workspace", "jj_dir", "jj_dev", "jj_ino", "identity_digest"):
        if current[key] != recorded[key]:
            raise Operational("BLOCKED", f"canonical repository identity changed ({key})")
    return current


def resolve_plan(repo: str, plan: str) -> tuple[str, str]:
    supplied = os.path.abspath(plan if os.path.isabs(plan) else os.path.join(repo, plan))
    try:
        current = os.lstat(supplied)
    except OSError as exc:
        raise Operational("REFUSED", f"selected plan is missing: {exc}") from exc
    if stat.S_ISLNK(current.st_mode) or not stat.S_ISREG(current.st_mode):
        raise Operational("REFUSED", "selected plan must be one regular non-symlink file")
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
}


def route_model_allowed(route: str, model: str) -> bool:
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
        return lowered not in {"composer", "grok"} and not lowered.startswith(("composer-", "grok-", "cursor-grok-"))
    if route == "composer":
        return bool(re.fullmatch(r"composer-[A-Za-z0-9._-]+", model))
    if route == "grok-cursor":
        return bool(re.fullmatch(r"cursor-grok-[A-Za-z0-9._-]+", model))
    return False


def fixed_route_contract(binding: dict, egress: dict, word: str = "BLOCKED") -> dict:
    if not isinstance(binding, dict) or not isinstance(egress, dict):
        raise Operational(word, "run binding or egress sanction is malformed")
    if set(binding) != {"mode", "target", "model", "source"}:
        raise Operational(word, "binding must contain exactly mode, target, model, and source")
    if binding.get("mode") not in {"prefer", "require"}:
        raise Operational(word, "binding mode must be prefer or require")
    source = binding.get("source")
    if not isinstance(source, str) or not source or "\0" in source or len(source.encode()) > 256:
        raise Operational(word, "binding source must be a non-empty bounded string")
    route = egress.get("route")
    contract = ROUTE_CONTRACTS.get(route)
    if not contract:
        raise Operational(word, f"unsupported egress route {route!r}")
    if binding.get("target") != contract["target"] or egress.get("intermediaries") != contract["intermediaries"]:
        raise Operational(word, "binding target or intermediaries do not match the fixed route")
    model = binding.get("model")
    requested_model = model or contract["default_model"]
    if not isinstance(requested_model, str) or not route_model_allowed(route, requested_model):
        raise Operational(word, "binding model is not compatible with the fixed route")
    restrictions = egress.get("restrictions", [])
    if not isinstance(restrictions, list) or not all(isinstance(item, str) for item in restrictions):
        raise Operational(word, "egress restrictions must be a string list")
    return contract


def attempt_authorization(doc: dict, activity_posture: str, unit_id: str, attempt_id: str, packet_digest: str) -> dict:
    contract = fixed_route_contract(doc.get("binding"), doc.get("egress"))
    route = doc["egress"]["route"]
    model = doc["binding"].get("model")
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
        "restrictions": list(doc["egress"].get("restrictions", [])),
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
        current = os.fstat(fd)
        if not stat.S_ISREG(current.st_mode) or current.st_size > MAX_PACKET_BYTES:
            raise Operational("REFUSED", f"{label} must be one bounded regular non-symlink file")
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
    rid = safe_id(args.run_id, "run id")
    info = repo_info(args.repo)
    ensure_root(info["toplevel"])
    if args.plan:
        if not args.plan_digest or args.prompt_digest:
            raise Operational("REFUSED", "plan source requires only --plan-digest")
        source_abs, source_rel = resolve_plan(info["toplevel"], args.plan)
        source_bytes = Path(source_abs).read_bytes()
        source_kind = "plan"
        supplied_digest = args.plan_digest
        source_record = {"kind": "plan", "storage": "repository", "path": source_rel, "digest": digest_bytes(source_bytes)}
    else:
        if not args.prompt_digest or args.plan_digest:
            raise Operational("REFUSED", "prompt source requires only --prompt-digest")
        prompt_path = require_path_within(args.prompt_brief, storage_boundary(info["toplevel"]), "prompt brief")
        source_bytes = read_external_packet(prompt_path, "prompt brief")
        source_kind = "prompt"
        source_rel = None
        supplied_digest = args.prompt_digest
        source_record = {"kind": "prompt", "storage": "run", "path": "source/bare-prompt.md", "digest": digest_bytes(source_bytes)}
    if source_record["digest"] != supplied_digest:
        raise Operational("REFUSED", f"selected {source_kind} digest does not match content")
    binding = parse_json_arg(args.binding_json, "binding")
    egress = parse_json_arg(args.egress_json, "egress")
    fixed_route_contract(binding, egress, "REFUSED")
    rd = locate_run_dir(rid, info["toplevel"])
    if os.path.isdir(rd):
        validate_private_dir(rd)
        with locked_manifest(rid, directory=rd) as existing:
            validate_repo(existing)
            if existing.get("source") != source_record or existing.get("binding") != binding or existing.get("egress") != egress:
                raise Operational("BLOCKED", "run id already belongs to another repository, source, binding, or route")
            return "READY", {"run_id": rid, "revision": existing["revision"], "resumed": True, "source_kind": source_kind, "source_digest": source_record["digest"], "recovery_path": rd}
    ensure_private_dir(rd)
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
        "repository": {key: info[key] for key in ("toplevel", "workspace", "jj_dir", "jj_dev", "jj_ino", "identity_digest")},
        "canonical": {"initial_change": info["change_id"], "initial_commit": info["commit"], "initial_operation": info["operation"]},
        "source": source_record,
        "plan": {"kind": source_kind, "path": source_rel, "digest": source_record["digest"], "checkpoint": None},
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
    return "READY", {"run_id": rid, "revision": 0, "resumed": False, "source_kind": source_kind, "source_digest": source_record["digest"], "recovery_path": rd}


def cmd_checkpoint_plan(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        plan = doc["plan"]
        if plan.get("kind") != "plan" or not plan.get("path"):
            if status_paths(info["toplevel"]):
                raise Operational("BLOCKED", "prompt-backed external execution requires an empty canonical working-copy change")
            return "NOOP", {"checkpoint": None, "canonical_change": info["change_id"], "source_kind": "prompt"}
        plan_abs, plan_rel = resolve_plan(info["toplevel"], plan["path"])
        if digest_bytes(Path(plan_abs).read_bytes()) != plan["digest"]:
            raise Operational("BLOCKED", "selected plan content no longer matches the recorded digest")
        paths = status_paths(info["toplevel"])
        if not paths:
            return "NOOP", {"checkpoint": plan.get("checkpoint"), "canonical_change": info["change_id"]}
        if paths != {plan_rel}:
            raise Operational("BLOCKED", "canonical changes are not exactly the selected plan", {"changed_paths": sorted(paths)})
        before = revision_snapshot(info["toplevel"])
        description = before["description"] or (args.checkpoint_description or "").strip()
        if not description:
            raise Operational("REFUSED", f"checkpoint-plan requires --checkpoint-description when the current change is undescribed. {DESCRIPTION_GUIDANCE}")
    if before["description"] != description:
        jj(info["toplevel"], "describe", "-m", description)
    jj(info["toplevel"], "new")
    checkpoint = revision_snapshot(info["toplevel"], "@-")
    current = revision_snapshot(info["toplevel"])
    receipt = {
        "prior_change": before["change_id"],
        "change": checkpoint["change_id"],
        "commit": checkpoint["commit"],
        "path": plan_rel,
        "digest": plan["digest"],
        "next_change": current["change_id"],
        "at": now_iso(),
    }
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        doc["plan"]["checkpoint"] = receipt
        event(doc, "plan-checkpoint", detail={"change": receipt["change"], "path": plan_rel})
    return "CHECKPOINTED", {"checkpoint": receipt}


@contextlib.contextmanager
def admin_lock(identity: str):
    root = ensure_root()
    path = os.path.join(root, ".locks", f"workspace-{digest_bytes(identity.encode())}.lock")
    if not os.path.lexists(path):
        with contextlib.suppress(Operational):
            create_private(path, b"")
    fd = os.open(path, os.O_RDWR | O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def validate_workspace(doc: dict, unit: dict) -> dict:
    workspace = os.path.realpath(unit["workspace"]["path"])
    owned = os.path.join(locate_run_dir(doc["run_id"]), "units", unit["unit_id"])
    if os.path.commonpath([workspace, os.path.realpath(owned)]) != os.path.realpath(owned):
        raise Operational("BLOCKED", "workspace escaped its owned unit directory")
    validate_private_dir(workspace)
    root = workspace_root(workspace)
    if root != workspace:
        raise Operational("BLOCKED", "unit workspace root changed")
    rows = [row for row in workspace_rows(doc["repository"]["toplevel"]) if row["name"] == unit["workspace"]["name"] and row["path"] == workspace]
    if len(rows) != 1:
        raise Operational("BLOCKED", "unit workspace is not registered exactly once")
    return rows[0]


def validate_pristine_unit_base(doc: dict, unit: dict) -> dict:
    row = validate_workspace(doc, unit)
    snapshot = revision_snapshot(unit["workspace"]["path"])
    if snapshot["change_id"] != unit["workspace"]["change_id"] or snapshot["parents"] != [unit["workspace"]["base"]]:
        raise Operational("BLOCKED", "unit workspace change or parent no longer matches its recorded base")
    if status_paths(unit["workspace"]["path"]):
        raise Operational("BLOCKED", "unit workspace is changed before dispatch authorization")
    return row


def unit_accepted_commit(unit: dict) -> str | None:
    if not isinstance(unit, dict):
        return None
    if unit.get("state") == "native-completed":
        attempts = unit.get("attempts") or []
        completion = attempts[-1].get("fallback", {}).get("completed") if attempts else None
        return completion.get("accepted_commit") if isinstance(completion, dict) else None
    if unit.get("state") != "cleaned":
        return None
    canonical = unit.get("integration", {}).get("canonical_change")
    return canonical.get("commit") if isinstance(canonical, dict) else None


def unit_ready_for_run_verification(unit: object) -> bool:
    return isinstance(unit, dict) and unit_accepted_commit(unit) is not None


def accepted_unit_commit_snapshot(units: object) -> dict[str, str] | None:
    if not isinstance(units, dict):
        return None
    out: dict[str, str] = {}
    for unit_id in sorted(units):
        commit = unit_accepted_commit(units[unit_id])
        if commit is None:
            return None
        out[unit_id] = commit
    return out
