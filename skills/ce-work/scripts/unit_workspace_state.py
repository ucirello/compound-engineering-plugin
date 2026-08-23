"""Private, crash-recoverable Jujutsu workspace controller state."""

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
INTEGRATABLE_STATES = {"composition-pending", "composed", "verified"}
UNIT_STATES = {
    "queued", "authoring", "authored", "composition-pending", "composed",
    "restoring", "verified", "described", "preserved", "cleaned", "native-completed",
}
JJ_CONFIG = "snapshot.auto-track='all() ~ glob:\"root:.tmp/**\"'"


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
    configured = {v.strip() for v in os.environ.get("WORK_TEST_FAULT", "").split(",") if v.strip()}
    if point in configured:
        raise Operational("INTERRUPTED", f"injected test interruption at {point}")


def safe_id(value: str, label: str) -> str:
    if not SAFE_ID.fullmatch(value) or not value.strip("."):
        raise Operational("REFUSED", f"unsafe {label}: {value!r}")
    return value


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def jj(repo: str, *args: str, input_data: bytes | None = None, check: bool = True) -> bytes:
    proc = subprocess.run(
        ["jj", "--config", JJ_CONFIG, "--no-pager", "-R", repo, *args],
        input=input_data, capture_output=True, check=False,
    )
    if check and proc.returncode != 0:
        message = proc.stderr.decode("utf-8", "replace").strip()
        raise Operational("BLOCKED", f"jj {' '.join(args)} failed: {message}")
    return proc.stdout


def jj_text(repo: str, *args: str, check: bool = True) -> str:
    return jj(repo, *args, check=check).decode("utf-8", "surrogateescape").strip()


def workspace_root(repo: str) -> str:
    root = jj_text(os.path.abspath(repo), "workspace", "root")
    if not root:
        raise Operational("REFUSED", "repository is not a Jujutsu workspace")
    return os.path.realpath(root)


def revision_field(repo: str, revision: str, field: str) -> str:
    templates = {
        "change_id": 'change_id ++ "\\n"',
        "snapshot_id": 'commit_id ++ "\\n"',
        "description": "description",
        "parents": 'parents.map(|p| p.commit_id()).join(" ") ++ "\\n"',
    }
    return jj_text(repo, "log", "-r", revision, "--no-graph", "-T", templates[field])


def status_paths(repo: str, revision: str = "@") -> set[str]:
    out = jj_text(repo, "diff", "--summary", "-r", revision)
    paths = set()
    for line in out.splitlines():
        if len(line) >= 3:
            paths.add(line[2:])
    return paths


def semantic_snapshot(repo: str) -> dict:
    jj(repo, "util", "snapshot")
    return {
        "change_id": revision_field(repo, "@", "change_id"),
        "snapshot_id": revision_field(repo, "@", "snapshot_id"),
        "parents": revision_field(repo, "@", "parents").split(),
        "description": revision_field(repo, "@", "description"),
        "changed_paths": sorted(status_paths(repo)),
        "bookmark_digest": digest_bytes(jj(repo, "bookmark", "list", "--all-remotes")),
        "operation_id": jj_text(repo, "op", "log", "--limit", "1", "--no-graph", "-T", 'id ++ "\\n"'),
    }


def repo_info(repo: str) -> dict:
    root = workspace_root(repo)
    jj_dir = os.path.realpath(os.path.join(root, ".jj"))
    if not os.path.isdir(jj_dir):
        raise Operational("REFUSED", "Jujutsu workspace metadata is unavailable")
    current = semantic_snapshot(root)
    identity = digest_bytes((root + "\0" + jj_dir).encode())
    return {
        "toplevel": root,
        "jj_dir": jj_dir,
        "identity_digest": identity,
        "initial_change_id": current["change_id"],
        "initial_snapshot_id": current["snapshot_id"],
    }


def local_tmp_root(repo: str) -> str:
    try:
        root = workspace_root(repo)
    except Operational:
        root = os.path.abspath(repo)
    return os.path.join(root, ".tmp", "rocketclaw")


