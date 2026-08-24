"""JJ workspace preparation, runner evidence, and transport-change lifecycle."""

from __future__ import annotations

import json
import os
import re
import stat

from unit_workspace_state import *

MAX_RESULT_BYTES = 5 * 1024 * 1024
MAX_REPORTED_CHANGED_FILES = 1000


def find_attempt(unit: dict, attempt_id: str | None = None) -> dict:
    attempts = unit.get("attempts", [])
    matches = [row for row in attempts if row.get("attempt_id") == attempt_id] if attempt_id else attempts[-1:]
    if len(matches) != 1:
        raise Operational("AMBIGUOUS", "attempt could not be identified exactly")
    return matches[0]


def runner_job_dir(run_id: str, job_id: str) -> str:
    return os.path.join(run_dir(run_id), "jobs", safe_id(job_id, "job id"))


def private_result_dir_identity(path: str) -> dict:
    try:
        fd = os.open(path, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open result directory {path}: {exc}") from exc
    try:
        info = os.fstat(fd)
        uid_getter = getattr(os, "geteuid", None) or getattr(os, "getuid", None)
        effective_uid = uid_getter() if uid_getter else None
        if (
            not stat.S_ISDIR(info.st_mode)
            or (effective_uid is not None and info.st_uid != effective_uid)
            or (os.name != "nt" and stat.S_IMODE(info.st_mode) != 0o700)
        ):
            raise TrustFailure(f"result directory owner/type/mode validation failed: {path}")
        return {"dev": info.st_dev, "ino": info.st_ino}
    finally:
        os.close(fd)


def read_recorded_result_file(unit: dict, name: str, cap: int) -> bytes:
    result_dir = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")
    identity = unit.get("result_dir_identity")
    if not isinstance(identity, dict) or set(identity) != {"dev", "ino"}:
        raise TrustFailure("unit has no valid recorded result-directory identity")
    try:
        directory_fd = os.open(result_dir, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open result directory {result_dir}: {exc}") from exc
    try:
        directory = os.fstat(directory_fd)
        uid_getter = getattr(os, "geteuid", None) or getattr(os, "getuid", None)
        effective_uid = uid_getter() if uid_getter else None
        if (
            not stat.S_ISDIR(directory.st_mode)
            or (effective_uid is not None and directory.st_uid != effective_uid)
            or (os.name != "nt" and stat.S_IMODE(directory.st_mode) != 0o700)
            or (directory.st_dev, directory.st_ino) != (identity.get("dev"), identity.get("ino"))
        ):
            raise TrustFailure("controller result-directory identity or permissions changed")
        fd = os.open(name, os.O_RDONLY | O_NOFOLLOW, dir_fd=directory_fd)
        try:
            info = os.fstat(fd)
            if (
                not stat.S_ISREG(info.st_mode)
                or (effective_uid is not None and info.st_uid != effective_uid)
                or (os.name != "nt" and stat.S_IMODE(info.st_mode) != 0o600)
                or info.st_size > cap
            ):
                raise TrustFailure(f"invalid private result file: {os.path.join(result_dir, name)}")
            data = bytearray()
            while len(data) <= cap:
                part = os.read(fd, min(65536, cap + 1 - len(data)))
                if not part:
                    break
                data.extend(part)
            if len(data) > cap:
                raise TrustFailure(f"private result file exceeds {cap} bytes")
            return bytes(data)
        finally:
            os.close(fd)
    finally:
        os.close(directory_fd)


def process_evidence(job_dir: str) -> dict:
    validate_private_dir(job_dir)
    status_path = os.path.join(job_dir, "status")
    if os.path.lexists(status_path):
        state = read_private(status_path, 256).decode("ascii", "strict").strip()
        if state not in TERMINAL_PROCESS:
            raise TrustFailure("runner terminal state is invalid")
    elif os.path.lexists(os.path.join(job_dir, "pid")):
        state = "running"
    else:
        state = "never-started"
    log_path = os.path.join(job_dir, "out.log")
    activity = {"latest_at": None, "log_bytes": 0}
    if os.path.lexists(log_path):
        info = stat_private_file(log_path)
        activity = {"latest_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(info.st_mtime)), "log_bytes": info.st_size}
    reason_path = os.path.join(job_dir, "reason")
    reason = read_private(reason_path, 4096).decode("utf-8", "replace").strip() if os.path.lexists(reason_path) else None
    return {"process_state": state, "failure_reason": reason or None, "activity": activity}


def _result(unit: dict) -> tuple[dict, bytes]:
    path = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result", "implementation-result.json")
    raw = read_recorded_result_file(unit, "implementation-result.json", MAX_RESULT_BYTES)
    try:
        value = json.loads(raw)
    except ValueError as exc:
        raise Operational("BLOCKED", "worker result is malformed JSON") from exc
    if not isinstance(value, dict):
        raise Operational("BLOCKED", "worker result is not an object")
    return value, raw


def terminal_receipt(unit: dict, attempt: dict) -> dict:
    value, raw = _result(unit)
    authorization = attempt["authorization"]
    expected = {
        "requested_route": authorization["route"],
        "actual_route": None if value.get("terminal_status") == "unavailable" else authorization["route"],
        "target": authorization["target"],
        "harness": authorization["harness"],
        "intermediaries": authorization["intermediaries"],
        "model_requested": authorization["model_requested"],
        "restriction_posture": authorization["restriction_posture"],
        "packet_digest": unit["packet_digest"],
    }
    mismatch = {key: {"expected": wanted, "actual": value.get(key)} for key, wanted in expected.items() if value.get(key) != wanted}
    if mismatch:
        raise Operational("BLOCKED", "worker receipt disagrees with authorization", {"mismatches": mismatch})
    if value.get("terminal_status") not in {"completed", "blocked", "scope_expansion", "unavailable", "failed"}:
        raise Operational("BLOCKED", "worker terminal status is invalid")
    if value.get("terminal_status") == "scope_expansion" and not isinstance(value.get("scope_expansion"), dict):
        raise Operational("BLOCKED", "scope-expansion result has no expansion receipt")
    files = value.get("changed_files")
    if not isinstance(files, list) or len(files) > MAX_REPORTED_CHANGED_FILES or any(not isinstance(path, str) or not path for path in files):
        raise Operational("BLOCKED", "worker changed-files evidence is invalid")
    raw_log = value.get("raw_log")
    result_dir = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")
    expected_log = os.path.join(result_dir, "adapter.log")
    if not isinstance(raw_log, str) or os.path.abspath(raw_log) != expected_log:
        raise Operational("BLOCKED", "adapter raw-log receipt escaped the controller result directory")
    log_bytes = read_recorded_result_file(unit, "adapter.log", 10 * 1024 * 1024)
    return {
        **{key: value.get(key) for key in (
            "requested_route", "actual_route", "target", "harness", "intermediaries",
            "model_requested", "model_actual", "model_receipt_status", "activity_posture",
            "restriction_posture", "failure_reason", "raw_log", "packet_digest",
        )},
        "terminal_status": value["terminal_status"],
        "summary": str(value.get("summary", ""))[:4096],
        "changed_files": files,
        "changed_file_count": len(files),
        "result_sha256": digest_bytes(raw),
        "raw_log_sha256": digest_bytes(log_bytes),
        "raw_log_bytes": len(log_bytes),
        "scope_expansion_requested": value.get("scope_expansion") is not None,
    }


def _workspace_name(run_id: str, unit_id: str, attempt_id: str) -> str:
    digest = digest_bytes(f"{run_id}\0{unit_id}\0{attempt_id}".encode())[:20]
    return f"ce-work-{digest}"


def cmd_prepare(args) -> tuple[str, dict]:
    uid = safe_id(args.unit_id, "unit id")
    attempt_id = safe_id(args.attempt_id, "attempt id")
    packet = read_external_packet(args.packet)
    packet_digest = digest_bytes(packet)
    prior_attempts = []
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        repo = info["workspace_root"]
        if not is_empty(repo) or has_conflicts(repo):
            raise Operational("BLOCKED", "canonical working-copy change must be empty and conflict-free")
        base = revision_info(repo, args.base)
        current_parent = revision_info(repo, "@-")
        if base["commit_id"] != current_parent["commit_id"] and base["commit_id"] != revision_info(repo)["commit_id"]:
            raise Operational("BLOCKED", "requested base is not the canonical working copy or its parent")
        existing = doc["units"].get(uid)
        if existing and existing.get("state") == "preserved":
            raise Operational("REFUSED", "preserved output must be explicitly abandoned and cleaned before retry")
        if existing and existing.get("state") != "cleaned":
            attempt = find_attempt(existing, attempt_id)
            return "PREPARED", {
                "unit_id": uid, "attempt_id": attempt_id, "workspace": existing["workspace"]["path"],
                "workspace_name": existing["workspace"]["name"], "packet_path": existing["packet"]["path"],
                "packet_digest": packet_digest, "authorization_path": attempt["authorization_path"],
                "authorization_digest": attempt["authorization_digest"], "adapter": attempt["adapter"],
                "base_change": base, "resumed": True,
            }
        if existing:
            prior_attempts = list(existing.get("attempts", []))
            if any(row.get("attempt_id") == attempt_id for row in prior_attempts):
                raise Operational("REFUSED", "a retry requires a fresh attempt ID")
        unit_root = os.path.join(run_dir(args.run_id), "units", uid)
        workspace = os.path.join(unit_root, "workspace")
        result_dir = os.path.join(unit_root, "result")
        packet_path = os.path.join(unit_root, "packet.md")
        authorization_path = os.path.join(unit_root, "authorization.json")
        name = _workspace_name(args.run_id, uid, attempt_id)
        authorization = attempt_authorization(doc, args.activity_posture, uid, attempt_id, packet_digest)
        authorization_bytes = (json.dumps(authorization, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ensure_private_dir(unit_root)
    ensure_private_dir(result_dir)
    create_private(packet_path, packet)
    create_private(authorization_path, authorization_bytes)
    jj(repo, "workspace", "add", "--name", name, "-r", base["change_id"], workspace)
    worker_change = revision_info(workspace)
    attempt = {
        "attempt_id": attempt_id, "job_id": None, "process_state": "never-started",
        "activity": {"posture": args.activity_posture, "latest_at": None},
        "authorization": authorization, "authorization_path": authorization_path,
        "authorization_digest": digest_bytes(authorization_bytes),
        "adapter": os.path.realpath(os.path.join(os.path.dirname(__file__), "cross-model-work.sh")),
        "terminal_receipt": None, "fallback": {"eligible": False, "reason": None, "claimed": None, "completed": None},
    }
    unit = {
        "unit_id": uid, "state": "queued", "dependencies": list(args.dependency),
        "wave": {"id": args.wave_id, "base": base, "position": args.wave_position, "accepted": []},
        "packet_digest": packet_digest, "packet": {"path": packet_path, "digest": packet_digest, "retained": True},
        "workspace": {"path": workspace, "name": name, "base": base, "change": worker_change, "registered": True},
        "result_dir_identity": private_result_dir_identity(result_dir), "attempts": [*prior_attempts, attempt],
        "transport": None, "integration": {"pre_operation": None, "pre_snapshot": None, "accepted_change": None, "restore": None},
        "cleanup": None, "recovery_path": unit_root,
    }
    with locked_manifest(args.run_id, write=True) as doc:
        if uid in doc["units"] and doc["units"][uid].get("state") not in {"cleaned", "preserved"}:
            raise Operational("BLOCKED", "unit was concurrently claimed")
        doc["units"][uid] = unit
        event(doc, "jj-workspace-prepared", uid, {"workspace": workspace, "change_id": worker_change["change_id"]})
    return "PREPARED", {
        "unit_id": uid, "attempt_id": attempt_id, "workspace": workspace, "workspace_name": name,
        "result_dir": result_dir, "packet_path": packet_path, "packet_digest": packet_digest,
        "authorization_path": authorization_path, "authorization_digest": attempt["authorization_digest"],
        "adapter": attempt["adapter"], "base_change": base, "worker_change": worker_change, "resumed": False,
    }


def _validate_runner_contract(run_id: str, unit: dict, meta: dict) -> None:
    attempt = find_attempt(unit)
    result = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result", "implementation-result.json")
    expected = [attempt["adapter"], attempt["authorization_path"], unit["workspace"]["path"], unit["packet"]["path"], unit["packet_digest"], os.path.dirname(result)]
    if meta.get("skill") != "ce-work" or meta.get("run_id") != run_id or meta.get("label") != unit["unit_id"]:
        raise Operational("BLOCKED", "runner identity does not match the unit")
    authorization_bytes = read_private(attempt["authorization_path"], MAX_JSON_BYTES)
    try:
        observed_authorization = json.loads(authorization_bytes)
    except (ValueError, UnicodeDecodeError) as exc:
        raise TrustFailure("controller authorization artifact is malformed") from exc
    if observed_authorization != attempt["authorization"] or digest_bytes(authorization_bytes) != attempt["authorization_digest"]:
        raise Operational("BLOCKED", "controller authorization artifact no longer matches the recorded attempt")
    if meta.get("input_digest") != unit["packet_digest"] or meta.get("worker_argv") != expected or os.path.abspath(meta.get("result_path", "")) != result:
        raise Operational("BLOCKED", "runner dispatch contract does not match the unit")


def cmd_authorize_dispatch(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit, args.attempt_id)
        job_dir = runner_job_dir(args.run_id, args.job_id)
        meta = read_private_json(os.path.join(job_dir, "meta.json"))
        _validate_runner_contract(args.run_id, unit, meta)
        if os.path.abspath(args.workspace) != unit["workspace"]["path"] or os.path.abspath(args.packet) != unit["packet"]["path"]:
            raise Operational("BLOCKED", "dispatch paths differ from controller paths")
        if args.packet_digest != unit["packet_digest"] or args.authorization_digest != attempt["authorization_digest"]:
            raise Operational("BLOCKED", "dispatch digest differs from controller digest")
        if semantic_snapshot(unit["workspace"]["path"])["changed_paths"]:
            raise Operational("BLOCKED", "worker workspace changed before dispatch authorization")
        if attempt.get("job_id") not in {None, args.job_id}:
            raise Operational("AMBIGUOUS", "attempt is bound to another job")
        resumed = attempt.get("job_id") == args.job_id
        attempt["job_id"] = args.job_id
        expected_result_dir = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")
        if os.path.abspath(args.authorization) != attempt["authorization_path"] or os.path.abspath(args.result_dir) != expected_result_dir:
            raise Operational("BLOCKED", "dispatch authorization or result path differs from controller paths")
        if private_result_dir_identity(expected_result_dir) != unit.get("result_dir_identity"):
            raise Operational("BLOCKED", "dispatch result-directory identity differs from controller identity")
        attempt["dispatch_authorization_receipt"] = {
            "attempt_id": args.attempt_id, "job_id": args.job_id,
            "authorization_path": attempt["authorization_path"], "authorization_digest": args.authorization_digest,
            "workspace": unit["workspace"]["path"], "packet_path": unit["packet"]["path"],
            "packet_digest": args.packet_digest, "result_dir": expected_result_dir,
            "result_dir_identity": unit["result_dir_identity"],
        }
        unit["state"] = "authoring"
        event(doc, "job-bound", args.unit_id, {"job_id": args.job_id})
    return "AUTHORIZED", {"run_id": args.run_id, "unit_id": args.unit_id, "attempt_id": args.attempt_id, "job_id": args.job_id, "resumed": resumed}


def cmd_record_job(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit, args.attempt_id)
        meta = read_private_json(os.path.join(runner_job_dir(args.run_id, args.job_id), "meta.json"))
        _validate_runner_contract(args.run_id, unit, meta)
        if attempt.get("job_id") not in {None, args.job_id}:
            raise Operational("AMBIGUOUS", "attempt is bound to another job")
        resumed = attempt.get("job_id") == args.job_id
        attempt["job_id"] = args.job_id
        unit["state"] = "authoring"
    return "AUTHORING", {"unit_id": args.unit_id, "job_id": args.job_id, "resumed": resumed}


def matching_runner_jobs(run_id: str, unit: dict) -> list[str]:
    jobs = os.path.join(run_dir(run_id), "jobs")
    validate_private_dir(jobs)
    matches = []
    for entry in os.scandir(jobs):
        if not entry.is_dir(follow_symlinks=False):
            continue
        safe_id(entry.name, "job id")
        meta = read_private_json(os.path.join(entry.path, "meta.json"))
        if meta.get("run_id") == run_id and meta.get("label") == unit["unit_id"] and meta.get("input_digest") == unit["packet_digest"]:
            _validate_runner_contract(run_id, unit, meta)
            matches.append(entry.name)
    return sorted(matches)


def sync_job(run_id: str, unit_id: str) -> dict:
    with locked_manifest(run_id) as doc:
        unit = doc["units"].get(unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        if not attempt.get("job_id"):
            return {"process_state": "never-started", "activity": attempt["activity"], "failure_reason": None}
        evidence = process_evidence(runner_job_dir(run_id, attempt["job_id"]))
        receipt = None
        if evidence["process_state"] in {"done", "failed"}:
            with contextlib.suppress(Operational, TrustFailure, OSError):
                receipt = terminal_receipt(unit, attempt)
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        attempt = find_attempt(unit)
        attempt["process_state"] = evidence["process_state"]
        attempt["activity"].update(evidence["activity"])
        if receipt:
            attempt["terminal_receipt"] = receipt
        if evidence["process_state"] in TERMINAL_PROCESS - {"done"}:
            attempt["fallback"] = {**attempt.get("fallback", {}), "eligible": True, "reason": evidence["failure_reason"] or evidence["process_state"]}
        event(doc, "job-synced", unit_id, {"process_state": evidence["process_state"]})
    return evidence


def cmd_sync_job(args) -> tuple[str, dict]:
    return "SYNCED", {"unit_id": args.unit_id, **sync_job(args.run_id, args.unit_id)}


def scope_expansion_pending(unit: dict) -> bool:
    receipt = find_attempt(unit).get("terminal_receipt")
    return isinstance(receipt, dict) and receipt.get("terminal_status") == "scope_expansion"


def record_terminal_validation_failure(run_id: str, unit_id: str, error: Operational) -> None:
    if isinstance(error, TrustFailure):
        raise error
    with locked_manifest(run_id) as doc:
        unit = doc["units"][unit_id]
        result_digest = digest_bytes(read_recorded_result_file(unit, "implementation-result.json", MAX_RESULT_BYTES))
    with locked_manifest(run_id, write=True) as doc:
        attempt = find_attempt(doc["units"][unit_id])
        attempt["terminal_validation_failure"] = {
            "at": now_iso(), "word": error.word, "reason": str(error), "detail": error.detail,
            "job_id": attempt.get("job_id"), "result_sha256": result_digest,
        }
        fallback = attempt.setdefault("fallback", {})
        fallback.update({"eligible": True, "reason": "terminal-validation-failure"})
        event(doc, "terminal-validation-failed", unit_id, {"reason": str(error)})


def terminalize(run_id: str, unit_id: str) -> dict:
    evidence = sync_job(run_id, unit_id)
    if evidence["process_state"] != "done":
        raise Operational("BLOCKED", f"worker is not authoritatively done ({evidence['process_state']})")
    try:
        with locked_manifest(run_id) as doc:
            unit = doc["units"].get(unit_id)
            if not unit:
                raise Operational("REFUSED", "unknown unit")
            attempt = find_attempt(unit)
            receipt = terminal_receipt(unit, attempt)
            if receipt.get("model_receipt_status") == "mismatch":
                raise Operational("BLOCKED", "adapter reported a served-model mismatch")
    except Operational as exc:
        record_terminal_validation_failure(run_id, unit_id, exc)
        raise
        if receipt["terminal_status"] == "blocked":
            raise Operational("BLOCKED", "worker returned a host-resolvable blocker", {"terminal_receipt": receipt, "recovery_path": unit["recovery_path"]})
        workspace = unit["workspace"]["path"]
        expected_change = unit["workspace"]["change"]["change_id"]
    snapshot = semantic_snapshot(workspace)
    if snapshot["change_id"] != expected_change:
        raise Operational("BLOCKED", "worker replaced or diverged from its assigned JJ change")
    if snapshot["conflicted"]:
        raise Operational("BLOCKED", "worker change contains unresolved JJ conflicts")
    if receipt["terminal_status"] == "completed" and not snapshot["changed_paths"]:
        raise Operational("BLOCKED", "worker reported completion with an empty change")
    actual = set(snapshot["changed_paths"])
    reported = set(receipt["changed_files"])
    if actual != reported:
        raise Operational("BLOCKED", "worker changed-file receipt differs from the JJ fileset", {"actual": sorted(actual), "reported": sorted(reported)})
    transport = {
        "change_id": snapshot["change_id"], "commit_id": snapshot["commit_id"],
        "parents": snapshot["parents"], "changed_paths": snapshot["changed_paths"],
        "diff_sha256": snapshot["diff_sha256"], "operation_id": snapshot["operation_id"],
    }
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        find_attempt(unit)["terminal_receipt"] = receipt
        unit["transport"] = transport
        unit["state"] = "integration-pending"
        event(doc, "transport-change-pinned", unit_id, {"change_id": transport["change_id"], "commit_id": transport["commit_id"]})
    return transport


def cmd_terminalize(args) -> tuple[str, dict]:
    transport = terminalize(args.run_id, args.unit_id)
    return "INTEGRATION_PENDING", {"unit_id": args.unit_id, "transport": transport}
