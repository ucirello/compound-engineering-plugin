"""Resume, native fallback, reap, and finalized JJ workspace lifecycle."""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys

from unit_workspace_state import *
from unit_workspace_jobs import *
from unit_workspace_integration import *


def cmd_status(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        if args.unit_id:
            unit = doc["units"].get(args.unit_id)
            if not unit:
                raise Operational("REFUSED", "unknown unit")
            body = {"run_id": args.run_id, "revision": doc["revision"], "source": doc["source"], "unit": unit, "integration_lock": doc.get("integration_lock"), "verifications": doc.get("verifications", []), "blockers": doc.get("blockers", [])}
        else:
            body = {"run_id": args.run_id, "revision": doc["revision"], "source": doc["source"], "units": doc["units"], "integration_lock": doc.get("integration_lock"), "verifications": doc.get("verifications", []), "blockers": doc.get("blockers", []), "recovery_path": run_dir(args.run_id)}
    return "STATUS", body


def unfinished_run(doc: dict) -> bool:
    units = doc.get("units", {})
    if not units:
        return True
    if any(unit.get("state") not in {"cleaned", "native-completed"} for unit in units.values()):
        return True
    accepted = accepted_unit_change_snapshot(units)
    return doc.get("integration_lock") is not None or not any(receipt.get("verification_exit") == 0 and receipt.get("accepted_units") == accepted for receipt in doc.get("verifications", []))


def discover_resume_run(repo: str, plan_digest: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", plan_digest):
        raise Operational("REFUSED", "plan digest must be lowercase SHA-256")
    info = repo_info(repo)
    root = runs_root(info["workspace_root"])
    candidates = []
    for entry in os.scandir(root):
        if entry.name == ".locks" or not entry.is_dir(follow_symlinks=False):
            continue
        safe_id(entry.name, "run id")
        doc = read_private_json(os.path.join(entry.path, "manifest.json"))
        if doc.get("repository", {}).get("identity_digest") != info["identity_digest"]:
            continue
        if doc.get("source", {}).get("kind") != "plan" or doc.get("source", {}).get("digest") != plan_digest:
            continue
        if unfinished_run(doc):
            candidates.append({"run_id": entry.name, "recovery_path": entry.path})
    if not candidates:
        raise Operational("NOT_FOUND", "no unfinished run matches repository and plan digest", {"candidates": []})
    if len(candidates) > 1:
        raise Operational("AMBIGUOUS", "multiple unfinished runs match; pass --run-id", {"candidates": candidates})
    return candidates[0]["run_id"]


def resolve_resume_run(args) -> str:
    if args.run_id:
        if args.repo or args.plan_digest:
            raise Operational("REFUSED", "resume accepts --run-id alone or --repo with --plan-digest")
        return safe_id(args.run_id, "run id")
    if not args.repo or not args.plan_digest:
        raise Operational("REFUSED", "resume requires --run-id or repository plus plan digest")
    return discover_resume_run(args.repo, args.plan_digest)


def plan_wide_verification_attempts(doc: dict) -> list[dict]:
    attempts = doc.get("verification_attempts", [])
    if not isinstance(attempts, list) or any(not isinstance(attempt, dict) for attempt in attempts):
        raise TrustFailure("manifest plan-wide verification attempts are malformed")
    for attempt in attempts:
        if (
            not isinstance(attempt.get("attempt_id"), str)
            or not re.fullmatch(r"[0-9a-f]{32}", attempt["attempt_id"])
            or attempt.get("status") not in {"pending", "receipt-recorded"}
            or not isinstance(attempt.get("integration_lock_nonce"), str)
            or not re.fullmatch(r"[0-9a-f]{48}", attempt["integration_lock_nonce"])
        ):
            raise TrustFailure("manifest plan-wide verification attempt identity or state is malformed")
    return attempts


def pending_plan_wide_verification(doc: dict, lock: dict) -> dict | None:
    matches = [
        attempt for attempt in plan_wide_verification_attempts(doc)
        if attempt["status"] == "pending"
        and attempt["integration_lock_nonce"] == lock.get("nonce")
        and attempt.get("lock_unit_id") == lock.get("unit_id")
    ]
    if len(matches) > 1:
        raise TrustFailure("multiple pending plan-wide verification attempts share one integration lock")
    return matches[0] if matches else None


def receipted_plan_wide_verification(doc: dict, lock: dict) -> dict | None:
    matches = [
        attempt for attempt in plan_wide_verification_attempts(doc)
        if attempt["status"] == "receipt-recorded"
        and attempt["integration_lock_nonce"] == lock.get("nonce")
        and attempt.get("lock_unit_id") == lock.get("unit_id")
    ]
    if len(matches) > 1:
        raise TrustFailure("multiple receipted plan-wide verification attempts share one integration lock")
    if not matches:
        return None
    receipts = [row for row in doc.get("verifications", []) if row.get("evidence_digest") == matches[0].get("evidence_digest")]
    if len(receipts) != 1:
        raise TrustFailure("plan-wide verification receipt is missing or duplicated")
    return matches[0]


def cmd_resume(args) -> tuple[str, dict]:
    run_id = resolve_resume_run(args)
    actions = []
    with locked_manifest(run_id) as doc:
        validate_repo(doc)
        unit_ids = list(doc["units"])
        lock = doc.get("integration_lock")
        all_pending = [attempt for attempt in plan_wide_verification_attempts(doc) if attempt.get("status") == "pending"]
        if all_pending and (
            not isinstance(lock, dict)
            or len(all_pending) != 1
            or all_pending[0].get("integration_lock_nonce") != lock.get("nonce")
            or all_pending[0].get("lock_unit_id") != lock.get("unit_id")
        ):
            raise TrustFailure("pending plan-wide verification is not bound to the active integration lock")
        pending_verification = pending_plan_wide_verification(doc, lock) if isinstance(lock, dict) else None
        receipted_verification = receipted_plan_wide_verification(doc, lock) if isinstance(lock, dict) else None
    if pending_verification:
        raise Operational(
            "BLOCKED", "pending plan-wide verification retains the canonical integration lock",
            {"verification_attempt_id": pending_verification["attempt_id"], "retain_integration_lock": True},
        )
    if lock and receipted_verification:
        matching_receipts = [row for row in doc.get("verifications", []) if row.get("evidence_digest") == receipted_verification.get("evidence_digest")]
        receipt = matching_receipts[0]
        if receipt.get("verification_exit") == 0:
            log_path = receipted_verification.get("verification_log")
            if isinstance(log_path, str) and os.path.lexists(log_path):
                jobs_root = os.path.join(run_dir(run_id), "jobs")
                if os.path.commonpath([jobs_root, os.path.abspath(log_path)]) != jobs_root:
                    raise Operational("BLOCKED", "verification log escaped the controller jobs directory")
                stat_private_file(log_path)
                os.unlink(log_path)
        integration_release(run_id, lock["unit_id"], lock["nonce"])
        actions.append({"unit_id": lock["unit_id"], "action": "verification-lock-release-reconciled"})
        lock = None
    for unit_id in unit_ids:
        with locked_manifest(run_id) as doc:
            unit = doc["units"][unit_id]
            state = unit["state"]
            attempt = find_attempt(unit)
        if state == "queued" and not attempt.get("job_id"):
            matches = matching_runner_jobs(run_id, unit)
            if len(matches) > 1:
                raise Operational("AMBIGUOUS", f"multiple runner jobs match queued unit {unit_id}")
            if len(matches) == 1:
                with locked_manifest(run_id, write=True) as doc:
                    current = find_attempt(doc["units"][unit_id])
                    current["job_id"] = matches[0]
                    doc["units"][unit_id]["state"] = "authoring"
                    event(doc, "job-adopted", unit_id, {"job_id": matches[0]})
                actions.append({"unit_id": unit_id, "action": "job-adopted", "job_id": matches[0]})
                evidence = sync_job(run_id, unit_id)
                actions.append({"unit_id": unit_id, "action": "monitored", "process_state": evidence["process_state"]})
                if evidence["process_state"] == "done":
                    transport = terminalize(run_id, unit_id)
                    actions.append({"unit_id": unit_id, "action": "terminalized", "change_id": transport["change_id"]})
        elif state == "authoring" and attempt.get("job_id"):
            evidence = sync_job(run_id, unit_id)
            actions.append({"unit_id": unit_id, "action": "monitored", "process_state": evidence["process_state"]})
            if evidence["process_state"] == "done":
                transport = terminalize(run_id, unit_id)
                actions.append({"unit_id": unit_id, "action": "terminalized", "change_id": transport["change_id"]})
        elif state == "authored":
            transport = terminalize(run_id, unit_id)
            actions.append({"unit_id": unit_id, "action": "terminalized", "change_id": transport["change_id"]})
        elif state == "integrating" and lock and lock.get("unit_id") == unit_id:
            if not restore(run_id, unit_id, lock["nonce"]):
                raise Operational("BLOCKED", "exact JJ operation restoration could not be proven")
            integration_release(run_id, unit_id, lock["nonce"])
            actions.append({"unit_id": unit_id, "action": "operation-restored", "integration_lock_released": True})
        elif state == "accepted":
            cmd_cleanup(type("Args", (), {"run_id": run_id, "unit_id": unit_id, "abandon": False, "expect_transport": None, "expect_job": None})())
            actions.append({"unit_id": unit_id, "action": "workspace-cleaned"})
            if lock and lock.get("unit_id") == unit_id:
                integration_release(run_id, unit_id, lock["nonce"])
                actions.append({"unit_id": unit_id, "action": "integration-lock-released"})
        elif state in {"cleaned", "native-completed"} and lock and lock.get("unit_id") == unit_id:
            integration_release(run_id, unit_id, lock["nonce"])
            actions.append({"unit_id": unit_id, "action": "integration-lock-released"})
    return "RESUMED", {"run_id": run_id, "actions": actions, "redispatched": False, "applied": False}


def cmd_claim_fallback(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        fallback = attempt.setdefault("fallback", {"eligible": False, "reason": None, "claimed": None, "completed": None})
        if fallback.get("claimed"):
            return "FALLBACK_ALREADY_AUTHORIZED", {"unit_id": args.unit_id, "start_native": False, "claim": fallback["claimed"]}
        if attempt.get("process_state") == "running":
            raise Operational("REFUSED", "a live external attempt still owns implementation")
        restored = unit.get("integration", {}).get("restore")
        terminal = attempt.get("process_state") in TERMINAL_PROCESS - {"done"}
        validation_failure = attempt.get("terminal_validation_failure")
        if validation_failure:
            if attempt.get("process_state") != "done" or validation_failure.get("job_id") != attempt.get("job_id"):
                raise Operational("BLOCKED", "terminal-validation failure no longer matches runner evidence")
            observed = process_evidence(runner_job_dir(args.run_id, attempt["job_id"]))["process_state"]
            result_digest = digest_bytes(read_recorded_result_file(unit, "implementation-result.json", MAX_RESULT_BYTES))
            if observed != "done" or result_digest != validation_failure.get("result_sha256"):
                raise Operational("BLOCKED", "terminal-validation failure evidence changed")
        if not terminal and not validation_failure and not (isinstance(restored, dict) and restored.get("exact") is True):
            raise Operational("REFUSED", "fallback requires authoritative failure or exact operation restoration")
        repo = doc["repository"]["workspace_root"]
        snap = semantic_snapshot(repo)
        if not snap["empty"] or snap["conflicted"] or doc.get("integration_lock"):
            raise Operational("BLOCKED", "canonical JJ state is not safe for native fallback")
        claim = {"at": now_iso(), "reason": fallback.get("reason") or "external-attempt-unavailable", "caller_mode": args.caller_mode, "mode": doc["binding"]["mode"], "operation_id": snap["operation_id"], "base_change": revision_info(repo, "@-")["change_id"]}
        fallback.update({"eligible": False, "claimed": claim})
        event(doc, "native-fallback-authorized", args.unit_id, {"reason": claim["reason"]})
    return "FALLBACK_AUTHORIZED", {"unit_id": args.unit_id, "start_native": True, "reason": claim["reason"], "claim": claim}


def cmd_complete_fallback(args) -> tuple[str, dict]:
    if not re.fullmatch(r"[0-9a-f]{64}", args.evidence_digest):
        raise Operational("REFUSED", "fallback evidence digest must be lowercase SHA-256")
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        fallback = find_attempt(unit).get("fallback", {})
        if not fallback.get("claimed") or fallback.get("completed"):
            raise Operational("REFUSED", "fallback completion requires one uncompleted claim")
        repo = doc["repository"]["workspace_root"]
        accepted = revision_info(repo, args.accepted_change)
        canonical = revision_info(repo, "@-")
        if accepted["commit_id"] != canonical["commit_id"]:
            raise Operational("BLOCKED", "native fallback accepted change does not match the canonical result")
        if has_conflicts(repo, accepted["change_id"]):
            raise Operational("BLOCKED", "native fallback change contains conflicts")
        claim = fallback["claimed"]
        required = [unit.get("workspace", {}).get("base", {}).get("change_id"), claim.get("base_change")]
        required.extend(unit_accepted_change(doc["units"].get(dep, {})) for dep in unit.get("dependencies", []))
        required.extend(unit.get("wave", {}).get("accepted", []))
        missing = [ancestor for ancestor in required if ancestor and not jj_text(repo, "log", "-r", f"({ancestor}) & ::({accepted['change_id']})", "--no-graph", "-T", 'change_id ++ "\\n"', check=False)]
        if missing:
            raise Operational("BLOCKED", "native fallback result omits recorded base, dependency, or wave ancestry", {"missing_ancestry": missing})
        completion = {**accepted, "at": now_iso(), "evidence_digest": args.evidence_digest, "summary": args.summary, "operation_id": operation_id(repo), "changed_paths": changed_paths(repo, accepted["change_id"]), "claim": dict(claim)}
        fallback["completed"] = completion
        unit["integration"]["accepted_change"] = completion
        unit["state"] = "native-completed"
        event(doc, "native-fallback-completed", args.unit_id, {"change_id": accepted["change_id"]})
    return "FALLBACK_COMPLETED", {"unit_id": args.unit_id, "completion": completion}


def cmd_reap(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        if not attempt.get("job_id"):
            return "REAPED", {"unit_id": args.unit_id, "process_state": "never-started"}
        job_dir = runner_job_dir(args.run_id, attempt["job_id"])
    runner = os.path.join(os.path.dirname(__file__), "peer-job-runner.py")
    proc = subprocess.run([sys.executable, runner, "reap", job_dir], capture_output=True, check=False)
    if proc.returncode != 0:
        raise Operational("BLOCKED", f"runner reap failed: {proc.stderr.decode('utf-8', 'replace').strip()}")
    evidence = sync_job(args.run_id, args.unit_id)
    return "REAPED", {"unit_id": args.unit_id, **evidence, "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id)}


def cmd_cleanup(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        if unit.get("state") == "cleaned":
            return "CLEANED", {"unit_id": args.unit_id, "resumed": True}
        attempt = find_attempt(unit)
        if attempt.get("process_state") == "running":
            raise Operational("REFUSED", "cannot clean a live worker")
        transport = (unit.get("transport") or {}).get("change_id")
        if args.abandon:
            if transport and args.expect_transport != transport:
                raise Operational("REFUSED", "abandonment requires the exact transport change ID")
            if not transport and args.expect_job != attempt.get("job_id"):
                raise Operational("REFUSED", "transport-free abandonment requires the exact terminal job ID")
        elif unit.get("state") not in {"accepted", "native-completed"}:
            raise Operational("REFUSED", "unaccepted output is retained unless explicitly abandoned")
        repo = doc["repository"]["workspace_root"]
        workspace_name = unit["workspace"]["name"]
        workspace_path = unit["workspace"]["path"]
    expected_workspace = os.path.join(run_dir(args.run_id), "units", args.unit_id, "workspace")
    if os.path.abspath(workspace_path) != expected_workspace:
        raise TrustFailure("manifest workspace path does not match the controller-owned unit workspace")
    jj(repo, "workspace", "forget", workspace_name)
    registered = set(jj_text(repo, "workspace", "list", "-T", 'name ++ "\\n"').splitlines())
    if workspace_name in registered:
        raise Operational("BLOCKED", "workspace remained registered after forget")
    with locked_manifest(args.run_id) as doc:
        current = doc["units"].get(args.unit_id)
        if not current or current.get("workspace", {}).get("path") != workspace_path or current.get("workspace", {}).get("name") != workspace_name:
            raise Operational("BLOCKED", "workspace ownership record changed during cleanup")
    if os.path.lexists(workspace_path):
        info = os.lstat(workspace_path)
        uid_getter = getattr(os, "geteuid", None) or getattr(os, "getuid", None)
        effective_uid = uid_getter() if uid_getter else None
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode) or (effective_uid is not None and info.st_uid != effective_uid):
            raise Operational("BLOCKED", "unregistered workspace is not a controller-owned directory")
        shutil.rmtree(workspace_path)
    if os.path.lexists(workspace_path):
        raise Operational("BLOCKED", "workspace remained after cleanup")
    if args.abandon:
        for path in (
            unit.get("packet", {}).get("path"),
            find_attempt(unit).get("authorization_path"),
            os.path.join(os.path.dirname(workspace_path), "result"),
        ):
            if not path or not os.path.lexists(path):
                continue
            absolute = os.path.abspath(path)
            root = run_dir(args.run_id)
            if os.path.commonpath([root, absolute]) != root or absolute == root:
                raise Operational("BLOCKED", "cleanup artifact path escaped the controller-owned run")
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
            else:
                os.unlink(path)
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        prior_state = unit["state"]
        unit["cleanup"] = {"at": now_iso(), "workspace_forgotten": True, "workspace_removed": True, "abandoned": bool(args.abandon)}
        unit["state"] = "native-completed" if prior_state == "native-completed" else "cleaned"
        event(doc, "unit-cleaned", args.unit_id, {"workspace_name": workspace_name})
    return "CLEANED", {"unit_id": args.unit_id, "resumed": False}
