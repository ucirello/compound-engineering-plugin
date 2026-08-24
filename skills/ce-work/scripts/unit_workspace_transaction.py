"""Fail-stop canonical Jujutsu integration for external units."""

from __future__ import annotations

import hashlib
import contextlib
import json
import os
import secrets
import subprocess
from pathlib import Path
from types import SimpleNamespace

from unit_workspace_state import *
from unit_workspace_integration import (
    apply_transport,
    cmd_integration_acquire,
    cmd_integration_release,
    cmd_mark_committed,
    cmd_mark_verified,
    cmd_preflight,
    cmd_restore,
    cmd_wave_advance,
    matches_expected_apply,
    same_exact_revision_state,
    same_revision_state,
    semantic_snapshot,
    validate_lock,
)
from unit_workspace_lifecycle import cmd_cleanup
from unit_workspace_ignored import diff_ignored_state, inventory_ignored_state


def _args(**values):
    return SimpleNamespace(**values)


def _verification_command(args, operation: str = "integrate") -> list[str]:
    command = list(args.verification_command)
    if command and command[0] == "--":
        command.pop(0)
    if not command or any(not value or "\0" in value for value in command):
        raise Operational("REFUSED", f"{operation} requires a non-empty verification command after --")
    return command


def _exclusive_log(parent: str, prefix: str) -> tuple[str, object]:
    validate_private_dir(parent)
    for _ in range(128):
        path = os.path.join(parent, f"{prefix}-{secrets.token_hex(8)}.log")
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
            return path, os.fdopen(fd, "wb")
        except FileExistsError:
            continue
    raise Operational("BLOCKED", "could not reserve a workspace-local verification log")


def _verification_log(run_id: str, unit_id: str) -> tuple[str, object]:
    return _exclusive_log(os.path.join(locate_run_dir(run_id), "units", unit_id, "result"), "host-verification")


def _run_verification_log(run_id: str) -> tuple[str, object]:
    return _exclusive_log(os.path.join(locate_run_dir(run_id), "jobs"), "run-verification")


def _run_command(command: list[str], repo: str, stream) -> int:
    try:
        return subprocess.run(
            command,
            cwd=repo,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            env=sanitized_process_environment({"PYTHONDONTWRITEBYTECODE": "1"}),
            check=False,
        ).returncode
    except OSError as exc:
        stream.write(f"verification launch failed: {exc}\n".encode("utf-8", "replace"))
        return 127


def _validate_accepted_run_change(repo: str, units: dict, current_commit: str) -> None:
    commits: set[str] = set()
    for unit in units.values():
        commit = unit_accepted_commit(unit)
        if commit is None:
            raise Operational("BLOCKED", "unit completion evidence changed before source-wide verification")
        if commit in commits:
            raise Operational("BLOCKED", "unit completion evidence contains duplicate accepted commits")
        if not is_ancestor(repo, commit, current_commit):
            raise Operational("BLOCKED", "canonical change does not contain every accepted unit", {"missing_commit": commit})
        commits.add(commit)


def plan_wide_verification_attempts(doc: dict) -> list[dict]:
    attempts = doc.get("verification_attempts", [])
    if not isinstance(attempts, list) or any(not isinstance(attempt, dict) for attempt in attempts):
        raise TrustFailure("source-wide verification attempts are malformed")
    return attempts


def pending_plan_wide_verification(doc: dict, lock: dict) -> dict | None:
    if not isinstance(lock, dict):
        return None
    matches = [attempt for attempt in plan_wide_verification_attempts(doc) if attempt.get("status") == "pending" and attempt.get("integration_lock_nonce") == lock.get("nonce")]
    if len(matches) > 1:
        raise TrustFailure("multiple pending source-wide verification attempts share one integration lock")
    return matches[0] if matches else None


