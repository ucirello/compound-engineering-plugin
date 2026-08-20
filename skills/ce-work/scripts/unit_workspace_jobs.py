"""Unit preparation, runner evidence, and Jujutsu transport lifecycle."""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys

from unit_workspace_state import *

MAX_RESULT_BYTES = 5 * 1024 * 1024


def find_attempt(unit: dict, attempt_id: str | None = None) -> dict:
    attempts = unit.get("attempts", [])
    matches = [a for a in attempts if a.get("attempt_id") == attempt_id] if attempt_id else attempts[-1:]
    if len(matches) != 1:
        raise Operational("AMBIGUOUS", "attempt could not be identified exactly")
    return matches[0]


def runner_job_dir(run_id: str, job_id: str, doc: dict | None = None) -> str:
    if doc is None:
        rd = locate_run(run_id)
    else:
        rd = locate_run(run_id, doc["repository"]["toplevel"])
    return os.path.join(rd, "jobs", safe_id(job_id, "job id"))


def process_evidence(job_dir: str) -> dict:
    validate_private_dir(job_dir)
    status = os.path.join(job_dir, "status")
    if os.path.exists(status):
        state = read_private(status, 256).decode().strip()
        if state not in TERMINAL_PROCESS:
            raise TrustFailure("runner terminal state is invalid")
    elif os.path.exists(os.path.join(job_dir, "pid")):
        state = "running"
    else:
        state = "never-started"
    log = os.path.join(job_dir, "out.log")
    activity = {"latest_at": None, "log_bytes": 0}
    if os.path.exists(log):
        st = os.stat(log)
        activity = {"latest_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)), "log_bytes": st.st_size}
    return {"process_state": state, "activity": activity}


def _workspace_name(run_id: str, unit_id: str) -> str:
    return f"work-{digest_bytes(run_id.encode())[:10]}-{digest_bytes(unit_id.encode())[:10]}"


def cmd_prepare(args) -> tuple[str, dict]:
    uid = safe_id(args.unit_id, "unit id")
    attempt_id = safe_id(args.attempt_id, "attempt id")
    packet = read_external_packet(args.packet)
    packet_digest = digest_bytes(packet)
    with locked_manifest(args.run_id, repo=args.repo if hasattr(args, "repo") else None) as doc:
        info = validate_repo(doc)
        repo = info["toplevel"]
        base_change = revision_field(repo, args.base, "change_id")
        base_snapshot = semantic_snapshot(repo)
        if base_snapshot["change_id"] != base_change or base_snapshot["changed_paths"]:
            raise Operational("BLOCKED", "canonical working-copy change is not the clean requested unit base")
        unit_root = os.path.join(locate_run(args.run_id, repo), "units", uid)
        workspace = os.path.join(unit_root, "workspace")
        packet_path = os.path.join(unit_root, "packet.md")
        authorization_path = os.path.join(unit_root, "authorization.json")
        workspace_name = _workspace_name(args.run_id, uid)
        existing = doc["units"].get(uid)
        if existing and existing.get("state") != "cleaned":
            attempt = find_attempt(existing, attempt_id)
            return "PREPARED", {
                "unit_id": uid, "attempt_id": attempt_id, "workspace": workspace,
                "workspace_name": workspace_name, "result_dir": os.path.join(unit_root, "result"),
                "packet_path": packet_path, "packet_digest": packet_digest,
                "authorization_path": authorization_path, "authorization_digest": attempt["authorization_digest"],
                "adapter": attempt["adapter"], "base": base_change, "resumed": True,
            }
        authorization = attempt_authorization(doc, args.activity_posture, uid, attempt_id, packet_digest)
    ensure_private_dir(unit_root)
    ensure_private_dir(os.path.join(unit_root, "result"))
    create_private(packet_path, packet)
    auth_bytes = (json.dumps(authorization, sort_keys=True, separators=(",", ":")) + "\n").encode()
    create_private(authorization_path, auth_bytes)
    if not os.path.exists(workspace):
        jj(repo, "workspace", "add", "--name", workspace_name, "-r", base_change, workspace)
    workspace_snapshot = semantic_snapshot(workspace)
    if workspace_snapshot["parents"] != [base_snapshot["snapshot_id"]] or workspace_snapshot["changed_paths"]:
        raise Operational("BLOCKED", "prepared Jujutsu workspace does not have the recorded pristine base")
    attempt = {
        "attempt_id": attempt_id, "job_id": None, "process_state": "never-started",
        "activity": {"posture": args.activity_posture, "latest_at": None},
        "authorization": authorization, "authorization_path": authorization_path,
        "authorization_digest": digest_bytes(auth_bytes),
        "adapter": os.path.realpath(os.path.join(os.path.dirname(__file__), "cross-model-work.sh")),
        "terminal_receipt": None, "fallback": {"eligible": False, "claimed": None, "completed": None},
    }
    unit = {
        "unit_id": uid, "state": "queued", "dependencies": list(args.dependency),
        "wave": {"id": args.wave_id, "base": base_change, "position": args.wave_position, "allowed_changes": [base_change]},
        "packet_digest": packet_digest, "packet": {"path": packet_path, "digest": packet_digest},
        "workspace": {"name": workspace_name, "path": workspace, "base_change_id": base_change, "base_snapshot_id": base_snapshot["snapshot_id"]},
        "attempts": [attempt], "transport": None,
        "composition": {"pre_fold": None, "expected_paths": None, "verification": None, "canonical_change": None, "restore": None},
        "cleanup": None, "recovery_path": unit_root,
    }
    with locked_manifest(args.run_id, write=True, repo=repo) as doc:
        doc["units"][uid] = unit
        event(doc, "workspace-prepared", uid, {"workspace": workspace_name, "base_change_id": base_change})
    return "PREPARED", {
        "unit_id": uid, "attempt_id": attempt_id, "workspace": workspace,
        "workspace_name": workspace_name, "result_dir": os.path.join(unit_root, "result"),
        "packet_path": packet_path, "packet_digest": packet_digest,
        "authorization_path": authorization_path, "authorization_digest": digest_bytes(auth_bytes),
        "adapter": attempt["adapter"], "base": base_change, "resumed": False,
    }


def _validate_dispatch(args, doc: dict, unit: dict, attempt: dict) -> None:
    expected = {
        "workspace": unit["workspace"]["path"], "packet": unit["packet"]["path"],
        "packet_digest": unit["packet_digest"],
        "authorization": attempt["authorization_path"],
        "authorization_digest": attempt["authorization_digest"],
        "result_dir": os.path.join(os.path.dirname(unit["workspace"]["path"]), "result"),
    }
    actual = {k: os.path.abspath(getattr(args, k)) if k in {"workspace", "packet", "authorization", "result_dir"} else getattr(args, k) for k in expected}
    normalized = {k: os.path.abspath(v) if k in {"workspace", "packet", "authorization", "result_dir"} else v for k, v in expected.items()}
    if actual != normalized:
        raise Operational("BLOCKED", "dispatch does not match the controller-issued workspace and packet contract")
    if digest_bytes(read_private(expected["authorization"])) != expected["authorization_digest"]:
        raise Operational("BLOCKED", "authorization bytes changed")
    if digest_bytes(read_private(expected["packet"], MAX_PACKET_BYTES)) != expected["packet_digest"]:
        raise Operational("BLOCKED", "packet bytes changed")


def cmd_authorize_dispatch(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit, args.attempt_id)
        _validate_dispatch(args, doc, unit, attempt)
        if attempt.get("job_id") not in (None, args.job_id):
            raise Operational("AMBIGUOUS", "attempt belongs to another job")
        attempt["job_id"] = safe_id(args.job_id, "job id")
        unit["state"] = "authoring"
        event(doc, "job-authorized", args.unit_id, {"job_id": args.job_id})
    return "AUTHORIZED", {"run_id": args.run_id, "unit_id": args.unit_id, "attempt_id": args.attempt_id, "job_id": args.job_id}


def cmd_record_job(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit, args.attempt_id)
        if attempt.get("job_id") not in (None, args.job_id):
            raise Operational("AMBIGUOUS", "attempt belongs to another job")
        attempt["job_id"] = safe_id(args.job_id, "job id")
        unit["state"] = "authoring"
    return "AUTHORING", {"unit_id": args.unit_id, "job_id": args.job_id}


def sync_job(run_id: str, unit_id: str) -> dict:
    with locked_manifest(run_id) as doc:
        unit = doc["units"].get(unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        evidence = process_evidence(runner_job_dir(run_id, attempt["job_id"], doc)) if attempt.get("job_id") else {"process_state": "never-started", "activity": attempt["activity"]}
    with locked_manifest(run_id, write=True) as doc:
        attempt = find_attempt(doc["units"][unit_id])
        attempt["process_state"] = evidence["process_state"]
        attempt["activity"].update(evidence["activity"])
        event(doc, "job-synced", unit_id, {"process_state": evidence["process_state"]})
    return evidence


def cmd_sync_job(args) -> tuple[str, dict]:
    return "SYNCED", {"unit_id": args.unit_id, **sync_job(args.run_id, args.unit_id)}


def _terminal_receipt(unit: dict) -> dict:
    path = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result", "implementation-result.json")
    raw = read_private(path, MAX_RESULT_BYTES)
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("terminal_status") not in {"completed", "blocked", "scope_expansion"}:
        raise Operational("BLOCKED", "worker did not publish a host-resolvable terminal result")
    return value


def terminalize(run_id: str, unit_id: str) -> dict:
    evidence = sync_job(run_id, unit_id)
    if evidence["process_state"] != "done":
        raise Operational("BLOCKED", f"worker is not authoritatively done ({evidence['process_state']})")
    with locked_manifest(run_id) as doc:
        unit = doc["units"].get(unit_id)
        receipt = _terminal_receipt(unit)
        workspace = unit["workspace"]["path"]
        jj(workspace, "util", "snapshot")
        transport = semantic_snapshot(workspace)
        if transport["parents"] != [unit["workspace"]["base_snapshot_id"]]:
            raise Operational("BLOCKED", "worker transport does not have the recorded base as sole parent")
        transport["changed_paths"] = sorted(status_paths(workspace))
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        find_attempt(unit)["terminal_receipt"] = receipt
        unit["transport"] = transport
        unit["state"] = "composition-pending"
        event(doc, "transport-recorded", unit_id, {"change_id": transport["change_id"]})
    if receipt["terminal_status"] == "blocked":
        raise Operational("BLOCKED", "worker returned a host-resolvable blocker", {"terminal_receipt": receipt})
    return transport


def cmd_terminalize(args) -> tuple[str, dict]:
    transport = terminalize(args.run_id, args.unit_id)
    return "TERMINALIZED", {"unit_id": args.unit_id, "transport_change": transport["change_id"], "changed_paths": transport["changed_paths"]}


def scope_expansion_pending(unit: dict) -> bool:
    receipt = find_attempt(unit).get("terminal_receipt")
    return isinstance(receipt, dict) and receipt.get("terminal_status") == "scope_expansion"
