"""Unit preparation, runner evidence, and pinned Jujutsu change lifecycle."""

from __future__ import annotations

import json
import os
import re
import stat
import time

from unit_workspace_state import (
    MAX_JSON_BYTES,
    MAX_PACKET_BYTES,
    O_DIRECTORY,
    O_NOFOLLOW,
    REVISION_ID,
    TERMINAL_PROCESS,
    Operational,
    TrustFailure,
    changed_paths,
    create_private,
    digest_bytes,
    ensure_private_dir,
    event,
    fixed_route_contract,
    jj,
    locked_manifest,
    now_iso,
    read_external_packet,
    read_private,
    read_private_json,
    revision,
    revision_contains,
    run_dir,
    safe_id,
    snapshot,
    test_fault,
    validate_private_dir,
    validate_repo,
    workspace_name,
)


def _valid_retry_commit_id(value: object) -> bool:
    return isinstance(value, str) and REVISION_ID.fullmatch(value) is not None


def _validate_retry_base(doc: dict, unit: dict, requested_base: str) -> None:
    wave = unit.get("wave", {})
    original_base = wave.get("base")
    allowed_revisions = wave.get("allowed_revisions", [])
    if not _valid_retry_commit_id(original_base):
        raise TrustFailure("recorded retry base is malformed")
    if not isinstance(allowed_revisions, list) or any(
        not _valid_retry_commit_id(item) for item in allowed_revisions
    ):
        raise TrustFailure("recorded retry revision allowances are malformed")

    accepted = {
        change["commit_id"]
        for candidate in doc.get("units", {}).values()
        if isinstance((change := (candidate.get("integration") or {}).get("canonical_change")), dict)
        and _valid_retry_commit_id(change.get("commit_id"))
    }
    latest_allowed = allowed_revisions[-1] if allowed_revisions else original_base
    if requested_base != original_base and requested_base not in accepted:
        raise Operational(
            "BLOCKED",
            "retry base is not a controller-accepted canonical revision",
            {"requested_base": requested_base, "latest_allowed_revision": latest_allowed},
        )
    repo = doc["repository"]["toplevel"]
    missing = sorted(
        candidate
        for candidate in accepted | {original_base, *allowed_revisions}
        if not revision_contains(repo, candidate, requested_base)
    )
    if missing:
        raise Operational(
            "BLOCKED",
            "retry base omits controller-accepted canonical history",
            {
                "requested_base": requested_base,
                "latest_allowed_revision": latest_allowed,
                "missing_ancestry": missing,
            },
        )


def _record_retry_base(doc: dict, unit: dict, requested_base: str) -> None:
    wave = unit["wave"]
    position = wave.get("position")
    if not isinstance(position, int):
        raise TrustFailure("recorded retry wave position is malformed")
    targets = [unit]
    if wave.get("id"):
        for candidate in doc.get("units", {}).values():
            candidate_wave = candidate.get("wave", {})
            if candidate is unit or candidate_wave.get("id") != wave["id"]:
                continue
            candidate_position = candidate_wave.get("position")
            if not isinstance(candidate_position, int):
                raise TrustFailure("recorded wave position is malformed")
            if candidate_position > position:
                targets.append(candidate)
    for candidate in targets:
        candidate_wave = candidate.get("wave", {})
        if candidate_wave.get("base") != wave.get("base"):
            raise Operational("BLOCKED", "wave members do not share one recorded base")
        allowed = candidate_wave.setdefault("allowed_revisions", [])
        if not isinstance(allowed, list) or any(not _valid_retry_commit_id(item) for item in allowed):
            raise TrustFailure("recorded retry revision allowances are malformed")
        if requested_base not in allowed:
            allowed.append(requested_base)


def _authorization(doc: dict, args, unit_id: str, attempt_id: str, packet_digest: str) -> dict:
    route = fixed_route_contract(doc["binding"], doc["egress"])
    return {
        "schema_version": 2,
        "run_id": args.run_id,
        "unit_id": unit_id,
        "attempt_id": attempt_id,
        "route": doc["egress"]["route"],
        "target": route["target"],
        "harness": route["harness"],
        "intermediaries": route["intermediaries"],
        "model_requested": doc["binding"].get("model") or "auto",
        "restrictions": doc["egress"].get("restrictions", []),
        "activity_posture": args.activity_posture,
        "packet_digest": packet_digest,
    }