def receipted_plan_wide_verification(doc: dict, lock: dict) -> dict | None:
    if not isinstance(lock, dict):
        return None
    matches = [attempt for attempt in plan_wide_verification_attempts(doc) if attempt.get("status") == "receipt-recorded" and attempt.get("integration_lock_nonce") == lock.get("nonce")]
    if len(matches) > 1:
        raise TrustFailure("multiple receipted source-wide verification attempts share one integration lock")
    return matches[0] if matches else None


def _record_run_attempt(args, attempt_id: str, lock_unit: str, token: str, command: list[str], before: dict, log_path: str) -> None:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, lock_unit, token)
        doc.setdefault("verification_attempts", []).append({
            "attempt_id": attempt_id,
            "started_at": now_iso(),
            "status": "pending",
            "integration_lock_nonce": token,
            "lock_unit_id": lock_unit,
            "argv": command,
            "summary": args.verification_summary,
            "canonical_snapshot": before,
            "verification_log": log_path,
        })
        event(doc, "run-verification-started", detail={"attempt_id": attempt_id})


def _record_run_receipt(args, attempt_id: str, token: str, receipt: dict) -> None:
    with locked_manifest(args.run_id, write=True) as doc:
        matches = [attempt for attempt in plan_wide_verification_attempts(doc) if attempt.get("attempt_id") == attempt_id]
        if len(matches) != 1 or matches[0].get("status") != "pending" or matches[0].get("integration_lock_nonce") != token:
            raise TrustFailure("source-wide verification attempt state changed")
        validate_lock(doc, matches[0]["lock_unit_id"], token)
        doc.setdefault("verifications", []).append(receipt)
        matches[0].update({"status": "receipt-recorded", "completed_at": now_iso(), "evidence_digest": receipt["evidence_digest"]})
        event(doc, "run-verification-passed" if receipt["verification_exit"] == 0 else "run-verification-failed", detail={"attempt_id": attempt_id, "evidence_digest": receipt["evidence_digest"]})
        if receipt["verification_exit"] != 0:
            doc["blockers"].append({"at": now_iso(), "unit_id": None, "reason": "source-wide verification failed", "evidence_digest": receipt["evidence_digest"]})


def _restore_snapshot(repo: str, before: dict, allowed_current: list[dict]) -> dict:
    current = semantic_snapshot(repo)
    if same_exact_revision_state(current, before):
        return current
    if not any(same_exact_revision_state(current, candidate) for candidate in allowed_current):
        raise Operational(
            "BLOCKED",
            "canonical state does not match an exact controller-recorded restoration source; refusing to touch @",
            {"current_snapshot": current, "retain_integration_lock": True},
        )
    jj(repo, "restore", "--from", before["commit"], "--to", "@")
    # Restoration reuses the previously recorded description byte-for-byte; it does not compose one.
    if revision_snapshot(repo)["description"] != before["description"]:
        jj(repo, "describe", "-m", before["description"])
    return semantic_snapshot(repo)


