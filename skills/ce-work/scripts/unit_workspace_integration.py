"""Canonical JJ integration, locking, wave sequencing, and restoration."""

from __future__ import annotations

import json
import os
import re
import secrets

from unit_workspace_state import *
from unit_workspace_jobs import find_attempt, scope_expansion_pending


def integration_lock_path(doc: dict) -> str:
    return os.path.join(os.path.dirname(run_dir(doc["run_id"])), ".locks", f"integration-{doc['repository']['identity_digest']}.json")


def read_integration_lock(path: str) -> dict:
    return read_private_json(path)


def validate_lock(doc: dict, unit_id: str, token: str) -> tuple[str, dict]:
    path = integration_lock_path(doc)
    lock = read_integration_lock(path)
    if lock.get("run_id") != doc["run_id"] or lock.get("unit_id") != unit_id or lock.get("nonce") != token:
        raise Operational("BLOCKED", "integration lock token or identity mismatch")
    return path, lock


def cmd_integration_acquire(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit["state"] not in {"integration-pending", "integrated", "verified", "preserved", "committed", "cleaned", "native-completed"}:
            raise Operational("REFUSED", "unit is not ready for integration")
        existing = doc.get("integration_lock")
        if existing:
            if not args.resume or existing.get("unit_id") != args.unit_id:
                raise Operational("REFUSED", "integration claim already exists")
            validate_lock(doc, args.unit_id, existing["nonce"])
            return "ACQUIRED", {"lock_token": existing["nonce"], "resumed": True, "path": existing["path"]}
        path = integration_lock_path(doc)
        nonce = secrets.token_hex(24)
        payload = {"run_id": args.run_id, "unit_id": args.unit_id, "nonce": nonce, "repository": doc["repository"]["identity_digest"], "created_at": now_iso()}
        create_private(path, (json.dumps(payload, sort_keys=True) + "\n").encode())
    with locked_manifest(args.run_id, write=True) as doc:
        doc["integration_lock"] = {"unit_id": args.unit_id, "nonce": nonce, "path": path}
        event(doc, "integration-lock-acquired", args.unit_id)
    return "ACQUIRED", {"lock_token": nonce, "resumed": False, "path": path}


def operation_id(repo: str) -> str:
    value = jj_text(repo, "operation", "log", "--no-graph", "-n", "1", "-T", "id")
    if not re.fullmatch(r"[0-9a-f]+", value):
        raise Operational("BLOCKED", "could not capture the current JJ operation id")
    return value


def semantic_snapshot(repo: str) -> dict:
    jj(repo, "status")
    current = change_info(repo)
    paths = sorted(status_paths(repo))
    conflicts = jj_text(repo, "log", "--no-graph", "-r", "conflicts() & @", "-T", "change_id")
    return {
        "operation_id": operation_id(repo), "change_id": current["change_id"],
        "commit_id": current["commit_id"], "changed_paths": paths,
        "status_empty": not paths, "conflicted": bool(conflicts),
    }


def validate_dependencies_ready(doc: dict, unit: dict) -> None:
    missing = [dependency for dependency in unit.get("dependencies", []) if unit_accepted_commit(doc["units"].get(dependency, {})) is None]
    if missing:
        raise Operational("BLOCKED", "unit dependencies lack accepted canonical JJ changes", {"units": missing})


def wave_members(doc: dict, unit: dict) -> list[dict]:
    wave_id = unit.get("wave", {}).get("id")
    if not wave_id:
        return []
    return sorted((row for row in doc["units"].values() if row.get("wave", {}).get("id") == wave_id), key=lambda row: row["wave"]["position"])


def validate_wave_order(doc: dict, unit: dict) -> None:
    unresolved = [row["unit_id"] for row in wave_members(doc, unit) if row["wave"]["position"] < unit["wave"]["position"] and unit_accepted_commit(row) is None]
    if unresolved:
        raise Operational("BLOCKED", "earlier wave units must have accepted canonical changes", {"units": unresolved})


def validate_wave_collisions(doc: dict, unit: dict) -> None:
    members = wave_members(doc, unit)
    for index, left in enumerate(members):
        left_paths = set(left.get("transport", {}).get("changed_paths", []))
        for right in members[index + 1:]:
            overlap = sorted(left_paths & set(right.get("transport", {}).get("changed_paths", [])))
            if overlap:
                raise Operational("BLOCKED", "wave changes have a path collision", {"units": [left["unit_id"], right["unit_id"]], "paths": overlap})


def cmd_preflight(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit["state"] not in {"integration-pending", "preserved"}:
            raise Operational("REFUSED", "unit is not integration-pending")
        validate_lock(doc, args.unit_id, args.lock_token)
        validate_dependencies_ready(doc, unit)
        validate_wave_order(doc, unit)
        validate_wave_collisions(doc, unit)
        if scope_expansion_pending(unit):
            raise Operational("BLOCKED", "worker requested scope expansion", {"recovery_path": unit["recovery_path"]})
        snap = semantic_snapshot(info["workspace_root"])
        if not snap["status_empty"] or snap["conflicted"]:
            raise Operational("BLOCKED", "canonical JJ working-copy change is not clean at preflight")
        allowed = set(unit.get("wave", {}).get("allowed_changes", [])) | set(args.allowed_change)
        if allowed and snap["commit_id"] not in allowed:
            raise Operational("BLOCKED", "canonical JJ change advanced outside the recorded wave")
        unit["integration"]["pre_operation"] = snap
        unit["state"] = "integration-pending"
        event(doc, "canonical-squash-intent", args.unit_id, {"transport": unit["transport"]["change_id"]})
    return "PREFLIGHT_OK", {"unit_id": args.unit_id, "pre_operation": snap, "transport": unit["transport"]}


def matches_expected_apply(repo: str, unit: dict, snap: dict | None = None) -> bool:
    snap = snap or semantic_snapshot(repo)
    return set(snap["changed_paths"]) == set(unit["transport"]["changed_paths"]) and not snap["conflicted"]


def cmd_mark_applied(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        repo = validate_repo(doc)["workspace_root"]
        snap = semantic_snapshot(repo)
        if not matches_expected_apply(repo, unit, snap):
            raise Operational("BLOCKED", "canonical working-copy change does not match the transported JJ change")
        unit["state"] = "integrated"
        unit["integration"]["applied"] = snap
        event(doc, "change-squashed", args.unit_id, {"commit_id": snap["commit_id"]})
    return "APPLIED", {"unit_id": args.unit_id, "snapshot": snap}


def cmd_mark_verified(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        repo = validate_repo(doc)["workspace_root"]
        if not matches_expected_apply(repo, unit):
            raise Operational("BLOCKED", "canonical JJ change moved after verification")
        evidence = {"at": now_iso(), "digest": args.evidence_digest, "summary": args.summary}
        unit["integration"]["verification"] = evidence
        unit["state"] = "verified"
        event(doc, "canonical-verification-passed", args.unit_id, {"digest": args.evidence_digest})
    return "VERIFIED", {"unit_id": args.unit_id, "verification": evidence}


def reconcile_change(doc: dict, unit: dict) -> dict | None:
    repo = doc["repository"]["workspace_root"]
    finalized = change_info(repo, "@-")
    if status_paths(repo, "@-") == set(unit["transport"]["changed_paths"]):
        return finalized
    return None


def cmd_mark_finalized(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        if unit["state"] not in {"verified", "committed"}:
            raise Operational("REFUSED", "unit has not passed canonical verification")
        canonical = reconcile_change(doc, unit)
        if not canonical:
            raise Operational("BLOCKED", "canonical finalized JJ change does not match the transported paths")
        unit["integration"]["canonical_change"] = canonical
        unit["state"] = "committed"
        event(doc, "canonical-change-confirmed", args.unit_id, {"change_id": canonical["change_id"]})
    return "FINALIZED", {"unit_id": args.unit_id, "canonical_change": canonical}


def cmd_wave_advance(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        validate_lock(doc, args.unit_id, args.lock_token)
        canonical = unit.get("integration", {}).get("canonical_change", {})
        if canonical.get("commit_id") != args.canonical_change:
            raise Operational("BLOCKED", "wave change does not match the accepted canonical JJ change")
        advanced = []
        for candidate in wave_members(doc, unit):
            if candidate["wave"]["position"] > unit["wave"]["position"]:
                candidate["wave"].setdefault("allowed_changes", []).append(args.canonical_change)
                advanced.append(candidate["unit_id"])
        event(doc, "wave-advanced", args.unit_id, {"canonical_change": args.canonical_change, "eligible_siblings": advanced})
    return "WAVE_ADVANCED", {"unit_id": args.unit_id, "canonical_change": args.canonical_change, "eligible_siblings": advanced}


def restore(run_id: str, unit_id: str, lock_token: str) -> bool:
    with locked_manifest(run_id) as doc:
        validate_lock(doc, unit_id, lock_token)
        unit = doc["units"][unit_id]
        pre = unit.get("integration", {}).get("pre_operation")
        if not pre:
            raise Operational("REFUSED", "unit has no pre-integration JJ operation")
        repo = doc["repository"]["workspace_root"]
    jj(repo, "operation", "restore", pre["operation_id"])
    actual = semantic_snapshot(repo)
    exact = actual["change_id"] == pre["change_id"] and actual["commit_id"] == pre["commit_id"] and actual["changed_paths"] == pre["changed_paths"]
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        unit["integration"]["restore"] = {"at": now_iso(), "exact": exact, "snapshot": actual}
        unit["state"] = "preserved" if exact else "restoring"
        event(doc, "canonical-restored" if exact else "restore-blocked", unit_id)
    return exact


def cmd_restore(args) -> tuple[str, dict]:
    if not restore(args.run_id, args.unit_id, args.lock_token):
        raise Operational("BLOCKED", "exact JJ operation restoration could not be proven")
    return "PRESERVED", {"unit_id": args.unit_id, "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id)}


def integration_release(run_id: str, unit_id: str, lock_token: str) -> None:
    with locked_manifest(run_id, write=True) as doc:
        path, _ = validate_lock(doc, unit_id, lock_token)
        os.unlink(path)
        doc["integration_lock"] = None
        event(doc, "integration-lock-released", unit_id)


def cmd_integration_release(args) -> tuple[str, dict]:
    integration_release(args.run_id, args.unit_id, args.lock_token)
    return "RELEASED", {"unit_id": args.unit_id}
