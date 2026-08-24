"""Private JJ workspace state for bounded external implementation units."""

from __future__ import annotations

import argparse
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
UNIT_STATES = {
    "queued", "authoring", "authored", "integration-pending", "integrated",
    "restoring", "verified", "committed", "preserved", "cleaned", "native-completed",
}
COMMIT_GUIDANCE = "Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards."
PROTOCOL_ACTOR = ("AI Assistant", "ai:assistant")


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
    configured = {value.strip() for value in os.environ.get("CE_WORK_TEST_FAULT", "").split(",") if value.strip()}
    if point in configured:
        raise Operational("INTERRUPTED", f"injected interruption at {point}")


def safe_id(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value) or not value.strip("."):
        raise Operational("REFUSED", f"unsafe {label}: {value!r}")
    return value


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run(argv: list[str], *, cwd: str | None = None, input_data: bytes | None = None, check: bool = True) -> bytes:
    proc = subprocess.run(argv, cwd=cwd, input=input_data, capture_output=True, check=False)
    if check and proc.returncode != 0:
        message = proc.stderr.decode("utf-8", "replace").strip()
        raise Operational("BLOCKED", f"{' '.join(argv)} failed: {message}")
    return proc.stdout


def jj(repo: str, *args: str, input_data: bytes | None = None, check: bool = True) -> bytes:
    argv = ["jj", "-R", repo, *args]
    if args and args[0] in {"commit", "describe", "duplicate", "new", "squash", "split"}:
        argv[1:1] = ["--config", f"user.name={PROTOCOL_ACTOR[0]}", "--config", f"user.email={PROTOCOL_ACTOR[1]}"]
    return _run(argv, input_data=input_data, check=check)


def jj_text(repo: str, *args: str, check: bool = True) -> str:
    return jj(repo, *args, check=check).decode("utf-8", "surrogateescape").strip()


def workspace_root(path: str) -> str:
    out = _run(["jj", "-R", os.path.abspath(path), "workspace", "root"], check=False).decode().strip()
    if not out:
        raise Operational("REFUSED", "a writable JJ workspace is required")
    return os.path.realpath(out)


def local_tmp_root(path: str) -> str:
    try:
        root = workspace_root(path)
    except Operational:
        root = os.path.abspath(path)
    return os.path.join(root, ".tmp", "rocketclaw")


def ensure_private_dir(path: str) -> None:
    os.makedirs(path, mode=0o700, exist_ok=True)
    st = os.lstat(path)
    if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode):
        raise TrustFailure(f"not a real directory: {path}")
    if hasattr(os, "geteuid") and st.st_uid != os.geteuid():
        raise TrustFailure(f"directory is not owned by current user: {path}")
    if os.name != "nt":
        os.chmod(path, 0o700)


def runs_root(repo: str | None = None) -> str:
    configured = os.environ.get("CE_WORK_RUNS_ROOT")
    if configured:
        root = os.path.abspath(configured)
        marker = f"{os.sep}.tmp{os.sep}rocketclaw{os.sep}"
        if marker not in root + os.sep:
            raise TrustFailure("CE_WORK_RUNS_ROOT must be below a workspace-local .tmp/rocketclaw directory")
        ensure_private_dir(root)
        ensure_private_dir(os.path.join(root, ".locks"))
        return root
    anchor = repo or os.getcwd()
    root = os.path.join(local_tmp_root(anchor), "ce-work")
    ensure_private_dir(root)
    ensure_private_dir(os.path.join(root, ".locks"))
    return root


def ensure_root(repo: str | None = None) -> str:
    return runs_root(repo)


def run_dir(run_id: str, repo: str | None = None) -> str:
    return os.path.join(runs_root(repo), safe_id(run_id, "run id"))


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
        if not stat.S_ISREG(st.st_mode) or st.st_size > cap:
            raise TrustFailure(f"invalid or oversized state file: {path}")
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


