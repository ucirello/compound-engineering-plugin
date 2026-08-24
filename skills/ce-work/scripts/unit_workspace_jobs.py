"""JJ unit workspace preparation, runner evidence, and change transport."""

from __future__ import annotations

import json
import os
import stat
import time

from unit_workspace_state import *


MAX_RESULT_BYTES = 5 * 1024 * 1024


def find_attempt(unit: dict, attempt_id: str | None = None) -> dict:
    attempts = unit.get("attempts", [])
    matches = [row for row in attempts if row.get("attempt_id") == attempt_id] if attempt_id else attempts[-1:]
    if len(matches) != 1:
        raise Operational("AMBIGUOUS", "attempt could not be identified exactly")
    return matches[0]


def private_result_dir_identity(path: str) -> dict:
    st = os.stat(path, follow_symlinks=False)
    if not stat.S_ISDIR(st.st_mode):
        raise TrustFailure("result path is not a directory")
    return {"dev": st.st_dev, "ino": st.st_ino}


def open_recorded_result_dir(unit: dict) -> tuple[int, str]:
    result_dir = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")
    fd = os.open(result_dir, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    st = os.fstat(fd)
    identity = unit.get("result_dir_identity")
    if identity != {"dev": st.st_dev, "ino": st.st_ino}:
        os.close(fd)
        raise TrustFailure("controller result directory identity changed")
    return fd, result_dir


def read_recorded_result_file(unit: dict, name: str, cap: int) -> bytes:
    fd, result_dir = open_recorded_result_dir(unit)
    os.close(fd)
    return read_private(os.path.join(result_dir, name), cap)


def runner_job_dir(run_id: str, job_id: str) -> str:
    return os.path.join(run_dir(run_id), "jobs", safe_id(job_id, "job id"))


def process_evidence(job_dir: str) -> dict:
    status_path = os.path.join(job_dir, "status")
    if os.path.exists(status_path):
        word = read_private(status_path, 256).decode("ascii", "strict").strip()
        if word not in TERMINAL_PROCESS:
            raise TrustFailure("runner terminal state is invalid")
    elif os.path.exists(os.path.join(job_dir, "pid")):
        word = "running"
    else:
        word = "never-started"
    log_path = os.path.join(job_dir, "out.log")
    activity = {"latest_at": None, "log_bytes": 0}
    if os.path.exists(log_path):
        st = os.stat(log_path, follow_symlinks=False)
        activity = {"latest_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)), "log_bytes": st.st_size}
    reason_path = os.path.join(job_dir, "reason")
    reason = read_private(reason_path, 4096).decode().strip() if os.path.exists(reason_path) else None
    return {"process_state": word, "failure_reason": reason, "activity": activity}


def validate_workspace(doc: dict, unit: dict) -> dict:
    path = unit["workspace"]["path"]
    if workspace_root(path) != os.path.realpath(path):
        raise Operational("BLOCKED", "unit path is not its registered JJ workspace root")
    if os.path.realpath(jj_text(path, "git", "root")) != doc["repository"]["jj_root"]:
        raise Operational("BLOCKED", "unit workspace belongs to another JJ repository")
    return change_info(path)


def validate_pristine_unit_base(doc: dict, unit: dict) -> dict:
    current = validate_workspace(doc, unit)
    parent = change_info(unit["workspace"]["path"], "@-")
    if parent["commit_id"] != unit["workspace"]["base_commit_id"] or status_paths(unit["workspace"]["path"]):
        raise Operational("BLOCKED", "unit workspace is not pristine on its recorded base")
    return current


def _workspace_name(run_id: str, unit_id: str) -> str:
    return f"rocketclaw-{digest_bytes(run_id.encode())[:10]}-{digest_bytes(unit_id.encode())[:10]}"


def cmd_prepare(args) -> tuple[str, dict]:
    uid = safe_id(args.unit_id, "unit id")
    attempt_id = safe_id(args.attempt_id, "attempt id")
    packet_bytes = read_external_packet(args.packet)
    packet_digest = digest_bytes(packet_bytes)
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        repo = info["workspace_root"]
        base = change_info(repo, args.base)
        if info["commit_id"] != base["commit_id"] or status_paths(repo):
            raise Operational("BLOCKED", "canonical working-copy change does not equal the requested clean unit base")
        existing = doc["units"].get(uid)
        if existing and existing.get("state") != "cleaned":
            attempt = find_attempt(existing, attempt_id)
            validate_workspace(doc, existing)
            return "PREPARED", {
                "unit_id": uid, "attempt_id": attempt_id, "workspace": existing["workspace"]["path"],
                "result_dir": os.path.join(os.path.dirname(existing["workspace"]["path"]), "result"),
                "packet_path": existing["packet"]["path"], "packet_digest": packet_digest,
                "authorization_path": attempt["authorization_path"], "authorization_digest": attempt["authorization_digest"],
                "adapter": attempt["adapter"], "base": base["commit_id"], "resumed": True,
            }
        unit_root = os.path.join(run_dir(args.run_id), "units", uid)
        workspace = os.path.join(unit_root, "workspace")
        result_dir = os.path.join(unit_root, "result")
        packet_path = os.path.join(unit_root, "packet.md")
        authorization_path = os.path.join(unit_root, "authorization.json")
        authorization = attempt_authorization(doc, args.activity_posture, uid, attempt_id, packet_digest)
    ensure_private_dir(unit_root)
    ensure_private_dir(result_dir)
    if not os.path.exists(packet_path):
        create_private(packet_path, packet_bytes)
    authorization_bytes = (json.dumps(authorization, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if not os.path.exists(authorization_path):
        create_private(authorization_path, authorization_bytes)
    if not os.path.exists(workspace):
        jj(repo, "workspace", "add", "--name", _workspace_name(args.run_id, uid), "-r", base["commit_id"], workspace)
    unit = {
        "unit_id": uid, "state": "queued", "dependencies": list(args.dependency),
        "wave": {"id": args.wave_id, "base": base["commit_id"], "position": args.wave_position, "allowed_changes": [base["commit_id"]]},
        "packet_digest": packet_digest, "packet": {"path": packet_path, "digest": packet_digest, "retained": True},
        "workspace": {"path": workspace, "name": _workspace_name(args.run_id, uid), "base_change_id": base["change_id"], "base_commit_id": base["commit_id"], "registered": True},
        "result_dir_identity": private_result_dir_identity(result_dir),
        "attempts": [{
            "attempt_id": attempt_id, "job_id": None, "process_state": "never-started",
            "activity": {"posture": args.activity_posture, "latest_at": None},
            "fallback": {"eligible": False, "reason": None, "claimed": None},
            "authorization": authorization, "authorization_path": authorization_path,
            "authorization_digest": digest_bytes(authorization_bytes),
            "adapter": os.path.realpath(os.path.join(os.path.dirname(__file__), "cross-model-work.sh")),
            "terminal_receipt": None,
        }],
        "transport": {"change_id": None, "commit_id": None, "changed_paths": []},
        "integration": {"pre_operation": None, "verification": None, "canonical_change": None, "restore": None},
        "cleanup": None, "recovery_path": unit_root,
    }
    with locked_manifest(args.run_id, write=True) as doc:
        if uid in doc["units"] and doc["units"][uid].get("state") != "cleaned":
            raise Operational("BLOCKED", "unit was concurrently claimed")
        doc["units"][uid] = unit
        event(doc, "workspace-prepared", uid, {"path": workspace, "base": base["commit_id"]})
    validate_pristine_unit_base(doc, unit)
    return "PREPARED", {
        "unit_id": uid, "attempt_id": attempt_id, "workspace": workspace, "result_dir": result_dir,
        "packet_path": packet_path, "packet_digest": packet_digest,
        "authorization_path": authorization_path, "authorization_digest": digest_bytes(authorization_bytes),
        "adapter": unit["attempts"][0]["adapter"], "base": base["commit_id"], "resumed": False,
    }


def validate_runner_contract(run_id: str, unit: dict, meta: dict) -> None:
    attempt = find_attempt(unit)
    expected = [attempt["adapter"], attempt["authorization_path"], unit["workspace"]["path"], unit["packet"]["path"], unit["packet_digest"], os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")]
    if meta.get("skill") != "ce-work" or meta.get("run_id") != run_id or meta.get("label") != unit["unit_id"] or meta.get("worker_argv") != expected:
        raise Operational("BLOCKED", "runner metadata does not match the controller-issued unit contract")


def cmd_authorize_dispatch(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit, args.attempt_id)
        meta = read_private_json(os.path.join(runner_job_dir(args.run_id, args.job_id), "meta.json"))
        validate_runner_contract(args.run_id, unit, meta)
        if os.path.abspath(args.workspace) != unit["workspace"]["path"] or os.path.abspath(args.packet) != unit["packet"]["path"] or args.packet_digest != unit["packet_digest"]:
            raise Operational("BLOCKED", "dispatch paths or digest differ from the prepared unit")
        if os.path.abspath(args.authorization) != attempt["authorization_path"] or args.authorization_digest != attempt["authorization_digest"]:
            raise Operational("BLOCKED", "dispatch authorization differs from the prepared attempt")
        validate_pristine_unit_base(doc, unit)
        attempt["job_id"] = args.job_id
        unit["state"] = "authoring"
        event(doc, "job-bound", args.unit_id, {"job_id": args.job_id})
    return "AUTHORIZED", {"run_id": args.run_id, "unit_id": args.unit_id, "attempt_id": args.attempt_id, "job_id": args.job_id, "packet_digest": unit["packet_digest"]}


def cmd_record_job(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit, args.attempt_id)
        if attempt.get("job_id") not in (None, args.job_id):
            raise Operational("AMBIGUOUS", "attempt is already bound to another job")
        attempt["job_id"] = args.job_id
        unit["state"] = "authoring"
    return "AUTHORING", {"unit_id": args.unit_id, "job_id": args.job_id}


def sync_job(run_id: str, unit_id: str) -> dict:
    with locked_manifest(run_id) as doc:
        unit = doc["units"].get(unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        if not attempt.get("job_id"):
            return {"process_state": "never-started", "activity": attempt["activity"]}
        evidence = process_evidence(runner_job_dir(run_id, attempt["job_id"]))
    with locked_manifest(run_id, write=True) as doc:
        attempt = find_attempt(doc["units"][unit_id])
        attempt["process_state"] = evidence["process_state"]
        attempt["activity"].update(evidence["activity"])
        if evidence["process_state"] in TERMINAL_PROCESS - {"done"}:
            attempt["fallback"] = {"eligible": True, "reason": evidence["failure_reason"] or evidence["process_state"], "claimed": None}
        event(doc, "job-synced", unit_id, {"process_state": evidence["process_state"]})
    return evidence


def cmd_sync_job(args) -> tuple[str, dict]:
    return "SYNCED", {"unit_id": args.unit_id, **sync_job(args.run_id, args.unit_id)}


def terminal_receipt(unit: dict, attempt: dict) -> dict:
    raw = read_recorded_result_file(unit, "implementation-result.json", MAX_RESULT_BYTES)
    try:
        receipt = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise Operational("BLOCKED", "worker result is malformed JSON") from exc
    if receipt.get("terminal_status") not in {"completed", "blocked", "scope_expansion", "unavailable", "failed"}:
        raise Operational("BLOCKED", "worker result has no host-resolvable terminal status")
    return receipt


def terminalize(run_id: str, unit_id: str) -> dict:
    evidence = sync_job(run_id, unit_id)
    if evidence["process_state"] != "done":
        raise Operational("BLOCKED", f"worker is not authoritatively done ({evidence['process_state']})")
    with locked_manifest(run_id) as doc:
        unit = doc["units"][unit_id]
        attempt = find_attempt(unit)
        receipt = terminal_receipt(unit, attempt)
        if receipt["terminal_status"] != "completed":
            raise Operational("BLOCKED", "worker returned a host-resolvable blocker", {"terminal_receipt": receipt})
        workspace = unit["workspace"]["path"]
        jj(workspace, "status")
        if jj_text(workspace, "log", "--no-graph", "-r", "conflicts() & @", "-T", "change_id"):
            raise Operational("BLOCKED", "worker workspace contains unresolved JJ conflicts")
        transport = change_info(workspace)
        changed_paths = sorted(status_paths(workspace))
        reported = receipt.get("changed_files", [])
        if not isinstance(reported, list):
            raise Operational("BLOCKED", "worker changed-files evidence is invalid")
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        unit["state"] = "integration-pending"
        unit["transport"] = {"change_id": transport["change_id"], "commit_id": transport["commit_id"], "changed_paths": changed_paths}
        find_attempt(unit)["terminal_receipt"] = receipt
        event(doc, "change-terminalized", unit_id, {"change_id": transport["change_id"], "changed_paths": changed_paths})
    return unit["transport"]


def cmd_terminalize(args) -> tuple[str, dict]:
    return "TERMINALIZED", {"unit_id": args.unit_id, "transport": terminalize(args.run_id, args.unit_id)}


def matching_runner_jobs(run_id: str, unit: dict) -> list[str]:
    jobs = os.path.join(run_dir(run_id), "jobs")
    matches = []
    for entry in os.scandir(jobs):
        if entry.is_dir(follow_symlinks=False):
            meta = read_private_json(os.path.join(entry.path, "meta.json"))
            if meta.get("run_id") == run_id and meta.get("label") == unit["unit_id"]:
                matches.append(entry.name)
    return sorted(matches)


def scope_expansion_pending(unit: dict) -> bool:
    receipt = find_attempt(unit).get("terminal_receipt")
    return isinstance(receipt, dict) and receipt.get("terminal_status") == "scope_expansion"
