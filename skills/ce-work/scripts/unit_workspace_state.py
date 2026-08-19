"""Private, crash-recoverable jj workspace controller state."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import time
from pathlib import Path

SCHEMA_VERSION = 2
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_PACKET_BYTES = 200_000
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
TERMINAL_PROCESS = {"done", "failed", "timeout", "died-without-result"}
INTEGRATABLE_STATES = {"integration-pending", "integrated", "verified"}
UNIT_STATES = {
    "queued", "authoring", "authored", "integration-pending", "integrated",
    "restoring", "verified", "accepted", "preserved", "cleaned", "native-completed",
}
MESSAGE_GUIDANCE = "Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards."


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
    configured = {v.strip() for v in os.environ.get("CE_WORK_TEST_FAULT", "").split(",") if v.strip()}
    if point in configured:
        raise Operational("INTERRUPTED", f"injected interruption at {point}")


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_id(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value) or not value.strip("."):
        raise Operational("REFUSED", f"unsafe {label}: {value!r}")
    return value


def validate_change_description(description: str) -> str:
    value = description.strip()
    if not value or "\0" in value or len(value.encode()) > 4096:
        raise Operational("REFUSED", f"change description must be non-empty, NUL-free, and at most 4096 bytes. {MESSAGE_GUIDANCE}")
    return value


def _mode(st: os.stat_result) -> int:
    return stat.S_IMODE(st.st_mode)


def validate_private_dir(path: str) -> None:
    try:
        fd = os.open(path, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open directory {path}: {exc}") from exc
    try:
        st = os.fstat(fd)
        euid = getattr(os, "geteuid", lambda: None)()
        if not stat.S_ISDIR(st.st_mode) or (euid is not None and st.st_uid != euid) or _mode(st) != 0o700:
            raise TrustFailure(f"directory owner/type/mode validation failed: {path}")
    finally:
        os.close(fd)


def ensure_private_dir(path: str) -> None:
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        st = os.lstat(path)
        euid = getattr(os, "geteuid", lambda: None)()
        if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode) or (euid is not None and st.st_uid != euid):
            raise TrustFailure(f"cannot repair foreign or non-directory private path: {path}")
        os.chmod(path, 0o700)
    validate_private_dir(path)


def create_private(path: str, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def read_private(path: str, cap: int = MAX_JSON_BYTES) -> bytes:
    fd = os.open(path, os.O_RDONLY | O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        euid = getattr(os, "geteuid", lambda: None)()
        if not stat.S_ISREG(st.st_mode) or (euid is not None and st.st_uid != euid) or _mode(st) != 0o600:
            raise TrustFailure(f"state owner/type/mode validation failed: {path}")
        if st.st_size > cap:
            raise TrustFailure(f"state exceeds {cap}-byte limit: {path}")
        data = bytearray()
        while len(data) <= cap:
            part = os.read(fd, min(65536, cap + 1 - len(data)))
            if not part:
                break
            data.extend(part)
        if len(data) > cap:
            raise TrustFailure(f"state grew beyond {cap}-byte limit: {path}")
        return bytes(data)
    finally:
        os.close(fd)


def stat_private_file(path: str) -> os.stat_result:
    fd = os.open(path, os.O_RDONLY | O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        euid = getattr(os, "geteuid", lambda: None)()
        if not stat.S_ISREG(st.st_mode) or (euid is not None and st.st_uid != euid) or _mode(st) != 0o600:
            raise TrustFailure(f"state owner/type/mode validation failed: {path}")
        return st
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


def atomic_private_json(path: str, doc: dict) -> None:
    data = (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_JSON_BYTES:
        raise Operational("BLOCKED", "manifest exceeds bounded state size")
    parent = os.path.dirname(path)
    for _ in range(128):
        tmp = os.path.join(parent, f".manifest-{secrets.token_hex(8)}")
        try:
            create_private(tmp, data)
            break
        except FileExistsError:
            continue
    else:
        raise Operational("BLOCKED", "could not reserve manifest temporary file")
    try:
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def jj(repo: str, *args: str, input_data: bytes | None = None, check: bool = True) -> bytes:
    proc = subprocess.run(["jj", "-R", repo, "--no-pager", "--color=never", *args], input=input_data, capture_output=True, check=False)
    if check and proc.returncode != 0:
        raise Operational("BLOCKED", f"jj {' '.join(args)} failed: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout


def jj_text(repo: str, *args: str, check: bool = True) -> str:
    return jj(repo, *args, check=check).decode("utf-8", "surrogateescape").strip()


def workspace_root(repo: str = ".") -> str:
    return os.path.realpath(jj_text(repo, "workspace", "root"))


def _workspace_local_root(repo: str, path: str, label: str) -> str:
    local = os.path.realpath(os.path.join(workspace_root(repo), ".tmp"))
    absolute = os.path.realpath(os.path.abspath(path))
    if os.path.commonpath([local, absolute]) != local:
        raise TrustFailure(f"{label} must stay beneath the canonical jj workspace .tmp directory")
    return absolute


def runs_root(repo: str = ".") -> str:
    configured = os.environ.get("CE_WORK_RUNS_ROOT")
    if configured:
        return _workspace_local_root(repo, configured, "CE_WORK_RUNS_ROOT")
    peer_root = os.environ.get("CE_PEER_JOBS_ROOT")
    if peer_root:
        return os.path.join(_workspace_local_root(repo, peer_root, "CE_PEER_JOBS_ROOT"), "ce-work")
    return os.path.join(workspace_root(repo), ".tmp", "rocketclaw", "ce-work")


def ensure_runs_root(root: str) -> str:
    absolute_root = os.path.abspath(root)
    marker = os.sep + ".tmp" + os.sep
    if marker not in absolute_root:
        raise TrustFailure("run root must be beneath a jj workspace .tmp directory")
    workspace = absolute_root.split(marker, 1)[0]
    local = os.path.realpath(os.path.join(workspace, ".tmp"))
    absolute = os.path.realpath(root)
    if os.path.commonpath([local, absolute]) != local:
        raise TrustFailure("run root must stay beneath the jj workspace .tmp directory")
    current = workspace
    for component in os.path.relpath(root, workspace).split(os.sep):
        current = os.path.join(current, component)
        ensure_private_dir(current)
    ensure_private_dir(os.path.join(root, ".locks"))
    ensure_private_dir(os.path.join(root, ".inputs"))
    return root


def ensure_root(repo: str = ".") -> str:
    return ensure_runs_root(runs_root(repo))


def candidate_runs_roots() -> list[str]:
    return [runs_root()]


def run_dir(run_id: str) -> str:
    return os.path.join(runs_root(), safe_id(run_id, "run id"))


@contextlib.contextmanager
def locked_manifest(run_id: str, write: bool = False):
    rd = run_dir(run_id)
    ensure_runs_root(os.path.dirname(rd))
    validate_private_dir(rd)
    fd = os.open(os.path.join(rd, "manifest.lock"), os.O_RDWR | O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX if write else fcntl.LOCK_SH)
        doc = read_private_json(os.path.join(rd, "manifest.json"))
        if doc.get("schema_version") != SCHEMA_VERSION or doc.get("run_id") != run_id:
            raise TrustFailure("manifest schema or run identity mismatch")
        before = json.dumps(doc, sort_keys=True, separators=(",", ":"))
        yield doc
        if write and json.dumps(doc, sort_keys=True, separators=(",", ":")) != before:
            doc["revision"] = int(doc.get("revision", 0)) + 1
            doc["updated_at"] = now_iso()
            atomic_private_json(os.path.join(rd, "manifest.json"), doc)
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _template(repo: str, rev: str, expression: str) -> str:
    return jj_text(repo, "log", "-r", rev, "--no-graph", "-T", expression)


def change_id(repo: str, rev: str = "@") -> str:
    return _template(repo, rev, "change_id ++ '\\n'")


def commit_id(repo: str, rev: str = "@") -> str:
    return _template(repo, rev, "commit_id ++ '\\n'")


def operation_id(repo: str) -> str:
    return jj_text(repo, "operation", "log", "-n", "1", "--no-graph", "-T", "id ++ '\\n'")


def change_description(repo: str, rev: str = "@") -> str:
    return _template(repo, rev, "description")


def parent_ids(repo: str, rev: str = "@") -> list[str]:
    raw = _template(repo, rev, "parents.map(|p| p.commit_id()).join(' ') ++ '\\n'")
    return raw.split() if raw else []


def changed_paths(repo: str, rev: str = "@") -> list[str]:
    raw = jj_text(repo, "diff", "-r", rev, "--name-only")
    return [line for line in raw.splitlines() if line]


def current_bookmarks(repo: str) -> list[str]:
    raw = jj_text(repo, "bookmark", "list", "-r", "heads(::@ & bookmarks())", "-T", "name ++ '\\n'", check=False)
    return [line for line in raw.splitlines() if line]


def repo_info(repo: str) -> dict:
    root = workspace_root(repo)
    config_path = jj_text(root, "config", "path", "--repo")
    store = os.path.realpath(os.path.dirname(config_path))
    st = os.stat(store)
    bookmarks = current_bookmarks(root)
    if len(bookmarks) != 1:
        raise Operational("REFUSED", "canonical jj workspace must have exactly one local bookmark at @")
    return {
        "toplevel": root,
        "store_dir": store,
        "store_dev": st.st_dev,
        "store_ino": st.st_ino,
        "identity_digest": digest_bytes(f"{store}\0{st.st_dev}\0{st.st_ino}".encode()),
        "bookmark": bookmarks[0],
        "change_id": change_id(root),
        "commit_id": commit_id(root),
        "operation_id": operation_id(root),
    }


def validate_repo(doc: dict) -> dict:
    recorded = doc["repository"]
    current = repo_info(recorded["toplevel"])
    for key in ("toplevel", "store_dir", "store_dev", "store_ino", "identity_digest"):
        if current[key] != recorded[key]:
            raise Operational("BLOCKED", f"canonical repository identity changed ({key})")
    if current["bookmark"] != doc["bookmark"]["name"]:
        raise Operational("BLOCKED", "canonical bookmark changed")
    return current


def semantic_snapshot(repo: str) -> dict:
    jj(repo, "util", "snapshot")
    paths = changed_paths(repo)
    conflicts = jj_text(repo, "resolve", "--list", "-r", "@", check=False).splitlines()
    return {
        "change_id": change_id(repo),
        "commit_id": commit_id(repo),
        "parent_ids": parent_ids(repo),
        "operation_id": operation_id(repo),
        "description": change_description(repo),
        "changed_paths": paths,
        "status_sha256": digest_bytes("\0".join(paths).encode()),
        "status_empty": not paths,
        "conflicts": [line for line in conflicts if line],
    }


def status_paths(repo: str) -> set[str]:
    return set(changed_paths(repo))


def restore_operation(repo: str, operation: str) -> None:
    jj(repo, "operation", "restore", operation)
    jj(repo, "workspace", "update-stale")


def parse_json_arg(raw: str, label: str) -> dict:
    try:
        value = json.loads(raw)
    except ValueError as exc:
        raise Operational("REFUSED", f"invalid {label} JSON") from exc
    if not isinstance(value, dict):
        raise Operational("REFUSED", f"{label} must be a JSON object")
    return value


def read_external_packet(path: str, label: str = "unit packet") -> bytes:
    fd = os.open(os.path.abspath(path), os.O_RDONLY | O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_PACKET_BYTES:
            raise Operational("REFUSED", f"{label} must be a bounded regular non-symlink file")
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


ROUTE_CONTRACTS = {
    "codex": ("codex", "codex", [], "auto"),
    "claude": ("claude", "claude", [], "auto"),
    "grok-cli": ("grok", "grok", [], "auto"),
    "cursor": ("cursor", "cursor-agent", [], "auto"),
    "composer": ("composer", "cursor-agent", ["cursor"], "composer-2.5-fast"),
    "grok-cursor": ("grok", "cursor-agent", ["cursor"], "cursor-grok-4.6-high"),
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
    if set(binding) != {"mode", "target", "model", "source"} or binding.get("mode") not in {"prefer", "require"}:
        raise Operational(word, "binding contract is malformed")
    if set(egress) != {"route", "intermediaries", "restrictions"}:
        raise Operational(word, "egress contract must contain exactly route, intermediaries, and restrictions")
    route = egress.get("route")
    if route not in ROUTE_CONTRACTS:
        raise Operational(word, "egress route is unsupported")
    target, harness, intermediaries, default_model = ROUTE_CONTRACTS[route]
    restrictions = egress.get("restrictions")
    if not isinstance(restrictions, list) or not all(isinstance(item, str) and item for item in restrictions):
        raise Operational(word, "egress restrictions must be a string list")
    if binding.get("target") != target or egress.get("intermediaries") != intermediaries:
        raise Operational(word, "binding does not match fixed route")
    model = binding.get("model")
    if model is not None and (not isinstance(model, str) or not model):
        raise Operational(word, "binding model must be null or a non-empty string")
    selected_model = model or default_model
    if not route_model_allowed(route, selected_model):
        raise Operational(word, "binding model is not compatible with the fixed route")
    return {"target": target, "harness": harness, "intermediaries": intermediaries, "default_model": default_model}


def attempt_authorization(doc: dict, activity_posture: str, unit_id: str, attempt_id: str, packet_digest: str) -> dict:
    contract = fixed_route_contract(doc["binding"], doc["egress"])
    route = doc["egress"]["route"]
    return {
        "schema_version": 1, "run_id": doc["run_id"], "unit_id": unit_id,
        "attempt_id": attempt_id, "route": route,
        "target": contract["target"], "harness": contract["harness"],
        "intermediaries": contract["intermediaries"],
        "model_requested": doc["binding"].get("model") or contract["default_model"],
        "restriction_posture": "adapter-enforced" if route in {"codex", "cursor", "composer", "grok-cursor"} else "cooperative",
        "restrictions": list(doc["egress"].get("restrictions", [])),
        "activity_posture": activity_posture, "packet_digest": packet_digest,
    }


def resolve_plan(repo: str, plan: str) -> tuple[str, str]:
    absolute = os.path.realpath(os.path.abspath(plan if os.path.isabs(plan) else os.path.join(repo, plan)))
    if os.path.commonpath([repo, absolute]) != repo or not os.path.isfile(absolute) or os.path.islink(absolute):
        raise Operational("REFUSED", "selected plan must be one regular file inside the canonical workspace")
    return absolute, os.path.relpath(absolute, repo)


def cmd_init(args) -> tuple[str, dict]:
    info = repo_info(args.repo)
    root = ensure_root(info["toplevel"])
    rid = safe_id(args.run_id, "run id")
    if bool(args.plan) == bool(args.prompt_brief):
        raise Operational("REFUSED", "select exactly one plan or prompt source")
    if args.plan and (not args.plan_digest or args.prompt_digest):
        raise Operational("REFUSED", "plan source requires only --plan-digest")
    if args.prompt_brief and (not args.prompt_digest or args.plan_digest):
        raise Operational("REFUSED", "prompt source requires only --prompt-digest")
    source_path = args.plan or args.prompt_brief
    if args.plan:
        source_path, _ = resolve_plan(info["toplevel"], source_path)
    source_bytes = read_external_packet(source_path, "plan" if args.plan else "prompt brief")
    source_kind = "plan" if args.plan else "prompt"
    supplied = args.plan_digest if args.plan else args.prompt_digest
    actual = digest_bytes(source_bytes)
    if supplied != actual:
        raise Operational("REFUSED", f"selected {source_kind} digest does not match content")
    binding, egress = parse_json_arg(args.binding_json, "binding"), parse_json_arg(args.egress_json, "egress")
    fixed_route_contract(binding, egress, "REFUSED")
    rd = os.path.join(root, rid)
    if os.path.exists(rd):
        with locked_manifest(rid) as existing:
            validate_repo(existing)
            source = existing.get("source", {})
            if source.get("kind") != source_kind or source.get("digest") != actual:
                raise Operational("BLOCKED", "run id already belongs to another source")
            if existing.get("binding") != binding or existing.get("egress") != egress:
                raise Operational("BLOCKED", "run id binding or egress differs from its fixed contract")
            return "READY", {
                "run_id": rid,
                "revision": existing["revision"],
                "resumed": True,
                "source_kind": source_kind,
                "source_digest": actual,
                "recovery_path": rd,
            }
    ensure_private_dir(rd)
    for child in ("units", "jobs", "packets", "source"):
        ensure_private_dir(os.path.join(rd, child))
    create_private(os.path.join(rd, "manifest.lock"), b"")
    if source_kind == "prompt":
        create_private(os.path.join(rd, "source", "bare-prompt.md"), source_bytes)
    created = now_iso()
    doc = {
        "schema_version": SCHEMA_VERSION, "revision": 0, "run_id": rid,
        "created_at": created, "updated_at": created,
        "repository": {k: info[k] for k in ("toplevel", "store_dir", "store_dev", "store_ino", "identity_digest")},
        "bookmark": {"name": info["bookmark"], "initial_change": info["change_id"]},
        "source": {"kind": source_kind, "path": os.path.relpath(source_path, info["toplevel"]) if args.plan else "source/bare-prompt.md", "digest": actual},
        "binding": binding, "egress": egress, "integration_lock": None,
        "units": {}, "verifications": [], "blockers": [], "events": [{"at": created, "kind": "run-created"}],
    }
    create_private(os.path.join(rd, "manifest.json"), (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode())
    return "READY", {"run_id": rid, "revision": 0, "resumed": False, "source_kind": source_kind, "source_digest": actual, "recovery_path": rd}


def cmd_checkpoint_plan(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        source = doc["source"]
        if source["kind"] != "plan":
            if status_paths(info["toplevel"]):
                raise Operational("BLOCKED", "prompt-backed execution requires an empty canonical working-copy change")
            return "NOOP", {"checkpoint": None, "change_id": info["change_id"]}
        paths = status_paths(info["toplevel"])
        if not paths:
            return "NOOP", {"checkpoint": source.get("checkpoint"), "change_id": info["change_id"]}
        if paths != {source["path"]}:
            raise Operational("BLOCKED", "canonical changes are not exactly the selected plan", {"changed_paths": sorted(paths)})
        description = validate_change_description(args.change_description)
        jj(info["toplevel"], "commit", source["path"], "-m", description)
        checkpoint = {"change_id": change_id(info["toplevel"], "@-"), "commit_id": commit_id(info["toplevel"], "@-"), "description": description, "at": now_iso()}
        jj(info["toplevel"], "bookmark", "set", doc["bookmark"]["name"], "-r", checkpoint["change_id"])
        source["checkpoint"] = checkpoint
        event(doc, "plan-checkpoint", detail=checkpoint)
        return "CHECKPOINTED", {"checkpoint": checkpoint}


def unit_accepted_change(unit: dict) -> str | None:
    if unit.get("state") == "native-completed":
        return unit.get("fallback", {}).get("completed", {}).get("accepted_change")
    if unit.get("state") != "cleaned":
        return None
    return unit.get("integration", {}).get("canonical_change", {}).get("change_id")


def unit_ready_for_run_verification(unit: object) -> bool:
    return isinstance(unit, dict) and unit_accepted_change(unit) is not None


def accepted_unit_change_snapshot(units: object) -> dict[str, str] | None:
    if not isinstance(units, dict):
        return None
    result = {uid: unit_accepted_change(unit) for uid, unit in units.items()}
    return result if all(result.values()) else None


def sanitized_jj_environment(overrides: dict | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env.update(overrides or {})
    return env
