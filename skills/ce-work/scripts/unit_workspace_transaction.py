"""Fail-stop canonical Jujutsu composition for external units."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
from pathlib import Path
from types import SimpleNamespace

from unit_workspace_state import *
from unit_workspace_integration import *
from unit_workspace_ignored import diff_untracked_state, inventory_untracked_state


def _args(**values):
    return SimpleNamespace(**values)


def _verification_command(args, operation: str) -> list[str]:
    command = list(args.verification_command)
    if command and command[0] == "--": command.pop(0)
    if not command or any(not part or "\0" in part for part in command):
        raise Operational("REFUSED", f"{operation} requires verification argv after --")
    return command


def _run_log(run_id: str, unit_id: str | None, prefix: str):
    with locked_manifest(run_id) as doc:
        parent = os.path.join(locate_run(run_id, doc["repository"]["toplevel"]), "units", unit_id, "result") if unit_id else os.path.join(locate_run(run_id, doc["repository"]["toplevel"]), "jobs")
    validate_private_dir(parent)
    path = os.path.join(parent, f"{prefix}-{secrets.token_hex(6)}.log")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
    return path, os.fdopen(fd, "wb")


def _execute_verification(repo: str, command: list[str], stream) -> int:
    try:
        return subprocess.run(command, cwd=repo, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, check=False).returncode
    except OSError as exc:
        stream.write(f"verification launch failed: {exc}\n".encode())
        return 127


def cmd_integrate(args) -> tuple[str, dict]:
    command = _verification_command(args, "integrate")
    description = args.change_description.strip()
    if not description or "\0" in description:
        raise Operational("REFUSED", "change description must be non-empty and contain no NUL")
    token = None
    described = False
    try:
        token = cmd_composition_acquire(_args(run_id=args.run_id, unit_id=args.unit_id, resume=False))[1]["lock_token"]
        cmd_preflight(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, allowed_change=args.allowed_change))
        with locked_manifest(args.run_id) as doc:
            repo = doc["repository"]["toplevel"]
            transport = doc["units"][args.unit_id]["transport"]["snapshot_id"]
        jj(repo, "restore", "--from", transport, "--into", "@")
        cmd_mark_composed(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        before = semantic_snapshot(repo)
        before_untracked = inventory_untracked_state(repo)
        log_path, stream = _run_log(args.run_id, args.unit_id, "host-verification")
        with stream:
            verification_exit = _execute_verification(repo, command, stream)
        after = semantic_snapshot(repo)
        untracked = diff_untracked_state(before_untracked, inventory_untracked_state(repo))
        changed = any(after[k] != before[k] for k in ("change_id", "parents", "description", "changed_paths", "bookmark_digest"))
        if verification_exit != 0 or changed:
            if not restore(args.run_id, args.unit_id, token):
                raise Operational("BLOCKED", "verification failed and exact Jujutsu restoration could not be proven", {"verification_log": log_path, "retain_composition_lock": True})
            cmd_composition_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
            token = None
            raise Operational("BLOCKED", "authoritative verification failed or changed canonical Jujutsu state", {"verification_exit": verification_exit, "verification_log": log_path, "untracked_state": untracked})
        evidence = digest_bytes(json.dumps({"argv": command, "exit": verification_exit, "before": before, "after": after, "untracked": untracked}, sort_keys=True, separators=(",", ":")).encode())
        cmd_mark_verified(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, evidence_digest=evidence, summary=args.verification_summary, untracked_state=json.dumps(untracked)))
        jj(repo, "describe", "-m", description)
        accepted = cmd_mark_described(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))[1]["canonical_change"]
        described = True
        with locked_manifest(args.run_id) as doc:
            wave_id = doc["units"][args.unit_id].get("wave", {}).get("id")
        if wave_id:
            cmd_wave_advance(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, canonical_change=accepted["change_id"]))
        jj(repo, "new")
        from unit_workspace_lifecycle import cmd_cleanup
        cmd_cleanup(_args(run_id=args.run_id, unit_id=args.unit_id, abandon=False, expect_transport=None, expect_job=None))
        cmd_composition_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        token = None
        if os.path.exists(log_path): os.unlink(log_path)
        return "UNIT_DESCRIBED", {"unit_id": args.unit_id, "canonical_change": accepted, "verification_digest": evidence, "untracked_state": untracked}
    except (Operational, TrustFailure) as exc:
        if token is not None and not exc.detail.get("retain_composition_lock"):
            if described:
                exc.detail.setdefault("recovery", "accepted change requires cleanup/release reconciliation")
            else:
                try:
                    restore(args.run_id, args.unit_id, token)
                    cmd_composition_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
                except (Operational, TrustFailure):
                    exc.detail["retain_composition_lock"] = True
        raise


def cmd_verify_run(args) -> tuple[str, dict]:
    command = _verification_command(args, "verify-run")
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        units = doc.get("units", {})
        accepted = accepted_unit_change_snapshot(units)
        if not units or accepted is None:
            raise Operational("REFUSED", "verify-run requires accepted canonical changes for every unit")
        if doc.get("canonical_lock"):
            raise Operational("BLOCKED", "verify-run requires no active composition lock")
        repo = info["toplevel"]
    before = semantic_snapshot(repo)
    if before["changed_paths"]:
        raise Operational("BLOCKED", "verify-run requires an empty canonical working-copy change")
    before_untracked = inventory_untracked_state(repo)
    log_path, stream = _run_log(args.run_id, None, "run-verification")
    with stream:
        verification_exit = _execute_verification(repo, command, stream)
    after = semantic_snapshot(repo)
    untracked = diff_untracked_state(before_untracked, inventory_untracked_state(repo))
    changed = any(after[k] != before[k] for k in ("change_id", "parents", "description", "changed_paths", "bookmark_digest"))
    if changed:
        jj(repo, "restore", "--from", before["snapshot_id"], "--into", "@")
        jj(repo, "describe", "-m", before["description"])
        restored = semantic_snapshot(repo)
        if any(restored[k] != before[k] for k in ("change_id", "parents", "description", "changed_paths", "bookmark_digest")):
            raise Operational("BLOCKED", "plan-wide verification changed Jujutsu state and exact restoration failed", {"verification_log": log_path})
    receipt = {"at": now_iso(), "argv": command, "summary": args.verification_summary, "verification_exit": verification_exit, "canonical_change": before["change_id"], "accepted_units": accepted, "untracked_state": untracked, "verification_log": log_path if verification_exit else None}
    receipt["evidence_digest"] = digest_bytes(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode())
    with locked_manifest(args.run_id, write=True) as doc:
        doc.setdefault("verifications", []).append(receipt)
        event(doc, "run-verification-passed" if verification_exit == 0 else "run-verification-failed", detail={"evidence_digest": receipt["evidence_digest"]})
    if verification_exit:
        raise Operational("BLOCKED", "plan-wide authoritative verification failed", {"verification_exit": verification_exit, "verification_log": log_path, "evidence_digest": receipt["evidence_digest"]})
    os.unlink(log_path)
    return "RUN_VERIFIED", {"verification_exit": 0, "evidence_digest": receipt["evidence_digest"], "canonical_change": before["change_id"], "untracked_state": untracked}
