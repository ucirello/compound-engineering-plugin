"""Crash-recoverable Jujutsu workspace controller for bounded implementation units."""

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
import sys
import time
from pathlib import Path
from types import SimpleNamespace

SCHEMA_VERSION = 2
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_PACKET_BYTES = 200_000
MAX_RESULT_BYTES = 5 * 1024 * 1024
MAX_IGNORED_ENTRIES = 512
MAX_IGNORED_BYTES = 64 * 1024 * 1024
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
REVISION_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
CHANGE_ID = re.compile(r"^[A-Za-z0-9]{16,128}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
TERMINAL_PROCESS = {"done", "failed", "timeout", "died-without-result"}
UNIT_STATES = {
    "queued", "authoring", "authored", "integration-pending", "integrated",
    "restoring", "verified", "described", "preserved", "cleaned", "native-completed",
}
DESCRIPTION_RULE = "Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards."


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


def validated_description(value: str | None) -> str:
    description = (value or "").strip()
    if not description or "\0" in description:
        raise Operational("REFUSED", f"change description must be non-empty and NUL-free. {DESCRIPTION_RULE}")
    return description


def test_fault(point: str) -> None:
    configured = os.environ.get("ROCKETCLAW_WORK_TEST_FAULT", "").split(",")
    if point in {value.strip() for value in configured if value.strip()}:
        raise Operational("INTERRUPTED", f"injected interruption at {point}")


def jj(repo: str, *args: str, input_data: bytes | None = None, check: bool = True) -> bytes:
    env = dict(os.environ)
    env.pop("JJ_WORKSPACE", None)
    proc = subprocess.run(
        ["jj", "--repository", repo, "--config", "snapshot.auto-track='all() ~ root:.tmp'", *args], input=input_data, capture_output=True,
        env=env, check=False,
    )
    if check and proc.returncode:
        message = proc.stderr.decode("utf-8", "replace").strip()
        raise Operational("BLOCKED", f"jj {' '.join(args)} failed: {message}")
    return proc.stdout


def jj_text(repo: str, *args: str, check: bool = True) -> str:
    return jj(repo, *args, check=check).decode("utf-8", "surrogateescape").strip()


def revision(repo: str, revset: str = "@") -> dict:
    change_id = jj_text(repo, "log", "--no-graph", "-r", revset, "-T", "change_id")
    revision_id = jj_text(repo, "log", "--no-graph", "-r", revset, "-T", "commit_id")
    description = jj(repo, "log", "--no-graph", "-r", revset, "-T", "description").decode("utf-8", "surrogateescape")
    if not CHANGE_ID.fullmatch(change_id) or not REVISION_ID.fullmatch(revision_id):
        raise Operational("BLOCKED", f"revset {revset!r} did not resolve to one Jujutsu revision")
    return {"change_id": change_id, "commit_id": revision_id, "description": description}


def changed_paths(repo: str, from_rev: str | None = None, to_rev: str = "@") -> list[str]:
    args = ["diff", "--name-only"]
    if from_rev is not None:
        args.extend(["--from", from_rev])
    args.extend(["--to", to_rev])
    paths: list[str] = []
    for line in jj_text(repo, *args).splitlines():
        if line:
            paths.append(line.strip())
    return sorted(set(paths))


def revision_contains(repo: str, ancestor: str, descendant: str) -> bool:
    resolved = jj_text(repo, "log", "--no-graph", "-r", f"{ancestor} & ::{descendant}", "-T", "commit_id", check=False)
    return resolved == ancestor


def ignored_snapshot(repo: str) -> dict[str, dict]:
    tracked = set(filter(None, jj_text(repo, "file", "list", "-r", "@").splitlines()))
    records: dict[str, dict] = {}
    total = 0
    for parent, names, files in os.walk(repo, topdown=True, followlinks=False):
        names[:] = [name for name in names if name not in {".jj", ".git", ".tmp"}]
        for name in files:
            absolute = os.path.join(parent, name)
            relative = os.path.relpath(absolute, repo)
            if relative in tracked:
                continue
            entry = os.lstat(absolute)
            if not stat.S_ISREG(entry.st_mode) or stat.S_ISLNK(entry.st_mode) or entry.st_nlink != 1:
                raise Operational("REFUSED", f"cannot safely snapshot ignored artifact: {relative}")
            total += entry.st_size
            if len(records) >= MAX_IGNORED_ENTRIES or total > MAX_IGNORED_BYTES:
                raise Operational("REFUSED", "ignored artifact snapshot exceeds its safety bound")
            fd = os.open(absolute, os.O_RDONLY | O_NOFOLLOW)
            try:
                opened = os.fstat(fd)
                if (opened.st_dev, opened.st_ino) != (entry.st_dev, entry.st_ino):
                    raise Operational("BLOCKED", f"ignored artifact changed during snapshot: {relative}")
                chunks = []
                remaining = entry.st_size
                while remaining:
                    chunk = os.read(fd, min(1024 * 1024, remaining))
                    if not chunk:
                        raise Operational("BLOCKED", f"ignored artifact changed during snapshot: {relative}")
                    chunks.append(chunk)
                    remaining -= len(chunk)
                data = b"".join(chunks)
            finally:
                os.close(fd)
            records[relative] = {"data": data, "mode": stat.S_IMODE(entry.st_mode), "digest": digest_bytes(data)}
    return records


def restore_ignored(repo: str, before: dict[str, dict]) -> list[str]:
    after = ignored_snapshot(repo)
    changed: list[str] = []
    for relative in sorted(set(after) - set(before), reverse=True):
        target = os.path.abspath(os.path.join(repo, relative))
        if os.path.commonpath([repo, target]) != repo:
            raise Operational("BLOCKED", "ignored artifact escaped canonical workspace")
        os.unlink(target)
        changed.append(relative)
    for relative, record in before.items():
        if relative in after and after[relative]["digest"] == record["digest"] and after[relative]["mode"] == record["mode"]:
            continue
        target = os.path.abspath(os.path.join(repo, relative))
        parent = os.path.dirname(target)
        parent_entry = os.lstat(parent)
        if not stat.S_ISDIR(parent_entry.st_mode) or stat.S_ISLNK(parent_entry.st_mode):
            raise Operational("BLOCKED", f"ignored artifact parent cannot be restored safely: {relative}")
        temporary = os.path.join(os.path.dirname(target), f".ce-work-restore-{secrets.token_hex(8)}")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, record["mode"])
        try:
            view = memoryview(record["data"])
            while view:
                view = view[os.write(fd, view):]
            os.fchmod(fd, record["mode"])
        finally:
            os.close(fd)
        os.replace(temporary, target)
        changed.append(relative)
    verified = ignored_snapshot(repo)
    if {path: (row["digest"], row["mode"]) for path, row in verified.items()} != {path: (row["digest"], row["mode"]) for path, row in before.items()}:
        raise Operational("BLOCKED", "ignored artifact restoration could not be proven")
    return sorted(changed)


def snapshot(repo: str) -> dict:
    current = revision(repo)
    operation_id = jj_text(repo, "op", "log", "--no-graph", "-n", "1", "-T", "id")
    summary = jj(repo, "diff", "--summary", "-r", "@")
    conflicts = jj_text(repo, "log", "--no-graph", "-r", "@ & conflicts()", "-T", "commit_id", check=False)
    bookmarks = sorted(filter(None, jj_text(repo, "bookmark", "list", "-r", "@", "-T", 'name ++ "\\n"', check=False).splitlines()))
    bookmark_state = jj(repo, "bookmark", "list")
    return {
        **current,
        "operation_id": operation_id,
        "summary_sha256": digest_bytes(summary),
        "working_copy_empty": not bool(summary),
        "conflicted": bool(conflicts),
        "bookmarks": bookmarks,
        "bookmark_state_sha256": digest_bytes(bookmark_state),
    }


