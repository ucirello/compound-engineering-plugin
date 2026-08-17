"""Crash-recoverable Jujutsu workspace controller state and commands."""

from __future__ import annotations

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
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_PACKET_BYTES = 200_000
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
TERMINAL_PROCESS = {"done", "failed", "timeout", "died-without-result"}
DESCRIPTION_STANDARD = "Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards."


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


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_id(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value) or not value.strip("."):
        raise Operational("REFUSED", f"unsafe {label}: {value!r}")
    return value


def jj(repo: str, *args: str, check: bool = True, input_data: bytes | None = None) -> bytes:
    proc = subprocess.run(
        ["jj", "--no-pager", "--config", 'snapshot.auto-track="~glob:.tmp/**"', "-R", repo, *args],
        input=input_data,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if check and proc.returncode != 0:
        reason = proc.stderr.decode("utf-8", "replace").strip()
        raise Operational("BLOCKED", f"jj {' '.join(args)} failed: {reason}")
    return proc.stdout


def jj_text(repo: str, *args: str, check: bool = True) -> str:
    return jj(repo, *args, check=check).decode("utf-8", "surrogateescape").strip()


def workspace_root(path: str) -> str:
    root = jj_text(os.path.abspath(path), "--ignore-working-copy", "workspace", "root", check=False)
    if not root:
        raise Operational("REFUSED", "a Jujutsu workspace is required")
    return os.path.realpath(root)


def scratch_root(root: str) -> str:
    configured = os.environ.get("ROCKETCLAW_WORK_RUNS_ROOT") or os.environ.get("ROCKETCLAW_PEER_JOBS_ROOT")
    base = os.path.realpath(os.path.join(root, ".tmp"))
    candidate = os.path.realpath(configured) if configured else os.path.join(base, "ce-work")
    if os.path.commonpath([base, candidate]) != base:
        raise TrustFailure("run-root override must remain inside the workspace-root .tmp directory")
    return candidate


def runs_root(repo: str | None = None) -> str:
    if repo:
        return scratch_root(workspace_root(repo))
    configured = os.environ.get("ROCKETCLAW_WORK_RUNS_ROOT")
    root = jj_text(os.getcwd(), "--ignore-working-copy", "workspace", "root", check=False)
    root = os.path.realpath(root or os.getcwd())
    base = os.path.realpath(os.path.join(root, ".tmp"))
    candidate = os.path.realpath(configured) if configured else os.path.join(base, "ce-work")
    if os.path.commonpath([base, candidate]) != base:
        raise TrustFailure("ROCKETCLAW_WORK_RUNS_ROOT must remain inside the workspace-root .tmp directory")
    return candidate


def _mode(st: os.stat_result) -> int:
    return stat.S_IMODE(st.st_mode)


def validate_private_dir(path: str) -> None:
    try:
        fd = os.open(path, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open directory {path}: {exc}") from exc
    try:
        st = os.fstat(fd)
        if not stat.S_ISDIR(st.st_mode) or _mode(st) != 0o700:
            raise TrustFailure(f"directory must be a real owner-private 0700 directory: {path}")
        if hasattr(os, "geteuid") and st.st_uid != os.geteuid():
            raise TrustFailure(f"directory is not owned by the current user: {path}")
    finally:
        os.close(fd)


def ensure_private_dir(path: str) -> None:
    os.makedirs(path, mode=0o700, exist_ok=True)
    os.chmod(path, 0o700)
    validate_private_dir(path)


def read_private(path: str, cap: int = MAX_JSON_BYTES) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open state file {path}: {exc}") from exc
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or _mode(st) != 0o600 or st.st_size > cap:
            raise TrustFailure(f"invalid private state file: {path}")
        if hasattr(os, "geteuid") and st.st_uid != os.geteuid():
            raise TrustFailure(f"state file is not owned by the current user: {path}")
        return os.read(fd, cap + 1)
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
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
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
    name = f".manifest-{secrets.token_hex(8)}"
    temporary = os.path.join(parent, name)
    create_private(temporary, data)
    os.replace(temporary, path)


def run_dir(run_id: str, root: str | None = None) -> str:
    return os.path.join(root or runs_root(), safe_id(run_id, "run id"))


@contextlib.contextmanager
def locked_manifest(run_id: str, write: bool = False):
    rd = run_dir(run_id)
    validate_private_dir(rd)
    fd = os.open(os.path.join(rd, "manifest.lock"), os.O_RDWR | O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX if write else fcntl.LOCK_SH)
        path = os.path.join(rd, "manifest.json")
        doc = read_private_json(path)
        if doc.get("schema_version") != SCHEMA_VERSION or doc.get("run_id") != run_id:
            raise TrustFailure("manifest schema or run identity mismatch")
        before = json.dumps(doc, sort_keys=True)
        yield doc
        if write and json.dumps(doc, sort_keys=True) != before:
            doc["revision"] = int(doc.get("revision", 0)) + 1
            doc["updated_at"] = now_iso()
            atomic_private_json(path, doc)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def event(doc: dict, kind: str, unit_id: str | None = None, detail: dict | None = None) -> None:
    row = {"at": now_iso(), "kind": kind}
    if unit_id:
        row["unit_id"] = unit_id
    if detail:
        row["detail"] = detail
    doc.setdefault("events", []).append(row)


def snapshot(repo: str, revision: str = "@") -> dict:
    template = "change_id ++ \"\\n\" ++ commit_id ++ \"\\n\" ++ parents.map(|p| p.commit_id()).join(\" \" ) ++ \"\\n\" ++ empty ++ \"\\n\" ++ conflict"
    rows = jj_text(repo, "log", "--no-graph", "-r", revision, "-T", template).splitlines()
    if len(rows) < 5:
        raise Operational("BLOCKED", "could not read the Jujutsu revision snapshot")
    operation = jj_text(repo, "operation", "log", "--at-op=@", "--ignore-working-copy", "--no-graph", "-n", "1", "-T", "id")
    names = [line for line in jj_text(repo, "diff", "-r", revision, "--name-only").splitlines() if line]
    summary = jj_text(repo, "diff", "-r", revision, "--summary")
    return {
        "operation_id": operation,
        "change_id": rows[0],
        "commit_id": rows[1],
        "parent_commit_ids": rows[2].split() if rows[2] else [],
        "empty": rows[3] == "true",
        "conflict": rows[4] == "true",
        "changed_paths": sorted(names),
        "delta_sha256": digest_bytes(summary.encode()),
    }


def repo_info(repo: str) -> dict:
    root = workspace_root(repo)
    repo_store = os.path.realpath(os.path.join(root, ".jj", "repo"))
    st = os.stat(repo_store)
    return {
        "workspace_root": root,
        "repo_store": repo_store,
        "repo_dev": st.st_dev,
        "repo_ino": st.st_ino,
        "identity_digest": digest_bytes(f"{repo_store}\0{st.st_dev}\0{st.st_ino}".encode()),
        "snapshot": snapshot(root),
    }


def validate_repo(doc: dict) -> dict:
    current = repo_info(doc["repository"]["workspace_root"])
    for key in ("workspace_root", "repo_store", "repo_dev", "repo_ino", "identity_digest"):
        if current[key] != doc["repository"][key]:
            raise Operational("BLOCKED", f"canonical Jujutsu repository identity changed ({key})")
    return current


def _read_external(path: str, label: str) -> bytes:
    absolute = os.path.abspath(path)
    fd = os.open(absolute, os.O_RDONLY | O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_PACKET_BYTES:
            raise Operational("REFUSED", f"{label} must be a bounded regular non-symlink file")
        return os.read(fd, MAX_PACKET_BYTES + 1)
    finally:
        os.close(fd)


def _json_arg(raw: str, label: str) -> dict:
    try:
        value = json.loads(raw)
    except ValueError as exc:
        raise Operational("REFUSED", f"invalid {label} JSON") from exc
    if not isinstance(value, dict):
        raise Operational("REFUSED", f"{label} must be an object")
    return value


def _validate_route(binding: dict, egress: dict) -> None:
    if set(binding) != {"mode", "target", "model", "source"} or binding.get("mode") not in {"prefer", "require"}:
        raise Operational("REFUSED", "binding must contain exactly a prefer/require mode, target, model, and source")
    contracts = {
        "codex": ("codex", []),
        "claude": ("claude", []),
        "grok-cli": ("grok", []),
        "cursor": ("cursor", []),
        "composer": ("composer", ["cursor"]),
        "grok-cursor": ("grok", ["cursor"]),
    }
    route = egress.get("route")
    if route not in contracts:
        raise Operational("REFUSED", "egress route is unsupported")
    target, intermediaries = contracts[route]
    if binding.get("target") != target or egress.get("intermediaries") != intermediaries:
        raise Operational("REFUSED", "binding target or intermediaries do not match the fixed route")
    restrictions = egress.get("restrictions")
    if not isinstance(restrictions, list) or any(not isinstance(item, str) for item in restrictions):
        raise Operational("REFUSED", "egress restrictions must be a string list")
    if binding.get("model") is not None and not isinstance(binding.get("model"), str):
        raise Operational("REFUSED", "binding model must be null or a string")
    if not isinstance(binding.get("source"), str) or not binding["source"]:
        raise Operational("REFUSED", "binding source must be non-empty")


def cmd_init(args) -> tuple[str, dict]:
    info = repo_info(args.repo)
    root = scratch_root(info["workspace_root"])
    ensure_private_dir(root)
    rd = run_dir(args.run_id, root)
    if args.plan:
        absolute = os.path.realpath(os.path.abspath(args.plan))
        if os.path.commonpath([info["workspace_root"], absolute]) != info["workspace_root"]:
            raise Operational("REFUSED", "plan must be inside the canonical workspace")
        data = Path(absolute).read_bytes()
        supplied = args.plan_digest
        source = {"kind": "plan", "path": os.path.relpath(absolute, info["workspace_root"]), "digest": digest_bytes(data)}
    else:
        data = _read_external(args.prompt_brief, "prompt brief")
        supplied = args.prompt_digest
        source = {"kind": "prompt", "path": "source/bare-prompt.md", "digest": digest_bytes(data)}
    if source["digest"] != supplied:
        raise Operational("REFUSED", "source digest does not match content")
    binding = _json_arg(args.binding_json, "binding")
    egress = _json_arg(args.egress_json, "egress")
    _validate_route(binding, egress)
    if os.path.exists(rd):
        with locked_manifest(args.run_id) as existing:
            validate_repo(existing)
            if existing.get("source") != source or existing.get("binding") != binding or existing.get("egress") != egress:
                raise Operational("BLOCKED", "run id already belongs to a different source or fixed-route contract")
            return "READY", {"run_id": args.run_id, "resumed": True, "source_kind": source["kind"], "source_digest": source["digest"], "recovery_path": rd}
    ensure_private_dir(rd)
    for child in ("units", "jobs", "packets", "source", ".locks"):
        ensure_private_dir(os.path.join(rd, child))
    create_private(os.path.join(rd, "manifest.lock"), b"")
    if source["kind"] == "prompt":
        create_private(os.path.join(rd, source["path"]), data)
    created = now_iso()
    doc = {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "run_id": safe_id(args.run_id, "run id"),
        "created_at": created,
        "updated_at": created,
        "repository": {key: info[key] for key in ("workspace_root", "repo_store", "repo_dev", "repo_ino", "identity_digest")},
        "initial_snapshot": info["snapshot"],
        "source": source,
        "binding": binding,
        "egress": egress,
        "plan_checkpoint": None,
        "integration_lock": None,
        "units": {},
        "verifications": [],
        "blockers": [],
        "events": [{"at": created, "kind": "run-created"}],
    }
    create_private(os.path.join(rd, "manifest.json"), (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode())
    return "READY", {"run_id": args.run_id, "resumed": False, "source_kind": source["kind"], "source_digest": source["digest"], "recovery_path": rd}


def _validate_description(description: str) -> str:
    value = description.strip()
    if not value or "\0" in value or len(value.encode()) > 4096:
        raise Operational("REFUSED", f"description must be non-empty and at most 4096 bytes. {DESCRIPTION_STANDARD}")
    if value.lower().startswith(("wip", "partial", "todo")) or value.startswith("["):
        raise Operational("REFUSED", f"replace the dynamic placeholder with a semantic description. {DESCRIPTION_STANDARD}")
    return value


def cmd_checkpoint_plan(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        if doc["source"]["kind"] != "plan":
            if not info["snapshot"]["empty"]:
                raise Operational("BLOCKED", "prompt-backed execution requires an empty canonical working-copy change")
            return "NOOP", {"checkpoint": None}
        path = doc["source"]["path"]
        snap = info["snapshot"]
        if snap["empty"]:
            return "NOOP", {"checkpoint": doc.get("plan_checkpoint")}
        if snap["changed_paths"] != [path]:
            raise Operational("BLOCKED", "canonical delta is not exactly the selected plan", {"changed_paths": snap["changed_paths"]})
        description = args.description
        _validate_description(description)
        jj(info["workspace_root"], "describe", "-m", description)
        checkpoint = snapshot(info["workspace_root"])
        jj(info["workspace_root"], "new", "-m", "[describe implementation after verification]")
        doc["plan_checkpoint"] = checkpoint
        event(doc, "plan-checkpoint", detail={"change_id": checkpoint["change_id"], "commit_id": checkpoint["commit_id"]})
        return "CHECKPOINTED", {"checkpoint": checkpoint, "description_rule": DESCRIPTION_STANDARD}


def cmd_prepare(args) -> tuple[str, dict]:
    packet = _read_external(args.packet, "unit packet")
    packet_digest = digest_bytes(packet)
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        base = jj_text(info["workspace_root"], "log", "--no-graph", "-r", args.base, "-T", "commit_id")
        if info["snapshot"]["commit_id"] != base or not info["snapshot"]["empty"] or info["snapshot"]["conflict"]:
            raise Operational("BLOCKED", "canonical working-copy change must be empty, conflict-free, and equal the requested base")
        uid = safe_id(args.unit_id, "unit id")
        unit_root = os.path.join(run_dir(args.run_id), "units", uid)
        existing = doc["units"].get(uid)
        prior_attempts = []
        if existing:
            if (
                existing.get("attempt", {}).get("attempt_id") == args.attempt_id
                and existing.get("workspace", {}).get("base") == base
                and existing.get("packet", {}).get("digest") == packet_digest
                and existing.get("dependencies") == list(args.dependency)
                and existing.get("state") in {"queued", "authoring", "integration-pending"}
            ):
                authorization = existing.get("authorization", {})
                return "PREPARED", {
                    "unit_id": uid,
                    "attempt_id": args.attempt_id,
                    "workspace": existing["workspace"]["path"],
                    "result_dir": existing["result_dir"],
                    "packet_path": existing["packet"]["path"],
                    "packet_digest": packet_digest,
                    "authorization_path": authorization.get("path"),
                    "authorization_digest": authorization.get("digest"),
                    "adapter": os.path.realpath(os.path.join(os.path.dirname(__file__), "cross-model-work.sh")),
                    "base": base,
                    "resumed": True,
                }
            cleanup = existing.get("cleanup")
            if existing.get("state") != "cleaned" or not isinstance(cleanup, dict) or cleanup.get("abandoned") is not True:
                raise Operational("REFUSED", "a fresh attempt requires an explicitly abandoned and cleaned prior attempt")
            if existing.get("dependencies") != list(args.dependency):
                raise Operational("BLOCKED", "retry dependencies differ from the recorded unit")
            prior_attempts = list(existing.get("prior_attempts", [])) + [{key: value for key, value in existing.items() if key != "prior_attempts"}]
            if os.path.isdir(unit_root):
                shutil.rmtree(unit_root)
        ensure_private_dir(unit_root)
        result = os.path.join(unit_root, "result")
        ensure_private_dir(result)
        packet_path = os.path.join(unit_root, "packet.md")
        if not os.path.exists(packet_path):
            create_private(packet_path, packet)
        workspace = os.path.join(unit_root, "workspace")
        route = doc.get("egress", {}).get("route")
        contracts = {
            "codex": ("codex", "codex", [], "adapter-enforced", "auto"),
            "claude": ("claude", "claude", [], "cooperative", "auto"),
            "grok-cli": ("grok", "grok", [], "cooperative", "auto"),
            "cursor": ("cursor", "cursor-agent", [], "adapter-enforced", "auto"),
            "composer": ("composer", "cursor-agent", ["cursor"], "adapter-enforced", "composer-2.5-fast"),
            "grok-cursor": ("grok", "cursor-agent", ["cursor"], "adapter-enforced", "cursor-grok-4.6-high"),
        }
        if route not in contracts:
            raise Operational("REFUSED", "egress route is unsupported")
        target, harness, intermediaries, restriction_posture, default_model = contracts[route]
        authorization = {
            "schema_version": 1,
            "run_id": args.run_id,
            "unit_id": uid,
            "attempt_id": args.attempt_id,
            "route": route,
            "target": target,
            "harness": harness,
            "intermediaries": intermediaries,
            "model_requested": doc.get("binding", {}).get("model") or default_model,
            "restriction_posture": restriction_posture,
            "restrictions": doc.get("egress", {}).get("restrictions", []),
            "activity_posture": args.activity_posture,
            "packet_digest": packet_digest,
        }
        authorization_bytes = (json.dumps(authorization, sort_keys=True, separators=(",", ":")) + "\n").encode()
        authorization_path = os.path.join(unit_root, "authorization.json")
        if not os.path.exists(authorization_path):
            create_private(authorization_path, authorization_bytes)
        workspace_name = f"ce-work-{digest_bytes((args.run_id + ':' + uid).encode())[:20]}"
        placeholder = f"[describe {uid} after verification]"
        if not os.path.exists(workspace):
            jj(info["workspace_root"], "workspace", "add", "--name", workspace_name, "-r", base, "-m", placeholder, workspace)
            os.chmod(workspace, 0o700)
        unit = {
            "unit_id": uid,
            "state": "queued",
            "dependencies": list(args.dependency),
            "wave": {"id": args.wave_id, "position": args.wave_position, "base": base},
            "workspace": {"path": workspace, "name": workspace_name, "base": base},
            "packet": {"path": packet_path, "digest": packet_digest},
            "authorization": {"path": authorization_path, "digest": digest_bytes(authorization_bytes)},
            "result_dir": result,
            "attempt": {"attempt_id": safe_id(args.attempt_id, "attempt id"), "job_id": None, "process_state": "never-started"},
            "transport": None,
            "integration": None,
            "cleanup": None,
            "prior_attempts": prior_attempts,
        }
        doc["units"][uid] = unit
        event(doc, "workspace-prepared", uid, {"workspace_name": workspace_name, "base": base})
    return "PREPARED", {"unit_id": uid, "attempt_id": args.attempt_id, "workspace": workspace, "result_dir": result, "packet_path": packet_path, "packet_digest": packet_digest, "authorization_path": authorization_path, "authorization_digest": digest_bytes(authorization_bytes), "adapter": os.path.realpath(os.path.join(os.path.dirname(__file__), "cross-model-work.sh")), "base": base}


def _unit(doc: dict, unit_id: str) -> dict:
    unit = doc.get("units", {}).get(unit_id)
    if not unit:
        raise Operational("REFUSED", "unknown unit")
    return unit


def cmd_record_job(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        unit = _unit(doc, args.unit_id)
        attempt = unit["attempt"]
        if attempt["attempt_id"] != args.attempt_id:
            raise Operational("BLOCKED", "attempt identity mismatch")
        if attempt["job_id"] not in (None, args.job_id):
            raise Operational("AMBIGUOUS", "attempt is already bound to another job")
        attempt["job_id"] = safe_id(args.job_id, "job id")
        attempt["process_state"] = "running"
        unit["state"] = "authoring"
        event(doc, "job-bound", args.unit_id, {"job_id": args.job_id})
    return "AUTHORING", {"unit_id": args.unit_id, "job_id": args.job_id}


def cmd_authorize_dispatch(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        unit = _unit(doc, args.unit_id)
        attempt = unit["attempt"]
        expected = {
            "attempt_id": attempt["attempt_id"],
            "workspace": unit["workspace"]["path"],
            "packet": unit["packet"]["path"],
            "packet_digest": unit["packet"]["digest"],
            "authorization": unit["authorization"]["path"],
            "authorization_digest": unit["authorization"]["digest"],
            "result_dir": unit["result_dir"],
        }
        observed = {
            "attempt_id": args.attempt_id,
            "workspace": os.path.abspath(args.workspace),
            "packet": os.path.abspath(args.packet),
            "packet_digest": args.packet_digest,
            "authorization": os.path.abspath(args.authorization),
            "authorization_digest": args.authorization_digest,
            "result_dir": os.path.abspath(args.result_dir),
        }
        if observed != expected:
            raise Operational("BLOCKED", "dispatch does not match the exact controller-recorded authorization", {"expected": expected, "observed": observed})
        authorization_bytes = read_private(expected["authorization"], MAX_JSON_BYTES)
        if digest_bytes(authorization_bytes) != expected["authorization_digest"]:
            raise Operational("BLOCKED", "authorization bytes no longer match the recorded digest")
        packet_bytes = read_private(expected["packet"], MAX_PACKET_BYTES)
        if digest_bytes(packet_bytes) != expected["packet_digest"]:
            raise Operational("BLOCKED", "packet bytes no longer match the recorded digest")
        job_id = safe_id(args.job_id, "job id")
        attempt["job_id"] = job_id
        attempt["process_state"] = "running"
        unit["state"] = "authoring"
        event(doc, "dispatch-authorized", args.unit_id, {"job_id": job_id})
    return "AUTHORIZED", {"run_id": args.run_id, "unit_id": args.unit_id, "attempt_id": args.attempt_id, "job_id": args.job_id, "packet_digest": args.packet_digest}


def _job_state(run_id: str, job_id: str) -> str:
    directory = os.path.join(run_dir(run_id), "jobs", job_id)
    status_path = os.path.join(directory, "status")
    if os.path.exists(status_path):
        return read_private(status_path, 256).decode().strip()
    return "running" if os.path.exists(os.path.join(directory, "pid")) else "never-started"


def cmd_sync_job(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        unit = _unit(doc, args.unit_id)
        job_id = unit["attempt"].get("job_id")
        state = _job_state(args.run_id, job_id) if job_id else "never-started"
        unit["attempt"]["process_state"] = state
        event(doc, "job-synced", args.unit_id, {"process_state": state})
    return "SYNCED", {"unit_id": args.unit_id, "process_state": state}


def cmd_terminalize(args) -> tuple[str, dict]:
    cmd_sync_job(args)
    with locked_manifest(args.run_id, write=True) as doc:
        unit = _unit(doc, args.unit_id)
        if unit["attempt"]["process_state"] != "done":
            raise Operational("BLOCKED", "worker is not authoritatively done")
        result_path = os.path.join(unit["result_dir"], "implementation-result.json")
        result = read_private_json(result_path)
        terminal_status = result.get("terminal_status")
        if terminal_status not in {"completed", "blocked", "scope_expansion"}:
            raise Operational("BLOCKED", "worker result has no host-resolvable terminal status")
        if terminal_status != "completed":
            unit["state"] = "authored"
            unit["terminal_receipt"] = result
            raise Operational("BLOCKED", "worker returned a host-resolvable blocker", {"terminal_status": terminal_status, "summary": result.get("summary", "")})
        transport = snapshot(unit["workspace"]["path"])
        if transport["conflict"]:
            raise Operational("BLOCKED", "worker change contains unresolved conflicts")
        reported = result.get("changed_files")
        if not isinstance(reported, list) or any(not isinstance(path, str) for path in reported):
            raise Operational("BLOCKED", "worker changed-files evidence is malformed")
        unit["transport"] = transport
        unit["terminal_receipt"] = result
        unit["state"] = "integration-pending"
        event(doc, "unit-terminalized", args.unit_id, {"change_id": transport["change_id"], "commit_id": transport["commit_id"]})
    return "TERMINALIZED", {"unit_id": args.unit_id, "transport": transport}


def _restore_operation(repo: str, operation_id: str) -> dict:
    jj(repo, "operation", "restore", operation_id)
    jj(repo, "workspace", "update-stale", check=False)
    return snapshot(repo)


def _run_verification(repo: str, command: list[str], log_path: str) -> int:
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise Operational("REFUSED", "verification command is required")
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        try:
            proc = subprocess.run(command, cwd=repo, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, check=False, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            return proc.returncode
        except OSError as exc:
            stream.write(f"verification launch failed: {exc}\n".encode())
            return 127


def cmd_integrate(args) -> tuple[str, dict]:
    from unit_workspace_ignored import diff_ignored_state, inventory_ignored_state

    description = _validate_description(args.description)
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        unit = _unit(doc, args.unit_id)
        if unit["state"] != "integration-pending" or not unit.get("transport"):
            raise Operational("REFUSED", "unit is not ready for integration")
        if unit["transport"].get("parent_commit_ids") != [unit["workspace"]["base"]]:
            raise Operational("BLOCKED", "terminalized worker change does not have the recorded base as its sole parent")
        unresolved_dependencies = [
            dependency
            for dependency in unit.get("dependencies", [])
            if doc.get("units", {}).get(dependency, {}).get("state") != "cleaned"
        ]
        if unresolved_dependencies:
            raise Operational("BLOCKED", "unit dependencies do not have accepted canonical changes", {"dependencies": unresolved_dependencies})
        wave_id = unit.get("wave", {}).get("id")
        if wave_id:
            members = [candidate for candidate in doc["units"].values() if candidate.get("wave", {}).get("id") == wave_id]
            unterminated = [candidate["unit_id"] for candidate in members if candidate.get("state") not in {"integration-pending", "cleaned"}]
            if unterminated:
                raise Operational("BLOCKED", "every wave worker must terminalize before the first integration", {"units": unterminated})
            earlier = [candidate["unit_id"] for candidate in members if candidate["wave"]["position"] < unit["wave"]["position"] and candidate.get("state") != "cleaned"]
            if earlier:
                raise Operational("BLOCKED", "earlier wave changes must be accepted before this integration", {"units": earlier})
            paths_by_unit = {candidate["unit_id"]: set(candidate.get("transport", {}).get("changed_paths", [])) for candidate in members if candidate.get("transport")}
            collisions = {
                f"{left}:{right}": sorted(paths_by_unit[left] & paths_by_unit[right])
                for index, left in enumerate(paths_by_unit)
                for right in list(paths_by_unit)[index + 1:]
                if paths_by_unit[left] & paths_by_unit[right]
            }
            if collisions:
                raise Operational("BLOCKED", "wave changes have a changed-path collision", {"collisions": collisions})
        if doc.get("integration_lock"):
            raise Operational("BLOCKED", "another integration owns the canonical workspace")
        before = info["snapshot"]
        if not before["empty"] or before["conflict"]:
            raise Operational("BLOCKED", "canonical working-copy change is not empty and conflict-free")
        token = secrets.token_hex(24)
        doc["integration_lock"] = {"unit_id": args.unit_id, "nonce": token, "operation_id": before["operation_id"]}
        unit["integration"] = {"pre": before, "description_rule": DESCRIPTION_STANDARD}
        event(doc, "integration-started", args.unit_id, {"operation_id": before["operation_id"]})
    repo = info["workspace_root"]
    accepted = False
    try:
        jj(repo, "squash", "--from", unit["transport"]["change_id"], "--into", "@", "--use-destination-message")
        applied = snapshot(repo)
        if applied["conflict"] or applied["changed_paths"] != unit["transport"]["changed_paths"]:
            raise Operational("BLOCKED", "integrated delta differs from the terminalized worker change")
        ignored_before = inventory_ignored_state(repo)
        log_path = os.path.join(run_dir(args.run_id), "units", args.unit_id, f"verification-{secrets.token_hex(6)}.log")
        verification_exit = _run_verification(repo, list(args.verification_command), log_path)
        verified = snapshot(repo)
        ignored_state = diff_ignored_state(ignored_before, inventory_ignored_state(repo))
        if verification_exit != 0 or verified != applied:
            raise Operational("BLOCKED", "authoritative verification failed or changed canonical Jujutsu state", {"verification_exit": verification_exit, "verification_log": log_path})
        jj(repo, "describe", "-m", description)
        canonical = snapshot(repo)
        os.unlink(log_path)
        with locked_manifest(args.run_id) as doc:
            pending_units = [
                candidate_id
                for candidate_id, candidate in doc["units"].items()
                if candidate_id != args.unit_id and candidate.get("state") == "integration-pending"
            ]
        if pending_units:
            jj(repo, "new", "-m", f"[describe the next verified unit: {pending_units[0]}]")
        with locked_manifest(args.run_id, write=True) as doc:
            unit = _unit(doc, args.unit_id)
            unit["state"] = "accepted"
            unit["integration"].update({"applied": applied, "canonical": canonical, "verification_exit": 0, "verification_summary": args.verification_summary, "ignored_state": ignored_state})
            doc["integration_lock"] = None
            event(doc, "canonical-change-accepted", args.unit_id, {"change_id": canonical["change_id"], "commit_id": canonical["commit_id"]})
        accepted = True
        cmd_cleanup(type("Args", (), {"run_id": args.run_id, "unit_id": args.unit_id, "abandon": False, "expect_transport": None, "expect_job": None})())
        return "UNIT_ACCEPTED", {"unit_id": args.unit_id, "canonical_change": canonical, "ignored_state": ignored_state, "description_rule": DESCRIPTION_STANDARD}
    except Operational as exc:
        if accepted:
            with locked_manifest(args.run_id, write=True) as doc:
                doc["blockers"].append({"at": now_iso(), "unit_id": args.unit_id, "reason": "canonical change accepted but workspace cleanup is incomplete"})
                event(doc, "post-integration-cleanup-blocked", args.unit_id)
            raise Operational("BLOCKED", "canonical change accepted but workspace cleanup is incomplete", {"canonical_change": canonical, "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id)}) from exc
        restored = _restore_operation(repo, before["operation_id"])
        if restored["change_id"] != before["change_id"] or restored["commit_id"] != before["commit_id"] or restored["delta_sha256"] != before["delta_sha256"]:
            exc.detail["retain_integration_lock"] = True
            raise Operational("BLOCKED", "exact Jujutsu operation restoration could not be proven", exc.detail) from exc
        with locked_manifest(args.run_id, write=True) as doc:
            doc["integration_lock"] = None
            doc["blockers"].append({"at": now_iso(), "unit_id": args.unit_id, "reason": str(exc)})
            event(doc, "integration-restored", args.unit_id, {"operation_id": before["operation_id"]})
        raise


def cmd_verify_run(args) -> tuple[str, dict]:
    from unit_workspace_ignored import diff_ignored_state, inventory_ignored_state

    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        if any(unit.get("state") != "cleaned" for unit in doc["units"].values()):
            raise Operational("REFUSED", "verify-run requires every unit to have an accepted and cleaned canonical change")
        before = info["snapshot"]
    ignored_before = inventory_ignored_state(info["workspace_root"])
    log_path = os.path.join(run_dir(args.run_id), "jobs", f"run-verification-{secrets.token_hex(6)}.log")
    exit_code = _run_verification(info["workspace_root"], list(args.verification_command), log_path)
    after = snapshot(info["workspace_root"])
    if after != before:
        restored = _restore_operation(info["workspace_root"], before["operation_id"])
        if restored["change_id"] != before["change_id"] or restored["commit_id"] != before["commit_id"]:
            raise Operational("BLOCKED", "plan-wide verification changed state and exact operation restoration failed", {"verification_log": log_path})
    ignored_state = diff_ignored_state(ignored_before, inventory_ignored_state(info["workspace_root"]))
    receipt = {"at": now_iso(), "verification_exit": exit_code, "canonical_change": before, "summary": args.verification_summary, "log_sha256": digest_bytes(Path(log_path).read_bytes()), "ignored_state": ignored_state}
    receipt["evidence_digest"] = digest_bytes(json.dumps(receipt, sort_keys=True).encode())
    with locked_manifest(args.run_id, write=True) as doc:
        doc["verifications"].append(receipt)
        event(doc, "run-verification-passed" if exit_code == 0 else "run-verification-failed")
    if exit_code:
        raise Operational("BLOCKED", "plan-wide authoritative verification failed", {"verification_log": log_path, "verification_exit": exit_code})
    os.unlink(log_path)
    return "RUN_VERIFIED", receipt


def cmd_status(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        body = dict(doc)
        body["recovery_path"] = run_dir(args.run_id)
        if args.unit_id:
            body = {"run_id": args.run_id, "unit": _unit(doc, args.unit_id), "verifications": doc["verifications"], "blockers": doc["blockers"]}
    return "STATUS", body


def cmd_resume(args) -> tuple[str, dict]:
    run_id = args.run_id
    if not run_id:
        if not args.repo or not args.plan_digest or not re.fullmatch(r"[0-9a-f]{64}", args.plan_digest):
            raise Operational("REFUSED", "resume requires --run-id or both --repo and a lowercase SHA-256 --plan-digest")
        info = repo_info(args.repo)
        root = scratch_root(info["workspace_root"])
        candidates = []
        if os.path.isdir(root):
            for entry in os.scandir(root):
                if entry.name == ".locks" or not entry.is_dir(follow_symlinks=False) or not SAFE_ID.fullmatch(entry.name):
                    continue
                manifest = os.path.join(entry.path, "manifest.json")
                if not os.path.isfile(manifest):
                    continue
                doc = read_private_json(manifest)
                if (
                    doc.get("schema_version") == SCHEMA_VERSION
                    and doc.get("repository", {}).get("identity_digest") == info["identity_digest"]
                    and doc.get("source", {}).get("kind") == "plan"
                    and doc.get("source", {}).get("digest") == args.plan_digest
                    and (
                        any(unit.get("state") != "cleaned" for unit in doc.get("units", {}).values())
                        or not any(receipt.get("verification_exit") == 0 for receipt in doc.get("verifications", []))
                    )
                ):
                    candidates.append(entry.name)
        if not candidates:
            raise Operational("NOT_FOUND", "no unfinished run matches the Jujutsu repository and plan digest", {"candidates": []})
        if len(candidates) > 1:
            raise Operational("AMBIGUOUS", "multiple unfinished runs match; pass --run-id", {"candidates": sorted(candidates)})
        run_id = candidates[0]
        os.environ["ROCKETCLAW_WORK_RUNS_ROOT"] = root
    run_id = safe_id(run_id, "run id")
    with locked_manifest(run_id) as doc:
        validate_repo(doc)
        lock = dict(doc["integration_lock"]) if isinstance(doc.get("integration_lock"), dict) else None
        repo = doc["repository"]["workspace_root"]
    actions = []
    if lock:
        restored = _restore_operation(repo, lock["operation_id"])
        with locked_manifest(run_id, write=True) as doc:
            unit = _unit(doc, lock["unit_id"])
            expected = unit.get("integration", {}).get("pre")
            if not expected or restored["change_id"] != expected["change_id"] or restored["commit_id"] != expected["commit_id"] or restored["delta_sha256"] != expected["delta_sha256"]:
                raise Operational("BLOCKED", "interrupted integration could not restore its exact Jujutsu operation", {"retain_integration_lock": True})
            doc["integration_lock"] = None
            unit["state"] = "integration-pending"
            event(doc, "integration-restored-by-resume", lock["unit_id"], {"operation_id": lock["operation_id"]})
        actions.append({"unit_id": lock["unit_id"], "action": "integration-restored", "operation_id": lock["operation_id"]})
    with locked_manifest(run_id) as doc:
        validate_repo(doc)
        pending = []
        for unit_id, unit in doc["units"].items():
            if unit["state"] == "authoring" and unit["attempt"].get("job_id"):
                pending.append((unit_id, "observe"))
            elif unit["state"] == "accepted":
                pending.append((unit_id, "cleanup"))
    for unit_id, action in pending:
        if action == "observe":
            state = cmd_sync_job(type("Args", (), {"run_id": run_id, "unit_id": unit_id})())[1]["process_state"]
            actions.append({"unit_id": unit_id, "action": "observed", "process_state": state})
            if state == "done":
                terminal = cmd_terminalize(type("Args", (), {"run_id": run_id, "unit_id": unit_id})())[1]
                actions.append({"unit_id": unit_id, "action": "terminalized", "transport": terminal["transport"]})
        else:
            cmd_cleanup(type("Args", (), {"run_id": run_id, "unit_id": unit_id, "abandon": False, "expect_transport": None, "expect_job": None})())
            actions.append({"unit_id": unit_id, "action": "workspace-cleaned"})
    return "RESUMED", {"run_id": run_id, "actions": actions, "redispatched": False}


def cmd_cleanup(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        unit = _unit(doc, args.unit_id)
        if unit["state"] not in {"accepted", "cleaned"} and not args.abandon:
            raise Operational("REFUSED", "workspace cleanup requires accepted integration or explicit abandonment")
        if args.abandon and unit["state"] != "cleaned":
            transport = unit.get("transport")
            job_id = unit.get("attempt", {}).get("job_id")
            process_state = unit.get("attempt", {}).get("process_state")
            if transport:
                expected = args.expect_transport
                if expected not in {transport.get("change_id"), transport.get("commit_id")}:
                    raise Operational("REFUSED", "abandonment requires the exact terminalized change or commit ID")
            elif not job_id or args.expect_job != job_id or process_state not in TERMINAL_PROCESS:
                raise Operational("REFUSED", "transport-free abandonment requires the exact terminal job ID")
        workspace = unit["workspace"]
        info = validate_repo(doc)
        if unit["state"] != "cleaned":
            jj(info["workspace_root"], "workspace", "forget", workspace["name"], check=False)
            if os.path.isdir(workspace["path"]):
                shutil.rmtree(workspace["path"])
            unit["state"] = "cleaned"
            unit["cleanup"] = {"at": now_iso(), "abandoned": bool(args.abandon)}
            event(doc, "workspace-cleaned", args.unit_id, {"workspace_name": workspace["name"]})
    return "CLEANED", {"unit_id": args.unit_id}


def cmd_reap(args) -> tuple[str, dict]:
    return cmd_sync_job(args)


def cmd_claim_fallback(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        unit = _unit(doc, args.unit_id)
        if unit["attempt"]["process_state"] not in TERMINAL_PROCESS - {"done"}:
            raise Operational("REFUSED", "fallback requires authoritative failed or reaped state")
        claim = unit.setdefault("fallback", {}).get("claim")
        if claim:
            return "FALLBACK_ALREADY_AUTHORIZED", {"unit_id": args.unit_id, "start_native": False, "claim": claim}
        mode = doc.get("binding", {}).get("mode")
        if mode == "require" and (args.caller_mode != "interactive" or not args.confirm_native):
            raise Operational("CHOICE_REQUIRED", "required external route needs explicit interactive native-fallback confirmation")
        claim = {"at": now_iso(), "mode": mode, "caller_mode": args.caller_mode, "confirmed_native": bool(args.confirm_native)}
        unit["fallback"] = {"claim": claim, "completion": None}
        event(doc, "native-fallback-authorized", args.unit_id)
    return "FALLBACK_AUTHORIZED", {"unit_id": args.unit_id, "start_native": True, "claim": claim}


def cmd_complete_fallback(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        unit = _unit(doc, args.unit_id)
        fallback = unit.get("fallback")
        if not fallback or not fallback.get("claim"):
            raise Operational("REFUSED", "native fallback completion requires an authorized claim")
        current = info["snapshot"]
        accepted = args.accepted_change
        if accepted not in {current["change_id"], current["commit_id"]}:
            raise Operational("BLOCKED", "accepted fallback identity does not match the canonical Jujutsu change")
        _validate_description(jj_text(info["workspace_root"], "log", "--no-graph", "-r", "@", "-T", "description"))
        completion = {"at": now_iso(), "canonical_change": current, "evidence_digest": args.evidence_digest, "summary": args.summary, "description_rule": DESCRIPTION_STANDARD}
        fallback["completion"] = completion
        unit["state"] = "accepted"
        event(doc, "native-fallback-completed", args.unit_id)
    cmd_cleanup(type("Args", (), {"run_id": args.run_id, "unit_id": args.unit_id, "abandon": False, "expect_transport": None, "expect_job": None})())
    return "FALLBACK_COMPLETED", {"unit_id": args.unit_id, "completion": completion}