def cmd_verify_run(args) -> tuple[str, dict]:
    command = _verification_command(args, "verify-run")
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        units = doc.get("units", {})
        if not units or any(not unit_ready_for_run_verification(unit) for unit in units.values()):
            raise Operational("REFUSED", "verify-run requires every unit to have an accepted canonical change")
        if doc.get("integration_lock") is not None:
            raise Operational("BLOCKED", "verify-run requires no active integration lock")
        repo = info["toplevel"]
        lock_unit = sorted(units)[-1]
    acquired = cmd_integration_acquire(_args(run_id=args.run_id, unit_id=lock_unit, resume=False, plan_verification=True))[1]
    token = acquired["lock_token"]
    attempt_id = secrets.token_hex(16)
    retain_lock = False
    try:
        before = semantic_snapshot(repo)
        if not before["empty"] or before["conflicted"]:
            raise Operational("BLOCKED", "verify-run requires an empty, conflict-free canonical working-copy change")
        with locked_manifest(args.run_id) as doc:
            units = doc["units"]
            _validate_accepted_run_change(repo, units, before["commit"])
            accepted_units = accepted_unit_commit_snapshot(units)
        before_ignored = inventory_ignored_state(repo)
        log_path, stream = _run_verification_log(args.run_id)
        _record_run_attempt(args, attempt_id, lock_unit, token, command, before, log_path)
        with stream:
            verification_exit = _run_command(command, repo, stream)
        test_fault("verify-run-before-receipt")
        after = semantic_snapshot(repo)
        ignored_state = diff_ignored_state(before_ignored, inventory_ignored_state(repo))
        changed = not same_revision_state(after, before)
        if changed:
            restored = _restore_snapshot(repo, before, [before])
            if not same_exact_revision_state(restored, before):
                retain_lock = True
                raise Operational("BLOCKED", "source-wide verification restoration could not be proven", {"retain_integration_lock": True, "verification_log": log_path, "ignored_state": ignored_state})
        log_digest = hashlib.sha256(Path(log_path).read_bytes()).hexdigest()
        receipt = {
            "attempt_id": attempt_id,
            "at": now_iso(),
            "argv": command,
            "summary": args.verification_summary,
            "verification_exit": verification_exit,
            "log_sha256": log_digest,
            "canonical_change": before["change_id"],
            "canonical_commit": before["commit"],
            "accepted_units": accepted_units,
            "canonical_state_changed": changed,
            "ignored_state": ignored_state,
            "verification_log": log_path if verification_exit != 0 else None,
            "verification_log_retained": verification_exit != 0,
        }
        receipt["evidence_digest"] = digest_bytes(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode())
        _record_run_receipt(args, attempt_id, token, receipt)
        if verification_exit != 0:
            raise Operational("BLOCKED", "source-wide authoritative verification failed", {"verification_exit": verification_exit, "verification_log": log_path, "evidence_digest": receipt["evidence_digest"], "ignored_state": ignored_state})
        os.unlink(log_path)
        result = "RUN_VERIFIED", {"verification_exit": 0, "evidence_digest": receipt["evidence_digest"], "canonical_change": before["change_id"], "canonical_commit": before["commit"], "ignored_state": ignored_state, "verification_log_retained": False}
    except Operational as exc:
        retain_lock = retain_lock or bool(exc.detail.get("retain_integration_lock"))
        raise
    finally:
        if not retain_lock:
            with contextlib.suppress(Operational):
                cmd_integration_release(_args(run_id=args.run_id, unit_id=lock_unit, lock_token=token))
    return result


