"""Resume, fallback, reap, and finalized-artifact lifecycle operations."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from types import SimpleNamespace

from unit_workspace_state import *
from unit_workspace_jobs import find_attempt, process_evidence, runner_job_dir, sync_job, terminalize
from unit_workspace_integration import cmd_composition_release, reconcile_described, restore, validate_lock


def cmd_status(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        body = {"run_id": args.run_id, "revision": doc["revision"], "source": doc["source"], "canonical_lock": doc.get("canonical_lock"), "verifications": doc.get("verifications", []), "blockers": doc.get("blockers", []), "recovery_path": locate_run(args.run_id, doc["repository"]["toplevel"])}
        if args.unit_id:
            if args.unit_id not in doc["units"]: raise Operational("REFUSED", "unknown unit")
            body["unit"] = doc["units"][args.unit_id]
        else:
            body["units"] = doc["units"]
    return "STATUS", body


def _discover(repo: str, plan_digest: str) -> str:
    root = runs_root(repo)
    if not os.path.isdir(root):
        raise Operational("NOT_FOUND", "no repository-local work runs exist")
    matches = []
    for entry in os.scandir(root):
        if entry.name == ".locks" or not entry.is_dir(follow_symlinks=False): continue
        doc = read_private_json(os.path.join(entry.path, "manifest.json"))
        if doc.get("repository", {}).get("identity_digest") == repo_info(repo)["identity_digest"] and doc.get("source", {}).get("kind") == "plan" and doc.get("source", {}).get("digest") == plan_digest:
            if any(unit.get("state") not in {"cleaned", "native-completed"} for unit in doc.get("units", {}).values()) or not doc.get("verifications"):
                matches.append(entry.name)
    if not matches: raise Operational("NOT_FOUND", "no unfinished run matches workspace and plan digest")
    if len(matches) > 1: raise Operational("AMBIGUOUS", "multiple unfinished runs match", {"candidates": matches})
    return matches[0]


def cmd_resume(args) -> tuple[str, dict]:
    run_id = safe_id(args.run_id, "run id") if args.run_id else _discover(args.repo, args.plan_digest)
    actions = []
    with locked_manifest(run_id) as doc:
        validate_repo(doc)
        unit_ids = list(doc["units"])
    for unit_id in unit_ids:
        with locked_manifest(run_id) as doc:
            unit = doc["units"][unit_id]
            state = unit["state"]
            lock = doc.get("canonical_lock")
        if state == "authoring":
            evidence = sync_job(run_id, unit_id)
            actions.append({"unit_id": unit_id, "action": "monitored", **evidence})
            if evidence["process_state"] == "done":
                transport = terminalize(run_id, unit_id)
                actions.append({"unit_id": unit_id, "action": "terminalized", "transport_change": transport["change_id"]})
        elif state == "restoring" and lock and lock.get("unit_id") == unit_id:
            if not restore(run_id, unit_id, lock["nonce"]):
                raise Operational("BLOCKED", "exact Jujutsu restoration could not be proven")
            cmd_composition_release(SimpleNamespace(run_id=run_id, unit_id=unit_id, lock_token=lock["nonce"]))
            actions.append({"unit_id": unit_id, "action": "restored-and-released"})
        elif state == "verified" and lock and lock.get("unit_id") == unit_id:
            with locked_manifest(run_id) as current:
                accepted = reconcile_described(current, current["units"][unit_id])
            if accepted:
                with locked_manifest(run_id, write=True) as current:
                    current["units"][unit_id]["composition"]["canonical_change"] = accepted
                    current["units"][unit_id]["state"] = "described"
                    event(current, "canonical-change-reconciled", unit_id, {"change_id": accepted["change_id"]})
                actions.append({"unit_id": unit_id, "action": "described-change-reconciled", "change_id": accepted["change_id"]})
            else:
                if not restore(run_id, unit_id, lock["nonce"]): raise Operational("BLOCKED", "restoration failed")
                cmd_composition_release(SimpleNamespace(run_id=run_id, unit_id=unit_id, lock_token=lock["nonce"]))
                actions.append({"unit_id": unit_id, "action": "pre-description-composition-restored"})
        elif state == "described":
            cmd_cleanup(SimpleNamespace(run_id=run_id, unit_id=unit_id, abandon=False, expect_transport=None, expect_job=None))
            if lock and lock.get("unit_id") == unit_id:
                cmd_composition_release(SimpleNamespace(run_id=run_id, unit_id=unit_id, lock_token=lock["nonce"]))
            actions.append({"unit_id": unit_id, "action": "accepted-change-finalized"})
    return "RESUMED", {"run_id": run_id, "actions": actions, "redispatched": False}


def cmd_claim_fallback(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit: raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        fallback = attempt.setdefault("fallback", {"eligible": False, "claimed": None, "completed": None})
        if fallback.get("claimed"):
            return "FALLBACK_ALREADY_AUTHORIZED", {"unit_id": args.unit_id, "start_native": False, "claim": fallback["claimed"]}
        if attempt.get("process_state") not in TERMINAL_PROCESS or attempt.get("process_state") == "done" and unit.get("transport"):
            raise Operational("REFUSED", "no authoritative terminal state authorizes fallback")
        mode = doc.get("binding", {}).get("mode")
        if mode == "require" and (args.caller_mode != "interactive" or not args.confirm_native):
            raise Operational("CHOICE_REQUIRED" if args.caller_mode == "interactive" else "BLOCKED", "required external route needs explicit native-fallback authority")
        if mode not in {"prefer", "require"}: raise Operational("REFUSED", "binding does not authorize native fallback")
        snapshot = semantic_snapshot(doc["repository"]["toplevel"])
        if snapshot["changed_paths"]: raise Operational("BLOCKED", "canonical working-copy change is not empty")
        claim = {"at": now_iso(), "mode": mode, "caller_mode": args.caller_mode, "confirmed_native": bool(args.confirm_native), "canonical_change_id": snapshot["change_id"]}
        fallback["claimed"] = claim
        event(doc, "native-fallback-authorized", args.unit_id)
    return "FALLBACK_AUTHORIZED", {"unit_id": args.unit_id, "start_native": True, "claim": claim}


def cmd_complete_fallback(args) -> tuple[str, dict]:
    if not re.fullmatch(r"[0-9a-f]{64}", args.evidence_digest): raise Operational("REFUSED", "evidence digest must be lowercase SHA-256")
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit: raise Operational("REFUSED", "unknown unit")
        fallback = find_attempt(unit).get("fallback", {})
        claim = fallback.get("claimed")
        if not claim or fallback.get("completed"): raise Operational("REFUSED", "fallback completion requires one open claim")
        repo = doc["repository"]["toplevel"]
        accepted = revision_field(repo, args.accepted_change, "change_id")
        accepted_snapshot = revision_field(repo, args.accepted_change, "snapshot_id")
        snapshot = semantic_snapshot(repo)
        if accepted != args.accepted_change or accepted_snapshot not in snapshot["parents"] or snapshot["changed_paths"]:
            raise Operational("BLOCKED", "accepted fallback change is not the parent of the empty canonical working-copy change")
        receipt = {"at": now_iso(), "accepted_change_id": accepted, "evidence_digest": args.evidence_digest, "summary": args.summary.strip(), "snapshot": snapshot, "claim": claim}
        fallback["completed"] = receipt
        unit["fallback"] = fallback
        unit["state"] = "native-completed"
        event(doc, "native-fallback-completed", args.unit_id, {"accepted_change_id": accepted})
    return "FALLBACK_COMPLETED", {"unit_id": args.unit_id, "completion": receipt}


def cmd_reap(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        unit = doc["units"].get(args.unit_id)
        if not unit: raise Operational("REFUSED", "unknown unit")
        attempt = find_attempt(unit)
        if not attempt.get("job_id"): return "REAPED", {"unit_id": args.unit_id, "process_state": "never-started"}
        job_dir = runner_job_dir(args.run_id, attempt["job_id"], doc)
    runner = os.path.join(os.path.dirname(__file__), "peer-job-runner.py")
    proc = subprocess.run([sys.executable, runner, "reap", job_dir], capture_output=True, check=False)
    if proc.returncode: raise Operational("BLOCKED", proc.stderr.decode("utf-8", "replace").strip())
    return "REAPED", {"unit_id": args.unit_id, **sync_job(args.run_id, args.unit_id)}


def cmd_cleanup(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit: raise Operational("REFUSED", "unknown unit")
        if unit["state"] == "cleaned": return "CLEANED", {"unit_id": args.unit_id, "resumed": True}
        if unit["state"] not in {"described", "native-completed", "preserved"} and not args.abandon:
            raise Operational("REFUSED", "unfinished output is retained unless explicitly abandoned")
        workspace = unit["workspace"]["path"]
        workspace_name = unit["workspace"]["name"]
        repo = doc["repository"]["toplevel"]
        root = os.path.join(locate_run(args.run_id, repo), "units", args.unit_id)
        if os.path.commonpath([os.path.realpath(workspace), os.path.realpath(root)]) != os.path.realpath(root):
            raise Operational("BLOCKED", "workspace escaped controller-owned unit root")
    listed = jj_text(repo, "workspace", "list")
    if workspace_name in listed:
        jj(repo, "workspace", "forget", workspace_name)
    if os.path.lexists(workspace):
        validate_private_dir(workspace)
        shutil.rmtree(workspace)
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        unit["cleanup"] = {"at": now_iso(), "workspace_forgotten": True, "abandoned": bool(args.abandon)}
        unit["state"] = "cleaned" if unit["state"] != "native-completed" else "native-completed"
        event(doc, "workspace-cleaned", args.unit_id)
    return "CLEANED", {"unit_id": args.unit_id, "resumed": False}