def same_repository_state(left: dict, right: dict) -> bool:
    fields = {
        "change_id", "commit_id", "description", "summary_sha256", "working_copy_empty",
        "conflicted", "bookmarks", "bookmark_state_sha256",
    }
    return all(left.get(field) == right.get(field) for field in fields)


def repo_info(repo: str) -> dict:
    root = os.path.realpath(jj_text(os.path.abspath(repo), "root"))
    current = snapshot(root)
    marker = os.path.join(root, ".jj")
    st = os.lstat(marker)
    identity = digest_bytes(f"{root}\0{st.st_dev}\0{st.st_ino}".encode())
    return {"toplevel": root, "identity_digest": identity, **current}


def runs_root(repo: str | None = None) -> str:
    configured = os.environ.get("ROCKETCLAW_WORK_RUNS_ROOT")
    if configured:
        return os.path.abspath(configured)
    root = os.path.realpath(repo or os.getcwd())
    return os.path.join(root, ".tmp", "rocketclaw", "ce-work")


def validate_private_dir(path: str) -> None:
    try:
        fd = os.open(path, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open directory {path}: {exc}") from exc
    try:
        st = os.fstat(fd)
        uid = getattr(os, "geteuid", lambda: st.st_uid)()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != uid or stat.S_IMODE(st.st_mode) != 0o700:
            raise TrustFailure(f"directory owner/type/mode validation failed: {path}")
    finally:
        os.close(fd)


def ensure_private_dir(path: str) -> None:
    try:
        os.mkdir(path, 0o700)
    except FileExistsError:
        pass
    validate_private_dir(path)


def ensure_root(repo: str | None = None) -> str:
    root = runs_root(repo)
    if not os.environ.get("ROCKETCLAW_WORK_RUNS_ROOT"):
        workspace = os.path.realpath(repo or os.getcwd())
        local = os.path.join(workspace, ".tmp")
        try:
            os.mkdir(local, 0o700)
        except FileExistsError:
            entry = os.lstat(local)
            uid = getattr(os, "geteuid", lambda: entry.st_uid)()
            if not stat.S_ISDIR(entry.st_mode) or stat.S_ISLNK(entry.st_mode) or entry.st_uid != uid:
                raise TrustFailure("workspace .tmp is not a real current-user-owned directory")
        rocketclaw = os.path.join(local, "rocketclaw")
        ensure_private_dir(rocketclaw)
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
        uid = getattr(os, "geteuid", lambda: st.st_uid)()
        if not stat.S_ISREG(st.st_mode) or st.st_uid != uid or stat.S_IMODE(st.st_mode) != 0o600 or st.st_size > cap:
            raise TrustFailure(f"state owner/type/mode/size validation failed: {path}")
        out = bytearray()
        while len(out) <= cap:
            part = os.read(fd, min(65536, cap + 1 - len(out)))
            if not part:
                break
            out.extend(part)
        if len(out) > cap:
            raise TrustFailure(f"state grew beyond its size cap: {path}")
        return bytes(out)
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


def atomic_private_json(path: str, doc: dict) -> None:
    data = (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_JSON_BYTES:
        raise Operational("BLOCKED", "manifest exceeds bounded state size")
    parent = os.path.dirname(path)
    temporary = os.path.join(parent, f".manifest-{secrets.token_hex(8)}")
    create_private(temporary, data)
    os.replace(temporary, path)
    dfd = os.open(parent, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def run_dir(run_id: str, root: str | None = None) -> str:
    if root is None:
        root = runs_root()
    return os.path.join(os.path.abspath(root), safe_id(run_id, "run id"))


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


def event(doc: dict, kind: str, unit_id: str | None = None, detail: dict | None = None) -> None:
    row = {"at": now_iso(), "kind": kind}
    if unit_id is not None:
        row["unit_id"] = unit_id
    if detail:
        row["detail"] = detail
    doc.setdefault("events", []).append(row)


def validate_repo(doc: dict) -> dict:
    current = repo_info(doc["repository"]["toplevel"])
    for key in ("toplevel", "identity_digest"):
        if current[key] != doc["repository"][key]:
            raise Operational("BLOCKED", f"canonical repository identity changed ({key})")
    lock = doc.get("integration_lock")
    fallback_inflight = any(
        isinstance(unit, dict)
        and bool(unit.get("attempts"))
        and bool(unit["attempts"][-1].get("fallback", {}).get("claimed"))
        and not unit["attempts"][-1].get("fallback", {}).get("completed")
        for unit in doc.get("units", {}).values()
    )
    inflight = bool(doc.get("checkpoint_intent")) or fallback_inflight or isinstance(lock, dict) and doc.get("units", {}).get(lock.get("unit_id"), {}).get("state") in {
        "integration-pending", "integrated", "verified", "described", "restoring", "preserved", "cleaned",
    }
    if current["change_id"] != doc["canonical"]["change_id"] and not inflight:
        raise Operational("BLOCKED", "canonical working-copy change changed")
    if current["bookmark_state_sha256"] != doc["canonical"].get("bookmark_state_sha256") and not inflight:
        raise Operational("BLOCKED", "canonical bookmark state changed")
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
    "codex": ("codex", "codex", []), "claude": ("claude", "claude", []),
    "grok-cli": ("grok", "grok", []), "cursor": ("cursor", "cursor-agent", []),
    "composer": ("composer", "cursor-agent", ["cursor"]),
    "grok-cursor": ("grok", "cursor-agent", ["cursor"]),
}


def fixed_route_contract(binding: dict, egress: dict, word: str = "BLOCKED") -> dict:
    if set(binding) != {"mode", "target", "model", "source"} or binding.get("mode") not in {"prefer", "require"}:
        raise Operational(word, "binding contract is malformed")
    route = egress.get("route")
    if route not in ROUTE_CONTRACTS:
        raise Operational(word, "egress route is unsupported")
    target, harness, intermediaries = ROUTE_CONTRACTS[route]
    if binding.get("target") != target or egress.get("intermediaries") != intermediaries:
        raise Operational(word, "binding does not match the fixed route")
    restrictions = egress.get("restrictions", [])
    if not isinstance(restrictions, list) or not all(isinstance(item, str) for item in restrictions):
        raise Operational(word, "egress restrictions must be strings")
    return {"target": target, "harness": harness, "intermediaries": intermediaries}


def cmd_init(args) -> tuple[str, dict]:
    info = repo_info(args.repo)
    if not info["working_copy_empty"] and not args.plan:
        raise Operational("BLOCKED", "prompt-backed execution requires an empty canonical working-copy change")
    binding = parse_json_arg(args.binding_json, "binding")
    egress = parse_json_arg(args.egress_json, "egress")
    fixed_route_contract(binding, egress, "REFUSED")
    source_path = args.plan or args.prompt_brief
    source_absolute = os.path.abspath(source_path)
    source_entry = os.lstat(source_absolute)
    if not stat.S_ISREG(source_entry.st_mode) or stat.S_ISLNK(source_entry.st_mode):
        raise Operational("REFUSED", "selected source must be one regular non-link file")
    if args.plan and os.path.commonpath([info["toplevel"], source_absolute]) != info["toplevel"]:
        raise Operational("REFUSED", "selected plan must be inside the canonical workspace")
    if args.prompt_brief and os.path.commonpath([os.path.join(info["toplevel"], ".tmp"), source_absolute]) != os.path.join(info["toplevel"], ".tmp"):
        raise Operational("REFUSED", "prompt brief must use the canonical workspace's .tmp fallback")
    source = Path(source_absolute).read_bytes()
    supplied = args.plan_digest or args.prompt_digest
    if digest_bytes(source) != supplied:
        raise Operational("REFUSED", "selected source digest does not match content")
    root = ensure_root(info["toplevel"])
    os.environ["ROCKETCLAW_WORK_RUNS_ROOT"] = root
    rid = safe_id(args.run_id, "run id")
    rd = os.path.join(root, rid)
    if os.path.exists(rd):
        with locked_manifest(rid) as existing:
            validate_repo(existing)
            if existing["source"]["digest"] != supplied or existing["binding"] != binding or existing["egress"] != egress:
                raise Operational("BLOCKED", "run id belongs to another source or route contract")
            return "READY", {"run_id": rid, "resumed": True, "recovery_path": rd}
    ensure_private_dir(rd)
    for child in ("units", "jobs", "packets", "source"):
        ensure_private_dir(os.path.join(rd, child))
    create_private(os.path.join(rd, "manifest.lock"), b"")
    kind = "plan" if args.plan else "prompt"
    source_record_path = os.path.relpath(os.path.abspath(args.plan), info["toplevel"]) if args.plan else "source/bare-prompt.md"
    if kind == "prompt":
        create_private(os.path.join(rd, "source", "bare-prompt.md"), source)
    created = now_iso()
    doc = {
        "schema_version": SCHEMA_VERSION, "revision": 0, "run_id": rid,
        "created_at": created, "updated_at": created,
        "repository": {"toplevel": info["toplevel"], "identity_digest": info["identity_digest"]},
        "canonical": {"change_id": info["change_id"], "initial_commit_id": info["commit_id"], "bookmarks": info["bookmarks"], "bookmark_state_sha256": info["bookmark_state_sha256"]},
        "source": {"kind": kind, "path": source_record_path, "digest": supplied},
        "plan_checkpoint": None, "checkpoint_intent": None, "binding": binding, "egress": egress,
        "integration_lock": None, "units": {}, "verification_attempts": [],
        "verifications": [], "blockers": [], "events": [{"at": created, "kind": "run-created"}],
    }
    create_private(os.path.join(rd, "manifest.json"), (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode())
    return "READY", {"run_id": rid, "resumed": False, "source_kind": kind, "source_digest": supplied, "recovery_path": rd}


def cmd_checkpoint_plan(args) -> tuple[str, dict]:
    description = validated_description(getattr(args, "description", None))
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        if doc["source"]["kind"] != "plan":
            return "NOOP", {"checkpoint": None, "commit_id": info["commit_id"]}
        intent = doc.get("checkpoint_intent")
        if intent:
            if intent.get("description") != description:
                raise Operational("BLOCKED", "checkpoint recovery description differs from recorded intent")
            current = snapshot(info["toplevel"])
            if current["change_id"] == intent["change_id"] and current["description"] == description and not current["working_copy_empty"]:
                jj(info["toplevel"], "new")
                current = snapshot(info["toplevel"])
            accepted = revision(info["toplevel"], "@-")
            plan_bytes = jj(info["toplevel"], "file", "show", "-r", "@-", intent["path"])
            if not current["working_copy_empty"] or accepted["description"] != description or digest_bytes(plan_bytes) != doc["source"]["digest"]:
                raise Operational("BLOCKED", "interrupted plan checkpoint does not match recorded intent")
            checkpoint = {"prior_revision_id": intent["prior_revision_id"], "change": accepted, "path": intent["path"], "digest": doc["source"]["digest"], "at": now_iso()}
            doc["canonical"]["change_id"] = current["change_id"]
            doc["canonical"]["bookmark_state_sha256"] = current["bookmark_state_sha256"]
            doc["plan_checkpoint"] = checkpoint
            doc["checkpoint_intent"] = None
            event(doc, "plan-checkpoint-reconciled", detail={"change_id": accepted["change_id"], "path": intent["path"]})
            return "CHECKPOINTED", {"checkpoint": checkpoint, "resumed": True}
        dirty = changed_paths(info["toplevel"])
        plan = doc["source"]["path"]
        if not dirty:
            return "NOOP", {"checkpoint": doc.get("plan_checkpoint"), "revision_id": info["commit_id"]}
        if dirty != [plan]:
            raise Operational("BLOCKED", "canonical changes are not exactly the selected plan", {"changed_paths": dirty})
        if digest_bytes(Path(info["toplevel"], plan).read_bytes()) != doc["source"]["digest"]:
            raise Operational("BLOCKED", "selected plan content changed")
        before = revision(info["toplevel"])
        doc["checkpoint_intent"] = {"description": description, "change_id": before["change_id"], "prior_revision_id": before["commit_id"], "path": plan}
    jj(info["toplevel"], "describe", "-m", description)
    jj(info["toplevel"], "new")
    accepted = revision(info["toplevel"], "@-")
    current = revision(info["toplevel"])
    test_fault("checkpoint-plan-after-describe")
    with locked_manifest(args.run_id, write=True) as doc:
        doc["canonical"]["change_id"] = current["change_id"]
        doc["canonical"]["bookmark_state_sha256"] = snapshot(info["toplevel"])["bookmark_state_sha256"]
        checkpoint = {"prior_revision_id": before["commit_id"], "change": accepted, "path": plan, "digest": doc["source"]["digest"], "at": now_iso()}
        doc["plan_checkpoint"] = checkpoint
        doc["checkpoint_intent"] = None
        event(doc, "plan-checkpoint", detail={"change_id": accepted["change_id"], "path": plan})
    return "CHECKPOINTED", {"checkpoint": checkpoint}


def read_external_packet(path: str, label: str = "unit packet") -> bytes:
    absolute = os.path.abspath(path)
    fd = os.open(absolute, os.O_RDONLY | O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_PACKET_BYTES:
            raise Operational("REFUSED", f"{label} is not a bounded regular file")
        out = bytearray()
        while len(out) <= MAX_PACKET_BYTES:
            part = os.read(fd, min(65536, MAX_PACKET_BYTES + 1 - len(out)))
            if not part:
                break
            out.extend(part)
        if len(out) > MAX_PACKET_BYTES:
            raise Operational("REFUSED", f"{label} exceeds its byte limit")
        return bytes(out)
    finally:
        os.close(fd)


def find_attempt(unit: dict, attempt_id: str | None = None) -> dict:
    attempts = unit.get("attempts", [])
    matches = [row for row in attempts if attempt_id is None or row.get("attempt_id") == attempt_id]
    if attempt_id is None:
        matches = matches[-1:]
    if len(matches) != 1:
        raise Operational("AMBIGUOUS", "attempt could not be identified exactly")
    return matches[0]


def workspace_name(run_id: str, unit_id: str) -> str:
    return f"rc-{digest_bytes(run_id.encode())[:10]}-{digest_bytes(unit_id.encode())[:10]}"


def cmd_prepare(args) -> tuple[str, dict]:
    uid = safe_id(args.unit_id, "unit id")
    attempt_id = safe_id(args.attempt_id, "attempt id")
    packet = read_external_packet(args.packet)
    packet_digest = digest_bytes(packet)
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        if info["commit_id"] != args.base or not info["working_copy_empty"] or info["conflicted"]:
            raise Operational("BLOCKED", "canonical working-copy change is not the requested empty base")
        existing = doc["units"].get(uid)
        retrying = bool(existing and existing.get("state") == "cleaned" and existing.get("cleanup", {}).get("abandoned") is True and existing.get("cleanup", {}).get("artifacts_pruned") is True)
        if existing and not retrying:
            raise Operational("REFUSED", "unit id already exists; recovery or exact abandonment cleanup is required")
        if retrying:
            if existing.get("dependencies") != list(args.dependency):
                raise Operational("BLOCKED", "retry dependencies differ from the recorded unit")
            prior_wave = existing.get("wave", {})
            if (prior_wave.get("id"), prior_wave.get("position")) != (args.wave_id, args.wave_position):
                raise Operational("BLOCKED", "retry wave identity differs from the recorded unit")
            if any(attempt.get("attempt_id") == attempt_id for attempt in existing.get("attempts", [])):
                raise Operational("REFUSED", "retry requires a fresh attempt id")
            if not revision_contains(info["toplevel"], prior_wave.get("base", args.base), args.base):
                raise Operational("BLOCKED", "retry base omits the recorded unit base")
        rd = run_dir(args.run_id)
        unit_root = os.path.join(rd, "units", uid)
        workspace = os.path.join(unit_root, "workspace")
    ensure_private_dir(unit_root)
    ensure_private_dir(os.path.join(unit_root, "result"))
    packet_path = os.path.join(unit_root, "packet.md")
    create_private(packet_path, packet)
    route = fixed_route_contract(doc["binding"], doc["egress"])
    authorization = {
        "schema_version": 2, "run_id": args.run_id, "unit_id": uid, "attempt_id": attempt_id,
        "route": doc["egress"]["route"], "target": route["target"], "harness": route["harness"],
        "intermediaries": route["intermediaries"], "model_requested": doc["binding"].get("model") or "auto",
        "restrictions": doc["egress"].get("restrictions", []), "activity_posture": args.activity_posture,
        "packet_digest": packet_digest,
    }
    authorization_path = os.path.join(unit_root, "authorization.json")
    authorization_bytes = (json.dumps(authorization, sort_keys=True, separators=(",", ":")) + "\n").encode()
    authorization_digest = digest_bytes(authorization_bytes)
    create_private(authorization_path, authorization_bytes)
    name = workspace_name(args.run_id, uid)
    jj(info["toplevel"], "workspace", "add", "--name", name, "-r", args.base, workspace)
    base = revision(workspace, "@-")
    current = revision(workspace)
    if base["commit_id"] != args.base or changed_paths(workspace):
        raise Operational("BLOCKED", "new Jujutsu workspace did not start from the requested base")
    attempt_record = {"attempt_id": attempt_id, "job_id": None, "process_state": "never-started", "activity": {"posture": args.activity_posture, "latest_at": None}, "fallback": {"eligible": False, "reason": None, "claimed": None}, "authorization": authorization, "authorization_path": authorization_path, "authorization_digest": authorization_digest, "adapter": os.path.realpath(os.path.join(os.path.dirname(__file__), "cross-model-work.sh")), "terminal_receipt": None}
    unit = {
        "unit_id": uid, "state": "queued", "dependencies": list(args.dependency),
        "wave": {"id": args.wave_id, "base": args.base, "position": args.wave_position, "allowed_revisions": [args.base]},
        "workspace": {"path": workspace, "name": name, "base": args.base, "change_id": current["change_id"], "registered": True},
        "packet": {"path": packet_path, "digest": packet_digest, "retained": True},
        "attempts": [attempt_record],
        "transport": None, "integration": None, "cleanup": None, "recovery_path": unit_root,
    }
    with locked_manifest(args.run_id, write=True) as doc:
        current_existing = doc["units"].get(uid)
        if retrying:
            if not current_existing or current_existing.get("state") != "cleaned" or current_existing.get("cleanup", {}).get("artifacts_pruned") is not True:
                raise Operational("BLOCKED", "retry eligibility changed during workspace preparation")
            attempts = current_existing["attempts"]
            attempts.append(attempt_record)
            unit["attempts"] = attempts
            doc["units"][uid] = unit
            event(doc, "unit-retry-prepared", uid, {"attempt_id": attempt_id, "base": args.base})
        else:
            if current_existing:
                raise Operational("BLOCKED", "unit was concurrently claimed")
            doc["units"][uid] = unit
        event(doc, "workspace-prepared", uid, {"path": workspace, "name": name, "base": args.base})
    return "PREPARED", {"unit_id": uid, "attempt_id": attempt_id, "workspace": workspace, "result_dir": os.path.join(unit_root, "result"), "packet_path": packet_path, "packet_digest": packet_digest, "authorization_path": authorization_path, "authorization_digest": authorization_digest, "adapter": attempt_record["adapter"], "base": args.base, "resumed": False}


def runner_job_dir(run_id: str, job_id: str) -> str:
    return os.path.join(run_dir(run_id), "jobs", safe_id(job_id, "job id"))


def process_evidence(job_dir: str) -> dict:
    validate_private_dir(job_dir)
    status_path = os.path.join(job_dir, "status")
    if os.path.exists(status_path):
        word = read_private(status_path, 256).decode().strip()
    elif os.path.exists(os.path.join(job_dir, "pid")):
        word = "running"
    else:
        word = "never-started"
    if word not in TERMINAL_PROCESS | {"running", "never-started"}:
        raise TrustFailure("runner state is invalid")
    return {"process_state": word, "activity": {"latest_at": None}}


def validate_runner_contract(run_id: str, unit: dict, meta: dict) -> None:
    attempt = find_attempt(unit)
    authorization_bytes = read_private(attempt["authorization_path"])
    if digest_bytes(authorization_bytes) != attempt.get("authorization_digest"):
        raise Operational("BLOCKED", "controller authorization bytes changed")
    expected = [attempt["adapter"], attempt["authorization_path"], unit["workspace"]["path"], unit["packet"]["path"], unit["packet"]["digest"], os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")]
    if meta.get("skill") != "ce-work" or meta.get("run_id") != run_id or meta.get("label") != unit["unit_id"] or meta.get("input_digest") != unit["packet"]["digest"] or meta.get("worker_argv") != expected:
        raise Operational("BLOCKED", "runner metadata does not match the controller-issued dispatch")


def cmd_authorize_dispatch(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit, args.attempt_id)
        meta = read_private_json(os.path.join(runner_job_dir(args.run_id, args.job_id), "meta.json"))
        validate_runner_contract(args.run_id, unit, meta)
        if args.authorization_digest != attempt.get("authorization_digest"):
            raise Operational("BLOCKED", "observed authorization digest differs from controller state")
        expected = {"authorization": attempt["authorization_path"], "workspace": unit["workspace"]["path"], "packet": unit["packet"]["path"], "packet_digest": unit["packet"]["digest"], "result_dir": os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")}
        actual = {key: os.path.abspath(getattr(args, key)) if key in {"authorization", "workspace", "packet", "result_dir"} else getattr(args, key) for key in expected}
        normalized = {key: os.path.abspath(value) if key in {"authorization", "workspace", "packet", "result_dir"} else value for key, value in expected.items()}
        if actual != normalized:
            raise Operational("BLOCKED", "dispatch paths or digest differ from the recorded authorization")
        if attempt.get("job_id") not in {None, args.job_id}:
            raise Operational("AMBIGUOUS", "attempt is bound to another job")
        attempt["job_id"] = args.job_id
        unit["state"] = "authoring"
        event(doc, "job-bound", args.unit_id, {"job_id": args.job_id})
    return "AUTHORIZED", {"run_id": args.run_id, "unit_id": args.unit_id, "attempt_id": args.attempt_id, "job_id": args.job_id, "packet_digest": unit["packet"]["digest"]}


def cmd_record_job(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit, args.attempt_id)
        meta = read_private_json(os.path.join(runner_job_dir(args.run_id, args.job_id), "meta.json"))
        validate_runner_contract(args.run_id, unit, meta)
        if attempt.get("job_id") not in {None, args.job_id}:
            raise Operational("AMBIGUOUS", "attempt is bound to another job")
        attempt["job_id"] = args.job_id
        unit["state"] = "authoring"
    return "AUTHORING", {"unit_id": args.unit_id, "job_id": args.job_id}


def sync_job(run_id: str, unit_id: str) -> dict:
    with locked_manifest(run_id) as doc:
        unit = doc["units"].get(unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        evidence = process_evidence(runner_job_dir(run_id, attempt["job_id"])) if attempt.get("job_id") else {"process_state": "never-started", "activity": attempt["activity"]}
    with locked_manifest(run_id, write=True) as doc:
        attempt = find_attempt(doc["units"][unit_id])
        attempt["process_state"] = evidence["process_state"]
        attempt["activity"].update(evidence["activity"])
        if evidence["process_state"] in TERMINAL_PROCESS - {"done"}:
            attempt["fallback"] = {"eligible": True, "reason": evidence["process_state"], "claimed": attempt.get("fallback", {}).get("claimed")}
        event(doc, "job-synced", unit_id, {"process_state": evidence["process_state"]})
    return evidence


def cmd_sync_job(args) -> tuple[str, dict]:
    return "SYNCED", {"unit_id": args.unit_id, **sync_job(args.run_id, args.unit_id)}


def terminal_receipt(unit: dict) -> dict:
    path = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result", "implementation-result.json")
    raw = read_private(path, MAX_RESULT_BYTES)
    try:
        value = json.loads(raw)
    except ValueError as exc:
        raise Operational("BLOCKED", "worker result is malformed") from exc
    required = {"terminal_status", "summary", "changed_files", "evidence", "scope_expansion"}
    if not isinstance(value, dict) or not required.issubset(value) or value.get("terminal_status") not in {"completed", "blocked", "scope_expansion"}:
        raise Operational("BLOCKED", "worker result does not satisfy the terminal schema")
    attempt = find_attempt(unit)
    authorization = attempt["authorization"]
    expected = {
        "requested_route": authorization["route"], "actual_route": authorization["route"],
        "target": authorization["target"], "harness": authorization["harness"],
        "intermediaries": authorization["intermediaries"],
        "model_requested": authorization["model_requested"],
        "packet_digest": unit["packet"]["digest"],
    }
    mismatches = {key: {"expected": expected_value, "actual": value.get(key)} for key, expected_value in expected.items() if value.get(key) != expected_value}
    if mismatches:
        raise Operational("BLOCKED", "worker receipt differs from controller authorization", {"mismatches": mismatches})
    if value.get("model_receipt_status") == "mismatch":
        raise Operational("BLOCKED", "worker receipt reports a served-model mismatch")
    if not isinstance(value.get("changed_files"), list) or any(not isinstance(path, str) or not path for path in value["changed_files"]):
        raise Operational("BLOCKED", "worker changed-file evidence is malformed")
    expected_log = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result", "adapter.log")
    if os.path.abspath(str(value.get("raw_log", ""))) != expected_log:
        raise Operational("BLOCKED", "worker log receipt escaped the controller result directory")
    read_private(expected_log, 10 * 1024 * 1024)
    return value


def terminalize(run_id: str, unit_id: str) -> dict:
    evidence = sync_job(run_id, unit_id)
    if evidence["process_state"] != "done":
        raise Operational("BLOCKED", f"worker is not authoritatively done ({evidence['process_state']})")
    with locked_manifest(run_id) as doc:
        unit = json.loads(json.dumps(doc["units"][unit_id]))
    try:
        receipt = terminal_receipt(unit)
    except Operational as exc:
        with locked_manifest(run_id, write=True) as current_doc:
            current_attempt = find_attempt(current_doc["units"][unit_id])
            current_attempt["terminal_validation_failure"] = {"at": now_iso(), "reason": str(exc), "detail": exc.detail}
            current_attempt["fallback"] = {"eligible": True, "reason": "terminal-validation-failure", "claimed": current_attempt.get("fallback", {}).get("claimed")}
            event(current_doc, "terminal-validation-failed", unit_id, {"reason": str(exc)})
        raise
    with locked_manifest(run_id) as doc:
        unit = doc["units"][unit_id]
        if receipt["terminal_status"] != "completed":
            raise Operational("BLOCKED", "worker returned a host-resolvable blocker", {"unit_id": unit_id, "terminal_receipt": receipt, "recovery_path": unit["recovery_path"]})
        workspace = unit["workspace"]["path"]
        base = unit["workspace"]["base"]
        current = snapshot(workspace)
        if current["change_id"] != unit["workspace"]["change_id"] or current["conflicted"]:
            raise Operational("BLOCKED", "worker workspace identity changed or contains conflicts")
        if not revision_contains(workspace, base, current["commit_id"]):
            raise Operational("BLOCKED", "worker change does not descend from its recorded base revset")
        paths = changed_paths(workspace, base, "@")
        if not paths:
            raise Operational("BLOCKED", "worker produced no transportable Jujutsu change")
        transport = {"base": base, "change_id": current["change_id"], "commit_id": current["commit_id"], "changed_paths": paths, "digest": digest_bytes(json.dumps([base, current["change_id"], current["commit_id"], paths]).encode())}
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        unit["state"] = "integration-pending"
        unit["transport"] = transport
        find_attempt(unit)["terminal_receipt"] = receipt
        event(doc, "change-pinned", unit_id, {"change_id": transport["change_id"], "commit_id": transport["commit_id"]})
    return transport


def cmd_terminalize(args) -> tuple[str, dict]:
    transport = terminalize(args.run_id, args.unit_id)
    return "INTEGRATION_PENDING", {"unit_id": args.unit_id, "transport": transport}


def lock_path(doc: dict) -> str:
    return os.path.join(run_dir(doc["run_id"]), ".integration.lock")


def cmd_integration_acquire(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit["state"] not in {"integration-pending", "integrated", "verified", "described", "preserved", "cleaned", "native-completed"}:
            raise Operational("REFUSED", "unit is not ready for integration")
        if doc.get("integration_lock"):
            if args.resume and doc["integration_lock"]["unit_id"] == args.unit_id:
                return "ACQUIRED", {"lock_token": doc["integration_lock"]["nonce"], "resumed": True}
            raise Operational("REFUSED", "integration claim already exists")
        nonce = secrets.token_hex(24)
        create_private(lock_path(doc), (json.dumps({"run_id": args.run_id, "unit_id": args.unit_id, "nonce": nonce}) + "\n").encode())
        doc["integration_lock"] = {"unit_id": args.unit_id, "nonce": nonce, "path": lock_path(doc), "phase": "held"}
        event(doc, "integration-lock-acquired", args.unit_id)
    return "ACQUIRED", {"lock_token": nonce, "resumed": False}


def validate_lock(doc: dict, unit_id: str, token: str) -> None:
    lock = doc.get("integration_lock")
    if not lock or lock.get("unit_id") != unit_id or lock.get("nonce") != token:
        raise Operational("BLOCKED", "integration lock token or identity mismatch")
    if read_private_json(lock["path"]).get("nonce") != token:
        raise Operational("BLOCKED", "external integration lock changed")


def cmd_preflight(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        worker = snapshot(unit["workspace"]["path"])
        if worker["change_id"] != unit["transport"]["change_id"] or worker["commit_id"] != unit["transport"]["commit_id"]:
            raise Operational("BLOCKED", "pinned worker change moved before canonical preflight")
        if not info["working_copy_empty"] or info["conflicted"]:
            raise Operational("BLOCKED", "canonical working-copy change is not an empty, conflict-free integration base")
        missing = [dep for dep in unit["dependencies"] if unit_accepted_revision(doc["units"].get(dep)) is None]
        if missing:
            raise Operational("BLOCKED", "unit dependencies are not accepted", {"units": missing})
        omitted = [dep for dep in unit["dependencies"] if not revision_contains(info["toplevel"], unit_accepted_revision(doc["units"][dep]), info["commit_id"])]
        if omitted:
            raise Operational("BLOCKED", "canonical revset omits accepted dependencies", {"units": omitted})
        if args.allowed_revision and info["commit_id"] not in args.allowed_revision:
            raise Operational("BLOCKED", "canonical revision is outside the recorded wave")
        unit["integration"] = {"pre_fold": info, "applied": None, "verification": None, "canonical_change": None, "restore": None}
        event(doc, "canonical-squash-intent", args.unit_id, {"transport": unit["transport"]["commit_id"]})
    return "PREFLIGHT_OK", {"unit_id": args.unit_id, "pre_fold": info, "transport": unit["transport"]}


def cmd_mark_applied(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        current = snapshot(doc["repository"]["toplevel"])
        if current["change_id"] != unit["integration"]["pre_fold"]["change_id"] or current["conflicted"]:
            raise Operational("BLOCKED", "canonical squash changed identity or produced conflicts")
        unit["state"] = "integrated"
        unit["integration"]["applied"] = current
        event(doc, "transport-squashed", args.unit_id, {"commit_id": current["commit_id"]})
    return "APPLIED", {"unit_id": args.unit_id, "commit_id": current["commit_id"]}


def cmd_mark_verified(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        if snapshot(doc["repository"]["toplevel"])["commit_id"] != unit["integration"]["applied"]["commit_id"]:
            raise Operational("BLOCKED", "canonical change moved after authoritative verification")
        unit["state"] = "verified"
        unit["integration"]["verification"] = {"at": now_iso(), "digest": args.evidence_digest, "summary": args.summary}
    return "VERIFIED", {"unit_id": args.unit_id, "verification": unit["integration"]["verification"]}


def cmd_mark_described(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        if unit["state"] not in {"verified", "described"}:
            raise Operational("REFUSED", "unit has not passed canonical verification")
        accepted = revision(doc["repository"]["toplevel"], "@-")
        current = revision(doc["repository"]["toplevel"])
        if current["change_id"] == accepted["change_id"] or changed_paths(doc["repository"]["toplevel"]):
            raise Operational("BLOCKED", "canonical described change was not followed by an empty working-copy change")
        unit["state"] = "described"
        unit["integration"]["canonical_change"] = {**accepted, "at": now_iso(), "tip_commit_id": current["commit_id"]}
        doc["canonical"]["change_id"] = current["change_id"]
        doc["canonical"]["bookmark_state_sha256"] = snapshot(doc["repository"]["toplevel"])["bookmark_state_sha256"]
        event(doc, "canonical-change-confirmed", args.unit_id, {"change_id": accepted["change_id"]})
    return "DESCRIBED", {"unit_id": args.unit_id, "canonical_change": unit["integration"]["canonical_change"]}


def restore(run_id: str, unit_id: str, token: str) -> bool:
    with locked_manifest(run_id) as doc:
        validate_lock(doc, unit_id, token)
        unit = doc["units"][unit_id]
        pre = unit["integration"]["pre_fold"]
        repo = doc["repository"]["toplevel"]
    with locked_manifest(run_id, write=True) as doc:
        doc["units"][unit_id]["state"] = "restoring"
        event(doc, "restore-intent", unit_id)
    jj(repo, "op", "restore", pre["operation_id"])
    actual = snapshot(repo)
    exact = actual["change_id"] == pre["change_id"] and actual["commit_id"] == pre["commit_id"] and actual["working_copy_empty"] and not actual["conflicted"]
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        unit["integration"]["restore"] = {"at": now_iso(), "exact": exact, "snapshot": actual}
        unit["state"] = "preserved" if exact else "restoring"
        event(doc, "canonical-restored" if exact else "restore-blocked", unit_id)
    return exact


def cmd_restore(args) -> tuple[str, dict]:
    if not restore(args.run_id, args.unit_id, args.lock_token):
        raise Operational("BLOCKED", "exact pre-fold restoration could not be proven", {"retain_integration_lock": True})
    return "PRESERVED", {"unit_id": args.unit_id, "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id)}


def integration_release(run_id: str, unit_id: str, token: str) -> None:
    with locked_manifest(run_id, write=True) as doc:
        validate_lock(doc, unit_id, token)
        unit = doc["units"][unit_id]
        preflight_free = unit["state"] == "integration-pending" and not unit.get("integration")
        if unit["state"] not in {"described", "preserved", "cleaned", "native-completed"} and not preflight_free:
            raise Operational("REFUSED", "integration lock releases only after accepted completion or exact restoration")
        os.unlink(doc["integration_lock"]["path"])
        doc["integration_lock"] = None
        event(doc, "integration-lock-released", unit_id)


def cmd_integration_release(args) -> tuple[str, dict]:
    integration_release(args.run_id, args.unit_id, args.lock_token)
    return "RELEASED", {"unit_id": args.unit_id}


def _run_verification(repo: str, command: list[str], log_path: str) -> tuple[int, str]:
    before = snapshot(repo)
    ignored_before = ignored_snapshot(repo)
    with open(log_path, "xb") as stream:
        proc = subprocess.run(command, cwd=repo, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, check=False)
    after = snapshot(repo)
    if not same_repository_state(after, before):
        jj(repo, "op", "restore", before["operation_id"])
        restored = snapshot(repo)
        if not same_repository_state(restored, before):
            raise Operational("BLOCKED", "verification restoration could not be proven", {"retain_integration_lock": True, "verification_log": log_path})
    try:
        restore_ignored(repo, ignored_before)
    except Operational as exc:
        raise Operational("BLOCKED", "verification ignored-artifact restoration could not be proven", {"retain_integration_lock": True, "verification_log": log_path, "reason": str(exc)}) from exc
    return proc.returncode, digest_bytes(Path(log_path).read_bytes())


def cmd_integrate(args) -> tuple[str, dict]:
    command = list(args.verification_command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        raise Operational("REFUSED", "integrate requires a verification command")
    description = validated_description(args.description)
    token = cmd_integration_acquire(SimpleNamespace(run_id=args.run_id, unit_id=args.unit_id, resume=False))[1]["lock_token"]
    try:
        cmd_preflight(SimpleNamespace(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, allowed_revision=args.allowed_revision))
        with locked_manifest(args.run_id, write=True) as doc:
            doc["units"][args.unit_id]["integration"]["pending_description"] = description
        with locked_manifest(args.run_id) as doc:
            repo = doc["repository"]["toplevel"]
            transport = doc["units"][args.unit_id]["transport"]["commit_id"]
        jj(repo, "squash", "--from", transport, "--into", "@")
        cmd_mark_applied(SimpleNamespace(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        log = os.path.join(run_dir(args.run_id), "units", args.unit_id, "result", f"host-verification-{secrets.token_hex(6)}.log")
        code, log_digest = _run_verification(repo, command, log)
        if code:
            if not restore(args.run_id, args.unit_id, token):
                raise Operational("BLOCKED", "verification failed and exact restoration could not be proven", {"retain_integration_lock": True, "verification_log": log})
            integration_release(args.run_id, args.unit_id, token)
            raise Operational("BLOCKED", "authoritative verification failed", {"verification_exit": code, "verification_log": log})
        evidence = digest_bytes(json.dumps({"argv": command, "log_sha256": log_digest}, sort_keys=True).encode())
        cmd_mark_verified(SimpleNamespace(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, evidence_digest=evidence, summary=args.verification_summary))
        jj(repo, "describe", "-m", description)
        jj(repo, "new")
        described = cmd_mark_described(SimpleNamespace(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))[1]["canonical_change"]
        cmd_cleanup(SimpleNamespace(run_id=args.run_id, unit_id=args.unit_id, abandon=False, expect_transport=None, expect_job=None))
        integration_release(args.run_id, args.unit_id, token)
        os.unlink(log)
        return "UNIT_DESCRIBED", {"unit_id": args.unit_id, "canonical_change": described, "verification_digest": evidence, "cleaned": True}
    except Operational as exc:
        if exc.detail.get("retain_integration_lock"):
            raise
        with locked_manifest(args.run_id) as doc:
            unit = doc["units"][args.unit_id]
            state = unit["state"]
        if state not in {"preserved", "described", "cleaned"}:
            restore(args.run_id, args.unit_id, token)
        with contextlib.suppress(Operational):
            integration_release(args.run_id, args.unit_id, token)
        raise


def unit_accepted_revision(unit: dict | None) -> str | None:
    if not isinstance(unit, dict):
        return None
    if unit.get("state") == "native-completed":
        return find_attempt(unit).get("fallback", {}).get("completed", {}).get("accepted_revision_id")
    if unit.get("state") not in {"described", "cleaned"}:
        return None
    return (unit.get("integration") or {}).get("canonical_change", {}).get("commit_id")


def cmd_verify_run(args) -> tuple[str, dict]:
    command = list(args.verification_command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        raise Operational("REFUSED", "verify-run requires a verification command")
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        if not doc["units"] or any(unit_accepted_revision(unit) is None for unit in doc["units"].values()) or not info["working_copy_empty"]:
            raise Operational("REFUSED", "verify-run requires accepted units and an empty canonical working-copy change")
        accepted = {uid: unit_accepted_revision(unit) for uid, unit in doc["units"].items()}
        if len(set(accepted.values())) != len(accepted) or any(not revision_contains(info["toplevel"], accepted_revision, info["commit_id"]) for accepted_revision in accepted.values()):
            raise Operational("BLOCKED", "accepted unit revisions are duplicated or absent from the canonical revset")
    log = os.path.join(run_dir(args.run_id), "jobs", f"run-verification-{secrets.token_hex(6)}.log")
    code, log_digest = _run_verification(info["toplevel"], command, log)
    receipt = {"at": now_iso(), "argv": command, "summary": args.verification_summary, "verification_exit": code, "log_sha256": log_digest, "canonical_revision_id": info["commit_id"], "accepted_units": accepted}
    receipt["evidence_digest"] = digest_bytes(json.dumps(receipt, sort_keys=True).encode())
    with locked_manifest(args.run_id, write=True) as doc:
        doc["verifications"].append(receipt)
        event(doc, "run-verification-passed" if code == 0 else "run-verification-failed", detail={"evidence_digest": receipt["evidence_digest"]})
    if code:
        raise Operational("BLOCKED", "plan-wide authoritative verification failed", {"verification_exit": code, "verification_log": log, "evidence_digest": receipt["evidence_digest"]})
    os.unlink(log)
    return "RUN_VERIFIED", {"verification_exit": 0, "evidence_digest": receipt["evidence_digest"], "canonical_revision_id": info["commit_id"]}


def cmd_status(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        body = {"run_id": args.run_id, "revision": doc["revision"], "source": doc["source"], "integration_lock": doc.get("integration_lock"), "verifications": doc["verifications"], "blockers": doc["blockers"], "recovery_path": run_dir(args.run_id)}
        if args.unit_id:
            body["unit"] = doc["units"].get(args.unit_id)
        else:
            body["units"] = doc["units"]
    return "STATUS", body


def cmd_resume(args) -> tuple[str, dict]:
    if not args.run_id:
        raise Operational("REFUSED", "Jujutsu recovery requires an explicit run id")
    actions: list[dict] = []
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        units = list(doc["units"])
    for uid in units:
        with locked_manifest(args.run_id) as doc:
            unit = doc["units"][uid]
            state = unit["state"]
            attempt = find_attempt(unit)
            lock = doc.get("integration_lock")
        if state == "authoring" and attempt.get("job_id"):
            evidence = sync_job(args.run_id, uid)
            actions.append({"unit_id": uid, "action": "monitored", **evidence})
            if evidence["process_state"] == "done":
                actions.append({"unit_id": uid, "action": "terminalized", "transport": terminalize(args.run_id, uid)})
        elif state == "integration-pending" and lock and lock["unit_id"] == uid and not unit.get("integration"):
            integration_release(args.run_id, uid, lock["nonce"])
            actions.append({"unit_id": uid, "action": "preflight-lock-released"})
        elif state in {"integration-pending", "integrated"} and lock and lock["unit_id"] == uid:
            if not restore(args.run_id, uid, lock["nonce"]):
                raise Operational("BLOCKED", "exact restoration remains unproven", {"retain_integration_lock": True})
            integration_release(args.run_id, uid, lock["nonce"])
            actions.append({"unit_id": uid, "action": "inflight-squash-restored"})
        elif state == "verified" and lock and lock["unit_id"] == uid:
            repo = doc["repository"]["toplevel"]
            pending = unit["integration"].get("pending_description")
            current = snapshot(repo)
            parent = revision(repo, "@-") if current["working_copy_empty"] else None
            if pending and current["working_copy_empty"] and parent and parent["description"] == pending:
                cmd_mark_described(SimpleNamespace(run_id=args.run_id, unit_id=uid, lock_token=lock["nonce"]))
                actions.append({"unit_id": uid, "action": "description-reconciled"})
            elif pending and current["change_id"] == unit["integration"]["pre_fold"]["change_id"] and current["description"] == pending:
                jj(repo, "new")
                cmd_mark_described(SimpleNamespace(run_id=args.run_id, unit_id=uid, lock_token=lock["nonce"]))
                actions.append({"unit_id": uid, "action": "description-advance-reconciled"})
            else:
                if not restore(args.run_id, uid, lock["nonce"]):
                    raise Operational("BLOCKED", "exact restoration remains unproven", {"retain_integration_lock": True})
                integration_release(args.run_id, uid, lock["nonce"])
                actions.append({"unit_id": uid, "action": "verified-change-restored"})
                continue
            cmd_cleanup(SimpleNamespace(run_id=args.run_id, unit_id=uid, abandon=False, expect_transport=None, expect_job=None))
            integration_release(args.run_id, uid, lock["nonce"])
            actions.append({"unit_id": uid, "action": "described-unit-finalized"})
        elif state == "restoring" and lock and lock["unit_id"] == uid:
            if not restore(args.run_id, uid, lock["nonce"]):
                raise Operational("BLOCKED", "exact restoration remains unproven", {"retain_integration_lock": True})
            integration_release(args.run_id, uid, lock["nonce"])
            actions.append({"unit_id": uid, "action": "restored"})
        elif state == "described":
            cmd_cleanup(SimpleNamespace(run_id=args.run_id, unit_id=uid, abandon=False, expect_transport=None, expect_job=None))
            actions.append({"unit_id": uid, "action": "cleanup-reconciled"})
            if lock and lock["unit_id"] == uid:
                integration_release(args.run_id, uid, lock["nonce"])
                actions.append({"unit_id": uid, "action": "integration-release-reconciled"})
        elif state == "cleaned" and lock and lock["unit_id"] == uid:
            integration_release(args.run_id, uid, lock["nonce"])
            actions.append({"unit_id": uid, "action": "integration-release-reconciled"})
    return "RESUMED", {"run_id": args.run_id, "actions": actions, "redispatched": False, "applied": False}


def cmd_claim_fallback(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"][args.unit_id]
        attempt = find_attempt(unit)
        fallback = attempt.setdefault("fallback", {})
        if fallback.get("claimed"):
            return "FALLBACK_ALREADY_AUTHORIZED", {"unit_id": args.unit_id, "start_native": False, "claim": fallback["claimed"]}
        if attempt.get("process_state") not in TERMINAL_PROCESS - {"done"} and unit["state"] != "preserved" and not attempt.get("fallback", {}).get("eligible"):
            raise Operational("REFUSED", "no authoritative terminal or restored attempt authorizes fallback")
        mode = doc["binding"]["mode"]
        if mode == "require" and (args.caller_mode != "interactive" or not args.confirm_native):
            raise Operational("CHOICE_REQUIRED" if args.caller_mode == "interactive" else "BLOCKED", "required route cannot fall back without explicit interactive confirmation")
        claim = {"at": now_iso(), "mode": mode, "caller_mode": args.caller_mode, "confirmed_native": bool(args.confirm_native), "canonical_revision_id": snapshot(doc["repository"]["toplevel"])["commit_id"], "reason": fallback.get("reason") or attempt.get("process_state")}
        fallback["claimed"] = claim
        event(doc, "native-fallback-authorized", args.unit_id, {"reason": claim["reason"]})
    return "FALLBACK_AUTHORIZED", {"unit_id": args.unit_id, "start_native": True, "reason": claim["reason"], "claim": claim}


def cmd_complete_fallback(args) -> tuple[str, dict]:
    if not SHA256.fullmatch(args.evidence_digest):
        raise Operational("REFUSED", "native fallback evidence digest must be lowercase SHA-256")
    if not args.summary.strip() or "\0" in args.summary:
        raise Operational("REFUSED", "native fallback summary must be non-empty and NUL-free")
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        unit = doc["units"][args.unit_id]
        fallback = find_attempt(unit).get("fallback", {})
        if not fallback.get("claimed") or fallback.get("completed"):
            raise Operational("REFUSED", "native fallback completion requires one unused claim")
        accepted = revision(info["toplevel"], "@-")
        if accepted["commit_id"] != args.accepted_revision or not info["working_copy_empty"]:
            raise Operational("BLOCKED", "accepted native fallback revision does not match the empty canonical working-copy change")
        completion = {"at": now_iso(), "accepted_revision_id": args.accepted_revision, "evidence_digest": args.evidence_digest, "summary": args.summary, "claim": fallback["claimed"]}
        fallback["completed"] = completion
        unit["state"] = "native-completed"
        doc["canonical"]["change_id"] = info["change_id"]
        doc["canonical"]["bookmark_state_sha256"] = info["bookmark_state_sha256"]
        event(doc, "native-fallback-completed", args.unit_id, {"accepted_revision_id": args.accepted_revision})
    return "FALLBACK_COMPLETED", {"unit_id": args.unit_id, "completion": completion}


def cmd_reap(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        attempt = find_attempt(doc["units"][args.unit_id])
        if not attempt.get("job_id"):
            return "REAPED", {"unit_id": args.unit_id, "process_state": "never-started"}
        job = runner_job_dir(args.run_id, attempt["job_id"])
    runner = os.path.join(os.path.dirname(__file__), "peer-job-runner.py")
    proc = subprocess.run([sys.executable, runner, "reap", "--skill", "ce-work", job], capture_output=True, check=False)
    if proc.returncode:
        raise Operational("BLOCKED", f"runner reap failed: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return "REAPED", {"unit_id": args.unit_id, **sync_job(args.run_id, args.unit_id)}


def cmd_cleanup(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"][args.unit_id]
        if unit["state"] == "cleaned":
            return "CLEANED", {"unit_id": args.unit_id, "resumed": True}
        attempt = find_attempt(unit)
        if args.abandon:
            transport = unit.get("transport")
            if transport:
                if args.expect_transport != transport.get("commit_id"):
                    raise Operational("REFUSED", "abandon cleanup requires the exact pinned transport revision")
            else:
                if not attempt.get("job_id") or args.expect_job != attempt["job_id"]:
                    raise Operational("REFUSED", "transport-free abandonment requires the exact runner job id")
                if attempt.get("process_state") not in TERMINAL_PROCESS and not attempt.get("terminal_validation_failure"):
                    raise Operational("REFUSED", "transport-free abandonment requires authoritative terminal evidence")
        if unit["state"] not in {"described", "native-completed"} and not args.abandon:
            raise Operational("REFUSED", "unaccepted output is retained unless explicitly abandoned")
        if attempt.get("process_state") == "running":
            raise Operational("REFUSED", "cannot clean a live worker")
        workspace = unit["workspace"]
        repo = doc["repository"]["toplevel"]
    with locked_manifest(args.run_id, write=True) as doc:
        event(doc, "cleanup-intent", args.unit_id, {"workspace": workspace["path"], "name": workspace["name"]})
    jj(repo, "workspace", "forget", workspace["name"])
    registered = jj_text(repo, "workspace", "list", "-T", 'name ++ "\\n"').splitlines()
    if workspace["name"] in registered:
        raise Operational("BLOCKED", "isolated workspace remained registered after forget")
    if os.path.exists(workspace["path"]):
        shutil.rmtree(workspace["path"])
    unit_root = os.path.dirname(workspace["path"])
    artifact_paths = [unit.get("packet", {}).get("path")]
    artifact_paths.extend(attempt.get("authorization_path") for attempt in unit.get("attempts", []))
    result_dir = os.path.join(unit_root, "result")
    if os.path.isdir(result_dir):
        artifact_paths.extend(entry.path for entry in os.scandir(result_dir) if entry.is_file(follow_symlinks=False))
    for artifact in artifact_paths:
        if not artifact or not os.path.exists(artifact):
            continue
        if os.path.commonpath([run_dir(args.run_id), os.path.abspath(artifact)]) != run_dir(args.run_id):
            raise Operational("BLOCKED", "cleanup artifact escaped the owned run")
        read_private(artifact, 10 * 1024 * 1024)
        os.unlink(artifact)
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        unit["cleanup"] = {"at": now_iso(), "workspace_removed": True, "abandoned": bool(args.abandon), "artifacts_pruned": True}
        if unit["state"] != "native-completed":
            unit["state"] = "cleaned"
        event(doc, "unit-cleaned", args.unit_id)
    return "CLEANED", {"unit_id": args.unit_id, "resumed": False}


def cmd_wave_advance(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        accepted = unit_accepted_revision(unit)
        if not accepted or accepted != args.canonical_revision:
            raise Operational("BLOCKED", "wave revision does not match the accepted canonical change")
        advanced = []
        for candidate in doc["units"].values():
            if candidate.get("wave", {}).get("id") == unit.get("wave", {}).get("id") and candidate["wave"]["position"] > unit["wave"]["position"]:
                candidate["wave"].setdefault("allowed_revisions", []).append(accepted)
                advanced.append(candidate["unit_id"])
        event(doc, "wave-advanced", args.unit_id, {"canonical_revision": accepted, "eligible_siblings": advanced})
    return "WAVE_ADVANCED", {"unit_id": args.unit_id, "canonical_revision": accepted, "eligible_siblings": advanced}
