"""Fail-stop canonical jj integration for external unit changes."""

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
    cmd_integration_acquire, cmd_integration_release, cmd_mark_applied,
    cmd_mark_accepted, cmd_mark_verified, cmd_preflight, cmd_restore,
    cmd_wave_advance, validate_lock,
)
from unit_workspace_lifecycle import cmd_cleanup
from unit_workspace_ignored import diff_ignored_state, inventory_ignored_state


def _args(**values):
    return SimpleNamespace(**values)


def _verification_command(args, operation: str) -> list[str]:
    command = list(args.verification_command)
    if command and command[0] == "--":
        command.pop(0)
    if not command or any(not value or "\0" in value for value in command):
        raise Operational("REFUSED", f"{operation} requires a non-empty verification command after --")
    return command


def _run_verification(repo: str, command: list[str], log_path: str) -> tuple[int, str]:
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        try:
            proc = subprocess.run(command, cwd=repo, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, env=sanitized_jj_environment({"PYTHONDONTWRITEBYTECODE": "1"}), check=False)
            code = proc.returncode
        except OSError as exc:
            stream.write(f"verification launch failed: {exc}\n".encode())
            code = 127
    return code, hashlib.sha256(Path(log_path).read_bytes()).hexdigest()


def _same_tracked_snapshot(before: dict, after: dict) -> bool:
    return all(before[key] == after[key] for key in (
        "change_id", "commit_id", "parent_ids", "description", "changed_paths",
        "status_sha256", "status_empty", "conflicts",
    ))


def cmd_integrate(args) -> tuple[str, dict]:
    command = _verification_command(args, "integrate")
    description = validate_change_description(args.change_description)
    token = None
    try:
        token = cmd_integration_acquire(_args(run_id=args.run_id, unit_id=args.unit_id, resume=False))[1]["lock_token"]
        cmd_preflight(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, allowed_change=args.allowed_change))
        with locked_manifest(args.run_id) as doc:
            repo = doc["repository"]["toplevel"]
            unit = doc["units"][args.unit_id]
            transport = unit["transport"]["change_id"]
            pre = unit["integration"]["pre_fold"]
            bookmark = doc["bookmark"]["name"]

        jj(repo, "rebase", "-r", transport, "-o", pre["change_id"])
        jj(repo, "edit", transport)
        cmd_mark_applied(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        before = semantic_snapshot(repo)
        before_ignored = inventory_ignored_state(repo)
        log_path = os.path.join(run_dir(args.run_id), "units", args.unit_id, "result", f"host-verification-{secrets.token_hex(6)}.log")
        verification_exit, log_digest = _run_verification(repo, command, log_path)
        after = semantic_snapshot(repo)
        ignored_state = diff_ignored_state(before_ignored, inventory_ignored_state(repo))
        if verification_exit != 0 or not _same_tracked_snapshot(before, after):
            cmd_restore(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
            cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
            token = None
            raise Operational("BLOCKED", "authoritative verification failed or changed canonical jj state", {"verification_exit": verification_exit, "verification_log": log_path, "ignored_state": ignored_state})
        evidence = digest_bytes(json.dumps({"argv": command, "exit": verification_exit, "log_sha256": log_digest, "snapshot": before, "ignored_state": ignored_state}, sort_keys=True).encode())
        cmd_mark_verified(_args(
            run_id=args.run_id,
            unit_id=args.unit_id,
            lock_token=token,
            evidence_digest=evidence,
            summary=args.verification_summary,
            ignored_state=ignored_state,
        ))

        jj(repo, "squash", "--from", transport, "--into", pre["change_id"], "-m", description)
        accepted_change = change_id(repo, pre["change_id"])
        jj(repo, "bookmark", "set", bookmark, "-r", accepted_change)
        canonical = {"change_id": accepted_change, "commit_id": commit_id(repo, accepted_change), "description": description, "parent_ids": parent_ids(repo, accepted_change), "at": now_iso()}
        jj(repo, "new", accepted_change)
        with locked_manifest(args.run_id, write=True) as doc:
            doc["units"][args.unit_id]["integration"]["canonical_change"] = canonical
        cmd_mark_accepted(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        with locked_manifest(args.run_id) as doc:
            wave_id = doc["units"][args.unit_id].get("wave", {}).get("id")
        if wave_id:
            cmd_wave_advance(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token, canonical_change=accepted_change))
        cmd_cleanup(_args(run_id=args.run_id, unit_id=args.unit_id, abandon=False, expect_transport=None, expect_job=None))
        cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        token = None
        with contextlib.suppress(OSError):
            os.unlink(log_path)
        return "UNIT_ACCEPTED", {"unit_id": args.unit_id, "canonical_change": accepted_change, "verification_digest": evidence, "ignored_state": ignored_state}
    except (Operational, TrustFailure):
        if token is not None:
            with contextlib.suppress(Operational, TrustFailure):
                cmd_restore(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
                cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        raise


def cmd_verify_run(args) -> tuple[str, dict]:
    command = _verification_command(args, "verify-run")
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        units = doc.get("units", {})
        accepted = accepted_unit_change_snapshot(units)
        if not units or accepted is None:
            raise Operational("REFUSED", "verify-run requires every unit to have an accepted jj change")
        repo = info["toplevel"]
    before = semantic_snapshot(repo)
    if not before["status_empty"]:
        raise Operational("BLOCKED", "verify-run requires an empty canonical working-copy change")
    before_ignored = inventory_ignored_state(repo)
    log_path = os.path.join(run_dir(args.run_id), "jobs", f"run-verification-{secrets.token_hex(6)}.log")
    verification_exit, log_digest = _run_verification(repo, command, log_path)
    after = semantic_snapshot(repo)
    ignored_state = diff_ignored_state(before_ignored, inventory_ignored_state(repo))
    if not _same_tracked_snapshot(before, after):
        restore_operation(repo, before["operation_id"])
        restored = semantic_snapshot(repo)
        if not _same_tracked_snapshot(before, restored):
            raise Operational("BLOCKED", "plan-wide verification operation restoration could not be proven", {"verification_log": log_path, "ignored_state": ignored_state})
    receipt = {"at": now_iso(), "argv": command, "summary": args.verification_summary, "verification_exit": verification_exit, "log_sha256": log_digest, "canonical_change": before["change_id"], "accepted_units": accepted, "ignored_state": ignored_state, "verification_log": log_path if verification_exit else None}
    receipt["evidence_digest"] = digest_bytes(json.dumps(receipt, sort_keys=True).encode())
    with locked_manifest(args.run_id, write=True) as doc:
        doc.setdefault("verifications", []).append(receipt)
        event(doc, "run-verification-passed" if verification_exit == 0 else "run-verification-failed", detail={"evidence_digest": receipt["evidence_digest"]})
    if verification_exit:
        raise Operational("BLOCKED", "plan-wide authoritative verification failed", receipt)
    os.unlink(log_path)
    return "RUN_VERIFIED", {"verification_exit": 0, "evidence_digest": receipt["evidence_digest"], "canonical_change": before["change_id"], "ignored_state": ignored_state}
