"""Shared state and JJ primitives for the ce-work workspace controller."""

from __future__ import annotations

import argparse
import contextlib
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

try:
    import fcntl
except ImportError:  # Native Windows uses owner-private files without advisory locking.
    fcntl = None

SCHEMA_VERSION = 2
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_PACKET_BYTES = 200_000
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
TERMINAL_PROCESS = {"done", "failed", "timeout", "died-without-result"}
UNIT_STATES = {
    "queued", "authoring", "authored", "integration-pending", "integrating",
    "verified", "accepted", "preserved", "cleaned", "native-completed",
}


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
    configured = {item.strip() for item in os.environ.get("CE_WORK_TEST_FAULT", "").split(",") if item.strip()}
    if point in configured:
        raise Operational("INTERRUPTED", f"injected interruption at {point}")


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_id(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value) or not value.strip("."):
        raise Operational("REFUSED", f"unsafe {label}: {value!r}")
    return value


def _mode(info: os.stat_result) -> int:
    return stat.S_IMODE(info.st_mode)


def _euid() -> int | None:
    getter = getattr(os, "geteuid", None) or getattr(os, "getuid", None)
    return getter() if getter else None


def validate_private_dir(path: str) -> None:
    try:
        fd = os.open(path, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open directory {path}: {exc}") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISDIR(info.st_mode):
            raise TrustFailure(f"not a real directory: {path}")
        if _euid() is not None and info.st_uid != _euid():
            raise TrustFailure(f"directory is not owned by current user: {path}")
        if os.name != "nt" and _mode(info) != 0o700:
            raise TrustFailure(f"directory mode is {_mode(info):04o}, expected 0700: {path}")
    finally:
        os.close(fd)


def ensure_private_dir(path: str) -> None:
    os.makedirs(path, mode=0o700, exist_ok=True)
    if os.name != "nt":
        os.chmod(path, 0o700)
    validate_private_dir(path)


def jj(repo: str, *args: str, input_data: bytes | None = None, check: bool = True) -> bytes:
    proc = subprocess.run(
        ["jj", "-R", repo, "--no-pager", "--color=never", *args],
        input=input_data,
        capture_output=True,
        check=False,
    )
    if check and proc.returncode != 0:
        message = proc.stderr.decode("utf-8", "replace").strip()
        raise Operational("BLOCKED", f"jj {' '.join(args)} failed: {message}")
    return proc.stdout


def jj_text(repo: str, *args: str, check: bool = True) -> str:
    return jj(repo, *args, check=check).decode("utf-8", "surrogateescape").strip()


def workspace_root(path: str = ".") -> str:
    proc = subprocess.run(
        ["jj", "-R", os.path.abspath(path), "workspace", "root"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise Operational("REFUSED", "a writable JJ workspace is required")
    return os.path.realpath(proc.stdout.strip())


def local_tmp_root(repo: str | None = None) -> str:
    try:
        root = workspace_root(repo or ".")
    except Operational:
        root = os.path.abspath(".")
    path = os.path.join(root, ".tmp")
    ensure_private_dir(path)
    ignore = os.path.join(path, ".gitignore")
    if not os.path.lexists(ignore):
        try:
            create_private(ignore, b"*\n")
        except Operational:
            if not os.path.isfile(ignore):
                raise
    return path


def runs_root(repo: str | None = None) -> str:
    path = os.path.join(local_tmp_root(repo), "ce-work", "runs")
    ensure_private_dir(path)
    ensure_private_dir(os.path.join(path, ".locks"))
    return path


def ensure_root(repo: str | None = None) -> str:
    return runs_root(repo)


def run_dir(run_id: str, repo: str | None = None) -> str:
    rid = safe_id(run_id, "run id")
    if repo:
        return os.path.join(runs_root(repo), rid)
    configured = os.environ.get("CE_WORK_RUNS_ROOT")
    if configured:
        candidate = os.path.join(os.path.abspath(configured), rid)
        if os.path.isdir(candidate):
            return candidate
    candidate = os.path.join(runs_root(), rid)
    return candidate


def read_private(path: str, cap: int = MAX_JSON_BYTES) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open state file {path}: {exc}") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise TrustFailure(f"state is not a regular file: {path}")
        if _euid() is not None and info.st_uid != _euid():
            raise TrustFailure(f"state is not owned by current user: {path}")
        if os.name != "nt" and _mode(info) != 0o600:
            raise TrustFailure(f"state mode is {_mode(info):04o}, expected 0600: {path}")
        if info.st_size > cap:
            raise TrustFailure(f"state exceeds {cap}-byte limit: {path}")
        data = bytearray()
        while len(data) <= cap:
            part = os.read(fd, min(65536, cap + 1 - len(data)))
            if not part:
                break
            data.extend(part)
        if len(data) > cap:
            raise TrustFailure(f"state exceeds {cap}-byte limit: {path}")
        return bytes(data)
    finally:
        os.close(fd)


def stat_private_file(path: str) -> os.stat_result:
    try:
        fd = os.open(path, os.O_RDONLY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open state file {path}: {exc}") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise TrustFailure(f"state is not a regular file: {path}")
        if _euid() is not None and info.st_uid != _euid():
            raise TrustFailure(f"state is not owned by current user: {path}")
        if os.name != "nt" and _mode(info) != 0o600:
            raise TrustFailure(f"state mode is {_mode(info):04o}, expected 0600: {path}")
        return info
    finally:
        os.close(fd)


def read_private_json(path: str) -> dict:
    try:
        value = json.loads(read_private(path))
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
    parent_fd = os.open(os.path.dirname(path), os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)


def atomic_private_json(path: str, doc: dict) -> None:
    data = (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_JSON_BYTES:
        raise Operational("BLOCKED", "manifest exceeds bounded state size")
    parent = os.path.dirname(path)
    staging = None
    fd = None
    for _ in range(64):
        candidate = os.path.join(parent, f".manifest-{os.getpid()}-{secrets.token_hex(8)}")
        try:
            fd = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
            staging = candidate
            break
        except FileExistsError:
            continue
    if fd is None or staging is None:
        raise Operational("BLOCKED", "could not reserve an atomic manifest path")
    try:
        os.write(fd, data)
        os.fsync(fd)
        os.close(fd)
        fd = None
        os.replace(staging, path)
        parent_fd = os.open(parent, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        if fd is not None:
            os.close(fd)
        if staging and os.path.lexists(staging):
            os.unlink(staging)


@contextlib.contextmanager
def locked_manifest(run_id: str, write: bool = False):
    rd = run_dir(run_id)
    validate_private_dir(rd)
    fd = os.open(os.path.join(rd, "manifest.lock"), os.O_RDWR | O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or (_euid() is not None and info.st_uid != _euid())
            or (os.name != "nt" and _mode(info) != 0o600)
        ):
            raise TrustFailure("manifest lock owner/type/mode validation failed")
        if fcntl is not None:
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
        if fcntl is not None:
            with contextlib.suppress(OSError):
                fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def revision_info(repo: str, revset: str = "@") -> dict:
    template = 'commit_id ++ "\\n" ++ change_id ++ "\\n" ++ parents.map(|p| p.commit_id()).join(" ") ++ "\\n"'
    lines = jj_text(repo, "log", "-r", f"exactly({revset}, 1)", "--no-graph", "-T", template).splitlines()
    if len(lines) < 2:
        raise Operational("BLOCKED", f"revset did not resolve exactly once: {revset}")
    return {"commit_id": lines[0], "change_id": lines[1], "parents": lines[2].split() if len(lines) > 2 else []}


def operation_id(repo: str) -> str:
    value = jj_text(repo, "op", "log", "--limit", "1", "--no-graph", "-T", 'id ++ "\\n"')
    if not re.fullmatch(r"[0-9a-f]+", value):
        raise Operational("BLOCKED", "could not resolve the current JJ operation")
    return value


def changed_paths(repo: str, revset: str = "@") -> list[str]:
    output = jj_text(repo, "diff", "-r", revset, "--name-only")
    return sorted({line for line in output.splitlines() if line})


def has_conflicts(repo: str, revset: str = "@") -> bool:
    return jj_text(repo, "log", "-r", f"({revset}) & conflicts()", "--no-graph", "-T", 'change_id ++ "\\n"', check=False) != ""


def is_empty(repo: str, revset: str = "@") -> bool:
    return jj_text(repo, "log", "-r", f"({revset}) & empty()", "--no-graph", "-T", 'change_id ++ "\\n"', check=False) != ""


def semantic_snapshot(repo: str) -> dict:
    info = revision_info(repo)
    patch = jj(repo, "diff", "-r", "@", "--git")
    return {
        **info,
        "operation_id": operation_id(repo),
        "changed_paths": changed_paths(repo),
        "diff_sha256": digest_bytes(patch),
        "empty": is_empty(repo),
        "conflicted": has_conflicts(repo),
    }


def repo_info(repo: str) -> dict:
    root = workspace_root(repo)
    marker = os.path.realpath(os.path.join(root, ".jj", "repo"))
    info = os.stat(marker)
    current = revision_info(root)
    trunk = revision_info(root, "trunk()")
    identity = digest_bytes(f"{marker}\0{info.st_dev}\0{info.st_ino}".encode())
    return {
        "workspace_root": root,
        "repo_store": marker,
        "store_dev": info.st_dev,
        "store_ino": info.st_ino,
        "identity_digest": identity,
        "working_copy": current,
        "trunk": trunk,
        "operation_id": operation_id(root),
    }


def validate_repo(doc: dict) -> dict:
    validate_source(doc)
    fixed_route_contract(doc.get("binding"), doc.get("egress"))
    current = repo_info(doc["repository"]["workspace_root"])
    for key in ("workspace_root", "repo_store", "store_dev", "store_ino", "identity_digest"):
        if current[key] != doc["repository"][key]:
            raise Operational("BLOCKED", f"canonical JJ repository identity changed ({key})")
    return current


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
        return not (lowered in {"composer", "grok"} or lowered.startswith(("composer-", "grok-", "cursor-grok-")))
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
        raise Operational(word, "binding source must be a non-empty string of at most 256 bytes")
    route = egress.get("route")
    if route not in ROUTE_CONTRACTS:
        raise Operational(word, "unsupported fixed route")
    contract = ROUTE_CONTRACTS[route]
    if binding.get("target") != contract["target"] or egress.get("intermediaries") != contract["intermediaries"]:
        raise Operational(word, "binding and egress route disagree")
    model = binding.get("model")
    if model is not None and (not isinstance(model, str) or not model):
        raise Operational(word, "binding model must be null or a non-empty string")
    requested_model = model or contract["default_model"]
    if not route_model_allowed(route, requested_model):
        raise Operational(word, "binding model is not compatible with the sanctioned fixed route")
    restrictions = egress.get("restrictions", [])
    if not isinstance(restrictions, list) or any(not isinstance(item, str) for item in restrictions):
        raise Operational(word, "egress restrictions must be a string list")
    return {"route": route, **contract}


def attempt_authorization(doc: dict, posture: str, unit_id: str, attempt_id: str, packet_digest: str) -> dict:
    contract = fixed_route_contract(doc["binding"], doc["egress"])
    route = contract["route"]
    return {
        "schema_version": 1,
        "run_id": doc["run_id"],
        "unit_id": unit_id,
        "attempt_id": attempt_id,
        "route": route,
        "target": contract["target"],
        "harness": contract["harness"],
        "intermediaries": list(contract["intermediaries"]),
        "model_requested": doc["binding"].get("model") or contract["default_model"],
        "restriction_posture": contract["restriction_posture"],
        "restrictions": doc["egress"].get("restrictions", []),
        "activity_posture": posture,
        "packet_digest": packet_digest,
    }


def read_external_packet(path: str, label: str = "unit packet") -> bytes:
    absolute = os.path.abspath(path)
    fd = os.open(absolute, os.O_RDONLY | O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_PACKET_BYTES:
            raise Operational("REFUSED", f"{label} must be a bounded regular file")
        data = bytearray()
        while len(data) <= MAX_PACKET_BYTES:
            part = os.read(fd, min(65536, MAX_PACKET_BYTES + 1 - len(data)))
            if not part:
                break
            data.extend(part)
        if len(data) > MAX_PACKET_BYTES:
            raise Operational("REFUSED", f"{label} exceeds the bounded size")
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


def resolve_plan(repo: str, plan: str) -> tuple[str, str]:
    supplied = os.path.abspath(plan if os.path.isabs(plan) else os.path.join(repo, plan))
    info = os.lstat(supplied)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise Operational("REFUSED", "selected plan must be a regular non-symlink file")
    absolute = os.path.realpath(supplied)
    if os.path.commonpath([repo, absolute]) != repo:
        raise Operational("REFUSED", "plan must be inside the canonical workspace")
    return absolute, os.path.relpath(absolute, repo)


def validate_source(doc: dict) -> None:
    source = doc.get("source")
    if not isinstance(source, dict) or source.get("kind") not in {"plan", "prompt"}:
        raise TrustFailure("manifest source record is malformed")
    digest = source.get("digest")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise TrustFailure("manifest source digest is malformed")
    if source["kind"] == "prompt":
        if source.get("storage") != "run" or source.get("path") != "source/bare-prompt.md":
            raise TrustFailure("prompt source location is malformed")
        data = read_private(os.path.join(run_dir(doc["run_id"]), source["path"]), MAX_PACKET_BYTES)
    else:
        if source.get("storage") != "workspace" or not isinstance(source.get("path"), str):
            raise TrustFailure("plan source location is malformed")
        absolute, relative = resolve_plan(doc["repository"]["workspace_root"], source["path"])
        if relative != source["path"]:
            raise TrustFailure("plan source path no longer resolves exactly")
        data = Path(absolute).read_bytes()
    if digest_bytes(data) != digest:
        raise TrustFailure("source digest no longer matches content")


def cmd_init(args) -> tuple[str, dict]:
    info = repo_info(args.repo)
    root = ensure_root(info["workspace_root"])
    rid = safe_id(args.run_id, "run id")
    rd = os.path.join(root, rid)
    source_path = args.plan or args.prompt_brief
    source_kind = "plan" if args.plan else "prompt"
    supplied_digest = args.plan_digest if args.plan else args.prompt_digest
    if not source_path or not supplied_digest:
        raise Operational("REFUSED", "source path and digest are required")
    if args.plan:
        absolute, relative = resolve_plan(info["workspace_root"], source_path)
        data = Path(absolute).read_bytes()
        source = {"kind": "plan", "storage": "workspace", "path": relative, "digest": digest_bytes(data)}
    else:
        absolute = os.path.realpath(os.path.abspath(source_path))
        tmp = local_tmp_root(info["workspace_root"])
        if os.path.commonpath([tmp, absolute]) != tmp:
            raise Operational("REFUSED", "prompt brief must be under the workspace .tmp root")
        data = read_external_packet(absolute, "prompt brief")
        source = {"kind": "prompt", "storage": "run", "path": "source/bare-prompt.md", "digest": digest_bytes(data)}
    if source["digest"] != supplied_digest:
        raise Operational("REFUSED", "source digest does not match content")
    binding = parse_json_arg(args.binding_json, "binding")
    egress = parse_json_arg(args.egress_json, "egress")
    fixed_route_contract(binding, egress, "REFUSED")
    if os.path.isdir(rd):
        with locked_manifest(rid) as existing:
            validate_repo(existing)
            if existing.get("source", {}).get("digest") != source["digest"]:
                raise Operational("BLOCKED", "run id belongs to another source")
            if existing.get("binding") != binding or existing.get("egress") != egress:
                raise Operational("BLOCKED", "run id binding or egress differs from the recorded fixed contract")
            return "READY", {"run_id": rid, "resumed": True, "source_kind": source_kind, "source_digest": source["digest"], "recovery_path": rd}
    ensure_private_dir(rd)
    for child in ("units", "jobs", "packets", "source"):
        ensure_private_dir(os.path.join(rd, child))
    if source_kind == "prompt":
        create_private(os.path.join(rd, source["path"]), data)
    create_private(os.path.join(rd, "manifest.lock"), b"")
    feature_base = f"ce-work-{rid}"
    feature = None
    for suffix in range(100):
        candidate = feature_base if suffix == 0 else f"{feature_base}-{suffix}"
        present = jj_text(
            info["workspace_root"], "bookmark", "list", candidate,
            "-T", 'name ++ "\\n"', check=False,
        )
        if not present:
            feature = candidate
            break
    if feature is None:
        raise Operational("BLOCKED", "could not reserve a non-conflicting feature bookmark name")
    created = now_iso()
    doc = {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "run_id": rid,
        "created_at": created,
        "updated_at": created,
        "repository": {key: info[key] for key in ("workspace_root", "repo_store", "store_dev", "store_ino", "identity_digest")},
        "canonical": {"initial_operation": info["operation_id"], "initial_working_copy": info["working_copy"], "trunk": info["trunk"], "feature_bookmark": feature},
        "source": source,
        "plan": {"kind": source_kind, "path": source.get("path") if source_kind == "plan" else None, "digest": source["digest"], "checkpoint": None},
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
    return "READY", {"run_id": rid, "resumed": False, "source_kind": source_kind, "source_digest": source["digest"], "recovery_path": rd}


def cmd_checkpoint_plan(args) -> tuple[str, dict]:
    # Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
    description = args.change_description.strip()
    if not description or "\0" in description:
        raise Operational("REFUSED", "a locally conforming change description is required")
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        plan = doc["plan"]
        if plan["kind"] != "plan":
            if not is_empty(info["workspace_root"]):
                raise Operational("BLOCKED", "prompt-backed execution requires an empty working-copy change")
            return "NOOP", {"checkpoint": None}
        if changed_paths(info["workspace_root"]) != [plan["path"]] or has_conflicts(info["workspace_root"]):
            raise Operational("BLOCKED", "checkpoint requires the selected plan as the sole conflict-free fileset")
        prior = semantic_snapshot(info["workspace_root"])
    jj(info["workspace_root"], "describe", "-r", "@", "-m", description)
    checkpoint = revision_info(info["workspace_root"])
    jj(info["workspace_root"], "new", checkpoint["change_id"])
    with locked_manifest(args.run_id, write=True) as doc:
        doc["plan"]["checkpoint"] = {**checkpoint, "description": description, "at": now_iso(), "prior": prior}
        event(doc, "plan-checkpoint", detail={"change_id": checkpoint["change_id"]})
    return "CHECKPOINTED", {"checkpoint": checkpoint}


def unit_accepted_change(unit: dict) -> str | None:
    if unit.get("state") in {"accepted", "cleaned", "native-completed"}:
        accepted = unit.get("integration", {}).get("accepted_change") or unit.get("fallback", {}).get("completed")
        if isinstance(accepted, dict):
            return accepted.get("change_id")
    return None


def unit_ready_for_run_verification(unit: object) -> bool:
    return isinstance(unit, dict) and unit_accepted_change(unit) is not None


def accepted_unit_change_snapshot(units: object) -> dict[str, str] | None:
    if not isinstance(units, dict):
        return None
    result = {}
    for uid, unit in units.items():
        change = unit_accepted_change(unit)
        if not change:
            return None
        result[uid] = change
    return result
