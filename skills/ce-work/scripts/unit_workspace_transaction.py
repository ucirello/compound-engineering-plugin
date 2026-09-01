"""Fail-stop canonical Jujutsu integration and plan-wide verification."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
from types import SimpleNamespace

from unit_workspace_state import *
from unit_workspace_integration import (
    cmd_integration_acquire,
    cmd_integration_release,
    cmd_mark_applied,
    cmd_mark_accepted,
    cmd_mark_verified,
    cmd_preflight,
    cmd_restore,
    cmd_wave_advance,
    semantic_snapshot,
)
from unit_workspace_lifecycle import cmd_cleanup, plan_wide_verification_attempts
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


def _verification_log(parent: str, prefix: str) -> tuple[str, object]:
    validate_private_dir(parent)
    path = os.path.join(parent, f"{prefix}-{secrets.token_hex(6)}.log")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
    return path, os.fdopen(fd, "wb")


def _run_verification(repo: str, command: list[str], log_stream: object) -> int:
    return subprocess.run(
        command,
        cwd=repo,
        stdout=log_stream,
        stderr=subprocess.STDOUT,
        env=sanitized_vcs_environment({"PYTHONDONTWRITEBYTECODE": "1"}),
        check=False,
    ).returncode


def _restore_snapshot(repo: str, before: dict, after_paths: set[str]) -> dict:
    paths = sorted(after_paths | set(before["changed_paths"]))
    if paths:
        jj(repo, "restore", "--from", before["commit_id"], "--into", "@", *root_file_filesets(paths))
    jj(repo, "describe", "-r", "@", "-m", before["description"])
    actual = semantic_snapshot(repo)
    if not (
        actual["change_id"] == before["change_id"]
        and actual["parent_commit_ids"] == before["parent_commit_ids"]
        and actual["changed_paths"] == before["changed_paths"]
        and actual["diff_sha256"] == before["diff_sha256"]
        and actual["description"] == before["description"]
    ):
        raise Operational("BLOCKED", "exact pre-verification Jujutsu state could not be restored")
    return actual


def _validate_accepted_run_revision(repo: str, units: dict, current: dict) -> dict[str, str]:
    accepted = accepted_unit_revision_snapshot(units)
    if accepted is None:
        raise Operational("BLOCKED", "every unit must have a controller-accepted revision")
    for unit_id, revision in accepted.items():
        if not revision_is_ancestor(repo, revision, current["commit_id"]):
            raise Operational("BLOCKED", "canonical revision omits an accepted unit", {"unit_id": unit_id, "revision": revision})
    return accepted


def cmd_verify_run(args) -> tuple[str, dict]:
    command = _verification_command(args, "verify-run")
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        if not doc.get("units"):
            raise Operational("REFUSED", "verify-run requires at least one unit")
        before = semantic_snapshot(info["toplevel"])
        if not before["empty"]:
            raise Operational("BLOCKED", "plan-wide verification requires an empty canonical working-copy change")
        accepted = _validate_accepted_run_revision(info["toplevel"], doc["units"], before)
        existing = [receipt for receipt in doc.get("verifications", []) if receipt.get("status") == "passed" and receipt.get("accepted_unit_revisions") == accepted]
        if existing:
            return "RUN_VERIFIED", {"verification": existing[-1], "resumed": True}
        unit_id = sorted(doc["units"])[-1]
    acquired = cmd_integration_acquire(_args(run_id=args.run_id, unit_id=unit_id, resume=False, plan_verification=True, recover_only=False))[1]
    token = acquired["lock_token"]
    attempt_id = f"verify-{secrets.token_hex(12)}"
    log_path, log_stream = _verification_log(os.path.join(run_dir(args.run_id), "jobs"), "run-verification")
    ignored_before = inventory_ignored_state(info["toplevel"])
    with locked_manifest(args.run_id, write=True) as doc:
        attempts = plan_wide_verification_attempts(doc)
        attempts.append({
            "attempt_id": attempt_id,
            "started_at": now_iso(),
            "status": "pending",
            "integration_lock_nonce": token,
            "lock_unit_id": unit_id,
            "argv": command,
            "summary": args.verification_summary,
            "canonical_snapshot": before,
            "accepted_unit_revisions": accepted,
            "verification_log": log_path,
        })
        event(doc, "run-verification-started", detail={"attempt_id": attempt_id})
    retain_lock = False
    try:
        with log_stream:
            returncode = _run_verification(info["toplevel"], command, log_stream)
        after = semantic_snapshot(info["toplevel"])
        ignored_state = diff_ignored_state(ignored_before, inventory_ignored_state(info["toplevel"]))
        tracked_unchanged = after["commit_id"] == before["commit_id"] and after["change_id"] == before["change_id"]
        restored = None
        if not tracked_unchanged:
            try:
                restored = _restore_snapshot(info["toplevel"], before, set(after["changed_paths"]))
            except Operational:
                retain_lock = True
                raise
        status = "passed" if returncode == 0 and tracked_unchanged else "failed"
        receipt = {
            "attempt_id": attempt_id,
            "at": now_iso(),
            "status": status,
            "exit_status": returncode,
            "summary": args.verification_summary,
            "evidence_digest": digest_bytes(read_private(log_path, MAX_JSON_BYTES)),
            "accepted_unit_revisions": accepted,
            "before": before,
            "after": after,
            "restored": restored,
            "ignored_state": ignored_state,
            "verification_log": log_path,
        }
        with locked_manifest(args.run_id, write=True) as doc:
            attempt = next(row for row in plan_wide_verification_attempts(doc) if row["attempt_id"] == attempt_id)
            attempt.update(receipt)
            doc.setdefault("verifications", []).append(receipt)
            event(doc, "run-verification-finished", detail={"attempt_id": attempt_id, "status": status})
        if status != "passed":
            raise Operational("BLOCKED", "plan-wide authoritative verification failed", {"verification": receipt})
        return "RUN_VERIFIED", {"verification": receipt, "resumed": False}
    finally:
        if not retain_lock:
            cmd_integration_release(_args(run_id=args.run_id, unit_id=unit_id, lock_token=token))


def _integration_recovery_failure(args, original: Operational, failure: Operational, phase: str) -> Operational:
    return Operational(
        "BLOCKED",
        f"integration failed and {phase} also failed",
        {"integration_error": str(original), "recovery_error": str(failure), "run_id": args.run_id, "unit_id": args.unit_id},
    )


def cmd_integrate(args) -> tuple[str, dict]:
    command = _verification_command(args)
    if not args.description.strip() or len(args.description.encode()) > 65536:
        raise Operational("REFUSED", "change description must be non-empty and at most 65536 bytes. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Use the repository's current local syntax; do not impose a fixed type, scope, prefix, footer, or body template.")
    token = None
    applied = False
    completed = False
    try:
        acquired = cmd_integration_acquire(_args(run_id=args.run_id, unit_id=args.unit_id, resume=False, plan_verification=False, recover_only=False))[1]
        token = acquired["lock_token"]
        cmd_preflight(_args(
            run_id=args.run_id,
            unit_id=args.unit_id,
            lock_token=token,
            allowed_revision=list(getattr(args, "allowed_revision", [])),
        ))
        with locked_manifest(args.run_id) as doc:
            unit = doc["units"][args.unit_id]
            repo = doc["repository"]["toplevel"]
            source = unit["transport"]["commit_id"]
            paths = list(unit["transport"]["changed_paths"])
        if paths:
            jj(repo, "restore", "--from", source, "--into", "@", *root_file_filesets(paths))
        applied = True
        cmd_mark_applied(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))

        before_verification = semantic_snapshot(repo)
        ignored_before = inventory_ignored_state(repo)
        log_path, log_stream = _verification_log(os.path.join(run_dir(args.run_id), "units", args.unit_id, "result"), "host-verification")
        with log_stream:
            returncode = _run_verification(repo, command, log_stream)
        after_verification = semantic_snapshot(repo)
        ignored_state = diff_ignored_state(ignored_before, inventory_ignored_state(repo))
        if after_verification["commit_id"] != before_verification["commit_id"]:
            _restore_snapshot(repo, before_verification, set(after_verification["changed_paths"]))
        if returncode != 0 or after_verification["commit_id"] != before_verification["commit_id"]:
            raise Operational("BLOCKED", "authoritative verification failed or changed the integrated fileset", {"exit_status": returncode, "verification_log": log_path})
        evidence_digest = hashlib.sha256(read_private(log_path, MAX_JSON_BYTES)).hexdigest()
        cmd_mark_verified(_args(
            run_id=args.run_id,
            unit_id=args.unit_id,
            lock_token=token,
            evidence_digest=evidence_digest,
            summary=args.verification_summary,
            ignored_state=json.dumps(ignored_state, sort_keys=True),
        ))
        canonical = describe_change(repo, args.description)
        accepted = cmd_mark_accepted(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))[1]["canonical_revision"]
        if accepted["commit_id"] != canonical["commit_id"]:
            raise Operational("BLOCKED", "recorded canonical revision differs from the described revision")
        completed = True
        jj(repo, "new", canonical["commit_id"])
        if unit.get("wave", {}).get("id"):
            cmd_wave_advance(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, canonical_revision=canonical["commit_id"]))
        cleanup = cmd_cleanup(_args(run_id=args.run_id, unit_id=args.unit_id, abandon=False, expect_transport=None, expect_job=None))[1]
        cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        token = None
        return "INTEGRATED", {
            "unit_id": args.unit_id,
            "canonical_revision": accepted,
            "verification": {"summary": args.verification_summary, "evidence_digest": evidence_digest, "ignored_state": ignored_state},
            "cleanup": cleanup,
        }
    except Operational as original:
        if token is not None and applied and not completed:
            try:
                cmd_restore(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
            except Operational as failure:
                raise _integration_recovery_failure(args, original, failure, "restoration") from original
        if token is not None:
            try:
                cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
            except Operational as failure:
                raise _integration_recovery_failure(args, original, failure, "lock release") from original
        raise
