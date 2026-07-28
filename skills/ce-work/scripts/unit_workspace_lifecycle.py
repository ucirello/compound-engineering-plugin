"""Resume, fallback, reap, and finalized-artifact lifecycle operations."""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
from types import SimpleNamespace

from unit_workspace_state import *
from unit_workspace_jobs import *
from unit_workspace_integration import *

DESCRIPTION_RULE = "Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards."
DESCRIPTION_PRECEDENCE = (
    "The project's active runtime instructions and syntax observed with `jj log` take precedence; "
    "apply the Go guidance only where compatible, without a fixed type, scope, template, example, "
    "or identity footer."
)


def cmd_status(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        source = doc.get("source") or {"kind": "plan", **doc.get("plan", {})}
        if args.unit_id:
            unit = doc["units"].get(args.unit_id)
            if not unit:
                raise Operational("REFUSED", "unknown unit")
            body = {
                "run_id": args.run_id,
                "revision": doc["revision"],
                "source": source,
                "unit": unit,
                "integration_lock": doc.get("integration_lock"),
                "verifications": doc.get("verifications", []),
                "blockers": doc.get("blockers", []),
            }
        else:
            body = {
                "run_id": args.run_id,
                "revision": doc["revision"],
                "source": source,
                "units": doc["units"],
                "integration_lock": doc.get("integration_lock"),
                "verifications": doc.get("verifications", []),
                "blockers": doc.get("blockers", []),
                "recovery_path": run_dir(args.run_id),
            }
    return "STATUS", body


def unfinished_run(doc: dict, canonical_revision: str) -> bool:
    units = doc.get("units")
    if not isinstance(units, dict):
        raise TrustFailure("manifest units are malformed")
    if not units:
        return True
    states: list[str] = []
    for uid, unit in units.items():
        if not isinstance(uid, str) or not SAFE_ID.fullmatch(uid) or not isinstance(unit, dict):
            raise TrustFailure("manifest unit identity or record is malformed")
        state = unit.get("state")
        if state not in UNIT_STATES:
            raise TrustFailure(f"manifest unit state is invalid: {uid}")
        states.append(state)
    terminal_states = {"cleaned", "native-completed"}
    if any(state not in terminal_states for state in states):
        return True
    for uid, unit in units.items():
        if unit.get("state") != "native-completed":
            continue
        attempt = find_attempt(unit)
        fallback = attempt.get("fallback", {})
        claim = fallback.get("claimed") if isinstance(fallback, dict) else None
        completion = fallback.get("completed") if isinstance(fallback, dict) else None
        claim_valid = isinstance(claim, dict) and (
            claim.get("mode") == "prefer"
            or (
                claim.get("mode") == "require"
                and claim.get("caller_mode") == "interactive"
                and claim.get("confirmed_native") is True
            )
        )
        if not (
            claim_valid
            and isinstance(completion, dict)
            and completion.get("claim") == claim
            and isinstance(completion.get("at"), str)
            and completion.get("at")
            and isinstance(completion.get("summary"), str)
            and completion.get("summary")
            and isinstance(completion.get("evidence_digest"), str)
            and SHA256.fullmatch(completion["evidence_digest"])
            and isinstance(completion.get("accepted_revision_id"), str)
            and REVISION_ID.fullmatch(completion["accepted_revision_id"])
        ):
            raise TrustFailure(f"native fallback completion receipt is malformed: {uid}")
    receipts = doc.get("verifications", [])
    if not isinstance(receipts, list) or any(not isinstance(receipt, dict) for receipt in receipts):
        raise TrustFailure("manifest verification receipts are malformed")
    accepted_units = {uid: unit_accepted_revision(unit) for uid, unit in units.items()}
    if any(value is None for value in accepted_units.values()):
        return True
    return doc.get("integration_lock") is not None or not any(
        receipt.get("verification_exit") == 0
        and receipt.get("accepted_units") == accepted_units
        and receipt.get("canonical_revision_id") == canonical_revision
        for receipt in receipts
    )


def discover_resume_run(repo: str, plan_digest: str) -> tuple[str, list[dict]]:
    if not SHA256.fullmatch(plan_digest):
        raise Operational("REFUSED", "plan digest must be a lowercase SHA-256 hex value")
    root = ensure_root(repo)
    info = repo_info(repo)
    candidates: list[dict] = []
    for entry in sorted(os.scandir(root), key=lambda row: row.name):
        if entry.name == ".locks":
            continue
        if not entry.is_dir(follow_symlinks=False):
            raise TrustFailure(f"unexpected non-directory entry in run root: {entry.path}")
        if not SAFE_ID.fullmatch(entry.name) or not entry.name.strip("."):
            raise TrustFailure(f"unsafe run entry name: {entry.path}")
        validate_private_dir(entry.path)
        doc = read_private_json(os.path.join(entry.path, "manifest.json"))
        if doc.get("schema_version") != SCHEMA_VERSION or doc.get("run_id") != entry.name:
            raise TrustFailure(f"manifest schema or run identity mismatch: {entry.path}")
        repository = doc.get("repository")
        source = doc.get("source")
        if not isinstance(repository, dict) or not isinstance(source, dict):
            raise TrustFailure(f"manifest repository or source record is malformed: {entry.path}")
        if (
            repository.get("identity_digest") != info["identity_digest"]
            or repository.get("toplevel") != info["toplevel"]
        ):
            continue
        if source.get("kind") != "plan" or source.get("digest") != plan_digest:
            continue
        previous_root = os.environ.get("ROCKETCLAW_WORK_RUNS_ROOT")
        os.environ["ROCKETCLAW_WORK_RUNS_ROOT"] = root
        try:
            validate_repo(doc)
            if unfinished_run(doc, info["commit_id"]):
                candidates.append({
                    "run_id": entry.name,
                    "updated_at": doc.get("updated_at"),
                    "recovery_path": entry.path,
                    "unit_states": {uid: unit.get("state") for uid, unit in doc["units"].items()},
                })
        finally:
            if previous_root is None:
                os.environ.pop("ROCKETCLAW_WORK_RUNS_ROOT", None)
            else:
                os.environ["ROCKETCLAW_WORK_RUNS_ROOT"] = previous_root
    if not candidates:
        raise Operational(
            "NOT_FOUND",
            "no unfinished run matches repository, workspace, and plan digest",
            {"candidates": []},
        )
    if len(candidates) > 1:
        raise Operational("AMBIGUOUS", "multiple unfinished runs match; pass --run-id", {"candidates": candidates})
    return candidates[0]["run_id"], candidates


def resolve_resume_run(args) -> str:
    if args.run_id:
        if args.repo or args.plan_digest:
            raise Operational("REFUSED", "resume accepts --run-id alone or both --repo and --plan-digest")
        return safe_id(args.run_id, "run id")
    if not args.repo or not args.plan_digest:
        raise Operational("REFUSED", "resume requires --run-id or both --repo and --plan-digest")
    run_id, _ = discover_resume_run(args.repo, args.plan_digest)
    os.environ["ROCKETCLAW_WORK_RUNS_ROOT"] = runs_root(args.repo)
    return run_id


def retained_worker_blocker(run_id: str, unit_id: str, error: Operational) -> dict | None:
    if error.word != "BLOCKED" or str(error) != "worker returned a host-resolvable blocker":
        return None
    with locked_manifest(run_id) as doc:
        unit = doc["units"].get(unit_id)
        if not unit or unit.get("state") not in {"authoring", "authored"}:
            return None
        attempt = find_attempt(unit)
        receipt = attempt.get("terminal_receipt")
        if (
            attempt.get("process_state") != "done"
            or attempt.get("terminal_validation_failure") is not None
            or not isinstance(receipt, dict)
            or receipt.get("terminal_status") != "blocked"
        ):
            return None
        blocker = {
            "unit_id": unit_id,
            "terminal_status": "blocked",
            "summary": receipt.get("summary", ""),
            "terminal_receipt": receipt,
            "recovery_path": os.path.join(run_dir(run_id), "units", unit_id),
        }
    detail = error.detail
    if detail.get("unit_id") == unit_id and detail.get("terminal_receipt") == receipt:
        return blocker
    return None


def resume_terminalize(run_id: str, unit_id: str) -> list[dict]:
    try:
        transport = terminalize(run_id, unit_id)
    except Operational as exc:
        blocker = retained_worker_blocker(run_id, unit_id, exc)
        if blocker is None:
            raise
        return [{
            "unit_id": unit_id,
            "action": "worker-blocker-retained",
            "terminal_status": blocker["terminal_status"],
            "summary": blocker["summary"],
            "recovery_path": blocker["recovery_path"],
        }]
    return [{"unit_id": unit_id, "action": "terminalized", "transport": transport["commit_id"]}]


def resume_monitor(run_id: str, unit_id: str) -> list[dict]:
    evidence = sync_job(run_id, unit_id)
    actions = [{"unit_id": unit_id, "action": "monitored", "process_state": evidence["process_state"]}]
    if evidence["process_state"] == "done":
        actions.extend(resume_terminalize(run_id, unit_id))
    return actions


def resolve_unit_recovery_blockers(run_id: str, unit_id: str, reason: str | None = None) -> None:
    with locked_manifest(run_id, write=True) as doc:
        resolved = 0
        for blocker in doc.get("blockers", []):
            if (
                blocker.get("unit_id") == unit_id
                and blocker.get("retain_integration_lock") is True
                and (reason is None or blocker.get("reason") == reason)
                and not blocker.get("resolved_at")
            ):
                blocker["resolved_at"] = now_iso()
                blocker["resolved_by"] = "resume"
                resolved += 1
        if resolved:
            event(doc, "recovery-blockers-resolved", unit_id, {"count": resolved})


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
            or not isinstance(attempt.get("lock_unit_id"), str)
            or not SAFE_ID.fullmatch(attempt["lock_unit_id"])
        ):
            raise TrustFailure("manifest plan-wide verification attempt identity or state is malformed")
    return attempts