def atomic_private_json(path: str, doc: dict) -> None:
    data = (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_JSON_BYTES:
        raise Operational("BLOCKED", "manifest exceeds bounded state size")
    parent = os.path.dirname(path)
    for _ in range(128):
        tmp = os.path.join(parent, f".manifest-{os.getpid()}-{secrets.token_hex(8)}")
        try:
            create_private(tmp, data)
            break
        except FileExistsError:
            continue
    else:
        raise Operational("BLOCKED", "could not reserve an atomic manifest file")
    os.replace(tmp, path)


@contextlib.contextmanager
def locked_manifest(run_id: str, write: bool = False):
    rd = run_dir(run_id)
    lock_path = os.path.join(rd, "manifest.lock")
    fd = os.open(lock_path, os.O_RDWR | O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX if write else fcntl.LOCK_SH)
        path = os.path.join(rd, "manifest.json")
        doc = read_private_json(path)
        if doc.get("schema_version") != SCHEMA_VERSION or doc.get("run_id") != run_id:
            raise TrustFailure("manifest schema or run identity mismatch")
        before = json.dumps(doc, sort_keys=True, separators=(",", ":"))
        yield doc
        after = json.dumps(doc, sort_keys=True, separators=(",", ":"))
        if write and after != before:
            doc["revision"] = int(doc.get("revision", 0)) + 1
            doc["updated_at"] = now_iso()
            atomic_private_json(path, doc)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def change_info(repo: str, revset: str = "@") -> dict:
    raw = jj_text(repo, "log", "--no-graph", "-r", f"exactly({revset}, 1)", "-T", 'change_id ++ "\\n" ++ commit_id ++ "\\n" ++ description')
    lines = raw.splitlines()
    if len(lines) < 2:
        raise Operational("BLOCKED", f"revset did not resolve to one JJ change: {revset}")
    return {"change_id": lines[0], "commit_id": lines[1], "description": "\n".join(lines[2:]).rstrip()}


def status_paths(repo: str, revset: str = "@") -> set[str]:
    raw = jj_text(repo, "diff", "--name-only", "-r", revset)
    return {line for line in raw.splitlines() if line}


def repo_info(repo: str) -> dict:
    root = workspace_root(repo)
    current = change_info(root)
    jj_root = os.path.realpath(jj_text(root, "git", "root"))
    identity = digest_bytes(jj_root.encode())
    return {
        "toplevel": root,
        "workspace_root": root,
        "jj_root": jj_root,
        "identity_digest": identity,
        "change_id": current["change_id"],
        "commit_id": current["commit_id"],
    }


def validate_repo(doc: dict) -> dict:
    current = repo_info(doc["repository"]["workspace_root"])
    for key in ("workspace_root", "jj_root", "identity_digest"):
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


def read_external_packet(path: str, label: str = "unit packet") -> bytes:
    supplied = os.path.abspath(path)
    st = os.lstat(supplied)
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode) or st.st_size > MAX_PACKET_BYTES:
        raise Operational("REFUSED", f"{label} must be a bounded regular non-symlink file")
    return Path(supplied).read_bytes()


def event(doc: dict, kind: str, unit_id: str | None = None, detail: dict | None = None) -> None:
    row = {"at": now_iso(), "kind": kind}
    if unit_id is not None:
        row["unit_id"] = unit_id
    if detail:
        row["detail"] = detail
    doc.setdefault("events", []).append(row)


def unit_accepted_commit(unit: dict) -> str | None:
    if unit.get("state") not in {"committed", "cleaned", "native-completed"}:
        return None
    return unit.get("integration", {}).get("canonical_change", {}).get("commit_id")


def accepted_unit_commit_snapshot(units: object) -> dict[str, str] | None:
    if not isinstance(units, dict):
        return None
    result = {}
    for unit_id, unit in units.items():
        commit_id = unit_accepted_commit(unit)
        if commit_id is None:
            return None
        result[unit_id] = commit_id
    return result


def unit_ready_for_run_verification(unit: object) -> bool:
    return isinstance(unit, dict) and unit_accepted_commit(unit) is not None


ROUTE_CONTRACTS = {
    "codex": {"target": "codex", "harness": "codex", "intermediaries": [], "default_model": "auto", "restriction_posture": "adapter-enforced"},
    "claude": {"target": "claude", "harness": "claude", "intermediaries": [], "default_model": "auto", "restriction_posture": "cooperative"},
    "grok-cli": {"target": "grok", "harness": "grok", "intermediaries": [], "default_model": "auto", "restriction_posture": "cooperative"},
    "cursor": {"target": "cursor", "harness": "cursor-agent", "intermediaries": [], "default_model": "auto", "restriction_posture": "adapter-enforced"},
    "composer": {"target": "composer", "harness": "cursor-agent", "intermediaries": ["cursor"], "default_model": "composer-2.5-fast", "restriction_posture": "adapter-enforced"},
    "grok-cursor": {"target": "grok", "harness": "cursor-agent", "intermediaries": ["cursor"], "default_model": "cursor-grok-4.6-high", "restriction_posture": "adapter-enforced"},
}


def fixed_route_contract(binding: dict, egress: dict, word: str = "BLOCKED") -> dict:
    if set(binding) != {"mode", "target", "model", "source"} or binding.get("mode") not in {"prefer", "require"}:
        raise Operational(word, "binding must contain a valid mode, target, model, and source")
    contract = ROUTE_CONTRACTS.get(egress.get("route"))
    if not contract or binding.get("target") != contract["target"] or egress.get("intermediaries") != contract["intermediaries"]:
        raise Operational(word, "binding does not match the sanctioned fixed route")
    return contract


