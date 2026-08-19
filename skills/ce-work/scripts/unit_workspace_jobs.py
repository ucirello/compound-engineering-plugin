"""Unit preparation, runner evidence, and jj transport-change lifecycle."""

from __future__ import annotations

import json
import os
import shutil
import time

from unit_workspace_state import *

MAX_RESULT_BYTES = 5 * 1024 * 1024
MAX_REPORTED_CHANGED_FILES = 1000
HOST_RECEIPT_FIELDS = {
    "schema_version", "terminal_status", "summary", "changed_files", "evidence",
    "scope_expansion", "requested_route", "actual_route", "target", "harness",
    "intermediaries", "model_requested", "model_actual", "model_receipt_status",
    "packet_digest", "activity_posture", "restriction_posture", "failure_reason",
    "raw_log",
}


def find_attempt(unit: dict, attempt_id: str | None = None) -> dict:
    attempts = unit.get("attempts", [])
    matches = [a for a in attempts if a.get("attempt_id") == attempt_id] if attempt_id else attempts[-1:]
    if len(matches) != 1:
        raise Operational("AMBIGUOUS", "attempt could not be identified exactly")
    return matches[0]


def private_result_dir_identity(path: str) -> dict:
    validate_private_dir(path)
    st = os.stat(path, follow_symlinks=False)
    return {"dev": st.st_dev, "ino": st.st_ino}


def open_recorded_result_dir(unit: dict) -> tuple[int, str]:
    path = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")
    validate_private_dir(path)
    st = os.stat(path, follow_symlinks=False)
    if unit.get("result_dir_identity") != {"dev": st.st_dev, "ino": st.st_ino}:
        raise TrustFailure("controller result directory identity changed")
    return os.open(path, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW), path


def runner_job_dir(run_id: str, job_id: str) -> str:
    return os.path.join(run_dir(run_id), "jobs", safe_id(job_id, "job id"))