def pending_plan_wide_verification(doc: dict, lock: dict) -> dict | None:
    attempts = plan_wide_verification_attempts(doc)
    pending = [
        attempt for attempt in attempts
        if attempt.get("status") == "pending"
        and attempt.get("integration_lock_nonce") == lock.get("nonce")
        and attempt.get("lock_unit_id") == lock.get("unit_id")
    ]
    if len(pending) > 1:
        raise TrustFailure("multiple pending plan-wide verification attempts share one integration lock")
    return pending[0] if pending else None


def receipted_plan_wide_verification(doc: dict, lock: dict) -> dict | None:
    attempts = plan_wide_verification_attempts(doc)
    recorded = [
        attempt for attempt in attempts
        if attempt.get("status") == "receipt-recorded"
        and attempt.get("integration_lock_nonce") == lock.get("nonce")
        and attempt.get("lock_unit_id") == lock.get("unit_id")
    ]
    if len(recorded) > 1:
        raise TrustFailure("multiple receipted plan-wide verification attempts share one integration lock")
    if not recorded:
        return None
    evidence_digest = recorded[0].get("evidence_digest")
    if not isinstance(evidence_digest, str) or not SHA256.fullmatch(evidence_digest):
        raise TrustFailure("plan-wide verification attempt receipt digest is malformed")
    verifications = doc.get("verifications", [])
    if not isinstance(verifications, list) or any(not isinstance(receipt, dict) for receipt in verifications):
        raise TrustFailure("manifest verification receipts are malformed")
    receipts = [receipt for receipt in verifications if receipt.get("evidence_digest") == evidence_digest]
    if len(receipts) != 1:
        raise TrustFailure("plan-wide verification receipt is missing or duplicated")
    return recorded[0]