def cmd_prepare(args) -> tuple[str, dict]:
    uid = safe_id(args.unit_id, "unit id")
    attempt_id = safe_id(args.attempt_id, "attempt id")
    packet_bytes = read_external_packet(args.packet)
    packet_digest = digest_bytes(packet_bytes)
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        repo = info["toplevel"]
        base = revision(repo, args.base)["commit_id"]
        if info["commit_id"] != base or not info["working_copy_empty"] or info["conflicted"]:
            raise Operational("BLOCKED", "canonical working-copy change is not the requested empty base")
        existing = doc["units"].get(uid)
        unit_root = os.path.join(run_dir(args.run_id), "units", uid)
        workspace = os.path.join(unit_root, "workspace")
        packet_path = os.path.join(unit_root, "packet.md")
        authorization_path = os.path.join(unit_root, "authorization.json")
        authorization = _authorization(doc, args, uid, attempt_id, packet_digest)
        authorization_bytes = (json.dumps(authorization, sort_keys=True, separators=(",", ":")) + "\n").encode()
        authorization_digest = digest_bytes(authorization_bytes)
        retrying = False
        attempt = None
        if existing:
            matches = [row for row in existing.get("attempts", []) if row.get("attempt_id") == attempt_id]
            if matches:
                attempt = find_attempt(existing, attempt_id)
            else:
                cleanup = existing.get("cleanup")
                fully_cleaned = isinstance(cleanup, dict) and (
                    cleanup.get("artifacts_pruned") is True
                    or cleanup.get("artifact_cleanup", {}).get("complete") is True
                )
                if (
                    existing.get("state") != "cleaned"
                    or not isinstance(cleanup, dict)
                    or cleanup.get("abandoned") is not True
                    or not fully_cleaned
                ):
                    raise Operational("REFUSED", "a fresh attempt requires an exactly abandoned and fully cleaned prior attempt")
                if doc.get("integration_lock"):
                    raise Operational("REFUSED", "release the prior integration lock before preparing a retry")
                if existing.get("dependencies") != list(args.dependency):
                    raise Operational("BLOCKED", "retry dependencies differ from the recorded unit")
                prior_wave = existing.get("wave", {})
                if (prior_wave.get("id"), prior_wave.get("position")) != (args.wave_id, args.wave_position):
                    raise Operational("BLOCKED", "retry wave identity/position differs from the recorded unit")
                _validate_retry_base(doc, existing, base)
                retrying = True
        if existing and not retrying:
            recorded = existing.get("workspace", {})
            if recorded.get("path") != workspace or recorded.get("base") != base:
                raise Operational("BLOCKED", "duplicate unit id has a different workspace contract")
            if existing.get("state") == "cleaned" or existing.get("cleanup"):
                raise Operational("REFUSED", "cleaned unit requires a fresh attempt id")
            expected = {
                "attempt_id": attempt_id,
                "authorization": authorization,
                "authorization_path": authorization_path,
                "authorization_digest": authorization_digest,
            }
            observed = {key: attempt.get(key) for key in expected}
            if observed != expected or existing.get("packet", {}).get("path") != packet_path:
                raise Operational("BLOCKED", "resumed prepare contract differs from the recorded unit")
            if read_private(packet_path, MAX_PACKET_BYTES) != packet_bytes:
                raise Operational("BLOCKED", "controller-owned unit packet no longer matches supplied bytes")
            if read_private(authorization_path, MAX_JSON_BYTES) != authorization_bytes:
                raise Operational("BLOCKED", "controller-owned authorization no longer matches the recorded attempt")
            result_fd, _ = open_recorded_result_dir(existing)
            os.close(result_fd)
            validate_workspace(doc, existing)
            return "PREPARED", {
                "unit_id": uid,
                "attempt_id": attempt_id,
                "workspace": workspace,
                "result_dir": os.path.join(unit_root, "result"),
                "packet_path": packet_path,
                "packet_digest": packet_digest,
                "authorization_path": authorization_path,
                "authorization_digest": authorization_digest,
                "adapter": attempt["adapter"],
                "base": base,
                "resumed": True,
            }

    ensure_private_dir(unit_root)
    result_dir = os.path.join(unit_root, "result")
    ensure_private_dir(result_dir)
    result_dir_identity = private_result_dir_identity(result_dir)
    for path, content, cap, label in (
        (packet_path, packet_bytes, MAX_PACKET_BYTES, "packet"),
        (authorization_path, authorization_bytes, MAX_JSON_BYTES, "authorization"),
    ):
        if os.path.lexists(path):
            if read_private(path, cap) != content:
                raise Operational("BLOCKED", f"controller-owned {label} path contains different bytes")
        else:
            create_private(path, content)
    name = workspace_name(args.run_id, uid)
    attempt_record = {
        "attempt_id": attempt_id,
        "job_id": None,
        "dispatch_authorization_receipt": None,
        "process_state": "never-started",
        "activity": {"posture": args.activity_posture, "latest_at": None},
        "fallback": {"eligible": False, "reason": None, "claimed": None},
        "authorization": authorization,
        "authorization_path": authorization_path,
        "authorization_digest": authorization_digest,
        "authorization_retained": True,
        "adapter": os.path.realpath(os.path.join(os.path.dirname(__file__), "cross-model-work.sh")),
        "terminal_receipt": None,
    }
    if not os.path.exists(workspace):
        jj(repo, "workspace", "add", "--name", name, "-r", base, workspace)
        test_fault("after-workspace-add")
    parent = revision(workspace, "@-")
    current = revision(workspace)
    if parent["commit_id"] != base or changed_paths(workspace) or snapshot(workspace)["conflicted"]:
        raise Operational("BLOCKED", "new Jujutsu workspace did not start from the requested base")
    unit = {
        "unit_id": uid,
        "state": "queued",
        "dependencies": list(args.dependency),
        "wave": {"id": args.wave_id, "base": base, "position": args.wave_position, "allowed_revisions": [base]},
        "packet_digest": packet_digest,
        "packet": {"path": packet_path, "digest": packet_digest, "bytes": len(packet_bytes), "retained": True},
        "workspace": {"path": workspace, "name": name, "base": base, "change_id": current["change_id"], "registered": True},
        "result_dir_identity": result_dir_identity,
        "attempts": [attempt_record],
        "transport": None,
        "integration": None,
        "cleanup": None,
        "recovery_path": unit_root,
    }
    with locked_manifest(args.run_id, write=True) as doc:
        current_existing = doc["units"].get(uid)
        if retrying:
            cleanup = current_existing.get("cleanup") if current_existing else None
            fully_cleaned = isinstance(cleanup, dict) and (
                cleanup.get("artifacts_pruned") is True
                or cleanup.get("artifact_cleanup", {}).get("complete") is True
            )
            if not current_existing or current_existing.get("state") != "cleaned" or not fully_cleaned:
                raise Operational("BLOCKED", "unit retry eligibility changed while it was being prepared")
            previous = find_attempt(current_existing)
            previous["cleanup_receipt"] = dict(cleanup)
            attempts = current_existing["attempts"]
            attempts.append(attempt_record)
            unit["attempts"] = attempts
            _record_retry_base(doc, current_existing, base)
            unit["wave"] = current_existing["wave"]
            doc["units"][uid] = unit
            event(doc, "unit-retry-prepared", uid, {"attempt_id": attempt_id, "base": base})
        else:
            if current_existing:
                raise Operational("BLOCKED", "unit was concurrently claimed")
            doc["units"][uid] = unit
        event(doc, "workspace-prepared", uid, {"path": workspace, "name": name, "base": base})
    return "PREPARED", {
        "unit_id": uid,
        "attempt_id": attempt_id,
        "workspace": workspace,
        "result_dir": result_dir,
        "packet_path": packet_path,
        "packet_digest": packet_digest,
        "authorization_path": authorization_path,
        "authorization_digest": authorization_digest,
        "adapter": attempt_record["adapter"],
        "base": base,
        "resumed": False,
    }