def runs_root(repo: str | None = None) -> str:
    configured = os.environ.get("WORK_RUNS_ROOT")
    if configured:
        return os.path.abspath(configured)
    if repo:
        return os.path.join(local_tmp_root(repo), "work-runs")
    raise TrustFailure("repository is required to derive the repository-local runs root")


def validate_private_dir(path: str) -> None:
    try:
        st = os.lstat(path)
    except OSError as exc:
        raise TrustFailure(f"cannot inspect private directory {path}: {exc}") from exc
    if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode):
        raise TrustFailure(f"not a real directory: {path}")
    euid = getattr(os, "geteuid", lambda: None)()
    if euid is not None and st.st_uid != euid:
        raise TrustFailure(f"directory is not owned by current user: {path}")


def ensure_private_dir(path: str) -> None:
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        pass
    validate_private_dir(path)
    try:
        fd = os.open(path, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open private directory {path}: {exc}") from exc
    try:
        os.fchmod(fd, 0o700)
    finally:
        os.close(fd)


def ensure_runs_root(root: str) -> str:
    rocketclaw_root = os.path.dirname(root)
    tmp_root = os.path.dirname(rocketclaw_root)
    paths = [root, os.path.join(root, ".locks")]
    if os.path.basename(root) == "work-runs" and os.path.basename(rocketclaw_root) == "rocketclaw" and os.path.basename(tmp_root) == ".tmp":
        paths = [tmp_root, rocketclaw_root, *paths]
    for path in paths:
        ensure_private_dir(path)
    return root


def read_private(path: str, cap: int = MAX_JSON_BYTES) -> bytes:
    fd = os.open(path, os.O_RDONLY | O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > cap:
            raise TrustFailure(f"invalid or oversized private file: {path}")
        data = bytearray()
        while len(data) <= cap:
            part = os.read(fd, min(65536, cap + 1 - len(data)))
            if not part:
                break
            data.extend(part)
        if len(data) > cap:
            raise TrustFailure(f"private file exceeds {cap} bytes: {path}")
        return bytes(data)
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
    for _ in range(128):
        tmp = os.path.join(parent, f".manifest-{os.getpid()}-{secrets.token_hex(8)}")
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


def run_dir(run_id: str, repo: str | None = None) -> str:
    rid = safe_id(run_id, "run id")
    if repo:
        return os.path.join(runs_root(repo), rid)
    configured = os.environ.get("WORK_RUNS_ROOT")
    if configured:
        return os.path.join(os.path.abspath(configured), rid)
    raise TrustFailure("WORK_RUNS_ROOT or repository context is required to locate the run")


def locate_run(run_id: str, repo: str | None = None) -> str:
    if repo:
        candidate = run_dir(run_id, repo)
        if os.path.isdir(candidate):
            return candidate
    configured = os.environ.get("WORK_RUNS_ROOT")
    if configured:
        candidate = os.path.join(os.path.abspath(configured), safe_id(run_id, "run id"))
        if os.path.isdir(candidate):
            return candidate
    if repo is None:
        try:
            candidate = run_dir(run_id, workspace_root(os.getcwd()))
        except (Operational, TrustFailure):
            candidate = ""
        if candidate and os.path.isdir(candidate):
            return candidate
    raise Operational("NOT_FOUND", "run is not available under the repository-local .tmp root")


@contextlib.contextmanager
def locked_manifest(run_id: str, write: bool = False, repo: str | None = None):
    rd = locate_run(run_id, repo)
    validate_private_dir(rd)
    lock_path = os.path.join(rd, "manifest.lock")
    try:
        fd = os.open(lock_path, os.O_RDWR | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open manifest lock: {exc}") from exc
    try:
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
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def validate_repo(doc: dict) -> dict:
    current = repo_info(doc["repository"]["toplevel"])
    for key in ("toplevel", "jj_dir", "identity_digest"):
        if current[key] != doc["repository"][key]:
            raise Operational("BLOCKED", f"canonical Jujutsu workspace identity changed ({key})")
    return current


def resolve_plan(repo: str, plan: str) -> tuple[str, str]:
    supplied = os.path.abspath(plan if os.path.isabs(plan) else os.path.join(repo, plan))
    st = os.lstat(supplied)
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise Operational("REFUSED", "selected plan must be one regular non-symlink file")
    absolute = os.path.realpath(supplied)
    if os.path.commonpath([repo, absolute]) != repo:
        raise Operational("REFUSED", "plan must be inside the canonical workspace")
    return absolute, os.path.relpath(absolute, repo)


def parse_json_arg(raw: str, label: str) -> dict:
    try:
        value = json.loads(raw)
    except ValueError as exc:
        raise Operational("REFUSED", f"invalid {label} JSON") from exc
    if not isinstance(value, dict):
        raise Operational("REFUSED", f"{label} must be a JSON object")
    return value


def event(doc: dict, kind: str, unit_id: str | None = None, detail: dict | None = None) -> None:
    row = {"at": now_iso(), "kind": kind}
    if unit_id is not None:
        row["unit_id"] = unit_id
    if detail:
        row["detail"] = detail
    doc.setdefault("events", []).append(row)


def accepted_unit_change(unit: dict) -> str | None:
    if unit.get("state") == "native-completed":
        return unit.get("fallback", {}).get("completed", {}).get("accepted_change_id")
    if unit.get("state") not in {"described", "cleaned"}:
        return None
    return unit.get("composition", {}).get("canonical_change", {}).get("change_id")


def accepted_unit_change_snapshot(units: object) -> dict[str, str] | None:
    if not isinstance(units, dict):
        return None
    result = {}
    for unit_id, unit in units.items():
        change = accepted_unit_change(unit)
        if change is None:
            return None
        result[unit_id] = change
    return result


def unit_ready_for_run_verification(unit: object) -> bool:
    return isinstance(unit, dict) and accepted_unit_change(unit) is not None


def read_external_packet(path: str, label: str = "unit packet") -> bytes:
    supplied = os.path.abspath(path)
    fd = os.open(supplied, os.O_RDONLY | O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_PACKET_BYTES:
            raise Operational("REFUSED", f"{label} is not a bounded regular file")
        return os.read(fd, MAX_PACKET_BYTES + 1)
    finally:
        os.close(fd)


def cmd_init(args) -> tuple[str, dict]:
    info = repo_info(args.repo)
    rid = safe_id(args.run_id, "run id")
    if args.plan:
        if not args.plan_digest or args.prompt_digest:
            raise Operational("REFUSED", "plan source requires only --plan-digest")
        source_abs, source_rel = resolve_plan(info["toplevel"], args.plan)
        source_bytes = Path(source_abs).read_bytes()
        source = {"kind": "plan", "path": source_rel, "digest": digest_bytes(source_bytes)}
        supplied = args.plan_digest
    else:
        if not args.prompt_digest or args.plan_digest:
            raise Operational("REFUSED", "prompt source requires only --prompt-digest")
        source_bytes = read_external_packet(args.prompt_brief, "prompt brief")
        source = {"kind": "prompt", "path": "source/bare-prompt.md", "digest": digest_bytes(source_bytes)}
        supplied = args.prompt_digest
    if source["digest"] != supplied:
        raise Operational("REFUSED", "source digest does not match content")
    binding = parse_json_arg(args.binding_json, "binding")
    egress = parse_json_arg(args.egress_json, "egress")

    root = ensure_runs_root(runs_root(info["toplevel"]))
    rd = os.path.join(root, rid)
    try:
        os.mkdir(rd, 0o700)
    except FileExistsError:
        validate_private_dir(rd)
        for name in ("manifest.lock", "manifest.json"):
            try:
                state = os.lstat(os.path.join(rd, name))
            except FileNotFoundError:
                raise Operational("BLOCKED", "run initialization is incomplete; retry after the active initializer finishes")
            if stat.S_ISLNK(state.st_mode) or not stat.S_ISREG(state.st_mode):
                raise TrustFailure(f"run initialization state is not a regular file: {name}")
        with locked_manifest(rid, repo=info["toplevel"]) as existing:
            validate_repo(existing)
            if existing.get("source") != source or existing.get("binding") != binding or existing.get("egress") != egress:
                raise Operational("BLOCKED", "run id already belongs to another source or execution contract")
            return "READY", {"run_id": rid, "resumed": True, "recovery_path": rd}
    validate_private_dir(rd)
    for child in ("units", "jobs", "packets", "source"):
        ensure_private_dir(os.path.join(rd, child))
    if source["kind"] == "prompt":
        create_private(os.path.join(rd, source["path"]), source_bytes)
    created = now_iso()
    doc = {
        "schema_version": SCHEMA_VERSION, "revision": 0, "run_id": rid,
        "created_at": created, "updated_at": created,
        "repository": info, "source": source,
        "binding": binding, "egress": egress,
        "canonical_lock": None, "units": {}, "verifications": [], "blockers": [],
        "events": [{"at": created, "kind": "run-created"}],
    }
    create_private(os.path.join(rd, "manifest.lock"), b"")
    create_private(os.path.join(rd, "manifest.json"), (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode())
    return "READY", {"run_id": rid, "resumed": False, "source_kind": source["kind"], "source_digest": source["digest"], "recovery_path": rd}


def cmd_checkpoint_plan(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        source = doc["source"]
        if source["kind"] != "plan":
            return "NOOP", {"checkpoint": None}
        dirty = status_paths(info["toplevel"])
        if not dirty:
            return "NOOP", {"checkpoint": None}
        if dirty != {source["path"]}:
            raise Operational("BLOCKED", "canonical changes are not exactly the selected plan", {"changed_paths": sorted(dirty)})
        if not args.change_description.strip():
            raise Operational("REFUSED", "checkpoint change description must be non-empty")
        before = semantic_snapshot(info["toplevel"])
        jj(info["toplevel"], "describe", "-m", args.change_description)
        checkpoint = semantic_snapshot(info["toplevel"])
        jj(info["toplevel"], "new")
        doc["plan_checkpoint"] = {"prior": before, "change": checkpoint, "path": source["path"], "digest": source["digest"], "at": now_iso()}
        event(doc, "plan-checkpoint", detail={"change_id": checkpoint["change_id"]})
        return "CHECKPOINTED", {"checkpoint": doc["plan_checkpoint"]}


ROUTE_CONTRACTS = {
    "codex": ("codex", "codex", []), "claude": ("claude", "claude", []),
    "grok-cli": ("grok", "grok", []), "cursor": ("cursor", "cursor-agent", []),
    "composer": ("composer", "cursor-agent", ["cursor"]),
    "grok-cursor": ("grok", "cursor-agent", ["cursor"]),
}


def attempt_authorization(doc: dict, posture: str, unit_id: str, attempt_id: str, packet_digest: str) -> dict:
    route = doc.get("egress", {}).get("route")
    if route not in ROUTE_CONTRACTS:
        raise Operational("BLOCKED", "unsupported fixed route")
    target, harness, intermediaries = ROUTE_CONTRACTS[route]
    binding = doc.get("binding", {})
    return {
        "schema_version": 2, "run_id": doc["run_id"], "unit_id": unit_id,
        "attempt_id": attempt_id, "route": route, "target": target, "harness": harness,
        "intermediaries": intermediaries, "model_requested": binding.get("model") or "auto",
        "restriction_posture": doc.get("egress", {}).get("restriction_posture", "cooperative"),
        "restrictions": doc.get("egress", {}).get("restrictions", []),
        "activity_posture": posture, "packet_digest": packet_digest,
    }