def plan_wide_blocker_retains_lock(doc: dict, lock: dict) -> bool:
    return any(
        blocker.get("unit_id") is None
        and blocker.get("retain_integration_lock") is True
        and blocker.get("integration_lock_nonce") == lock.get("nonce")
        and not blocker.get("resolved_at")
        for blocker in doc.get("blockers", [])
    )


def resume_finalize_committed(run_id: str, unit_id: str) -> list[dict]:
    with locked_manifest(run_id) as doc:
        unit = doc["units"][unit_id]
        state = unit["state"]
        lock = doc.get("integration_lock")
        pending_plan_verification = pending_plan_wide_verification(doc, lock) if lock else None
        receipted_plan_verification = receipted_plan_wide_verification(doc, lock) if lock else None
        retained_plan_lock = bool(lock and plan_wide_blocker_retains_lock(doc, lock))
        cleanup = unit.get("cleanup") or {}
        artifacts_pruned = cleanup.get("artifacts_pruned") is True
    if state in {"cleaned", "native-completed"}:
        actions: list[dict] = []
        if cleanup and not artifacts_pruned:
            remove_finalized_artifacts(run_id, unit_id)
            actions.append({"unit_id": unit_id, "action": "artifact-cleanup-reconciled"})
        if lock and lock.get("unit_id") == unit_id:
            if pending_plan_verification:
                raise Operational(
                    "BLOCKED",
                    "pending plan-wide verification retains the canonical integration lock",
                    {
                        "unit_id": unit_id,
                        "verification_attempt_id": pending_plan_verification.get("attempt_id"),
                        "retain_integration_lock": True,
                    },
                )
            if retained_plan_lock:
                raise Operational(
                    "BLOCKED",
                    "plan-wide verification blocker retains the canonical integration lock",
                    {"unit_id": unit_id, "retain_integration_lock": True},
                )
            if state == "native-completed" and plan_wide_verification_attempts(doc) and not receipted_plan_verification:
                raise Operational(
                    "BLOCKED",
                    "native-completed unit retains the canonical integration lock without a plan-wide verification receipt",
                    {"unit_id": unit_id, "retain_integration_lock": True},
                )
            integration_release(run_id, unit_id, lock["nonce"])
            actions.append({"unit_id": unit_id, "action": "integration-release-reconciled"})
        return actions
    canonical_change = unit.get("integration", {}).get("canonical_change")
    if state != "described" or not isinstance(canonical_change, dict):
        raise Operational("BLOCKED", "described-unit recovery lacks an accepted canonical change")
    if lock is None:
        lock_token = cmd_integration_acquire(
            SimpleNamespace(run_id=run_id, unit_id=unit_id, resume=False)
        )[1]["lock_token"]
    elif lock.get("unit_id") == unit_id:
        lock_token = lock["nonce"]
        with locked_manifest(run_id) as doc:
            validate_lock(doc, unit_id, lock_token)
    else:
        raise Operational("BLOCKED", "another unit holds the canonical integration lock")
    actions = []
    if unit.get("wave", {}).get("id"):
        cmd_wave_advance(SimpleNamespace(
            run_id=run_id,
            unit_id=unit_id,
            lock_token=lock_token,
            canonical_revision=canonical_change["commit_id"],
        ))
        actions.append({
            "unit_id": unit_id,
            "action": "wave-advance-reconciled",
            "revision": canonical_change["commit_id"],
        })
    cmd_cleanup(SimpleNamespace(
        run_id=run_id,
        unit_id=unit_id,
        abandon=False,
        expect_transport=None,
        expect_job=None,
    ))
    integration_release(run_id, unit_id, lock_token)
    resolve_unit_recovery_blockers(run_id, unit_id)
    actions.append({
        "unit_id": unit_id,
        "action": "described-unit-finalized",
        "revision": canonical_change["commit_id"],
    })
    return actions


