"""Status, recovery, fallback, reaping, and cleanup for Jujutsu unit runs."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from unit_workspace_state import *
from unit_workspace_jobs import find_attempt, sync_job, terminalize


def cmd_status(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        if args.unit_id:
            unit = doc["units"].get(args.unit_id)
            if not unit:
                raise Operational("REFUSED", "unknown unit")
            return "STATUS", {"run_id": args.run_id, "unit": unit, "integration_lock": doc.get("integration_lock")}
        return "STATUS", {
            "run_id": args.run_id,
            "revision": doc["revision"],
            "source": doc.get("source"),
            "workspace": doc.get("workspace"),
            "units": doc.get("units", {}),
            "integration_lock": doc.get("integration_lock"),
            "verifications": doc.get("verifications", []),
            "blockers": doc.get("blockers", []),
            "recovery_path": run_dir(args.run_id),
        }


def unfinished_run(doc: dict, canonical_revision: str) -> bool:
    units = doc.get("units", {})
    if not units:
        return True
    accepted = accepted_unit_revision_snapshot(units)
    if accepted is None:
        return True
    if not all(revision_is_ancestor(doc["repository"]["toplevel"], revision, canonical_revision) for revision in accepted.values()):
        return True
    return not any(receipt.get("status") == "passed" and receipt.get("accepted_unit_revisions") == accepted for receipt in doc.get("verifications", []))


def discover_resume_run(repo: str, plan_digest: str) -> tuple[str, list[dict]]:
    info = repo_info(repo)
    matches = []
    for root in candidate_runs_roots():
        if not os.path.isdir(root):
            continue
        for run_id in sorted(os.listdir(root)):
            if not SAFE_ID.fullmatch(run_id):
                continue
            try:
                with locked_manifest(run_id) as doc:
                    if (
                        doc.get("repository", {}).get("identity_digest") == info["identity_digest"]
                        and doc.get("workspace", {}).get("name") == info["workspace_name"]
                        and doc.get("source", {}).get("kind") == "plan"
                        and doc.get("source", {}).get("digest") == plan_digest
                        and unfinished_run(doc, info["commit_id"])
                    ):
                        matches.append({"run_id": run_id, "recovery_path": run_dir(run_id)})
            except Operational:
                raise
    if len(matches) != 1:
        word = "NO_MATCH" if not matches else "AMBIGUOUS"
        raise Operational(word, "resume discovery did not resolve exactly one unfinished run", {"matches": matches})
    return matches[0]["run_id"], matches


def resolve_resume_run(args) -> str:
    if args.run_id:
        if args.repo or args.plan_digest:
            raise Operational("REFUSED", "resume accepts either --run-id or --repo with --plan-digest")
        return safe_id(args.run_id, "run id")
    if not args.repo or not args.plan_digest:
        raise Operational("REFUSED", "resume discovery requires --repo and --plan-digest")
    return discover_resume_run(args.repo, args.plan_digest)[0]


def plan_wide_verification_attempts(doc: dict) -> list[dict]:
    attempts = doc.setdefault("verification_attempts", [])
    if not isinstance(attempts, list):
        raise TrustFailure("plan-wide verification attempts are malformed")
    return attempts


def pending_plan_wide_verification(doc: dict, lock: dict) -> dict | None:
    nonce = lock.get("nonce")
    pending = [attempt for attempt in plan_wide_verification_attempts(doc) if attempt.get("status") == "pending" and attempt.get("integration_lock_nonce") == nonce]
    if len(pending) > 1:
        raise TrustFailure("multiple plan-wide verification attempts own one lock")
    return pending[0] if pending else None


def receipted_plan_wide_verification(doc: dict, lock: dict) -> dict | None:
    nonce = lock.get("nonce")
    receipts = [attempt for attempt in plan_wide_verification_attempts(doc) if attempt.get("status") in {"passed", "failed"} and attempt.get("integration_lock_nonce") == nonce]
    return receipts[-1] if receipts else None


def plan_wide_blocker_retains_lock(doc: dict, lock: dict) -> bool:
    pending = pending_plan_wide_verification(doc, lock)
    return pending is not None


def cmd_resume(args) -> tuple[str, dict]:
    run_id = resolve_resume_run(args)
    actions = []
    with locked_manifest(run_id) as doc:
        validate_repo(doc)
        unit_ids = sorted(doc.get("units", {}))
    for unit_id in unit_ids:
        with locked_manifest(run_id) as doc:
            unit = doc["units"][unit_id]
            state = unit.get("state")
            attempt = find_attempt(unit)
            job_id = attempt.get("job_id")
        if job_id and state in {"authoring", "authored"}:
            evidence = sync_job(run_id, unit_id)
            actions.append({"unit_id": unit_id, "action": "sync", **evidence})
            if evidence.get("process_state") == "done":
                transport = terminalize(run_id, unit_id)
                actions.append({"unit_id": unit_id, "action": "terminalize", "transport": transport})
    with locked_manifest(run_id) as doc:
        return "RESUMED", {
            "run_id": run_id,
            "actions": actions,
            "units": doc.get("units", {}),
            "integration_lock": doc.get("integration_lock"),
            "verifications": doc.get("verifications", []),
            "recovery_path": run_dir(run_id),
        }


def fallback_basis(doc: dict, unit: dict) -> tuple[str, dict]:
    attempt = find_attempt(unit)
    fallback = attempt.setdefault("fallback", {"eligible": False, "reason": None, "claimed": None})
    if fallback.get("completed"):
        return "completed", fallback
    if fallback.get("claimed"):
        return "claimed", fallback
    process = attempt.get("process_state")
    restored = unit.get("integration", {}).get("restore")
    if process in TERMINAL_FAILURE:
        return "eligible", fallback
    if unit.get("state") == "preserved" and isinstance(restored, dict) and restored.get("exact") is True:
        return "eligible", fallback
    raise Operational("REFUSED", "native fallback is not eligible while external work remains viable or unreconciled")


def cmd_claim_fallback(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        if doc.get("integration_lock"):
            raise Operational("REFUSED", "release the integration lock before claiming fallback")
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        basis, fallback = fallback_basis(doc, unit)
        if basis == "completed":
            return "FALLBACK_COMPLETED", {"completion": fallback["completed"]}
        if basis == "claimed":
            return "FALLBACK_ALREADY_AUTHORIZED", {"claim": fallback["claimed"]}
        claim = {
            "at": now_iso(),
            "mode": doc["binding"]["mode"],
            "caller_mode": args.caller_mode,
            "canonical_revision": repo_info(doc["repository"]["toplevel"])["commit_id"],
            "canonical_change_id": repo_info(doc["repository"]["toplevel"])["change_id"],
            "requested_route": doc["egress"]["route"],
            "requested_model": doc["binding"].get("model"),
        }
        fallback.update({"eligible": True, "reason": find_attempt(unit).get("failure_reason"), "claimed": claim})
        event(doc, "fallback-authorized", args.unit_id, claim)
        return "FALLBACK_AUTHORIZED", {"claim": claim}


def validate_fallback_ancestry(doc: dict, unit: dict, accepted: dict) -> None:
    claim = find_attempt(unit).get("fallback", {}).get("claimed")
    if not claim or accepted["change_id"] != claim.get("canonical_change_id"):
        raise Operational("BLOCKED", "accepted fallback revision is not the authorized canonical change")


def cmd_complete_fallback(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        fallback = find_attempt(unit).setdefault("fallback", {})
        if fallback.get("completed"):
            return "FALLBACK_COMPLETED", {"completion": fallback["completed"], "resumed": True}
        if not fallback.get("claimed"):
            raise Operational("REFUSED", "fallback was not authorized")
        accepted = revision_info(info["toplevel"], args.accepted_revision)
        validate_fallback_ancestry(doc, unit, accepted)
        if not revision_is_ancestor(info["toplevel"], accepted["commit_id"], info["commit_id"]):
            raise Operational("BLOCKED", "accepted fallback revision is not present in the canonical history")
        changed_paths = sorted(filter(None, jj_text(info["toplevel"], "diff", "-r", accepted["commit_id"], "--name-only").splitlines()))
        completion = {
            "at": now_iso(),
            "claim": fallback["claimed"],
            "base": unit["workspace"]["base"],
            "accepted_revision": accepted["commit_id"],
            "accepted_change_id": accepted["change_id"],
            "summary": args.summary,
            "evidence_digest": args.evidence_digest,
            "changed_paths": changed_paths,
            "snapshot": {**semantic_completion_snapshot(info), "commit_id": accepted["commit_id"]},
        }
        fallback["completed"] = completion
        unit["state"] = "native-completed"
        event(doc, "fallback-completed", args.unit_id, {"revision": accepted["commit_id"]})
        return "FALLBACK_COMPLETED", {"completion": completion, "resumed": False}


def semantic_completion_snapshot(info: dict) -> dict:
    return {"empty": not status_paths(info["toplevel"]), "change_id": info["change_id"]}


def cmd_reap(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        job_id = attempt.get("job_id")
        if not job_id:
            raise Operational("REFUSED", "unit has no recorded job")
    runner = os.path.realpath(os.path.join(os.path.dirname(__file__), "peer-job-runner.py"))
    proc = subprocess.run([sys.executable, runner, "reap", "--skill", "ce-work", job_id], capture_output=True, text=True, check=False)
    evidence = sync_job(args.run_id, args.unit_id)
    if proc.returncode != 0 and evidence.get("process_state") not in TERMINAL_PROCESS:
        raise Operational("BLOCKED", "runner reap failed", {"stderr": proc.stderr.strip(), "process_state": evidence.get("process_state")})
    return "REAPED", {"unit_id": args.unit_id, **evidence}


def remove_finalized_artifacts(run_id: str, unit_id: str) -> None:
    unit_root = os.path.join(run_dir(run_id), "units", unit_id)
    for name in ("packet.md", "authorization.json", "result"):
        path = os.path.join(unit_root, name)
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        elif os.path.lexists(path):
            os.unlink(path)


def owned_workspace_path(run_id: str, unit_id: str, recorded_workspace: str) -> str:
    owned = os.path.realpath(os.path.join(run_dir(run_id), "units", unit_id))
    workspace = os.path.realpath(recorded_workspace)
    if os.path.commonpath([owned, workspace]) != owned:
        raise Operational("BLOCKED", "recorded unit workspace escaped controller-owned state")
    return workspace


def remove_unregistered_owned_workspace(run_id: str, unit_id: str, recorded_workspace: str) -> None:
    workspace = owned_workspace_path(run_id, unit_id, recorded_workspace)
    if os.path.isdir(workspace):
        shutil.rmtree(workspace)


def cmd_cleanup(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        transport = unit.get("transport", {})
        accepted = unit_accepted_revision(unit)
        if args.abandon:
            expected = args.expect_transport or args.expect_job
            actual = transport.get("commit_id") or attempt.get("job_id")
            if not expected or expected != actual:
                raise Operational("REFUSED", "abandonment requires the exact pinned revision or terminal job id")
        elif accepted is None:
            raise Operational("REFUSED", "cleanup requires an accepted revision or explicit abandonment")
        workspace = unit["workspace"]["path"]
        workspace_name = unit["workspace"]["name"]
        repo = doc["repository"]["toplevel"]
    jj(repo, "workspace", "forget", workspace_name)
    remove_unregistered_owned_workspace(args.run_id, args.unit_id, workspace)
    remove_finalized_artifacts(args.run_id, args.unit_id)
    receipt = {"at": now_iso(), "abandoned": bool(args.abandon), "workspace_forgotten": True, "artifact_cleanup": {"complete": True}}
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        unit["workspace"]["registered"] = False
        unit["cleanup"] = receipt
        unit["state"] = "cleaned" if not args.abandon else "cleaned"
        event(doc, "unit-cleaned", args.unit_id, {"abandoned": bool(args.abandon)})
    return "CLEANED", {"unit_id": args.unit_id, "cleanup": receipt}
