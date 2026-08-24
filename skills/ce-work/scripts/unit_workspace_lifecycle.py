"""Resume, fallback, reap, and finalized JJ workspace lifecycle operations."""

from __future__ import annotations

import os
import re
import shutil
import subprocess

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


def discover_resume_run(repo: str, plan_digest: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", plan_digest):
        raise Operational("REFUSED", "plan digest must be lowercase SHA-256")
    info = repo_info(repo)
    candidates = []
    for entry in os.scandir(runs_root(info["workspace_root"])):
        if entry.name == ".locks" or not entry.is_dir(follow_symlinks=False):
            continue
        doc = read_private_json(os.path.join(entry.path, "manifest.json"))
        if doc.get("repository", {}).get("identity_digest") == info["identity_digest"] and doc.get("source", {}).get("kind") == "plan" and doc.get("source", {}).get("digest") == plan_digest:
            if any(unit.get("state") not in {"cleaned", "native-completed"} for unit in doc.get("units", {}).values()) or not doc.get("verifications"):
                candidates.append(entry.name)
    if not candidates:
        raise Operational("NOT_FOUND", "no unfinished run matches repository and plan digest")
    if len(candidates) > 1:
        raise Operational("AMBIGUOUS", "multiple unfinished runs match; pass --run-id", {"candidates": candidates})
    return candidates[0]


def resolve_resume_run(args) -> str:
    if args.run_id:
        if args.repo or args.plan_digest:
            raise Operational("REFUSED", "resume accepts --run-id alone or both --repo and --plan-digest")
        return safe_id(args.run_id, "run id")
    if not args.repo or not args.plan_digest:
        raise Operational("REFUSED", "resume requires --run-id or both --repo and --plan-digest")
    return discover_resume_run(args.repo, args.plan_digest)


def cmd_resume(args) -> tuple[str, dict]:
    run_id = resolve_resume_run(args)
    actions = []
    with locked_manifest(run_id) as doc:
        validate_repo(doc)
        units = list(doc["units"])
    for unit_id in units:
        with locked_manifest(run_id) as doc:
            unit = doc["units"][unit_id]
            state = unit["state"]
            attempt = find_attempt(unit)
            lock = doc.get("integration_lock")
        if state == "authoring" and attempt.get("job_id"):
            evidence = sync_job(run_id, unit_id)
            actions.append({"unit_id": unit_id, "action": "monitored", "process_state": evidence["process_state"]})
            if evidence["process_state"] == "done":
                actions.append({"unit_id": unit_id, "action": "terminalized", "transport": terminalize(run_id, unit_id)})
        elif state == "restoring" and lock and lock.get("unit_id") == unit_id:
            if not restore(run_id, unit_id, lock["nonce"]):
                raise Operational("BLOCKED", "exact JJ operation restoration could not be proven")
            integration_release(run_id, unit_id, lock["nonce"])
            actions.append({"unit_id": unit_id, "action": "restored"})
        elif state in {"committed", "cleaned", "native-completed"} and lock and lock.get("unit_id") == unit_id:
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
        fallback = attempt.setdefault("fallback", {})
        if fallback.get("claimed"):
            return "FALLBACK_ALREADY_AUTHORIZED", {"unit_id": args.unit_id, "start_native": False, "claim": fallback["claimed"]}
        if attempt.get("process_state") not in TERMINAL_PROCESS - {"done"} and unit.get("state") != "preserved":
            raise Operational("REFUSED", "no terminal or restored attempt authorizes fallback")
        snap = semantic_snapshot(doc["repository"]["workspace_root"])
        if not snap["status_empty"] or snap["conflicted"]:
            raise Operational("BLOCKED", "canonical JJ working-copy change is not clean for fallback")
        claim = {"at": now_iso(), "reason": fallback.get("reason") or "preserved-attempt", "caller_mode": args.caller_mode, "mode": doc["binding"]["mode"], "canonical_change": snap}
        fallback["claimed"] = claim
        fallback["eligible"] = False
        event(doc, "native-fallback-authorized", args.unit_id, {"reason": claim["reason"]})
    return "FALLBACK_AUTHORIZED", {"unit_id": args.unit_id, "start_native": True, "reason": claim["reason"], "claim": claim}


def cmd_complete_fallback(args) -> tuple[str, dict]:
    if not re.fullmatch(r"[0-9a-f]{64}", args.evidence_digest):
        raise Operational("REFUSED", "native fallback evidence digest must be lowercase SHA-256")
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        fallback = attempt.get("fallback", {})
        claim = fallback.get("claimed")
        if not claim:
            raise Operational("REFUSED", "native fallback completion requires an existing claim")
        current = change_info(doc["repository"]["workspace_root"], args.accepted_change)
        receipt = {"at": now_iso(), "accepted_change": current, "evidence_digest": args.evidence_digest, "summary": args.summary, "claim": claim}
        fallback["completed"] = receipt
        unit["integration"]["canonical_change"] = current
        unit["state"] = "native-completed"
        event(doc, "native-fallback-completed", args.unit_id, {"change_id": current["change_id"]})
    return "FALLBACK_COMPLETED", {"unit_id": args.unit_id, "completion": receipt}


def cmd_reap(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        if not attempt.get("job_id"):
            return "REAPED", {"unit_id": args.unit_id, "process_state": "never-started"}
        job_dir = runner_job_dir(args.run_id, attempt["job_id"])
    runner = os.path.join(os.path.dirname(__file__), "peer-job-runner.py")
    proc = subprocess.run([os.sys.executable, runner, "reap", job_dir], capture_output=True, check=False)
    if proc.returncode:
        raise Operational("BLOCKED", f"runner reap failed: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return "REAPED", {"unit_id": args.unit_id, **sync_job(args.run_id, args.unit_id), "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id)}


def cmd_cleanup(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        if unit.get("state") == "cleaned":
            return "CLEANED", {"unit_id": args.unit_id, "resumed": True}
        if unit.get("state") not in {"committed", "native-completed", "preserved", "authored"}:
            raise Operational("REFUSED", "workspace cleanup requires accepted or explicitly abandoned output")
        workspace = unit["workspace"]["path"]
        name = unit["workspace"]["name"]
        repo = doc["repository"]["workspace_root"]
    jj(repo, "workspace", "forget", name, check=False)
    if os.path.exists(workspace):
        shutil.rmtree(workspace)
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        finalized = "native-completed" if unit["state"] == "native-completed" else "cleaned"
        unit["cleanup"] = {"at": now_iso(), "workspace_removed": True, "abandoned": bool(args.abandon)}
        unit["state"] = finalized
        event(doc, "unit-cleaned", args.unit_id)
    return "CLEANED", {"unit_id": args.unit_id, "resumed": False}