def cmd_resume(args) -> tuple[str, dict]:
    run_id = resolve_resume_run(args)
    actions: list[dict] = []
    with locked_manifest(run_id) as doc:
        validate_repo(doc)
        unit_ids = list(doc["units"])
        claim = doc.get("integration_lock")
        releasing = dict(claim) if isinstance(claim, dict) and claim.get("phase") == "releasing" else None
        orphan_unit = None
        orphan_path = integration_lock_path(doc)
        if claim is None and os.path.lexists(orphan_path):
            orphan = read_integration_lock(orphan_path)
            candidate = orphan.get("unit_id")
            if orphan.get("run_id") != run_id or not isinstance(candidate, str) or candidate not in doc["units"]:
                raise Operational(
                    "BLOCKED",
                    "external integration lock does not belong to this run/unit",
                    {"owner_run": orphan.get("run_id"), "owner_unit": candidate},
                )
            validated_lock_nonce(doc, candidate, orphan)
            orphan_unit = candidate
    if releasing:
        integration_release(run_id, releasing["unit_id"], releasing["nonce"])
        actions.append({"unit_id": releasing["unit_id"], "action": "integration-release-reconciled"})
    if orphan_unit:
        token = cmd_integration_acquire(SimpleNamespace(
            run_id=run_id,
            unit_id=orphan_unit,
            resume=True,
            recover_only=True,
        ))[1]["lock_token"]
        actions.append({"unit_id": orphan_unit, "action": "integration-lock-adopted", "lock_token": token})
    for uid in unit_ids:
        with locked_manifest(run_id) as doc:
            unit = doc["units"][uid]
            state = unit["state"]
            attempt = find_attempt(unit)
            lock = doc.get("integration_lock")
        if state == "queued" and not attempt.get("job_id"):
            matches = matching_runner_jobs(run_id, unit)
            if len(matches) > 1:
                raise Operational("AMBIGUOUS", f"multiple runner jobs match queued unit {uid}")
            if len(matches) == 1:
                with locked_manifest(run_id, write=True) as current:
                    current_unit = current["units"][uid]
                    current_attempt = find_attempt(current_unit)
                    if current_attempt.get("job_id") not in (None, matches[0]):
                        raise Operational("AMBIGUOUS", "attempt was concurrently bound")
                    current_attempt["job_id"] = matches[0]
                    current_unit["state"] = "authoring"
                    event(current, "job-adopted", uid, {"job_id": matches[0]})
                actions.append({"unit_id": uid, "action": "job-adopted", "job_id": matches[0]})
                actions.extend(resume_monitor(run_id, uid))
        elif state == "authoring" and attempt.get("job_id"):
            actions.extend(resume_monitor(run_id, uid))
        elif state == "authored":
            actions.extend(resume_terminalize(run_id, uid))
        elif state == "restoring" and lock and lock.get("unit_id") == uid:
            if not restore(run_id, uid, lock["nonce"]):
                raise Operational("BLOCKED", "exact pre-squash preservation could not be proven")
            integration_release(run_id, uid, lock["nonce"])
            resolve_unit_recovery_blockers(
                run_id,
                uid,
                reason="integration failed and exact restoration could not be proven",
            )
            actions.append({
                "unit_id": uid,
                "action": "restored",
                "canonical_preserved": True,
                "integration_lock_released": True,
            })
        elif state == "preserved" and lock and lock.get("unit_id") == uid:
            validate_lock(doc, uid, lock["nonce"])
            restore_evidence = unit.get("integration", {}).get("restore")
            pre_fold = unit.get("integration", {}).get("pre_fold")
            if (
                not isinstance(restore_evidence, dict)
                or restore_evidence.get("exact") is not True
                or not isinstance(pre_fold, dict)
            ):
                raise Operational("BLOCKED", "preserved-unit recovery lacks exact restoration evidence")
            actual = snapshot(doc["repository"]["toplevel"])
            if actual.get("change_id") != pre_fold.get("change_id") or actual.get("commit_id") != pre_fold.get("commit_id"):
                raise Operational("BLOCKED", "canonical workspace no longer matches the exact restored snapshot")
            integration_release(run_id, uid, lock["nonce"])
            resolve_unit_recovery_blockers(run_id, uid)
            actions.append({"unit_id": uid, "action": "integration-release-reconciled"})
        elif state == "integration-pending" and not unit.get("integration") and lock and lock.get("unit_id") == uid:
            validate_lock(doc, uid, lock["nonce"])
            integration_release(run_id, uid, lock["nonce"])
            actions.append({"unit_id": uid, "action": "preflight-lock-released"})
        elif state in {"integration-pending", "integrated"} and unit.get("integration") and lock and lock.get("unit_id") == uid:
            validate_lock(doc, uid, lock["nonce"])
            if not restore(run_id, uid, lock["nonce"]):
                raise Operational("BLOCKED", "exact pre-squash preservation could not be proven")
            integration_release(run_id, uid, lock["nonce"])
            actions.append({
                "unit_id": uid,
                "action": "inflight-squash-restored",
                "canonical_preserved": True,
                "integration_lock_released": True,
            })
        elif state == "verified" and lock and lock.get("unit_id") == uid:
            validate_lock(doc, uid, lock["nonce"])
            repo = doc["repository"]["toplevel"]
            pending = unit.get("integration", {}).get("pending_description")
            current = snapshot(repo)
            parent = revision(repo, "@-") if current["working_copy_empty"] else None
            if pending and current["working_copy_empty"] and parent and parent["description"] == pending:
                cmd_mark_described(SimpleNamespace(run_id=run_id, unit_id=uid, lock_token=lock["nonce"]))
                actions.append({"unit_id": uid, "action": "description-reconciled"})
            elif pending and current["change_id"] == unit["integration"]["pre_fold"]["change_id"] and current["description"] == pending:
                jj(repo, "new")
                cmd_mark_described(SimpleNamespace(run_id=run_id, unit_id=uid, lock_token=lock["nonce"]))
                actions.append({"unit_id": uid, "action": "description-advance-reconciled"})
            else:
                if not restore(run_id, uid, lock["nonce"]):
                    raise Operational("BLOCKED", "exact pre-squash preservation could not be proven")
                integration_release(run_id, uid, lock["nonce"])
                actions.append({
                    "unit_id": uid,
                    "action": "verified-change-restored",
                    "canonical_preserved": True,
                    "integration_lock_released": True,
                })
                continue
            actions.extend(resume_finalize_committed(run_id, uid))
        elif state in {"described", "cleaned", "native-completed"}:
            actions.extend(resume_finalize_committed(run_id, uid))
    return "RESUMED", {"run_id": run_id, "actions": actions, "redispatched": False, "applied": False}