def process_evidence(job_dir: str) -> dict:
    validate_private_dir(job_dir)
    status = os.path.join(job_dir, "status")
    if os.path.exists(status):
        word = read_private(status, 256).decode().strip()
    elif os.path.exists(os.path.join(job_dir, "pid")):
        word = "running"
    else:
        word = "never-started"
    log = os.path.join(job_dir, "out.log")
    activity = {"latest_at": None, "log_bytes": 0}
    if os.path.exists(log):
        st = stat_private_file(log)
        activity = {"latest_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)), "log_bytes": st.st_size}
    return {"process_state": word, "activity": activity}


def cmd_prepare(args) -> tuple[str, dict]:
    uid, attempt_id = safe_id(args.unit_id, "unit id"), safe_id(args.attempt_id, "attempt id")
    packet = read_external_packet(args.packet)
    packet_digest = digest_bytes(packet)
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        repo = info["toplevel"]
        base = change_id(repo, args.base)
        if info["change_id"] != base or status_paths(repo):
            raise Operational("BLOCKED", "canonical change must equal the requested empty unit base")
        if uid in doc["units"]:
            unit = doc["units"][uid]
            return "PREPARED", {"unit_id": uid, "attempt_id": find_attempt(unit)["attempt_id"], **unit["workspace"], "packet_path": unit["packet"]["path"], "packet_digest": unit["packet_digest"], "adapter": find_attempt(unit)["adapter"], "resumed": True}
        unit_root = os.path.join(run_dir(args.run_id), "units", uid)
        workspace = os.path.join(unit_root, "workspace")
        workspace_name = f"rocketclaw-{args.run_id}-{uid}"
        authorization = attempt_authorization(doc, args.activity_posture, uid, attempt_id, packet_digest)
    ensure_private_dir(unit_root)
    result_dir = os.path.join(unit_root, "result")
    ensure_private_dir(result_dir)
    packet_path = os.path.join(unit_root, "packet.md")
    authorization_path = os.path.join(unit_root, "authorization.json")
    create_private(packet_path, packet)
    authorization_bytes = (json.dumps(authorization, sort_keys=True, separators=(",", ":")) + "\n").encode()
    create_private(authorization_path, authorization_bytes)
    jj(repo, "workspace", "add", "--name", workspace_name, "-r", base, workspace)
    transport_change = change_id(workspace)
    attempt = {
        "attempt_id": attempt_id, "job_id": None, "process_state": "never-started",
        "activity": {"posture": args.activity_posture, "latest_at": None},
        "authorization": authorization, "authorization_path": authorization_path,
        "authorization_digest": digest_bytes(authorization_bytes),
        "adapter": os.path.realpath(os.path.join(os.path.dirname(__file__), "cross-model-work.sh")),
        "terminal_receipt": None, "fallback": {"claimed": None, "completed": None},
    }
    unit = {
        "unit_id": uid, "state": "queued", "dependencies": list(args.dependency),
        "wave": {"id": args.wave_id, "base": base, "position": args.wave_position, "allowed_changes": [base]},
        "packet_digest": packet_digest, "packet": {"path": packet_path, "digest": packet_digest, "retained": True},
        "workspace": {"path": workspace, "name": workspace_name, "base": base, "base_commit": commit_id(repo, base), "transport_change": transport_change, "registered": True},
        "result_dir_identity": private_result_dir_identity(result_dir), "attempts": [attempt],
        "transport": {}, "integration": {}, "cleanup": None, "recovery_path": unit_root,
    }
    with locked_manifest(args.run_id, write=True) as doc:
        if uid in doc["units"]:
            raise Operational("BLOCKED", "unit was concurrently claimed")
        doc["units"][uid] = unit
        event(doc, "workspace-prepared", uid, {"path": workspace, "change_id": transport_change})
    return "PREPARED", {"unit_id": uid, "attempt_id": attempt_id, "workspace": workspace, "workspace_name": workspace_name, "result_dir": result_dir, "packet_path": packet_path, "packet_digest": packet_digest, "authorization_path": authorization_path, "authorization_digest": attempt["authorization_digest"], "adapter": attempt["adapter"], "base": base, "resumed": False}


def validate_runner_contract(run_id: str, unit: dict, meta: dict) -> None:
    attempt = find_attempt(unit)
    expected_result = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result", "implementation-result.json")
    expected_argv = [attempt["adapter"], attempt["authorization_path"], unit["workspace"]["path"], unit["packet"]["path"], unit["packet_digest"], os.path.dirname(expected_result)]
    if meta.get("skill") != "ce-work" or meta.get("run_id") != run_id or meta.get("label") != unit["unit_id"] or meta.get("input_digest") != unit["packet_digest"] or meta.get("worker_argv") != expected_argv or os.path.abspath(meta.get("result_path", "")) != expected_result:
        raise Operational("BLOCKED", "runner metadata does not match the fixed dispatch contract")


def cmd_authorize_dispatch(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit, args.attempt_id)
        meta = read_private_json(os.path.join(runner_job_dir(args.run_id, args.job_id), "meta.json"))
        validate_runner_contract(args.run_id, unit, meta)
        if any((os.path.abspath(args.authorization) != attempt["authorization_path"], args.authorization_digest != attempt["authorization_digest"], os.path.abspath(args.workspace) != unit["workspace"]["path"], os.path.abspath(args.packet) != unit["packet"]["path"], args.packet_digest != unit["packet_digest"])):
            raise Operational("BLOCKED", "dispatch paths or digests differ from the controller contract")
        attempt["job_id"] = args.job_id
        unit["state"] = "authoring"
        event(doc, "job-bound", args.unit_id, {"job_id": args.job_id})
    return "AUTHORIZED", {"run_id": args.run_id, "unit_id": args.unit_id, "attempt_id": args.attempt_id, "job_id": args.job_id, "packet_digest": args.packet_digest}


def cmd_record_job(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit, args.attempt_id)
        if attempt.get("job_id") not in (None, args.job_id):
            raise Operational("AMBIGUOUS", "attempt is bound to another job")
        validate_runner_contract(args.run_id, unit, read_private_json(os.path.join(runner_job_dir(args.run_id, args.job_id), "meta.json")))
        attempt["job_id"] = args.job_id
        unit["state"] = "authoring"
    return "AUTHORING", {"unit_id": args.unit_id, "job_id": args.job_id}


def sync_job(run_id: str, unit_id: str) -> dict:
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"].get(unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        if not attempt.get("job_id"):
            return {"process_state": "never-started", "activity": attempt["activity"]}
        evidence = process_evidence(runner_job_dir(run_id, attempt["job_id"]))
        attempt["process_state"] = evidence["process_state"]
        attempt["activity"].update(evidence["activity"])
        event(doc, "job-synced", unit_id, {"process_state": evidence["process_state"]})
        return evidence


def cmd_sync_job(args) -> tuple[str, dict]:
    return "SYNCED", {"unit_id": args.unit_id, **sync_job(args.run_id, args.unit_id)}


def _result(unit: dict) -> dict:
    path = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result", "implementation-result.json")
    try:
        value = json.loads(read_private(path, MAX_RESULT_BYTES))
    except (ValueError, UnicodeDecodeError) as exc:
        raise Operational("BLOCKED", "worker result is malformed JSON") from exc
    if not isinstance(value, dict) or set(value) != HOST_RECEIPT_FIELDS:
        raise Operational("BLOCKED", "adapter receipt keys do not match the controller contract")
    attempt = find_attempt(unit)
    authorization = attempt["authorization"]
    expected_identity = {
        "schema_version": 1,
        "requested_route": authorization["route"],
        "target": authorization["target"],
        "harness": authorization["harness"],
        "intermediaries": authorization["intermediaries"],
        "model_requested": authorization["model_requested"],
        "packet_digest": unit["packet_digest"],
        "activity_posture": authorization["activity_posture"],
        "restriction_posture": authorization["restriction_posture"],
    }
    mismatches = sorted(key for key, expected in expected_identity.items() if value.get(key) != expected)
    if mismatches:
        raise Operational("BLOCKED", "adapter receipt does not match controller authorization", {"mismatches": mismatches})
    if value["actual_route"] not in {None, authorization["route"]}:
        raise Operational("BLOCKED", "adapter changed the fixed route")
    if value["model_receipt_status"] not in {"verified", "unverified", "mismatch"}:
        raise Operational("BLOCKED", "adapter model receipt status is invalid")
    if value["model_receipt_status"] == "mismatch":
        raise Operational("BLOCKED", "adapter reported a served-model mismatch")
    if not isinstance(value["model_actual"], str) or not value["model_actual"]:
        raise Operational("BLOCKED", "adapter model receipt is invalid")
    if value["terminal_status"] not in {"completed", "blocked", "scope_expansion"}:
        raise Operational("BLOCKED", "worker result is not host-resolvable")
    if not isinstance(value["summary"], str) or not value["summary"]:
        raise Operational("BLOCKED", "worker result summary must be non-empty")
    changed = value["changed_files"]
    evidence = value["evidence"]
    if not isinstance(changed, list) or len(changed) > MAX_REPORTED_CHANGED_FILES or not all(isinstance(item, str) and item for item in changed) or len(changed) != len(set(changed)):
        raise Operational("BLOCKED", "worker changed_files is invalid or exceeds its bound")
    if not isinstance(evidence, list) or not all(isinstance(item, str) and item for item in evidence):
        raise Operational("BLOCKED", "worker evidence must be a list of non-empty strings")
    expansion = value["scope_expansion"]
    if expansion is not None:
        if not isinstance(expansion, dict) or set(expansion) != {"requested_paths", "reason"}:
            raise Operational("BLOCKED", "worker scope_expansion does not match the public result schema")
        paths = expansion["requested_paths"]
        if not isinstance(paths, list) or not paths or not all(isinstance(item, str) and item for item in paths) or len(paths) != len(set(paths)) or not isinstance(expansion["reason"], str) or not expansion["reason"]:
            raise Operational("BLOCKED", "worker scope_expansion fields are invalid")
    if value["terminal_status"] == "scope_expansion" and expansion is None:
        raise Operational("BLOCKED", "scope_expansion status requires expansion detail")
    if value["terminal_status"] != "scope_expansion" and expansion is not None:
        raise Operational("BLOCKED", "scope expansion detail requires scope_expansion status")
    result_dir = os.path.dirname(path)
    raw_log = os.path.realpath(value["raw_log"])
    if raw_log != os.path.realpath(os.path.join(result_dir, "adapter.log")):
        raise Operational("BLOCKED", "adapter raw-log receipt escaped the controller result directory")
    read_private(raw_log, 10 * 1024 * 1024)
    return value


def record_terminal_validation_failure(run_id: str, unit_id: str, error: Operational) -> None:
    if isinstance(error, TrustFailure):
        raise error
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        attempt = find_attempt(unit)
        path = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result", "implementation-result.json")
        failure = {
            "at": now_iso(),
            "word": error.word,
            "reason": str(error),
            "detail": error.detail,
            "job_id": attempt.get("job_id"),
            "result_sha256": digest_bytes(read_private(path, MAX_RESULT_BYTES)),
        }
        attempt["terminal_validation_failure"] = failure
        fallback = attempt.setdefault("fallback", {"claimed": None, "completed": None})
        fallback["eligible"] = fallback.get("claimed") is None
        fallback["reason"] = "terminal-validation-failure"
        event(doc, "terminal-validation-failed", unit_id, failure)


def validate_terminal_validation_failure(run_id: str, unit: dict, attempt: dict) -> dict:
    failure = attempt.get("terminal_validation_failure")
    if not isinstance(failure, dict) or failure.get("job_id") != attempt.get("job_id"):
        raise Operational("REFUSED", "attempt has no exact terminal-validation failure")
    if process_evidence(runner_job_dir(run_id, attempt["job_id"]))["process_state"] != "done":
        raise Operational("BLOCKED", "terminal-validation job evidence changed")
    path = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result", "implementation-result.json")
    if digest_bytes(read_private(path, MAX_RESULT_BYTES)) != failure.get("result_sha256"):
        raise Operational("BLOCKED", "terminal-validation result evidence changed")
    return failure


def terminalize(run_id: str, unit_id: str) -> dict:
    evidence = sync_job(run_id, unit_id)
    if evidence["process_state"] != "done":
        raise Operational("BLOCKED", f"worker is not authoritatively done ({evidence['process_state']})")
    try:
        with locked_manifest(run_id) as doc:
            unit = doc["units"].get(unit_id)
            receipt = _result(unit)
    except Operational as exc:
        record_terminal_validation_failure(run_id, unit_id, exc)
        raise
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"].get(unit_id)
        find_attempt(unit)["terminal_receipt"] = receipt
        if receipt["terminal_status"] != "completed":
            unit["state"] = "authored"
            raise Operational("BLOCKED", "worker returned a host-resolvable blocker", {"terminal_receipt": receipt, "recovery_path": unit["recovery_path"]})
        workspace = unit["workspace"]["path"]
        jj(workspace, "util", "snapshot")
        snap = semantic_snapshot(workspace)
        if snap["conflicts"]:
            raise Operational("BLOCKED", "worker workspace contains unresolved conflicts", {"conflicts": snap["conflicts"]})
        if not snap["changed_paths"]:
            raise Operational("BLOCKED", "worker produced no transportable change")
        if snap["parent_ids"] != [unit["workspace"]["base_commit"]]:
            raise Operational("BLOCKED", "worker transport no longer has the recorded base as its sole parent")
        if snap["description"].strip():
            raise Operational("BLOCKED", "worker mutated jj history by describing its transport change")
        transport = {"change_id": snap["change_id"], "commit_id": snap["commit_id"], "parent_ids": snap["parent_ids"], "operation_id": snap["operation_id"], "description": snap["description"], "changed_paths": snap["changed_paths"], "digest": digest_bytes(json.dumps(snap, sort_keys=True).encode())}
        unit["transport"] = transport
        unit["state"] = "integration-pending"
        event(doc, "transport-change-pinned", unit_id, {"change_id": snap["change_id"]})
        return transport


def cmd_terminalize(args) -> tuple[str, dict]:
    transport = terminalize(args.run_id, args.unit_id)
    return "INTEGRATION_PENDING", {"unit_id": args.unit_id, "transport": transport}


def matching_runner_jobs(run_id: str, unit: dict) -> list[str]:
    jobs = os.path.join(run_dir(run_id), "jobs")
    matches = []
    for entry in os.scandir(jobs):
        if entry.is_dir(follow_symlinks=False):
            meta = read_private_json(os.path.join(entry.path, "meta.json"))
            if meta.get("run_id") == run_id and meta.get("label") == unit["unit_id"]:
                matches.append(entry.name)
    return sorted(matches)


def parse_diff_paths(raw: bytes) -> list[str]:
    return [line for line in raw.decode("utf-8", "surrogateescape").splitlines() if line]


def scope_expansion_pending(unit: dict) -> bool:
    receipt = find_attempt(unit).get("terminal_receipt")
    return isinstance(receipt, dict) and receipt.get("terminal_status") == "scope_expansion"
