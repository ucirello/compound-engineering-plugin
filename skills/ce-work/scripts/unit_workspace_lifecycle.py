"""Resume, fallback, reap, and finalized jj workspace lifecycle operations."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

from unit_workspace_state import *
from unit_workspace_jobs import *
from unit_workspace_integration import *


def cmd_status(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        body = {"run_id": args.run_id, "revision": doc["revision"], "source": doc["source"], "integration_lock": doc.get("integration_lock"), "verifications": doc.get("verifications", []), "blockers": doc.get("blockers", []), "recovery_path": run_dir(args.run_id)}
        body["unit" if args.unit_id else "units"] = doc["units"].get(args.unit_id) if args.unit_id else doc["units"]
        if args.unit_id and body["unit"] is None:
            raise Operational("REFUSED", "unknown unit")
    return "STATUS", body


def discover_resume_run(repo: str, plan_digest: str) -> tuple[str, list[dict]]:
    if not re.fullmatch(r"[0-9a-f]{64}", plan_digest):
        raise Operational("REFUSED", "plan digest must be lowercase SHA-256")
    info = repo_info(repo)
    root = ensure_root(repo)
    candidates = []
    for entry in os.scandir(root):
        if entry.name in {".locks", ".inputs"} or not entry.is_dir(follow_symlinks=False):
            continue
        doc = read_private_json(os.path.join(entry.path, "manifest.json"))
        if doc.get("repository", {}).get("identity_digest") == info["identity_digest"] and doc.get("bookmark", {}).get("name") == info["bookmark"] and doc.get("source", {}).get("kind") == "plan" and doc.get("source", {}).get("digest") == plan_digest:
            unfinished = any(unit.get("state") not in {"cleaned", "native-completed"} for unit in doc.get("units", {}).values()) or not doc.get("verifications")
            if unfinished:
                candidates.append({"run_id": entry.name, "recovery_path": entry.path})
    if not candidates:
        raise Operational("NOT_FOUND", "no unfinished run matches repository, bookmark, and plan digest", {"candidates": []})
    if len(candidates) > 1:
        raise Operational("AMBIGUOUS", "multiple unfinished runs match; pass --run-id", {"candidates": candidates})
    return candidates[0]["run_id"], candidates


def cmd_resume(args) -> tuple[str, dict]:
    run_id = safe_id(args.run_id, "run id") if args.run_id else discover_resume_run(args.repo, args.plan_digest)[0]
    actions = []
    with locked_manifest(run_id) as doc:
        validate_repo(doc)
        unit_ids = list(doc["units"])
    for uid in unit_ids:
        with locked_manifest(run_id) as doc:
            unit = doc["units"][uid]
            state = unit["state"]
            attempt = find_attempt(unit)
            lock = doc.get("integration_lock")
        if state == "queued" and not attempt.get("job_id"):
            matches = matching_runner_jobs(run_id, unit)
            if len(matches) == 1:
                cmd_record_job(type("Args", (), {"run_id": run_id, "unit_id": uid, "attempt_id": attempt["attempt_id"], "job_id": matches[0]})())
                actions.append({"unit_id": uid, "action": "job-adopted", "job_id": matches[0]})
        elif state == "authoring":
            evidence = sync_job(run_id, uid)
            actions.append({"unit_id": uid, "action": "monitored", **evidence})
            if evidence["process_state"] == "done":
                transport = terminalize(run_id, uid)
                actions.append({"unit_id": uid, "action": "terminalized", "change_id": transport["change_id"]})
        elif state == "restoring" and lock and lock.get("unit_id") == uid:
            if not restore(run_id, uid, lock["nonce"]):
                raise Operational("BLOCKED", "exact jj operation restoration could not be proven")
            integration_release(run_id, uid, lock["nonce"])
            actions.append({"unit_id": uid, "action": "operation-restored"})
        elif state in {"integrated", "verified"} and lock and lock.get("unit_id") == uid:
            with locked_manifest(run_id) as doc:
                current = doc["units"][uid]
                canonical = reconcile_change(doc, current)
            if canonical:
                cmd_mark_accepted(type("Args", (), {"run_id": run_id, "unit_id": uid, "lock_token": lock["nonce"]})())
                actions.append({"unit_id": uid, "action": "accepted-change-reconciled", "change_id": canonical["change_id"]})
            else:
                if not restore(run_id, uid, lock["nonce"]):
                    raise Operational("BLOCKED", "interrupted integration could not restore its recorded jj operation")
                actions.append({"unit_id": uid, "action": "interrupted-integration-restored"})
            integration_release(run_id, uid, lock["nonce"])
            if canonical:
                cmd_cleanup(type("Args", (), {"run_id": run_id, "unit_id": uid, "abandon": False, "expect_transport": None, "expect_job": None})())
                actions.append({"unit_id": uid, "action": "workspace-cleaned"})
        elif state == "accepted":
            cmd_cleanup(type("Args", (), {"run_id": run_id, "unit_id": uid, "abandon": False, "expect_transport": None, "expect_job": None})())
            actions.append({"unit_id": uid, "action": "workspace-cleaned"})
    return "RESUMED", {"run_id": run_id, "actions": actions, "redispatched": False}


def cmd_claim_fallback(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        terminal_validation_failure = attempt.get("terminal_validation_failure")
        if terminal_validation_failure is not None:
            validate_terminal_validation_failure(args.run_id, unit, attempt)
        elif attempt.get("process_state") not in TERMINAL_PROCESS - {"done"} and unit.get("state") != "preserved":
            raise Operational("REFUSED", "no authoritative failure or restored operation authorizes fallback")
        fallback = attempt.setdefault("fallback", {"claimed": None, "completed": None})
        if fallback.get("claimed"):
            return "FALLBACK_ALREADY_AUTHORIZED", {"start_native": False, "claim": fallback["claimed"]}
        mode = doc["binding"]["mode"]
        if mode == "require" and (args.caller_mode == "headless" or not args.confirm_native):
            raise Operational("BLOCKED" if args.caller_mode == "headless" else "CHOICE_REQUIRED", "required route needs explicit interactive native fallback confirmation")
        claim = {"at": now_iso(), "mode": mode, "caller_mode": args.caller_mode, "confirmed_native": bool(args.confirm_native), "canonical_change": repo_info(doc["repository"]["toplevel"])["change_id"]}
        fallback["claimed"] = claim
        event(doc, "native-fallback-authorized", args.unit_id, claim)
        return "FALLBACK_AUTHORIZED", {"unit_id": args.unit_id, "start_native": True, "claim": claim}


def cmd_complete_fallback(args) -> tuple[str, dict]:
    if not re.fullmatch(r"[0-9a-f]{64}", args.evidence_digest):
        raise Operational("REFUSED", "fallback evidence digest must be lowercase SHA-256")
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        attempt = find_attempt(unit)
        claim = attempt.get("fallback", {}).get("claimed")
        if not claim:
            raise Operational("REFUSED", "fallback completion requires an existing claim")
        accepted = change_id(info["toplevel"], args.accepted_change)
        if accepted != args.accepted_change:
            raise Operational("BLOCKED", "accepted fallback change does not resolve exactly")
        completion = {"at": now_iso(), "accepted_change": accepted, "commit_id": commit_id(info["toplevel"], accepted), "evidence_digest": args.evidence_digest, "summary": args.summary, "claim": claim}
        attempt["fallback"]["completed"] = completion
        unit["fallback"] = {"completed": completion}
        unit["state"] = "native-completed"
        event(doc, "native-fallback-completed", args.unit_id, {"accepted_change": accepted})
        return "FALLBACK_COMPLETED", {"unit_id": args.unit_id, "completion": completion}


def cmd_reap(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        unit = doc["units"].get(args.unit_id)
        attempt = find_attempt(unit)
        if not attempt.get("job_id"):
            return "REAPED", {"unit_id": args.unit_id, "process_state": "never-started"}
        job = runner_job_dir(args.run_id, attempt["job_id"])
    runner = os.path.join(os.path.dirname(__file__), "peer-job-runner.py")
    proc = subprocess.run([sys.executable, runner, "reap", job], capture_output=True, check=False)
    if proc.returncode:
        raise Operational("BLOCKED", proc.stderr.decode("utf-8", "replace").strip())
    return "REAPED", {"unit_id": args.unit_id, **sync_job(args.run_id, args.unit_id)}


def cmd_cleanup(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        if unit["state"] == "cleaned":
            return "CLEANED", {"unit_id": args.unit_id, "resumed": True}
        if unit["state"] not in {"accepted", "native-completed"} and not args.abandon:
            raise Operational("REFUSED", "unaccepted output is retained unless explicitly abandoned")
        transport = unit.get("transport", {}).get("change_id")
        job_id = find_attempt(unit).get("job_id")
        if args.expect_transport is not None and args.expect_transport != transport:
            raise Operational("BLOCKED", "cleanup transport guard does not match recorded state")
        if args.expect_job is not None and args.expect_job != job_id:
            raise Operational("BLOCKED", "cleanup job guard does not match recorded state")
        if args.abandon and not (args.expect_transport or args.expect_job):
            raise Operational("REFUSED", "abandonment requires an exact transport or terminal job guard")
        workspace, name = unit["workspace"]["path"], unit["workspace"]["name"]
        repo = doc["repository"]["toplevel"]
    jj(repo, "workspace", "forget", name, check=False)
    if os.path.exists(workspace):
        shutil.rmtree(workspace)
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        unit["cleanup"] = {"at": now_iso(), "workspace_removed": True, "workspace_forgotten": True, "abandoned": bool(args.abandon)}
        if unit["state"] != "native-completed":
            unit["state"] = "cleaned"
        event(doc, "unit-cleaned", args.unit_id)
    return "CLEANED", {"unit_id": args.unit_id, "resumed": False}