def fallback_basis(doc: dict, unit: dict) -> tuple[str, dict]:
    if unit.get("state") == "integration-pending" and unit.get("transport", {}).get("commit_id"):
        raise Operational("REFUSED", "pinned worker change must be reconciled rather than bypassed by fallback")
    attempt = find_attempt(unit)
    process_state = attempt.get("process_state")
    if process_state == "done" and attempt.get("terminal_validation_failure"):
        validate_terminal_validation_failure(doc["run_id"], unit, attempt)
        snap = snapshot(doc["repository"]["toplevel"])
        allowed_revisions = set(unit.get("wave", {}).get("allowed_revisions", []))
        if (
            snap["commit_id"] not in allowed_revisions
            and not dependency_advanced_revision(doc, unit, snap["commit_id"])
        ) or not snap["working_copy_empty"] or snap["conflicted"]:
            raise Operational("BLOCKED", "canonical workspace diverged or is not empty; native fallback is not safe")
        return "terminal-validation-failure", attempt
    if process_state in TERMINAL_PROCESS - {"done"} or (
        process_state == "never-started" and attempt.get("job_id")
    ):
        snap = snapshot(doc["repository"]["toplevel"])
        allowed_revisions = set(unit.get("wave", {}).get("allowed_revisions", []))
        if (
            snap["commit_id"] not in allowed_revisions
            and not dependency_advanced_revision(doc, unit, snap["commit_id"])
        ) or not snap["working_copy_empty"] or snap["conflicted"]:
            raise Operational("BLOCKED", "canonical workspace diverged or is not empty; native fallback is not safe")
        return str(attempt.get("fallback", {}).get("reason") or process_state), attempt
    restore_evidence = unit.get("integration", {}).get("restore")
    if unit.get("state") == "preserved" and restore_evidence and restore_evidence.get("exact") is True:
        if doc.get("integration_lock"):
            raise Operational("REFUSED", "release the integration lock after exact restoration before fallback")
        actual = snapshot(doc["repository"]["toplevel"])
        expected = unit["integration"].get("pre_fold")
        if (
            not isinstance(expected, dict)
            or actual.get("change_id") != expected.get("change_id")
            or actual.get("commit_id") != expected.get("commit_id")
            or not actual["working_copy_empty"]
        ):
            raise Operational("BLOCKED", "canonical workspace no longer matches the exact restored snapshot")
        return "canonical-attempt-preserved", attempt
    if process_state == "running":
        raise Operational("REFUSED", "a live attempt still owns implementation; fallback is not authorized")
    if process_state == "done":
        raise Operational("REFUSED", "successful worker output must be reconciled rather than bypassed by fallback")
    raise Operational("REFUSED", "no authoritative terminal or exactly restored attempt authorizes fallback")


