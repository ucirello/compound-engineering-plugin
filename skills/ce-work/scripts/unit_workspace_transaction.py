"""Fail-stop JJ integration and source-wide verification transactions."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

from unit_workspace_state import *
from unit_workspace_integration import *
from unit_workspace_ignored import diff_ignored_state, inventory_ignored_state


def _args(**values):
    return SimpleNamespace(**values)


def _verification_command(args, operation: str) -> list[str]:
    command = list(args.verification_command)
    if command and command[0] == "--":
        command.pop(0)
    if not command or any(not item or "\0" in item for item in command):
        raise Operational("REFUSED", f"{operation} requires a non-empty verification command after --")
    return command


def _private_log(parent: str, prefix: str) -> tuple[str, object]:
    validate_private_dir(parent)
    for _ in range(64):
        path = os.path.join(parent, f"{prefix}-{secrets.token_hex(8)}.log")
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
            return path, os.fdopen(fd, "wb")
        except FileExistsError:
            continue
    raise Operational("BLOCKED", "could not reserve a verification log")


def _run_verification(repo: str, command: list[str], log_path: str, stream) -> int:
    try:
        proc = subprocess.run(
            command,
            cwd=repo,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            check=False,
        )
        return proc.returncode
    except OSError as exc:
        stream.write(f"verification launch failed: {exc}\n".encode("utf-8", "replace"))
        return 127


def _same_working_copy(before: dict, after: dict) -> bool:
    keys = ("commit_id", "change_id", "parents", "changed_paths", "diff_sha256", "empty", "conflicted")
    return all(before.get(key) == after.get(key) for key in keys)


def cmd_integrate(args) -> tuple[str, dict]:
    # Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
    description = args.change_description.strip()
    if not description or "\0" in description or len(description.encode()) > 4096:
        raise Operational("REFUSED", "a bounded locally conforming change description is required")
    command = _verification_command(args, "integrate")
    token = None
    pre_operation = None
    pre_snapshot = None
    accepted_change = None
    try:
        acquired = cmd_integration_acquire(_args(run_id=args.run_id, unit_id=args.unit_id, resume=False))[1]
        token = acquired["lock_token"]
        cmd_preflight(_args(
            run_id=args.run_id,
            unit_id=args.unit_id,
            lock_token=token,
            allowed_change=args.allowed_change,
        ))
        with locked_manifest(args.run_id) as doc:
            repo = doc["repository"]["workspace_root"]
            unit = doc["units"][args.unit_id]
            transport = unit["transport"]["change_id"]
            destination = unit["integration"]["destination_change"]
            pre_operation = unit["integration"]["pre_operation"]
            pre_snapshot = unit["integration"]["pre_snapshot"]
        jj(repo, "rebase", "-r", transport, "-o", destination)
        if has_conflicts(repo, transport):
            raise Operational("BLOCKED", "rebased worker change contains first-class conflicts", {"change_id": transport})
        if jj_text(repo, "log", "-r", f"divergent() & {transport}", "--no-graph", "-T", 'change_id ++ "\\n"', check=False):
            raise Operational("BLOCKED", "worker change became divergent during integration", {"change_id": transport})
        cmd_mark_applied(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        jj(repo, "new", transport)
        verification_start = semantic_snapshot(repo)
        if not verification_start["empty"] or verification_start["conflicted"]:
            raise Operational("BLOCKED", "verification working-copy change is not empty and conflict-free")
        ignored_before = inventory_ignored_state(repo)
        log_path, stream = _private_log(os.path.join(run_dir(args.run_id), "units", args.unit_id, "result"), "host-verification")
        with stream:
            exit_code = _run_verification(repo, command, log_path, stream)
        verification_end = semantic_snapshot(repo)
        ignored_state = diff_ignored_state(ignored_before, inventory_ignored_state(repo))
        if exit_code != 0 or not _same_working_copy(verification_start, verification_end):
            raise Operational(
                "BLOCKED",
                "authoritative verification failed or mutated tracked JJ state",
                {"verification_exit": exit_code, "verification_log": log_path, "ignored_state": ignored_state},
            )
        log_digest = hashlib.sha256(Path(log_path).read_bytes()).hexdigest()
        evidence = digest_bytes(json.dumps({
            "argv": command, "exit": exit_code, "log_sha256": log_digest,
            "working_copy": verification_start, "ignored_state": ignored_state,
        }, sort_keys=True, separators=(",", ":")).encode())
        cmd_mark_verified(_args(
            run_id=args.run_id,
            unit_id=args.unit_id,
            lock_token=token,
            evidence_digest=evidence,
            summary=args.verification_summary,
            ignored_state=ignored_state,
        ))
        jj(repo, "describe", "-r", transport, "-m", description)
        with locked_manifest(args.run_id) as doc:
            bookmark = doc["canonical"]["feature_bookmark"]
        jj(repo, "bookmark", "set", bookmark, "-r", transport, "--allow-backwards")
        accepted = cmd_mark_accepted(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))[1]["accepted_change"]
        accepted_change = accepted
        with locked_manifest(args.run_id) as doc:
            wave_id = doc["units"][args.unit_id].get("wave", {}).get("id")
        if wave_id:
            cmd_wave_advance(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, canonical_change=accepted["change_id"]))
        from unit_workspace_lifecycle import cmd_cleanup
        cmd_cleanup(_args(run_id=args.run_id, unit_id=args.unit_id, abandon=False, expect_transport=None, expect_job=None))
        cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        token = None
        os.unlink(log_path)
        return "UNIT_ACCEPTED", {
            "unit_id": args.unit_id, "accepted_change": accepted, "feature_bookmark": bookmark,
            "verification_digest": evidence, "verification_log_retained": False, "ignored_state": ignored_state,
        }
    except (Operational, TrustFailure) as original:
        if token is not None and accepted_change is not None:
            detail = {
                "unit_id": args.unit_id, "accepted_change": accepted_change,
                "original_failure": str(original), "retain_integration_lock": True,
                "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id),
            }
            with locked_manifest(args.run_id, write=True) as doc:
                doc["blockers"].append({"at": now_iso(), **detail})
                event(doc, "post-acceptance-finalization-blocked", args.unit_id)
            raise Operational("BLOCKED", "accepted change finalization is incomplete", detail) from original
        if token is not None and pre_operation and pre_snapshot:
            try:
                if not restore(args.run_id, args.unit_id, token):
                    raise Operational("BLOCKED", "scoped JJ integration restoration could not be proven")
                cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
                token = None
            except (Operational, TrustFailure) as recovery:
                detail = {
                    "unit_id": args.unit_id, "original_failure": str(original),
                    "recovery_failure": str(recovery), "retain_integration_lock": True,
                    "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id),
                }
                with locked_manifest(args.run_id, write=True) as doc:
                    doc["blockers"].append({"at": now_iso(), **detail})
                    event(doc, "operation-restore-blocked", args.unit_id)
                raise Operational("BLOCKED", "integration failed and exact JJ operation restoration could not be proven", detail) from recovery
        elif token is not None:
            with locked_manifest(args.run_id, write=True) as doc:
                doc["units"][args.unit_id]["state"] = "preserved"
            cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        raise


def cmd_verify_run(args) -> tuple[str, dict]:
    command = _verification_command(args, "verify-run")
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        units = doc.get("units", {})
        if not units or any(not unit_ready_for_run_verification(unit) for unit in units.values()):
            raise Operational("REFUSED", "verify-run requires every unit to have an accepted change")
        if doc.get("integration_lock"):
            raise Operational("BLOCKED", "verify-run requires no active integration lock")
        repo = info["workspace_root"]
        lock_unit = sorted(units)[-1]
        accepted_units = accepted_unit_change_snapshot(units)
    acquired = cmd_integration_acquire(_args(run_id=args.run_id, unit_id=lock_unit, resume=False, plan_verification=True))[1]
    token = acquired["lock_token"]
    attempt_id = secrets.token_hex(16)
    before = semantic_snapshot(repo)
    if not before["empty"] or before["conflicted"]:
        cmd_integration_release(_args(run_id=args.run_id, unit_id=lock_unit, lock_token=token))
        raise Operational("BLOCKED", "verify-run requires an empty conflict-free working-copy change")
    with locked_manifest(args.run_id) as doc:
        current_accepted = accepted_unit_change_snapshot(doc.get("units", {}))
        if current_accepted != accepted_units:
            cmd_integration_release(_args(run_id=args.run_id, unit_id=lock_unit, lock_token=token))
            raise Operational("BLOCKED", "unit completion evidence changed before plan-wide verification")
    ignored_before = inventory_ignored_state(repo)
    log_path, stream = _private_log(os.path.join(run_dir(args.run_id), "jobs"), "run-verification")
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, lock_unit, token)
        doc.setdefault("verification_attempts", []).append({
            "attempt_id": attempt_id, "started_at": now_iso(), "status": "pending",
            "integration_lock_nonce": token, "lock_unit_id": lock_unit,
            "argv": command, "summary": args.verification_summary,
            "canonical_snapshot": before, "verification_log": log_path,
        })
        event(doc, "run-verification-started", detail={"attempt_id": attempt_id})
    with stream:
        exit_code = _run_verification(repo, command, log_path, stream)
    test_fault("verify-run-before-receipt")
    after = semantic_snapshot(repo)
    ignored_state = diff_ignored_state(ignored_before, inventory_ignored_state(repo))
    changed = not _same_working_copy(before, after)
    if changed:
        with locked_manifest(args.run_id, write=True) as doc:
            doc["blockers"].append({"at": now_iso(), "reason": "plan-wide verification changed canonical JJ state", "retain_integration_lock": True, "integration_lock_nonce": token})
            event(doc, "run-verification-restore-blocked", detail={"attempt_id": attempt_id})
        raise Operational("BLOCKED", "plan-wide verification changed canonical JJ state; automatic rollback is refused", {"retain_integration_lock": True, "verification_log": log_path})
    log_digest = hashlib.sha256(Path(log_path).read_bytes()).hexdigest()
    receipt = {
        "attempt_id": attempt_id,
        "at": now_iso(), "argv": command, "summary": args.verification_summary,
        "verification_exit": exit_code, "canonical_change": revision_info(repo, "@-")["change_id"],
        "log_sha256": log_digest,
        "accepted_units": accepted_units, "operation_id": before["operation_id"],
        "canonical_state_changed": changed, "ignored_state": ignored_state,
        "verification_log": log_path if exit_code else None,
        "verification_log_retained": exit_code != 0,
    }
    receipt["evidence_digest"] = digest_bytes(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode())
    with locked_manifest(args.run_id, write=True) as doc:
        matches = [attempt for attempt in doc.get("verification_attempts", []) if attempt.get("attempt_id") == attempt_id]
        if len(matches) != 1 or matches[0].get("status") != "pending" or matches[0].get("integration_lock_nonce") != token:
            raise TrustFailure("plan-wide verification attempt state changed before receipt")
        validate_lock(doc, lock_unit, token)
        doc["verifications"].append(receipt)
        matches[0].update({"status": "receipt-recorded", "completed_at": now_iso(), "evidence_digest": receipt["evidence_digest"]})
        event(doc, "run-verification-passed" if exit_code == 0 else "run-verification-failed", detail={"evidence_digest": receipt["evidence_digest"]})
    test_fault("verify-run-after-receipt")
    if exit_code != 0:
        cmd_integration_release(_args(run_id=args.run_id, unit_id=lock_unit, lock_token=token))
        raise Operational("BLOCKED", "source-wide authoritative verification failed", {"verification_exit": exit_code, "verification_log": log_path, "ignored_state": ignored_state})
    os.unlink(log_path)
    cmd_integration_release(_args(run_id=args.run_id, unit_id=lock_unit, lock_token=token))
    return "RUN_VERIFIED", {"verification_exit": 0, "evidence_digest": receipt["evidence_digest"], "canonical_change": receipt["canonical_change"], "ignored_state": ignored_state}