def runner_job_dir(run_id: str, job_id: str) -> str:
    return os.path.join(run_dir(run_id), "jobs", safe_id(job_id, "job id"))


def process_evidence(job_dir: str) -> dict:
    validate_private_dir(job_dir)
    status_path = os.path.join(job_dir, "status")
    if os.path.lexists(status_path):
        word = read_private(status_path, 256).decode("ascii", "strict").strip()
        if word not in TERMINAL_PROCESS:
            raise TrustFailure("runner terminal state is invalid")
    elif os.path.lexists(os.path.join(job_dir, "pid")):
        read_private_json(os.path.join(job_dir, "pid"))
        word = "running"
    else:
        word = "never-started"
    failure_reason = None
    reason_path = os.path.join(job_dir, "reason")
    if word in TERMINAL_PROCESS and os.path.lexists(reason_path):
        failure_reason = read_private(reason_path, 4096).decode("utf-8", "strict").strip() or None
    activity = {"latest_at": None, "log_bytes": 0}
    log = os.path.join(job_dir, "out.log")
    if os.path.lexists(log):
        entry = os.stat(log, follow_symlinks=False)
        if not stat.S_ISREG(entry.st_mode):
            raise TrustFailure("runner log is not a regular file")
        activity = {"latest_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(entry.st_mtime)), "log_bytes": entry.st_size}
    return {"process_state": word, "failure_reason": failure_reason, "activity": activity}


HOST_RECEIPT_FIELDS = (
    "requested_route", "actual_route", "target", "harness", "intermediaries",
    "model_requested", "model_actual", "model_receipt_status", "activity_posture",
    "restriction_posture", "failure_reason", "raw_log", "packet_digest",
)
MAX_RESULT_BYTES = 5 * 1024 * 1024
MAX_REPORTED_CHANGED_FILES = 1000


def _validate_private_dir_fd(fd: int, path: str) -> os.stat_result:
    entry = os.fstat(fd)
    effective_uid = os.geteuid() if hasattr(os, "geteuid") else None
    if not stat.S_ISDIR(entry.st_mode):
        raise TrustFailure(f"not a real directory: {path}")
    if effective_uid is not None and entry.st_uid != effective_uid:
        raise TrustFailure(f"directory is not owned by current user: {path}")
    mode = stat.S_IMODE(entry.st_mode)
    if mode != 0o700:
        raise TrustFailure(f"directory mode is {mode:04o}, expected 0700: {path}")
    return entry


def private_result_dir_identity(path: str) -> dict:
    try:
        fd = os.open(path, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open result directory {path}: {exc}") from exc
    try:
        entry = _validate_private_dir_fd(fd, path)
        return {"dev": entry.st_dev, "ino": entry.st_ino}
    finally:
        os.close(fd)


def open_recorded_result_dir(unit: dict) -> tuple[int, str]:
    result_dir = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")
    identity = unit.get("result_dir_identity")
    if not isinstance(identity, dict) or set(identity) != {"dev", "ino"} or any(
        not isinstance(identity.get(key), int) or isinstance(identity.get(key), bool) for key in ("dev", "ino")
    ):
        raise TrustFailure("unit has no valid controller-recorded result directory identity")
    try:
        fd = os.open(result_dir, os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open result directory {result_dir}: {exc}") from exc
    try:
        entry = _validate_private_dir_fd(fd, result_dir)
        if (entry.st_dev, entry.st_ino) != (identity["dev"], identity["ino"]):
            raise TrustFailure("controller result directory identity changed")
        return fd, result_dir
    except Exception:
        os.close(fd)
        raise


def read_private_at(dir_fd: int, name: str, cap: int, display_path: str) -> bytes:
    if os.path.basename(name) != name or name in {"", ".", ".."}:
        raise TrustFailure(f"unsafe state file name: {name!r}")
    try:
        fd = os.open(name, os.O_RDONLY | O_NOFOLLOW, dir_fd=dir_fd)
    except OSError as exc:
        raise TrustFailure(f"cannot safely open state file {display_path}: {exc}") from exc
    try:
        entry = os.fstat(fd)
        effective_uid = os.geteuid() if hasattr(os, "geteuid") else None
        if not stat.S_ISREG(entry.st_mode) or effective_uid is not None and entry.st_uid != effective_uid:
            raise TrustFailure(f"state owner/type validation failed: {display_path}")
        if stat.S_IMODE(entry.st_mode) != 0o600 or entry.st_size > cap:
            raise TrustFailure(f"state mode/size validation failed: {display_path}")
        output = bytearray()
        while len(output) <= cap:
            part = os.read(fd, min(65536, cap + 1 - len(output)))
            if not part:
                break
            output.extend(part)
        if len(output) > cap:
            raise TrustFailure(f"state grew beyond {cap}-byte limit: {display_path}")
        return bytes(output)
    finally:
        os.close(fd)


def stat_private_at(dir_fd: int, name: str, display_path: str, *, missing_ok: bool = False) -> os.stat_result | None:
    if os.path.basename(name) != name or name in {"", ".", ".."}:
        raise TrustFailure(f"unsafe state file name: {name!r}")
    try:
        fd = os.open(name, os.O_RDONLY | O_NOFOLLOW, dir_fd=dir_fd)
    except FileNotFoundError:
        if missing_ok:
            return None
        raise TrustFailure(f"cannot safely open state file {display_path}: file is missing")
    except OSError as exc:
        raise TrustFailure(f"cannot safely open state file {display_path}: {exc}") from exc
    try:
        entry = os.fstat(fd)
        effective_uid = os.geteuid() if hasattr(os, "geteuid") else None
        if not stat.S_ISREG(entry.st_mode) or effective_uid is not None and entry.st_uid != effective_uid:
            raise TrustFailure(f"state owner/type validation failed: {display_path}")
        if stat.S_IMODE(entry.st_mode) != 0o600:
            raise TrustFailure(f"state mode is not 0600: {display_path}")
        return entry
    finally:
        os.close(fd)


def read_recorded_result_file(unit: dict, name: str, cap: int) -> bytes:
    result_fd, result_dir = open_recorded_result_dir(unit)
    try:
        return read_private_at(result_fd, name, cap, os.path.join(result_dir, name))
    finally:
        os.close(result_fd)


def read_recorded_result_json(unit: dict) -> tuple[dict, bytes]:
    result_path = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result", "implementation-result.json")
    raw = read_recorded_result_file(unit, "implementation-result.json", MAX_RESULT_BYTES)
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise TrustFailure(f"malformed JSON state: {result_path}") from exc
    if not isinstance(value, dict):
        raise TrustFailure(f"JSON state is not an object: {result_path}")
    return value, raw


def terminal_receipt(unit: dict, attempt: dict, *, unavailable: bool = False, launched_failure: bool = False) -> dict:
    result_dir = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")
    receipt, result_bytes = read_recorded_result_json(unit)
    authorization = attempt.get("authorization")
    if not isinstance(authorization, dict):
        raise Operational("BLOCKED", "attempt has no controller-issued route authorization")
    expected = {
        "requested_route": authorization["route"],
        "actual_route": None if unavailable else authorization["route"],
        "target": authorization["target"],
        "harness": authorization["harness"],
        "intermediaries": authorization["intermediaries"],
        "model_requested": authorization["model_requested"],
        "restriction_posture": authorization.get("restriction_posture"),
        "packet_digest": unit["packet_digest"],
    }
    if unavailable or launched_failure:
        expected["activity_posture"] = authorization["activity_posture"]
    mismatches = {key: {"expected": value, "actual": receipt.get(key)} for key, value in expected.items() if receipt.get(key) != value}
    if mismatches:
        raise Operational("BLOCKED", "adapter terminal receipt does not match controller authorization", {"mismatches": mismatches})
    terminal_status = receipt.get("terminal_status")
    if unavailable:
        neutral = {"schema_version": 1, "terminal_status": "unavailable", "summary": "External route unavailable", "changed_files": [], "evidence": [], "scope_expansion": None, "model_actual": "unverified", "model_receipt_status": "unverified"}
        invalid = {key: {"expected": value, "actual": receipt.get(key)} for key, value in neutral.items() if receipt.get(key) != value}
        failure_reason = receipt.get("failure_reason")
        if invalid or not isinstance(failure_reason, str) or not failure_reason or len(failure_reason.encode()) > 4096:
            raise Operational("BLOCKED", "failed runner did not publish a bounded neutral unavailable receipt", {"mismatches": invalid})
    elif launched_failure:
        neutral = {"schema_version": 1, "terminal_status": "failed", "changed_files": [], "evidence": [], "scope_expansion": None}
        invalid = {key: {"expected": value, "actual": receipt.get(key)} for key, value in neutral.items() if receipt.get(key) != value}
        failure_reason = receipt.get("failure_reason")
        summary = receipt.get("summary")
        if invalid or not isinstance(failure_reason, str) or not failure_reason or len(failure_reason.encode()) > 4096 or not isinstance(summary, str) or not summary or len(summary.encode()) > 4096:
            raise Operational("BLOCKED", "failed runner did not publish a bounded neutral launched-route receipt", {"mismatches": invalid})
    elif terminal_status not in {"completed", "blocked", "scope_expansion"}:
        raise Operational("BLOCKED", "successful runner did not publish a host-resolvable adapter result")
    if terminal_status == "scope_expansion" and not isinstance(receipt.get("scope_expansion"), dict):
        raise Operational("BLOCKED", "scope-expansion adapter result has no expansion receipt")
    changed_files = receipt.get("changed_files")
    if not isinstance(changed_files, list) or len(changed_files) > MAX_REPORTED_CHANGED_FILES or any(not isinstance(path, str) or not path for path in changed_files):
        raise Operational("BLOCKED", "adapter terminal receipt has invalid changed-files evidence")
    raw_log = receipt.get("raw_log")
    expected_log = os.path.join(result_dir, "adapter.log")
    if not isinstance(raw_log, str) or os.path.abspath(raw_log) != expected_log:
        raise Operational("BLOCKED", "adapter raw-log receipt escaped the controller result directory")
    log_bytes = read_recorded_result_file(unit, "adapter.log", 10 * 1024 * 1024)
    return {key: receipt.get(key) for key in HOST_RECEIPT_FIELDS} | {
        "terminal_status": receipt["terminal_status"],
        "summary": str(receipt.get("summary", ""))[:4096],
        "changed_files": changed_files,
        "changed_file_count": len(changed_files),
        "evidence_count": len(receipt.get("evidence", [])),
        "scope_expansion_requested": receipt.get("scope_expansion") is not None,
        "result_sha256": digest_bytes(result_bytes),
        "raw_log_sha256": digest_bytes(log_bytes),
        "raw_log_bytes": len(log_bytes),
    }


def _validate_authorized_failed_job(run_id: str, unit: dict, attempt: dict) -> None:
    job_id = attempt.get("job_id")
    if not isinstance(job_id, str):
        raise Operational("BLOCKED", "failed receipt has no bound runner job")
    job_dir = runner_job_dir(run_id, job_id)
    if process_evidence(job_dir)["process_state"] != "failed":
        raise Operational("BLOCKED", "failed receipt requires authoritative failed runner evidence")
    meta = read_private_json(os.path.join(job_dir, "meta.json"))
    if meta.get("job_id") != job_id:
        raise Operational("BLOCKED", "runner job metadata identity mismatch")
    validate_runner_contract(run_id, unit, meta)
    expected_result_dir = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")
    expected_dispatch = {
        "attempt_id": attempt.get("attempt_id"), "job_id": job_id,
        "authorization_path": attempt.get("authorization_path"), "authorization_digest": attempt.get("authorization_digest"),
        "workspace": unit["workspace"]["path"], "packet_path": unit["packet"]["path"],
        "packet_digest": unit["packet_digest"], "result_dir": expected_result_dir,
        "result_dir_identity": unit.get("result_dir_identity"),
    }
    if attempt.get("dispatch_authorization_receipt") != expected_dispatch:
        raise Operational("BLOCKED", "failed receipt is not bound to the exact authorized dispatch")


def _authorized_failed_terminal_receipt(run_id: str, unit: dict, attempt: dict, *, unavailable: bool) -> dict:
    _validate_authorized_failed_job(run_id, unit, attempt)
    return terminal_receipt(unit, attempt, unavailable=unavailable, launched_failure=not unavailable)


def unavailable_terminal_receipt(run_id: str, unit: dict, attempt: dict) -> dict:
    return _authorized_failed_terminal_receipt(run_id, unit, attempt, unavailable=True)


def launched_failure_terminal_receipt(run_id: str, unit: dict, attempt: dict) -> dict:
    return _authorized_failed_terminal_receipt(run_id, unit, attempt, unavailable=False)


def record_terminal_validation_failure(run_id: str, unit_id: str, error: Operational) -> None:
    if isinstance(error, TrustFailure):
        raise error
    with locked_manifest(run_id) as doc:
        unit = doc["units"][unit_id]
        result_digest = digest_bytes(read_recorded_result_file(unit, "implementation-result.json", MAX_RESULT_BYTES))
    with locked_manifest(run_id, write=True) as doc:
        attempt = find_attempt(doc["units"][unit_id])
        failure = {"at": now_iso(), "word": error.word, "reason": str(error), "detail": error.detail, "job_id": attempt.get("job_id"), "result_sha256": result_digest}
        attempt["terminal_validation_failure"] = failure
        fallback = attempt.setdefault("fallback", {})
        fallback.setdefault("claimed", None)
        fallback["eligible"] = fallback.get("claimed") is None
        fallback["reason"] = "terminal-validation-failure"
        event(doc, "terminal-validation-failed", unit_id, failure)


def validate_terminal_validation_failure(run_id: str, unit: dict, attempt: dict) -> dict:
    failure = attempt.get("terminal_validation_failure")
    if not isinstance(failure, dict) or failure.get("job_id") != attempt.get("job_id"):
        raise Operational("REFUSED", "attempt has no exact terminal-validation failure")
    if process_evidence(runner_job_dir(run_id, attempt["job_id"]))["process_state"] != "done":
        raise Operational("BLOCKED", "terminal-validation job evidence changed")
    if digest_bytes(read_recorded_result_file(unit, "implementation-result.json", MAX_RESULT_BYTES)) != failure.get("result_sha256"):
        raise Operational("BLOCKED", "terminal-validation result evidence changed")
    return failure


def retire_terminal_validation_failure(unit: dict) -> None:
    attempt = find_attempt(unit)
    if attempt.get("terminal_validation_failure") is not None and not attempt.get("fallback", {}).get("claimed"):
        attempt.pop("terminal_validation_failure")
        attempt["fallback"] = {"eligible": False, "reason": None, "claimed": None}


def validate_runner_contract(run_id: str, unit: dict, meta: dict) -> None:
    unit_id = unit["unit_id"]
    expected_result_dir = os.path.join(run_dir(run_id), "units", unit_id, "result")
    expected_result_file = os.path.join(expected_result_dir, "implementation-result.json")
    if meta.get("skill") != "ce-work":
        raise Operational("BLOCKED", "runner skill must be 'ce-work'")
    if meta.get("run_id") != run_id or meta.get("label") != unit_id or meta.get("input_digest") != unit["packet_digest"]:
        raise Operational("BLOCKED", "runner identity or input digest does not match the controller contract")
    if not isinstance(meta.get("result_path"), str) or os.path.abspath(meta["result_path"]) != expected_result_file:
        raise Operational("BLOCKED", f"runner result path must be the controller result file: {expected_result_file}")
    attempt = find_attempt(unit)
    authorization_path = attempt.get("authorization_path")
    authorization_digest = attempt.get("authorization_digest")
    if not isinstance(authorization_path, str) or not isinstance(authorization_digest, str):
        raise Operational("BLOCKED", "attempt has no controller-issued authorization artifact")
    authorization_bytes = read_private(authorization_path, MAX_JSON_BYTES)
    try:
        observed = json.loads(authorization_bytes)
    except (ValueError, UnicodeDecodeError) as exc:
        raise TrustFailure("controller authorization artifact is malformed") from exc
    if observed != attempt.get("authorization") or digest_bytes(authorization_bytes) != authorization_digest:
        raise Operational("BLOCKED", "controller authorization artifact no longer matches the recorded attempt")
    expected_argv = [attempt.get("adapter"), authorization_path, unit["workspace"]["path"], unit["packet"]["path"], unit["packet_digest"], expected_result_dir]
    if meta.get("worker_argv") != expected_argv:
        raise Operational("BLOCKED", "runner worker argv does not match the controller-issued fixed-route contract", {"expected_argv": expected_argv, "actual_argv": meta.get("worker_argv")})


def cmd_authorize_dispatch(args) -> tuple[str, dict]:
    run_id = safe_id(args.run_id, "run id")
    unit_id = safe_id(args.unit_id, "unit id")
    attempt_id = safe_id(args.attempt_id, "attempt id")
    job_id = safe_id(args.job_id, "job id")
    if not re.fullmatch(r"[0-9a-f]{64}", args.authorization_digest) or not re.fullmatch(r"[0-9a-f]{64}", args.packet_digest):
        raise Operational("REFUSED", "observed authorization and packet digests must be lowercase SHA-256")
    with locked_manifest(run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit, attempt_id)
        if unit.get("state") not in {"queued", "authoring"}:
            raise Operational("REFUSED", "dispatch authorization is available only before worker completion")
        bound_job = attempt.get("job_id")
        if bound_job not in (None, job_id):
            raise Operational("AMBIGUOUS", "attempt is already bound to another job")
        job_dir = runner_job_dir(run_id, job_id)
        validate_private_dir(job_dir)
        meta = read_private_json(os.path.join(job_dir, "meta.json"))
        if meta.get("job_id") != job_id:
            raise Operational("BLOCKED", "runner job metadata identity mismatch")
        validate_runner_contract(run_id, unit, meta)
        expected_authorization_path = attempt["authorization_path"]
        expected_authorization_digest = attempt["authorization_digest"]
        if os.path.abspath(args.authorization) != expected_authorization_path or args.authorization_digest != expected_authorization_digest:
            raise Operational("BLOCKED", "authorization path or digest does not match the recorded attempt")
        authorization_bytes = read_private(expected_authorization_path, MAX_JSON_BYTES)
        if digest_bytes(authorization_bytes) != expected_authorization_digest:
            raise Operational("BLOCKED", "controller authorization bytes no longer match the recorded digest")
        expected_workspace = unit["workspace"]["path"]
        expected_packet = unit["packet"]["path"]
        expected_result_dir = os.path.join(os.path.dirname(expected_workspace), "result")
        if os.path.abspath(args.workspace) != expected_workspace or os.path.abspath(args.packet) != expected_packet or os.path.abspath(args.result_dir) != expected_result_dir:
            raise Operational("BLOCKED", "dispatch paths do not match the recorded unit")
        if args.packet_digest != unit["packet_digest"] or digest_bytes(read_private(expected_packet, MAX_PACKET_BYTES)) != unit["packet_digest"]:
            raise Operational("BLOCKED", "packet digest does not match the recorded authorization")
        result_fd, _ = open_recorded_result_dir(unit)
        os.close(result_fd)
        expected_dispatch = {
            "attempt_id": attempt_id, "job_id": job_id,
            "authorization_path": expected_authorization_path, "authorization_digest": expected_authorization_digest,
            "workspace": expected_workspace, "packet_path": expected_packet, "packet_digest": unit["packet_digest"],
            "result_dir": expected_result_dir, "result_dir_identity": unit.get("result_dir_identity"),
        }
        recorded_dispatch = attempt.get("dispatch_authorization_receipt")
        if recorded_dispatch is not None and (bound_job != job_id or recorded_dispatch != expected_dispatch):
            raise Operational("BLOCKED", "recorded dispatch authorization does not match the exact request")
        resumed = recorded_dispatch == expected_dispatch
        validate_workspace(doc, unit)
        if not resumed:
            parent = revision(expected_workspace, "@-")
            if parent["commit_id"] != unit["workspace"]["base"] or changed_paths(expected_workspace):
                raise Operational("BLOCKED", "worker workspace changed before dispatch authorization")
            attempt["job_id"] = job_id
            attempt["dispatch_authorization_receipt"] = expected_dispatch
            unit["state"] = "authoring"
            event(doc, "job-bound", unit_id, {"attempt_id": attempt_id, "job_id": job_id, "source": "authorize-dispatch"})
    return "AUTHORIZED", {"run_id": run_id, "unit_id": unit_id, "attempt_id": attempt_id, "job_id": job_id, "resumed": resumed, "authorization_digest": expected_authorization_digest, "packet_digest": unit["packet_digest"]}


def matching_runner_jobs(run_id: str, unit: dict) -> list[str]:
    jobs = os.path.join(run_dir(run_id), "jobs")
    validate_private_dir(jobs)
    matches = []
    for entry in os.scandir(jobs):
        if not entry.is_dir(follow_symlinks=False):
            continue
        safe_id(entry.name, "job id")
        validate_private_dir(entry.path)
        meta = read_private_json(os.path.join(entry.path, "meta.json"))
        if meta.get("skill") == "ce-work" and meta.get("run_id") == run_id and meta.get("label") == unit["unit_id"] and meta.get("input_digest") == unit["packet_digest"]:
            validate_runner_contract(run_id, unit, meta)
            matches.append(entry.name)
    return sorted(matches)


def find_attempt(unit: dict, attempt_id: str | None = None) -> dict:
    attempts = unit.get("attempts", [])
    matches = [row for row in attempts if attempt_id is None or row.get("attempt_id") == attempt_id]
    if attempt_id is None:
        matches = matches[-1:]
    if len(matches) != 1:
        raise Operational("AMBIGUOUS", "attempt could not be identified exactly")
    return matches[0]


def scope_expansion_pending(unit: dict) -> bool:
    """Return whether the current authored result still requires host resolution."""
    receipt = find_attempt(unit).get("terminal_receipt")
    return isinstance(receipt, dict) and receipt.get("terminal_status") == "scope_expansion"


def cmd_record_job(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit, args.attempt_id)
        if attempt.get("job_id"):
            if attempt["job_id"] != args.job_id:
                raise Operational("AMBIGUOUS", "attempt is already bound to another job")
            return "AUTHORING", {"unit_id": args.unit_id, "job_id": args.job_id, "resumed": True, "unit_state": unit["state"]}
        meta = read_private_json(os.path.join(runner_job_dir(args.run_id, args.job_id), "meta.json"))
        validate_runner_contract(args.run_id, unit, meta)
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        attempt = find_attempt(unit, args.attempt_id)
        if attempt.get("job_id") not in (None, args.job_id):
            raise Operational("AMBIGUOUS", "attempt was concurrently bound")
        if attempt.get("job_id") == args.job_id:
            return "AUTHORING", {"unit_id": args.unit_id, "job_id": args.job_id, "resumed": True, "unit_state": unit["state"]}
        if unit.get("state") != "queued":
            raise Operational("REFUSED", "an unbound job can be recorded only while the unit is queued")
        attempt["job_id"] = args.job_id
        unit["state"] = "authoring"
        event(doc, "job-bound", args.unit_id, {"attempt_id": args.attempt_id, "job_id": args.job_id})
    return "AUTHORING", {"unit_id": args.unit_id, "job_id": args.job_id, "resumed": False}


def sync_job(run_id: str, unit_id: str) -> dict:
    with locked_manifest(run_id) as doc:
        unit = doc["units"].get(unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        if not attempt.get("job_id"):
            return {"process_state": "never-started", "activity": attempt["activity"]}
        evidence = process_evidence(runner_job_dir(run_id, attempt["job_id"]))
        failure_receipt = None
        oversized_result_failure = False
        if evidence["process_state"] == "failed":
            result_fd, result_dir = open_recorded_result_dir(unit)
            try:
                result_stat = stat_private_at(result_fd, "implementation-result.json", os.path.join(result_dir, "implementation-result.json"), missing_ok=True)
            finally:
                os.close(result_fd)
            if result_stat is not None and result_stat.st_size > MAX_RESULT_BYTES:
                _validate_authorized_failed_job(run_id, unit, attempt)
                oversized_result_failure = True
            else:
                for reader in (unavailable_terminal_receipt, launched_failure_terminal_receipt):
                    try:
                        failure_receipt = reader(run_id, unit, attempt)
                        break
                    except TrustFailure:
                        raise
                    except Operational:
                        continue
    with locked_manifest(run_id, write=True) as doc:
        attempt = find_attempt(doc["units"][unit_id])
        prior = (attempt.get("process_state"), dict(attempt["activity"]), dict(attempt.get("fallback", {})), attempt.get("terminal_receipt"))
        attempt["process_state"] = evidence["process_state"]
        attempt["activity"].update(evidence["activity"])
        if failure_receipt is not None:
            attempt["terminal_receipt"] = failure_receipt
        authoritative_failure = evidence["process_state"] in TERMINAL_PROCESS - {"done"} or evidence["process_state"] == "never-started" and bool(attempt.get("job_id"))
        effective_failure_reason = None
        if authoritative_failure:
            effective_failure_reason = failure_receipt["failure_reason"] if failure_receipt is not None else evidence["failure_reason"] if oversized_result_failure and evidence["failure_reason"] else evidence["process_state"]
            fallback = attempt.setdefault("fallback", {})
            fallback.setdefault("claimed", None)
            fallback["eligible"] = fallback.get("claimed") is None
            fallback["reason"] = effective_failure_reason
        current = (attempt.get("process_state"), dict(attempt["activity"]), dict(attempt.get("fallback", {})), attempt.get("terminal_receipt"))
        if prior != current:
            event(doc, "job-synced", unit_id, {"process_state": evidence["process_state"]})
            if prior[0] != evidence["process_state"] and evidence["process_state"] in TERMINAL_PROCESS:
                event(doc, "job-terminal", unit_id, {"process_state": evidence["process_state"]})
        activity = dict(attempt["activity"])
    return {"process_state": evidence["process_state"], "failure_reason": effective_failure_reason, "activity": activity}


def cmd_sync_job(args) -> tuple[str, dict]:
    return "SYNCED", {"unit_id": args.unit_id, **sync_job(args.run_id, args.unit_id)}


def transport_ref(run_id: str, unit_id: str) -> str:
    """Return the stable neutral identity retained for legacy receipt consumers."""
    return f"rocketclaw/{digest_bytes(run_id.encode())[:20]}/{digest_bytes(unit_id.encode())[:20]}"


def no_sequencer(workspace: str) -> None:
    if snapshot(workspace)["conflicted"]:
        raise Operational("BLOCKED", "worker workspace contains unresolved Jujutsu conflicts")


def parse_diff_paths(raw: bytes) -> list[str]:
    parts = raw.split(b"\0")
    paths = []
    expect_paths = 0
    for part in parts:
        if not part:
            continue
        text = part.decode("utf-8", "surrogateescape")
        if expect_paths:
            paths.append(text)
            expect_paths -= 1
        else:
            expect_paths = 2 if text.startswith(("R", "C")) else 1
    if expect_paths:
        raise Operational("BLOCKED", "incomplete NUL-delimited transport inventory")
    return paths


def diff_changes_gitlink(raw: bytes) -> bool:
    for record in raw.split(b"\0"):
        if record.startswith(b":"):
            fields = record[1:].split(b" ", 4)
            if len(fields) >= 2 and b"160000" in fields[:2]:
                return True
    return False


def validate_workspace(doc: dict, unit: dict) -> dict:
    workspace = unit.get("workspace", {})
    path = workspace.get("path")
    if not isinstance(path, str) or not os.path.isdir(path):
        raise Operational("BLOCKED", "recorded Jujutsu workspace is unavailable")
    current = snapshot(path)
    if current["change_id"] != workspace.get("change_id"):
        raise Operational("BLOCKED", "worker Jujutsu change identity changed")
    if current["conflicted"]:
        raise Operational("BLOCKED", "worker Jujutsu change contains conflicts")
    if not revision_contains(path, workspace["base"], current["commit_id"]):
        raise Operational("BLOCKED", "worker change does not descend from its recorded base")
    return current


def terminalize(run_id: str, unit_id: str) -> dict:
    evidence = sync_job(run_id, unit_id)
    if evidence["process_state"] != "done":
        detail = {}
        if evidence["process_state"] == "failed":
            with locked_manifest(run_id) as doc:
                receipt = find_attempt(doc["units"][unit_id]).get("terminal_receipt")
                if isinstance(receipt, dict) and receipt.get("terminal_status") == "unavailable":
                    detail = {"terminal_receipt": receipt, "failure_reason": receipt["failure_reason"]}
        raise Operational("BLOCKED", f"worker is not authoritatively done ({evidence['process_state']})", detail)
    try:
        with locked_manifest(run_id) as doc:
            unit = doc["units"].get(unit_id)
            if not unit:
                raise Operational("REFUSED", "unknown unit")
            receipt = terminal_receipt(unit, find_attempt(unit))
            if receipt.get("model_receipt_status") == "mismatch":
                raise Operational("BLOCKED", "adapter reported a served-model mismatch")
    except Operational as exc:
        record_terminal_validation_failure(run_id, unit_id, exc)
        raise
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"].get(unit_id)
        if unit and unit["state"] == "authoring":
            find_attempt(unit)["terminal_receipt"] = receipt
            unit["state"] = "authored"
            event(doc, "worker-output-authored", unit_id, {"route": receipt["actual_route"], "model": receipt["model_actual"]})
    if receipt["terminal_status"] == "blocked":
        raise Operational("BLOCKED", "worker returned a host-resolvable blocker", {"unit_id": unit_id, "terminal_status": "blocked", "summary": receipt["summary"], "terminal_receipt": receipt, "recovery_path": os.path.join(run_dir(run_id), "units", unit_id)})
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"].get(unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        if unit["state"] == "integration-pending" and isinstance(unit.get("transport"), dict) and unit["transport"].get("commit_id"):
            retire_terminal_validation_failure(unit)
            return unit["transport"]
        if unit["state"] != "authored":
            raise Operational("BLOCKED", f"unit cannot terminalize from {unit['state']}")
        if find_attempt(unit).get("fallback", {}).get("claimed"):
            raise Operational("REFUSED", "native fallback already owns implementation; worker output cannot be terminalized")
        current = validate_workspace(doc, unit)
        base = unit["workspace"]["base"]
        workspace = unit["workspace"]["path"]
    try:
        no_sequencer(workspace)
        paths = changed_paths(workspace, base, "@")
        if not paths:
            raise Operational("BLOCKED", "worker produced no transportable Jujutsu change")
    except Operational as exc:
        record_terminal_validation_failure(run_id, unit_id, exc)
        raise
    transport = {
        "base": base,
        "change_id": current["change_id"],
        "commit_id": current["commit_id"],
        "changed_paths": paths,
        "digest": digest_bytes(json.dumps([base, current["change_id"], current["commit_id"], paths], separators=(",", ":")).encode()),
    }
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        if unit["state"] not in ("authored", "integration-pending"):
            raise Operational("BLOCKED", "unit state changed during terminalization")
        observed = validate_workspace(doc, unit)
        if observed["commit_id"] != transport["commit_id"]:
            raise Operational("BLOCKED", "worker Jujutsu revision changed during terminalization")
        retire_terminal_validation_failure(unit)
        unit["state"] = "integration-pending"
        unit["transport"] = transport
        event(doc, "change-pinned", unit_id, {"change_id": transport["change_id"], "commit_id": transport["commit_id"], "digest": transport["digest"]})
    return transport


def cmd_terminalize(args) -> tuple[str, dict]:
    transport = terminalize(args.run_id, args.unit_id)
    return "INTEGRATION_PENDING", {"unit_id": args.unit_id, "transport": transport}