def attempt_authorization(doc: dict, activity_posture: str, unit_id: str, attempt_id: str, packet_digest: str) -> dict:
    contract = fixed_route_contract(doc["binding"], doc["egress"])
    return {
        "schema_version": 1, "run_id": doc["run_id"], "unit_id": unit_id,
        "attempt_id": attempt_id, "route": doc["egress"]["route"],
        "target": contract["target"], "harness": contract["harness"],
        "intermediaries": contract["intermediaries"],
        "model_requested": doc["binding"].get("model") or contract["default_model"],
        "restriction_posture": contract["restriction_posture"],
        "restrictions": list(doc["egress"].get("restrictions", [])),
        "activity_posture": activity_posture, "packet_digest": packet_digest,
    }


def cmd_init(args) -> tuple[str, dict]:
    info = repo_info(args.repo)
    root = ensure_root(info["workspace_root"])
    rid = safe_id(args.run_id, "run id")
    rd = os.path.join(root, rid)
    if os.path.exists(rd):
        with locked_manifest(rid) as existing:
            validate_repo(existing)
            return "READY", {"run_id": rid, "revision": existing["revision"], "resumed": True, "recovery_path": rd}
    ensure_private_dir(rd)
    for child in ("units", "jobs", "packets", "source"):
        ensure_private_dir(os.path.join(rd, child))
    binding = parse_json_arg(args.binding_json, "binding")
    egress = parse_json_arg(args.egress_json, "egress")
    fixed_route_contract(binding, egress, "REFUSED")
    if args.plan:
        source = Path(args.plan if os.path.isabs(args.plan) else os.path.join(info["workspace_root"], args.plan))
        source_bytes = source.read_bytes()
        source_kind, supplied_digest = "plan", args.plan_digest
        source_record = {"kind": "plan", "storage": "repository", "path": os.path.relpath(source, info["workspace_root"]), "digest": digest_bytes(source_bytes)}
    else:
        source_bytes = read_external_packet(args.prompt_brief, "prompt brief")
        source_kind, supplied_digest = "prompt", args.prompt_digest
        source_record = {"kind": "prompt", "storage": "run", "path": "source/bare-prompt.md", "digest": digest_bytes(source_bytes)}
        create_private(os.path.join(rd, source_record["path"]), source_bytes)
    if source_record["digest"] != supplied_digest:
        raise Operational("REFUSED", f"selected {source_kind} digest does not match content")
    create_private(os.path.join(rd, "manifest.lock"), b"")
    created = now_iso()
    doc = {
        "schema_version": SCHEMA_VERSION, "revision": 0, "run_id": rid,
        "created_at": created, "updated_at": created,
        "repository": {k: info[k] for k in ("workspace_root", "jj_root", "identity_digest")},
        "canonical": {"initial_change_id": info["change_id"], "initial_commit_id": info["commit_id"]},
        "source": source_record, "binding": binding, "egress": egress,
        "integration_lock": None, "units": {}, "verifications": [], "blockers": [],
        "events": [{"at": created, "kind": "run-created"}],
    }
    create_private(os.path.join(rd, "manifest.json"), (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode())
    return "READY", {"run_id": rid, "revision": 0, "resumed": False, "source_kind": source_kind, "source_digest": source_record["digest"], "recovery_path": rd}


def validate_description(message: str) -> str:
    value = message.strip()
    if not value or "\0" in value or len(value.encode()) > 4096:
        raise Operational("REFUSED", f"change description must be non-empty and bounded. {COMMIT_GUIDANCE}")
    return value


def cmd_checkpoint_plan(args) -> tuple[str, dict]:
    description = validate_description(args.description)
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        source = doc["source"]
        if source["kind"] != "plan":
            return "NOOP", {"checkpoint": None, "source_kind": "prompt"}
        dirty = status_paths(info["workspace_root"])
        if not dirty:
            return "NOOP", {"checkpoint": None, "change": change_info(info["workspace_root"])}
        if dirty != {source["path"]}:
            raise Operational("BLOCKED", "canonical changes are not exactly the selected plan", {"changed_paths": sorted(dirty)})
        jj(info["workspace_root"], "commit", "-m", description, f'root-file:"{source["path"]}"')
        checkpoint = change_info(info["workspace_root"], "@-")
        doc["source"]["checkpoint"] = checkpoint
        event(doc, "plan-checkpoint", detail={"change_id": checkpoint["change_id"], "path": source["path"]})
        return "CHECKPOINTED", {"checkpoint": checkpoint}
