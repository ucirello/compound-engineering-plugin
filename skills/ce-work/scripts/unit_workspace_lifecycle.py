"""Resume, fallback, reap, and finalized-artifact lifecycle operations."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from types import SimpleNamespace

from unit_workspace_state import *
from unit_workspace_jobs import *
from unit_workspace_integration import *


def cmd_status(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        source = doc["source"]
        common = {"run_id": args.run_id, "revision": doc["revision"], "source": source, "integration_lock": doc.get("integration_lock"), "verifications": doc.get("verifications", []), "blockers": doc.get("blockers", [])}
        if args.unit_id:
            unit = doc["units"].get(args.unit_id)
            if not unit:
                raise Operational("REFUSED", "unknown unit")
            body = {**common, "unit": unit}
        else:
            body = {**common, "units": doc["units"], "recovery_path": locate_run_dir(args.run_id)}
    return "STATUS", body


def unfinished_run(doc: dict, canonical_commit: str) -> bool:
    units = doc.get("units")
    if not isinstance(units, dict) or not units:
        return True
    if any(not isinstance(unit, dict) or unit.get("state") not in UNIT_STATES for unit in units.values()):
        raise TrustFailure("manifest unit state is malformed")
    if any(unit.get("state") not in {"cleaned", "native-completed"} for unit in units.values()):
        return True
    accepted = accepted_unit_commit_snapshot(units)
    if accepted is None:
        return True
    receipts = doc.get("verifications", [])
    return not any(
        receipt.get("verification_exit") == 0
        and receipt.get("accepted_units") == accepted
        and all(is_ancestor(doc["repository"]["toplevel"], commit, canonical_commit) for commit in accepted.values())
        for receipt in receipts
        if isinstance(receipt, dict)
    )


def discover_resume_run(repo: str, plan_digest: str) -> tuple[str, list[dict]]:
    if not re.fullmatch(r"[0-9a-f]{64}", plan_digest):
        raise Operational("REFUSED", "plan digest must be a lowercase SHA-256 value")
    info = repo_info(repo)
    roots = [root for root in candidate_runs_roots(info["toplevel"]) if os.path.isdir(root)]
    if not roots:
        raise Operational("NOT_FOUND", "no unfinished run matches repository and plan digest", {"candidates": []})
    candidates: list[dict] = []
    seen: set[str] = set()
    for root in roots:
        real_root = os.path.realpath(root)
        if real_root in seen:
            continue
        seen.add(real_root)
        for entry in sorted(os.scandir(root), key=lambda item: item.path):
            if entry.name == ".locks":
                continue
            if not entry.is_dir(follow_symlinks=False) or not SAFE_ID.fullmatch(entry.name):
                raise TrustFailure(f"unsafe run-root entry: {entry.path}")
            raw = read_private_json(os.path.join(entry.path, "manifest.json"))
            if raw.get("schema_version") == 1:
                legacy_source = raw.get("source")
                legacy_plan = raw.get("plan", {})
                if legacy_source is None and isinstance(legacy_plan, dict):
                    legacy_source = {"kind": legacy_plan.get("kind", "plan"), "digest": legacy_plan.get("digest")}
                legacy_repo = raw.get("repository", {})
                if (
                    not isinstance(legacy_repo, dict)
                    or os.path.realpath(str(legacy_repo.get("toplevel", ""))) != info["toplevel"]
                    or not isinstance(legacy_source, dict)
                    or legacy_source.get("kind") != "plan"
                    or legacy_source.get("digest") != plan_digest
                ):
                    continue
            with locked_manifest(entry.name, directory=entry.path) as doc:
                repository = doc.get("repository", {})
                source = doc.get("source", {})
                if repository.get("identity_digest") != info["identity_digest"] or source.get("kind") != "plan" or source.get("digest") != plan_digest:
                    continue
                validate_source(doc)
                if unfinished_run(doc, info["commit"]):
                    candidates.append({"run_id": entry.name, "updated_at": doc.get("updated_at"), "recovery_path": entry.path, "unit_states": {key: value.get("state") for key, value in doc.get("units", {}).items()}})
    if not candidates:
        raise Operational("NOT_FOUND", "no unfinished run matches repository and plan digest", {"candidates": []})
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
    return discover_resume_run(args.repo, args.plan_digest)[0]


def retained_worker_blocker(run_id: str, unit_id: str, error: Operational) -> dict | None:
    if error.word != "BLOCKED" or str(error) != "worker returned a host-resolvable blocker":
        return None
    with locked_manifest(run_id) as doc:
        unit = doc["units"].get(unit_id)
        if not unit or unit.get("state") != "authored":
            return None
        attempt = find_attempt(unit)
        receipt = attempt.get("terminal_receipt")
        if attempt.get("process_state") != "done" or not isinstance(receipt, dict) or receipt.get("terminal_status") != "blocked":
            return None
        return {"unit_id": unit_id, "terminal_status": "blocked", "summary": receipt.get("summary", ""), "terminal_receipt": receipt, "recovery_path": os.path.join(locate_run_dir(run_id), "units", unit_id)}


def resolve_unit_recovery_blockers(run_id: str, unit_id: str) -> None:
    with locked_manifest(run_id, write=True) as doc:
        count = 0
        for blocker in doc.get("blockers", []):
            if blocker.get("unit_id") == unit_id and not blocker.get("resolved_at"):
                blocker["resolved_at"] = now_iso()
                blocker["resolved_by"] = "resume"
                count += 1
        if count:
            event(doc, "recovery-blockers-resolved", unit_id, {"count": count})


def cmd_resume(args) -> tuple[str, dict]:
    run_id = resolve_resume_run(args)
    actions: list[dict] = []
    with locked_manifest(run_id) as doc:
        validate_repo(doc)
        unit_ids = list(doc["units"])
    for unit_id in unit_ids:
        with locked_manifest(run_id) as doc:
            unit = doc["units"][unit_id]
            state = unit["state"]
            attempt = find_attempt(unit)
            lock = doc.get("integration_lock")
        if state == "queued" and not attempt.get("job_id"):
            matches = matching_runner_jobs(run_id, unit)
            if len(matches) > 1:
                raise Operational("AMBIGUOUS", f"multiple runner jobs match queued unit {unit_id}")
            if matches:
                with locked_manifest(run_id, write=True) as current:
                    current_attempt = find_attempt(current["units"][unit_id])
                    current_attempt["job_id"] = matches[0]
                    current["units"][unit_id]["state"] = "authoring"
                    event(current, "job-adopted", unit_id, {"job_id": matches[0]})
                actions.append({"unit_id": unit_id, "action": "job-adopted", "job_id": matches[0]})
        elif state == "authoring" and attempt.get("job_id"):
            evidence = sync_job(run_id, unit_id)
            actions.append({"unit_id": unit_id, "action": "monitored", "process_state": evidence["process_state"]})
            if evidence["process_state"] == "done":
                try:
                    transport = terminalize(run_id, unit_id)
                    actions.append({"unit_id": unit_id, "action": "terminalized", "transport": transport["change_id"]})
                except Operational as exc:
                    blocker = retained_worker_blocker(run_id, unit_id, exc)
                    if blocker is None:
                        raise
                    actions.append({"unit_id": unit_id, "action": "worker-blocker-retained", "recovery_path": blocker["recovery_path"]})
        elif state == "authored":
            try:
                transport = terminalize(run_id, unit_id)
                actions.append({"unit_id": unit_id, "action": "terminalized", "transport": transport["change_id"]})
            except Operational as exc:
                blocker = retained_worker_blocker(run_id, unit_id, exc)
                if blocker is None:
                    raise
                actions.append({"unit_id": unit_id, "action": "worker-blocker-retained", "recovery_path": blocker["recovery_path"]})
        elif state == "integration-pending" and lock and lock.get("unit_id") == unit_id:
            pre = unit.get("integration", {}).get("pre_fold")
            if pre is None:
                integration_release(run_id, unit_id, lock["nonce"])
                actions.append({"unit_id": unit_id, "action": "preflight-lock-released"})
            else:
                current = semantic_snapshot(doc["repository"]["toplevel"])
                integration = unit.get("integration", {})
                controller_states = [
                    candidate for candidate in (
                        integration.get("expected_apply"),
                        integration.get("applied", {}).get("snapshot") if isinstance(integration.get("applied"), dict) else None,
                    ) if isinstance(candidate, dict)
                ]
                if not same_exact_revision_state(current, pre) and not any(
                    same_exact_revision_state(current, candidate) for candidate in controller_states
                ):
                    raise Operational("BLOCKED", "canonical state changed during an interrupted integration; retain the lock for inspection")
                if not restore(run_id, unit_id, lock["nonce"]):
                    raise Operational("BLOCKED", "exact Jujutsu restoration could not be proven")
                integration_release(run_id, unit_id, lock["nonce"])
                actions.append({"unit_id": unit_id, "action": "preflight-state-recovered"})
        elif state == "verified" and lock and lock.get("unit_id") == unit_id:
            with locked_manifest(run_id) as current_doc:
                canonical = reconcile_commit(current_doc, current_doc["units"][unit_id])
            if canonical and canonical["description"].strip():
                with locked_manifest(run_id, write=True) as current_doc:
                    current_doc["units"][unit_id]["integration"]["canonical_change"] = canonical
                    current_doc["units"][unit_id]["state"] = "committed"
                    event(current_doc, "canonical-change-reconciled", unit_id, {"change": canonical["change_id"], "commit": canonical["commit"]})
                jj(doc["repository"]["toplevel"], "new")
                cmd_cleanup(SimpleNamespace(run_id=run_id, unit_id=unit_id, abandon=False, expect_transport=None, expect_job=None))
                integration_release(run_id, unit_id, lock["nonce"])
                actions.append({"unit_id": unit_id, "action": "accepted-change-reconciled", "canonical_change": canonical})
            else:
                if not restore(run_id, unit_id, lock["nonce"]):
                    raise Operational("BLOCKED", "exact Jujutsu restoration could not be proven")
                integration_release(run_id, unit_id, lock["nonce"])
                actions.append({"unit_id": unit_id, "action": "restored", "canonical_preserved": True})
        elif state in {"integrated", "restoring"} and lock and lock.get("unit_id") == unit_id:
            if not restore(run_id, unit_id, lock["nonce"]):
                raise Operational("BLOCKED", "exact Jujutsu restoration could not be proven")
            integration_release(run_id, unit_id, lock["nonce"])
            actions.append({"unit_id": unit_id, "action": "restored", "canonical_preserved": True})
        elif state == "preserved" and lock and lock.get("unit_id") == unit_id:
            integration_release(run_id, unit_id, lock["nonce"])
            actions.append({"unit_id": unit_id, "action": "integration-release-reconciled"})
        elif state == "committed":
            with locked_manifest(run_id) as current_doc:
                repo = current_doc["repository"]["toplevel"]
                accepted = current_doc["units"][unit_id].get("integration", {}).get("canonical_change", {})
            current_revision = revision_snapshot(repo)
            if current_revision["change_id"] == accepted.get("change_id"):
                jj(repo, "new")
                actions.append({"unit_id": unit_id, "action": "next-change-created"})
            elif accepted.get("commit") and not is_ancestor(repo, accepted["commit"], current_revision["commit"]):
                raise Operational("BLOCKED", "canonical workspace no longer descends from the accepted unit change")
            if lock is None:
                token = cmd_integration_acquire(SimpleNamespace(run_id=run_id, unit_id=unit_id, resume=False))[1]["lock_token"]
            elif lock.get("unit_id") == unit_id:
                token = lock["nonce"]
            else:
                raise Operational("BLOCKED", "another unit owns canonical integration")
            cmd_cleanup(SimpleNamespace(run_id=run_id, unit_id=unit_id, abandon=False, expect_transport=None, expect_job=None))
            integration_release(run_id, unit_id, token)
            resolve_unit_recovery_blockers(run_id, unit_id)
            actions.append({"unit_id": unit_id, "action": "accepted-unit-finalized"})
        elif state == "native-completed" and lock is None:
            completion = find_attempt(unit).get("fallback", {}).get("completed", {})
            current = revision_snapshot(doc["repository"]["toplevel"])
            if current["change_id"] == completion.get("accepted_change"):
                jj(doc["repository"]["toplevel"], "new")
                actions.append({"unit_id": unit_id, "action": "next-change-created"})
        elif state in {"cleaned", "native-completed"} and lock and lock.get("unit_id") == unit_id:
            integration_release(run_id, unit_id, lock["nonce"])
            actions.append({"unit_id": unit_id, "action": "integration-release-reconciled"})
    return "RESUMED", {"run_id": run_id, "actions": actions, "redispatched": False, "applied": False}


def fallback_basis(doc: dict, unit: dict) -> tuple[str, dict]:
    attempt = find_attempt(unit)
    state = attempt.get("process_state")
    if state == "running":
        raise Operational("REFUSED", "a live attempt still owns implementation")
    if state == "done" and not attempt.get("terminal_validation_failure") and unit.get("state") != "preserved":
        raise Operational("REFUSED", "successful worker output must be reconciled")
    if state in TERMINAL_PROCESS - {"done"} or attempt.get("terminal_validation_failure"):
        return str(attempt.get("fallback", {}).get("reason") or state or "terminal-validation-failure"), attempt
    if unit.get("state") == "preserved" and unit.get("integration", {}).get("restore", {}).get("exact") is True:
        return "canonical-attempt-preserved", attempt
    raise Operational("REFUSED", "no authoritative terminal or restored attempt authorizes fallback")


def cmd_claim_fallback(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        should_sync = bool(attempt.get("job_id")) and unit.get("state") == "authoring"
    if should_sync:
        sync_job(args.run_id, args.unit_id)
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"][args.unit_id]
        validate_dependencies_ready(doc, unit)
        attempt = find_attempt(unit)
        fallback = attempt.setdefault("fallback", {})
        if fallback.get("claimed"):
            return "FALLBACK_ALREADY_AUTHORIZED", {"unit_id": args.unit_id, "start_native": False, "reason": fallback["claimed"]["reason"], "claim": fallback["claimed"]}
        reason, _ = fallback_basis(doc, unit)
        mode = doc.get("binding", {}).get("mode")
        if mode not in {"prefer", "require"}:
            raise Operational("REFUSED", "binding does not authorize native fallback")
        snapshot = semantic_snapshot(doc["repository"]["toplevel"])
        if not snapshot["empty"] or snapshot["conflicted"]:
            raise Operational("BLOCKED", "canonical working-copy change is not safe for native fallback")
        claim = {"at": now_iso(), "reason": reason, "caller_mode": args.caller_mode, "mode": mode, "canonical_commit": snapshot["commit"], "canonical_change": snapshot["change_id"]}
        fallback.update({"eligible": False, "reason": reason, "claimed": claim})
        event(doc, "native-fallback-authorized", args.unit_id, {"reason": reason, "mode": mode})
    return "FALLBACK_AUTHORIZED", {"unit_id": args.unit_id, "start_native": True, "reason": reason, "claim": claim}


def validate_fallback_ancestry(doc: dict, unit: dict, accepted_commit: str) -> None:
    repo = doc["repository"]["toplevel"]
    required = [unit_accepted_commit(doc["units"][dependency]) for dependency in unit.get("dependencies", [])]
    missing = [commit for commit in required if commit is None or not is_ancestor(repo, commit, accepted_commit)]
    if missing:
        raise Operational("BLOCKED", "accepted native fallback change omits accepted prerequisites", {"missing_ancestry": missing})


def cmd_complete_fallback(args) -> tuple[str, dict]:
    if not re.fullmatch(r"[0-9a-f]{64}", args.evidence_digest):
        raise Operational("REFUSED", "native fallback evidence digest must be lowercase SHA-256")
    summary = args.summary.strip()
    if not summary or "\0" in summary or len(summary.encode()) > 1024:
        raise Operational("REFUSED", "native fallback summary must be non-empty and bounded")
    accepted_value = args.accepted_change
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        fallback = attempt.get("fallback")
        claim = fallback.get("claimed") if isinstance(fallback, dict) else None
        if not isinstance(claim, dict) or fallback.get("completed") is not None:
            raise Operational("REFUSED", "native fallback completion requires one unfinished claim")
        if doc.get("integration_lock") is not None:
            raise Operational("REFUSED", "release integration before completing native fallback")
        repo = doc["repository"]["toplevel"]
        snapshot = semantic_snapshot(repo)
        accepted_commit = resolve_revision(repo, accepted_value)
        if snapshot["commit"] != accepted_commit or snapshot["conflicted"]:
            raise Operational("BLOCKED", "accepted native fallback revision does not match the canonical working-copy change")
        if not snapshot["description"].strip():
            raise Operational("BLOCKED", f"accepted native fallback change has no description. {DESCRIPTION_GUIDANCE}")
        base = unit.get("workspace", {}).get("base")
        if not is_ancestor(repo, base, accepted_commit):
            raise Operational("BLOCKED", "accepted native fallback change does not descend from the recorded unit base")
        validate_fallback_ancestry(doc, unit, accepted_commit)
        changed = changed_paths(repo)
        wave = unit.get("wave", {})
        members = wave_members(doc, unit) if wave.get("id") else []
        if members:
            validate_wave_order(doc, unit)
            validate_wave_collisions(doc, unit, overrides={unit["unit_id"]: set(changed)}, require_complete=False)
            parent = claim.get("canonical_commit")
            if not isinstance(parent, str) or not is_ancestor(repo, parent, accepted_commit):
                raise Operational("BLOCKED", "native fallback does not extend its recorded canonical starting revision")
            validate_wave_advancement(members, unit, parent, accepted_commit)
        receipt = {"at": now_iso(), "base": base, "accepted_change": snapshot["change_id"], "accepted_commit": accepted_commit, "evidence_digest": args.evidence_digest, "summary": summary, "snapshot": snapshot, "claim": dict(claim), "changed_paths": changed}
        fallback["completed"] = receipt
        unit["state"] = "native-completed"
        advanced = advance_wave_allowed_revisions(members, wave["position"], accepted_commit) if members else []
        event(doc, "native-fallback-completed", args.unit_id, {"accepted_change": snapshot["change_id"], "accepted_commit": accepted_commit})
    jj(repo, "new")
    return "FALLBACK_COMPLETED", {"unit_id": args.unit_id, "completion": receipt, "eligible_siblings": advanced}


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
    proc = subprocess.run([sys.executable, runner, "reap", "--skill", "ce-work", job_dir], capture_output=True, check=False)
    if proc.returncode != 0:
        raise Operational("BLOCKED", f"runner reap failed: {proc.stderr.decode('utf-8', 'replace').strip()}")
    evidence = sync_job(args.run_id, args.unit_id)
    return "REAPED", {"unit_id": args.unit_id, **evidence, "recovery_path": os.path.join(locate_run_dir(args.run_id), "units", args.unit_id)}


def remove_finalized_artifacts(run_id: str, unit_id: str) -> None:
    with locked_manifest(run_id) as doc:
        unit = doc["units"].get(unit_id)
        if not unit or unit.get("state") not in {"cleaned", "native-completed"} or not isinstance(unit.get("cleanup"), dict):
            raise Operational("REFUSED", "artifact pruning requires a finalized unit")
        job_ids = [attempt.get("job_id") for attempt in unit.get("attempts", []) if attempt.get("job_id")]
        authorization_paths = [attempt.get("authorization_path") for attempt in unit.get("attempts", []) if attempt.get("authorization_path")]
        packet_path = unit.get("packet", {}).get("path")
        result_dir = os.path.join(os.path.dirname(unit["workspace"]["path"]), "result")
        root = locate_run_dir(run_id)
    paths = [(packet_path, "file"), (result_dir, "dir"), *[(path, "file") for path in authorization_paths], *[(runner_job_dir(run_id, value), "dir") for value in job_ids]]
    for candidate, kind in paths:
        if not candidate or not os.path.lexists(candidate):
            continue
        absolute = os.path.abspath(candidate)
        if os.path.commonpath([root, absolute]) != root or absolute == root:
            raise Operational("BLOCKED", "finalized artifact path escaped the owned run")
        if kind == "file":
            read_private(absolute, MAX_PACKET_BYTES)
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
        unit["cleanup"]["artifact_cleanup"] = {"at": now_iso(), "complete": True}
        event(doc, "finalized-artifacts-pruned", unit_id, {"job_count": len(job_ids)})


def cmd_cleanup(args) -> tuple[str, dict]:
    already_finalized = False
    needs_prune = False
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        if unit.get("state") in {"cleaned", "native-completed"} and isinstance(unit.get("cleanup"), dict):
            already_finalized = True
            needs_prune = not unit["cleanup"].get("artifact_cleanup", {}).get("complete")
        if already_finalized:
            attempt = None
            transport = None
            workspace = None
            workspace_name = None
            repo = None
        else:
            attempt = find_attempt(unit)
            if attempt.get("process_state") == "running":
                raise Operational("REFUSED", "cannot clean up a live worker")
            transport = unit.get("transport", {}).get("commit")
            if args.abandon:
                if transport and args.expect_transport != transport:
                    raise Operational("REFUSED", "abandon cleanup requires the exact transport commit id")
                if not transport and args.expect_job != attempt.get("job_id"):
                    raise Operational("REFUSED", "transport-free cleanup requires the exact terminal job id")
            elif unit.get("state") not in {"committed", "native-completed"}:
                raise Operational("REFUSED", "unaccepted output is retained unless explicitly abandoned")
            workspace = unit["workspace"]["path"]
            workspace_name = unit["workspace"]["name"]
            repo = doc["repository"]["toplevel"]
    if already_finalized:
        if needs_prune:
            remove_finalized_artifacts(args.run_id, args.unit_id)
        return "CLEANED", {"unit_id": args.unit_id, "resumed": True}
    with locked_manifest(args.run_id, write=True) as doc:
        event(doc, "cleanup-intent", args.unit_id, {"workspace": workspace, "workspace_name": workspace_name, "abandoned": bool(args.abandon)})
    with admin_lock(doc["repository"]["identity_digest"]):
        names = {row["name"] for row in workspace_rows(repo)}
        if workspace_name in names:
            jj(repo, "workspace", "forget", workspace_name)
            test_fault("cleanup-after-workspace-forget")
        if os.path.lexists(workspace):
            validate_private_dir(workspace)
            shutil.rmtree(workspace)
    if transport:
        jj(repo, "abandon", transport, check=False)
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        finalized = "native-completed" if unit.get("state") == "native-completed" else "cleaned"
        unit["cleanup"] = {"at": now_iso(), "workspace_removed": True, "transport_abandoned": bool(transport), "abandoned": bool(args.abandon), "artifact_cleanup": {"at": None, "complete": False}}
        unit["state"] = finalized
        event(doc, "unit-cleaned", args.unit_id)
    remove_finalized_artifacts(args.run_id, args.unit_id)
    return "CLEANED", {"unit_id": args.unit_id, "resumed": False}