def cmd_claim_fallback(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        should_sync = bool(attempt.get("job_id")) and unit.get("state") == "authoring"
    if should_sync:
        sync_job(args.run_id, args.unit_id)

    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        fallback = attempt.setdefault("fallback", {})
        fallback.setdefault("completed", None)
        claimed = fallback.get("claimed")
        if claimed:
            return "FALLBACK_ALREADY_AUTHORIZED", {
                "unit_id": args.unit_id,
                "start_native": False,
                "reason": claimed["reason"],
                "claim": claimed,
            }
        validate_dependencies_ready(doc, unit)
        reason, attempt = fallback_basis(doc, unit)
        claim_snapshot = snapshot(doc["repository"]["toplevel"])
        wave = unit.get("wave", {})
        if wave.get("id"):
            validate_wave_order(doc, unit)
            allowed_revisions = wave.get("allowed_revisions", [])
            if not allowed_revisions or (
                claim_snapshot["commit_id"] != allowed_revisions[-1]
                and not dependency_advanced_revision(doc, unit, claim_snapshot["commit_id"])
            ):
                raise Operational("BLOCKED", "native fallback must start from the latest recorded wave revision")
        mode = doc.get("binding", {}).get("mode")
        if mode == "require":
            if args.caller_mode == "headless":
                raise Operational(
                    "BLOCKED",
                    "required external route terminated; headless callers cannot choose native fallback",
                    {"unit_id": args.unit_id, "reason": reason},
                )
            if not args.confirm_native:
                raise Operational(
                    "CHOICE_REQUIRED",
                    "required external route terminated; ask whether to continue natively",
                    {"unit_id": args.unit_id, "reason": reason},
                )
        elif mode != "prefer":
            raise Operational("REFUSED", f"binding mode {mode!r} does not authorize native fallback")
        claim = {
            "at": now_iso(),
            "reason": reason,
            "caller_mode": args.caller_mode,
            "mode": mode,
            "confirmed_native": bool(args.confirm_native),
            "canonical_revision_id": claim_snapshot["commit_id"],
        }
        fallback.update({"eligible": False, "reason": reason, "claimed": claim})
        event(doc, "native-fallback-authorized", args.unit_id, {
            "reason": reason,
            "mode": mode,
            "caller_mode": args.caller_mode,
        })
        return "FALLBACK_AUTHORIZED", {
            "unit_id": args.unit_id,
            "start_native": True,
            "reason": reason,
            "claim": claim,
        }


def validate_fallback_ancestry(doc: dict, unit: dict, accepted_revision: str) -> None:
    required: list[dict] = []
    dependency_ids = set(unit.get("dependencies", []))
    for dependency_id in unit.get("dependencies", []):
        dependency = doc.get("units", {}).get(dependency_id)
        accepted = unit_accepted_revision(dependency)
        if accepted is None:
            raise Operational(
                "BLOCKED",
                "unit dependency completion evidence changed before native fallback completion",
                {"unit_id": unit["unit_id"], "dependency_id": dependency_id},
            )
        required.append({"kind": "dependency", "unit_id": dependency_id, "revision": accepted})

    wave = unit.get("wave", {})
    if wave.get("id"):
        wave_members(doc, unit)
        base = wave.get("base")
        for candidate in wave.get("allowed_revisions", []):
            if candidate != base:
                required.append({"kind": "wave-revision", "revision": candidate})

    represented = {item["revision"] for item in required}
    for accepted_unit_id in sorted(doc.get("units", {})):
        if accepted_unit_id == unit["unit_id"] or accepted_unit_id in dependency_ids:
            continue
        accepted = unit_accepted_revision(doc["units"][accepted_unit_id])
        if accepted is None or accepted in represented:
            continue
        required.append({"kind": "accepted-unit", "unit_id": accepted_unit_id, "revision": accepted})
        represented.add(accepted)

    missing = [
        item for item in required
        if not revision_contains(doc["repository"]["toplevel"], item["revision"], accepted_revision)
    ]
    if missing:
        raise Operational(
            "BLOCKED",
            "accepted native fallback revision does not contain every controller-accepted prerequisite",
            {
                "unit_id": unit["unit_id"],
                "accepted_revision": accepted_revision,
                "missing_ancestry": missing,
            },
        )


def cmd_complete_fallback(args) -> tuple[str, dict]:
    if not SHA256.fullmatch(args.evidence_digest):
        raise Operational("REFUSED", "native fallback evidence digest must be lowercase SHA-256 hex")
    summary = args.summary.strip()
    if not summary or "\0" in summary or len(summary.encode()) > 1024:
        raise Operational("REFUSED", "native fallback summary must be non-empty and at most 1024 bytes")
    if not REVISION_ID.fullmatch(args.accepted_revision):
        raise Operational("REFUSED", "native fallback accepted revision must be a Jujutsu revision id")

    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        fallback = attempt.get("fallback")
        claim = fallback.get("claimed") if isinstance(fallback, dict) else None
        if not isinstance(claim, dict):
            raise Operational("REFUSED", "native fallback completion requires an existing claim")
        if fallback.get("completed") is not None or unit.get("state") == "native-completed":
            raise Operational("REFUSED", "native fallback completion was already recorded")
        claim_mode = claim.get("mode")
        if claim_mode not in {"prefer", "require"}:
            raise Operational("REFUSED", "native fallback completion requires an authorized prefer or require claim")
        if claim_mode == "require" and not (
            claim.get("caller_mode") == "interactive" and claim.get("confirmed_native") is True
        ):
            raise Operational(
                "REFUSED",
                "require-mode native fallback completion requires explicit interactive confirmation",
            )
        if doc.get("integration_lock") is not None:
            raise Operational("REFUSED", "release the integration lock before completing native fallback")
        if not info["working_copy_empty"] or info["conflicted"]:
            raise Operational(
                "BLOCKED",
                "advance to an empty conflict-free working-copy change before completing native fallback",
            )
        accepted = revision(info["toplevel"], "@-")
        if accepted["commit_id"] != args.accepted_revision:
            raise Operational(
                "BLOCKED",
                "accepted native fallback revision does not match the parent of the empty working-copy change",
            )
        description = accepted["description"].strip()
        if not description or "\0" in description:
            raise Operational(
                "REFUSED",
                f"change description must be non-empty and NUL-free. {DESCRIPTION_RULE} {DESCRIPTION_PRECEDENCE}",
            )
        base = unit.get("workspace", {}).get("base")
        if not isinstance(base, str) or not revision_contains(info["toplevel"], base, args.accepted_revision):
            raise Operational("BLOCKED", "accepted native fallback revision does not descend from the recorded unit base")
        validate_fallback_ancestry(doc, unit, args.accepted_revision)

        wave = unit.get("wave", {})
        changed = changed_paths(info["toplevel"], claim["canonical_revision_id"], args.accepted_revision)
        advanced: list[str] = []
        if wave.get("id"):
            validate_wave_order(doc, unit)
            claim_revision = claim.get("canonical_revision_id")
            allowed_revisions = wave.get("allowed_revisions", [])
            if (
                not isinstance(claim_revision, str)
                or not allowed_revisions
                or claim_revision != allowed_revisions[-1]
                or not revision_contains(info["toplevel"], claim_revision, args.accepted_revision)
            ):
                raise Operational(
                    "BLOCKED",
                    "native fallback completion does not extend the latest recorded wave revision",
                )
            validate_wave_collisions(
                doc,
                unit,
                overrides={unit["unit_id"]: set(changed)},
                require_complete=False,
            )
            members = wave_members(doc, unit)
            validate_wave_advancement(members, unit, claim_revision, args.accepted_revision)

        completion = {
            "at": now_iso(),
            "base": base,
            "accepted_revision_id": args.accepted_revision,
            "accepted_change_id": accepted["change_id"],
            "evidence_digest": args.evidence_digest,
            "summary": summary,
            "claim": dict(claim),
            "changed_paths": changed,
        }
        fallback["completed"] = completion
        unit["state"] = "native-completed"
        doc["canonical"]["change_id"] = info["change_id"]
        doc["canonical"]["bookmark_state_sha256"] = info["bookmark_state_sha256"]
        if wave.get("id"):
            advanced = advance_wave_allowed_revisions(members, wave["position"], args.accepted_revision)
            event(doc, "wave-advanced", args.unit_id, {
                "canonical_revision": args.accepted_revision,
                "eligible_siblings": advanced,
            })
        event(doc, "native-fallback-completed", args.unit_id, {
            "accepted_revision_id": args.accepted_revision,
            "evidence_digest": args.evidence_digest,
        })
        return "FALLBACK_COMPLETED", {
            "unit_id": args.unit_id,
            "completion": completion,
            "eligible_siblings": advanced,
        }


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
    proc = subprocess.run(
        [sys.executable, runner, "reap", "--skill", "ce-work", job_dir],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise Operational("BLOCKED", f"runner reap failed: {proc.stderr.decode('utf-8', 'replace').strip()}")
    evidence = sync_job(args.run_id, args.unit_id)
    return "REAPED", {
        "unit_id": args.unit_id,
        **evidence,
        "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id),
    }


def remove_finalized_artifacts(run_id: str, unit_id: str) -> None:
    """Prune bulky controller-owned artifacts only after a unit is finalized."""
    with locked_manifest(run_id) as doc:
        unit = doc["units"].get(unit_id)
        cleanup = unit.get("cleanup") if unit else None
        if (
            not unit
            or unit.get("state") not in {"cleaned", "native-completed"}
            or not isinstance(cleanup, dict)
        ):
            raise Operational("REFUSED", "artifact pruning requires a finalized unit with recorded cleanup")
        attempt_job_ids = [
            attempt.get("job_id") for attempt in unit.get("attempts", []) if attempt.get("job_id")
        ]
        authorization_paths = [
            attempt.get("authorization_path")
            for attempt in unit.get("attempts", [])
            if attempt.get("authorization_path")
        ]
        packet_path = unit.get("packet", {}).get("path")
        result_dir = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")
        root = run_dir(run_id)
    paths = [(packet_path, "file"), (result_dir, "dir")]
    paths.extend((authorization_path, "file") for authorization_path in authorization_paths)
    paths.extend((runner_job_dir(run_id, job_id), "dir") for job_id in attempt_job_ids)
    for candidate, kind in paths:
        if not candidate or not os.path.lexists(candidate):
            continue
        absolute = os.path.abspath(candidate)
        if os.path.commonpath([root, absolute]) != root or absolute == root:
            raise Operational("BLOCKED", "finalized artifact path escaped the owned run")
        if kind == "file":
            read_private(absolute, MAX_RESULT_BYTES)
            os.unlink(absolute)
        else:
            validate_private_dir(absolute)
            shutil.rmtree(absolute)
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        unit["packet"]["retained"] = False
        for attempt in unit.get("attempts", []):
            attempt["bulky_artifacts_retained"] = False
            attempt["authorization_retained"] = False
        unit["cleanup"]["artifacts_pruned"] = True
        unit["cleanup"]["artifact_cleanup_at"] = now_iso()
        event(doc, "finalized-artifacts-pruned", unit_id, {"job_count": len(attempt_job_ids)})


def retained_blocked_abandonment_receipt(run_id: str, unit: dict, attempt: dict) -> dict:
    recorded = attempt.get("terminal_receipt")
    if (
        unit.get("state") not in {"authoring", "authored"}
        or attempt.get("process_state") != "done"
        or attempt.get("terminal_validation_failure") is not None
        or not isinstance(recorded, dict)
        or recorded.get("terminal_status") != "blocked"
    ):
        raise Operational("REFUSED", "done output is not an exactly retained worker blocker")
    observed_process = process_evidence(runner_job_dir(run_id, attempt["job_id"]))["process_state"]
    if observed_process != "done":
        raise Operational("BLOCKED", "retained worker-blocker job evidence changed")
    observed_receipt = terminal_receipt(unit)
    if observed_receipt != recorded:
        raise Operational("BLOCKED", "retained worker-blocker receipt evidence changed")
    return {
        "kind": "retained-worker-blocker",
        "value": attempt["job_id"],
        "process_state": observed_process,
        "terminal_status": recorded["terminal_status"],
        "result_sha256": digest_bytes(read_private(
            os.path.join(os.path.dirname(unit["workspace"]["path"]), "result", "implementation-result.json"),
            MAX_RESULT_BYTES,
        )),
    }


def owned_workspace_path(run_id: str, unit_id: str, recorded_workspace: str) -> str:
    unit_root = os.path.join(run_dir(run_id), "units", unit_id)
    expected_workspace = os.path.join(unit_root, "workspace")
    if os.path.abspath(recorded_workspace) != expected_workspace:
        raise TrustFailure("manifest workspace path does not match the controller-owned unit workspace")
    validate_private_dir(unit_root)
    return expected_workspace


def remove_unregistered_owned_workspace(run_id: str, unit_id: str, recorded_workspace: str) -> None:
    expected_workspace = owned_workspace_path(run_id, unit_id, recorded_workspace)
    if not os.path.lexists(expected_workspace):
        return
    entry = os.lstat(expected_workspace)
    uid_getter = getattr(os, "geteuid", None) or getattr(os, "getuid", None)
    effective_uid = uid_getter() if uid_getter is not None else None
    if not stat.S_ISDIR(entry.st_mode) or stat.S_ISLNK(entry.st_mode):
        raise Operational("BLOCKED", "unregistered workspace path is not a real directory")
    if effective_uid is not None and entry.st_uid != effective_uid:
        raise Operational("BLOCKED", "unregistered workspace is not owned by the current user")
    shutil.rmtree(expected_workspace)
    if os.path.lexists(expected_workspace):
        raise Operational("BLOCKED", "unregistered workspace remained after cleanup")


def cmd_cleanup(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        cleanup_recorded = isinstance(unit.get("cleanup"), dict)
        if unit["state"] == "cleaned" or (unit["state"] == "native-completed" and cleanup_recorded):
            if unit.get("cleanup", {}).get("artifacts_pruned") is not True:
                pass
            else:
                return "CLEANED", {"unit_id": args.unit_id, "resumed": True}
    if unit["state"] == "cleaned" or (unit["state"] == "native-completed" and cleanup_recorded):
        remove_finalized_artifacts(args.run_id, args.unit_id)
        return "CLEANED", {"unit_id": args.unit_id, "resumed": True}
    with locked_manifest(args.run_id) as doc:
        unit = doc["units"][args.unit_id]
        attempt = find_attempt(unit)
        if attempt.get("process_state") == "running":
            raise Operational("REFUSED", "cannot cleanup a live worker")
        transport = unit.get("transport")
        transport_revision = transport.get("commit_id") if isinstance(transport, dict) else None
        abandonment_receipt = None
        if args.abandon:
            if transport_revision:
                if args.expect_transport != transport_revision:
                    raise Operational("REFUSED", "abandon cleanup requires exact pinned transport revision")
                abandonment_receipt = {"kind": "transport", "value": transport_revision}
            else:
                terminal_failures = TERMINAL_PROCESS - {"done"}
                validation_failure = attempt.get("process_state") == "done" and attempt.get("terminal_validation_failure")
                if not attempt.get("job_id"):
                    raise Operational(
                        "REFUSED",
                        "transport-free cleanup requires an authoritative failed or reaped job",
                    )
                if args.expect_job != attempt["job_id"]:
                    raise Operational(
                        "REFUSED",
                        "transport-free cleanup requires the exact terminal job id",
                    )
                if validation_failure:
                    abandonment_receipt = {
                        "kind": "terminal-validation-failure",
                        "value": attempt["job_id"],
                        "process_state": "done",
                    }
                elif attempt.get("process_state") == "done":
                    abandonment_receipt = retained_blocked_abandonment_receipt(args.run_id, unit, attempt)
                else:
                    if attempt.get("process_state") not in terminal_failures:
                        raise Operational(
                            "REFUSED",
                            "transport-free cleanup requires an authoritative failed or reaped job",
                        )
                    observed = process_evidence(runner_job_dir(args.run_id, attempt["job_id"]))["process_state"]
                    if observed != attempt["process_state"] or observed not in terminal_failures:
                        raise Operational("BLOCKED", "terminal job evidence changed; refusing cleanup")
                    abandonment_receipt = {
                        "kind": "terminal-job",
                        "value": attempt["job_id"],
                        "process_state": observed,
                    }
        elif unit["state"] not in {"described", "native-completed"}:
            raise Operational("REFUSED", "unaccepted output is retained unless explicitly abandoned")
        workspace_record = unit["workspace"]
        repo = doc["repository"]["toplevel"]
    workspace = owned_workspace_path(args.run_id, args.unit_id, workspace_record["path"])
    with locked_manifest(args.run_id, write=True) as doc:
        event(doc, "cleanup-intent", args.unit_id, {
            "workspace": workspace,
            "name": workspace_record["name"],
            "abandonment_receipt": abandonment_receipt,
        })
    jj(repo, "workspace", "forget", workspace_record["name"])
    registered = jj_text(repo, "workspace", "list", "-T", 'name ++ "\\n"').splitlines()
    if workspace_record["name"] in registered:
        raise Operational("BLOCKED", "isolated workspace remained registered after forget")
    remove_unregistered_owned_workspace(args.run_id, args.unit_id, workspace)
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        finalized_state = "native-completed" if unit["state"] == "native-completed" else "cleaned"
        unit["cleanup"] = {
            "at": now_iso(),
            "workspace_removed": True,
            "workspace_forgotten": True,
            "abandoned": bool(args.abandon),
            "abandonment_receipt": abandonment_receipt,
            "artifacts_pruned": False,
        }
        unit["state"] = finalized_state
        event(doc, "unit-cleaned", args.unit_id)
    test_fault("cleanup-before-artifact-prune")
    remove_finalized_artifacts(args.run_id, args.unit_id)
    return "CLEANED", {"unit_id": args.unit_id, "resumed": False}