def cmd_integrate(args) -> tuple[str, dict]:
    command = _verification_command(args)
    description = args.change_description.strip()
    if not description or len(description.encode()) > 1024:
        raise Operational("REFUSED", f"change description must be non-empty and at most 1024 bytes. {DESCRIPTION_GUIDANCE}")
    token = None
    committed = False
    canonical = None
    ignored_state = None
    verification_log = None
    try:
        token = cmd_integration_acquire(_args(run_id=args.run_id, unit_id=args.unit_id, resume=False))[1]["lock_token"]
        cmd_preflight(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, allowed_change=args.allowed_change))
        with locked_manifest(args.run_id) as doc:
            repo = doc["repository"]["toplevel"]
        apply_transport(args.run_id, args.unit_id, token)
        with locked_manifest(args.run_id) as doc:
            unit = doc["units"][args.unit_id]
            if not matches_expected_apply(repo, unit):
                raise Operational("BLOCKED", "canonical integration changed before verification")
        before = semantic_snapshot(repo)
        before_ignored = inventory_ignored_state(repo)
        verification_log, stream = _verification_log(args.run_id, args.unit_id)
        with stream:
            verification_exit = _run_command(command, repo, stream)
        after = semantic_snapshot(repo)
        ignored_state = diff_ignored_state(before_ignored, inventory_ignored_state(repo))
        verification_changed = not same_revision_state(after, before)
        if verification_exit != 0 or verification_changed:
            cmd_restore(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
            cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
            token = None
            raise Operational("BLOCKED", "authoritative verification failed or changed canonical state", {"verification_exit": verification_exit, "verification_log": verification_log, "canonical_state_changed": verification_changed, "ignored_state": ignored_state})
        log_digest = hashlib.sha256(Path(verification_log).read_bytes()).hexdigest()
        evidence = digest_bytes(json.dumps({"argv": command, "exit": verification_exit, "log_sha256": log_digest, "before": before, "after": after, "ignored_state": ignored_state}, sort_keys=True, separators=(",", ":")).encode())
        cmd_mark_verified(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, evidence_digest=evidence, summary=args.verification_summary, ignored_state=ignored_state))
        test_fault("before-canonical-description")
        jj(repo, "describe", "-m", description)
        with locked_manifest(args.run_id, write=True) as doc:
            doc["units"][args.unit_id]["integration"]["expected_apply"] = semantic_snapshot(repo)
        committed_body = cmd_mark_committed(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))[1]
        committed = True
        canonical = committed_body["canonical_change"]
        test_fault("after-canonical-change-confirmed")
        with locked_manifest(args.run_id) as doc:
            wave_id = doc["units"][args.unit_id].get("wave", {}).get("id")
        if wave_id:
            cmd_wave_advance(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, canonical_change=canonical["commit"]))
        jj(repo, "new")
        cmd_cleanup(_args(run_id=args.run_id, unit_id=args.unit_id, abandon=False, expect_transport=None, expect_job=None))
        cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        token = None
        with contextlib.suppress(OSError):
            os.unlink(verification_log)
        return "UNIT_COMMITTED", {"unit_id": args.unit_id, "canonical_change": canonical, "canonical_commit": canonical["commit"], "verification_digest": evidence, "verification_log_retained": False, "ignored_state": ignored_state}
    except Operational as original:
        if ignored_state is not None:
            original.detail.setdefault("ignored_state", ignored_state)
        if token is not None and not committed:
            with locked_manifest(args.run_id) as current_doc:
                current_unit = current_doc["units"].get(args.unit_id)
                reconciled = reconcile_commit(current_doc, current_unit) if current_unit and current_unit.get("state") == "verified" else None
            if reconciled and reconciled["description"].strip():
                with locked_manifest(args.run_id, write=True) as current_doc:
                    current_doc["units"][args.unit_id]["integration"]["canonical_change"] = reconciled
                    current_doc["units"][args.unit_id]["state"] = "committed"
                    event(current_doc, "canonical-change-reconciled", args.unit_id, {"change": reconciled["change_id"], "commit": reconciled["commit"]})
                canonical = reconciled
                committed = True
        if token is not None and committed:
            detail = {"reason": "canonical change accepted but finalization is incomplete", "unit_id": args.unit_id, "canonical_change": canonical, "original_failure": str(original), "retain_integration_lock": True, "recovery_path": os.path.join(locate_run_dir(args.run_id), "units", args.unit_id), "ignored_state": ignored_state}
            with locked_manifest(args.run_id, write=True) as doc:
                doc["blockers"].append({"at": now_iso(), **detail})
                event(doc, "post-change-finalization-blocked", args.unit_id, detail)
            raise Operational("BLOCKED", "canonical change accepted but finalization is incomplete", detail) from original
        if token is not None and not original.detail.get("retain_integration_lock"):
            with locked_manifest(args.run_id) as doc:
                pre_fold = doc["units"].get(args.unit_id, {}).get("integration", {}).get("pre_fold")
            if pre_fold:
                try:
                    cmd_restore(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
                    cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
                except Operational as recovery:
                    raise Operational("BLOCKED", "integration failed and exact Jujutsu restoration or lock release could not be proven", {"unit_id": args.unit_id, "original_failure": str(original), "recovery_failure": str(recovery), "retain_integration_lock": True, "recovery_path": os.path.join(locate_run_dir(args.run_id), "units", args.unit_id)}) from recovery
            else:
                cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        raise
