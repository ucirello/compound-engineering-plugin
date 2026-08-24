"""Fail-stop canonical integration for one terminalized JJ change."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
from pathlib import Path
from types import SimpleNamespace

from unit_workspace_state import *
from unit_workspace_integration import (
    cmd_integration_acquire,
    cmd_integration_release,
    cmd_mark_applied,
    cmd_mark_finalized,
    cmd_mark_verified,
    cmd_preflight,
    cmd_restore,
    cmd_wave_advance,
    matches_expected_apply,
    semantic_snapshot,
)
from unit_workspace_lifecycle import cmd_cleanup
from unit_workspace_ignored import diff_untracked_state, inventory_untracked_state


def _args(**values):
    return SimpleNamespace(**values)


def _verification_command(args, operation: str = "integrate") -> list[str]:
    command = list(args.verification_command)
    if command and command[0] == "--":
        command.pop(0)
    if not command or any(not value or "\0" in value for value in command):
        raise Operational("REFUSED", f"{operation} requires a non-empty verification command after --")
    return command


def _verification_log(run_id: str, label: str) -> tuple[str, object]:
    parent = os.path.join(run_dir(run_id), "jobs")
    ensure_private_dir(parent)
    path = os.path.join(parent, f"{label}-{secrets.token_hex(8)}.log")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
    return path, os.fdopen(fd, "wb")


def _run_verification(repo: str, command: list[str], stream) -> int:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        return subprocess.run(command, cwd=repo, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, env=env, check=False).returncode
    except OSError as exc:
        stream.write(f"verification launch failed: {exc}\n".encode("utf-8", "replace"))
        return 127


def _restore_or_block(args, token: str, original: Operational) -> None:
    try:
        cmd_restore(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
    except Operational as recovery:
        raise Operational("BLOCKED", "integration failed and exact JJ operation restoration could not be proven", {"original_failure": str(original), "recovery_failure": str(recovery), "retain_integration_lock": True, "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id)}) from recovery


def cmd_integrate(args) -> tuple[str, dict]:
    command = _verification_command(args)
    description = validate_description(args.change_description)
    token = None
    finalized = False
    try:
        token = cmd_integration_acquire(_args(run_id=args.run_id, unit_id=args.unit_id, resume=False))[1]["lock_token"]
        cmd_preflight(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, allowed_change=args.allowed_change))
        with locked_manifest(args.run_id) as doc:
            repo = doc["repository"]["workspace_root"]
            unit = doc["units"][args.unit_id]
            transport = unit["transport"]["change_id"]
        jj(repo, "squash", "--from", transport, "--into", "@")
        cmd_mark_applied(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        before = semantic_snapshot(repo)
        before_untracked = inventory_untracked_state(repo)
        log_path, stream = _verification_log(args.run_id, f"unit-{args.unit_id}-verification")
        with stream:
            verification_exit = _run_verification(repo, command, stream)
        after = semantic_snapshot(repo)
        untracked_state = diff_untracked_state(before_untracked, inventory_untracked_state(repo))
        if verification_exit != 0 or after["commit_id"] != before["commit_id"] or after["changed_paths"] != before["changed_paths"] or after["conflicted"]:
            raise Operational("BLOCKED", "authoritative verification failed or changed the canonical JJ change", {"verification_exit": verification_exit, "verification_log": log_path, "untracked_state": untracked_state})
        log_digest = hashlib.sha256(Path(log_path).read_bytes()).hexdigest()
        evidence = digest_bytes(json.dumps({"argv": command, "exit": verification_exit, "log_sha256": log_digest, "before": before, "after": after, "untracked_state": untracked_state}, sort_keys=True, separators=(",", ":")).encode())
        cmd_mark_verified(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, evidence_digest=evidence, summary=args.verification_summary, ignored_state=untracked_state))
        jj(repo, "describe", "-m", description, "@")
        jj(repo, "new", "@")
        finalized_body = cmd_mark_finalized(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))[1]
        finalized = True
        canonical = finalized_body["canonical_change"]
        with locked_manifest(args.run_id) as doc:
            wave_id = doc["units"][args.unit_id].get("wave", {}).get("id")
        if wave_id:
            cmd_wave_advance(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, canonical_change=canonical["commit_id"]))
        cmd_cleanup(_args(run_id=args.run_id, unit_id=args.unit_id, abandon=False, expect_transport=None, expect_job=None))
        cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        os.unlink(log_path)
        return "UNIT_FINALIZED", {"unit_id": args.unit_id, "canonical_change": canonical, "verification_digest": evidence, "verification_log_retained": False, "untracked_state": untracked_state}
    except (Operational, TrustFailure) as original:
        if token is not None and not finalized:
            _restore_or_block(args, token, original)
        if token is not None and finalized:
            raise Operational("BLOCKED", "canonical JJ change was accepted but finalization is incomplete", {"unit_id": args.unit_id, "retain_integration_lock": True, "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id)}) from original
        raise


def cmd_verify_run(args) -> tuple[str, dict]:
    command = _verification_command(args, "verify-run")
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        units = doc.get("units", {})
        accepted = accepted_unit_commit_snapshot(units)
        if not units or accepted is None:
            raise Operational("REFUSED", "verify-run requires every unit to have an accepted canonical JJ change")
        repo = info["workspace_root"]
        before = semantic_snapshot(repo)
        if not before["status_empty"] or before["conflicted"]:
            raise Operational("BLOCKED", "verify-run requires a clean canonical working-copy change")
    log_path, stream = _verification_log(args.run_id, "run-verification")
    before_untracked = inventory_untracked_state(repo)
    with stream:
        verification_exit = _run_verification(repo, command, stream)
    after = semantic_snapshot(repo)
    untracked_state = diff_untracked_state(before_untracked, inventory_untracked_state(repo))
    if after["commit_id"] != before["commit_id"] or after["changed_paths"] != before["changed_paths"] or after["conflicted"]:
        jj(repo, "operation", "restore", before["operation_id"])
        restored = semantic_snapshot(repo)
        if restored["commit_id"] != before["commit_id"] or restored["changed_paths"] != before["changed_paths"]:
            raise Operational("BLOCKED", "plan-wide verification changed canonical JJ state and exact operation restoration failed", {"verification_log": log_path, "retain_integration_lock": True})
    receipt = {
        "at": now_iso(), "argv": command, "summary": args.verification_summary,
        "verification_exit": verification_exit, "canonical_change": before,
        "accepted_units": accepted, "untracked_state": untracked_state,
        "verification_log": log_path if verification_exit else None,
    }
    receipt["evidence_digest"] = digest_bytes(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode())
    with locked_manifest(args.run_id, write=True) as doc:
        doc.setdefault("verifications", []).append(receipt)
        event(doc, "run-verification-passed" if verification_exit == 0 else "run-verification-failed", detail={"evidence_digest": receipt["evidence_digest"]})
    if verification_exit:
        raise Operational("BLOCKED", "plan-wide authoritative verification failed", {"verification_exit": verification_exit, "verification_log": log_path, "evidence_digest": receipt["evidence_digest"], "untracked_state": untracked_state})
    os.unlink(log_path)
    return "RUN_VERIFIED", {"verification_exit": 0, "evidence_digest": receipt["evidence_digest"], "canonical_change": before, "untracked_state": untracked_state, "verification_log_retained": False}
