"""Canonical Jujutsu composition, locking, wave sequencing, and restoration."""

from __future__ import annotations

import json
import os
import re
import secrets

from unit_workspace_state import *
from unit_workspace_jobs import scope_expansion_pending


def composition_lock_path(doc: dict) -> str:
    root = os.path.dirname(locate_run(doc["run_id"], doc["repository"]["toplevel"]))
    return os.path.join(root, ".locks", f"composition-{doc['repository']['identity_digest']}.json")


def validate_lock(doc: dict, unit_id: str, token: str) -> tuple[str, dict]:
    path = composition_lock_path(doc)
    try:
        lock = read_private_json(path)
    except FileNotFoundError as exc:
        raise Operational("BLOCKED", "canonical composition lock file is absent") from exc
    except OSError as exc:
        raise Operational("BLOCKED", "canonical composition lock is unavailable") from exc
    expected = {"run_id": doc["run_id"], "unit_id": unit_id, "repository": doc["repository"]["identity_digest"]}
    if any(lock.get(k) != v for k, v in expected.items()) or lock.get("nonce") != token:
        raise Operational("BLOCKED", "canonical composition lock identity mismatch")
    return path, lock


def composition_lock_exists(path: str) -> bool:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise Operational("BLOCKED", "canonical composition lock changed during reconciliation") from exc
    return True


def cmd_composition_acquire(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit:
            raise Operational("REFUSED", "unknown unit")
        existing = doc.get("canonical_lock")
        path = composition_lock_path(doc)
        if existing and existing.get("state") == "releasing":
            if existing.get("path") != path or not isinstance(existing.get("unit_id"), str) or not isinstance(existing.get("nonce"), str):
                raise Operational("BLOCKED", "releasing canonical composition claim is malformed")
            if composition_lock_exists(path):
                raise Operational("REFUSED", "canonical composition release is still in progress")
            event(doc, "composition-lock-release-reconciled", existing["unit_id"])
            doc["canonical_lock"] = None
            existing = None
        if existing:
            if not args.resume or existing.get("unit_id") != args.unit_id:
                raise Operational("REFUSED", "canonical composition is already claimed")
            validate_lock(doc, args.unit_id, existing["nonce"])
            return "ACQUIRED", {"lock_token": existing["nonce"], "resumed": True, "path": path}

        if os.path.lexists(path):
            try:
                orphan = read_private_json(path)
            except OSError as exc:
                raise Operational("BLOCKED", "canonical composition lock changed during reconciliation") from exc
            expected = {
                "run_id": doc["run_id"],
                "unit_id": args.unit_id,
                "repository": doc["repository"]["identity_digest"],
            }
            if any(orphan.get(key) != value for key, value in expected.items()):
                raise Operational("REFUSED", "canonical composition is already claimed")
            nonce = orphan.get("nonce")
            if not isinstance(nonce, str) or not nonce:
                raise Operational("BLOCKED", "orphaned canonical composition lock is malformed")
            doc["canonical_lock"] = {"unit_id": args.unit_id, "nonce": nonce, "path": path}
            event(doc, "composition-lock-reconciled", args.unit_id)
            return "ACQUIRED", {"lock_token": nonce, "resumed": True, "path": path}

        nonce = secrets.token_hex(24)
        payload = {"run_id": args.run_id, "unit_id": args.unit_id, "repository": doc["repository"]["identity_digest"], "nonce": nonce, "created_at": now_iso()}
        try:
            create_private(path, (json.dumps(payload, sort_keys=True) + "\n").encode())
        except FileExistsError as exc:
            raise Operational("REFUSED", "canonical composition is already claimed") from exc
        doc["canonical_lock"] = {"unit_id": args.unit_id, "nonce": nonce, "path": path}
        event(doc, "composition-lock-acquired", args.unit_id)
        return "ACQUIRED", {"lock_token": nonce, "resumed": False, "path": path}


def validate_dependencies_ready(doc: dict, unit: dict) -> None:
    missing = [dep for dep in unit.get("dependencies", []) if accepted_unit_change(doc["units"].get(dep, {})) is None]
    if missing:
        raise Operational("BLOCKED", "unit dependencies have no accepted canonical changes", {"dependencies": missing})


def wave_members(doc: dict, unit: dict) -> list[dict]:
    wave_id = unit.get("wave", {}).get("id")
    if not wave_id:
        return []
    members = [u for u in doc["units"].values() if u.get("wave", {}).get("id") == wave_id]
    return sorted(members, key=lambda u: u["wave"]["position"])


def validate_wave_order(doc: dict, unit: dict) -> None:
    unresolved = [u["unit_id"] for u in wave_members(doc, unit) if u["wave"]["position"] < unit["wave"]["position"] and accepted_unit_change(u) is None]
    if unresolved:
        raise Operational("BLOCKED", "earlier wave units must have accepted changes", {"units": unresolved})


def validate_wave_collisions(doc: dict, unit: dict) -> None:
    members = wave_members(doc, unit)
    changed = {u["unit_id"]: set((u.get("transport") or {}).get("changed_paths", [])) for u in members if u.get("transport")}
    collisions = {}
    for i, left in enumerate(members):
        for right in members[i + 1:]:
            overlap = sorted(changed.get(left["unit_id"], set()) & changed.get(right["unit_id"], set()))
            if overlap:
                collisions[f"{left['unit_id']}:{right['unit_id']}"] = overlap
    if collisions:
        raise Operational("BLOCKED", "wave transports have changed-path collisions", {"collisions": collisions})


def cmd_preflight(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit["state"] not in {"composition-pending", "preserved"}:
            raise Operational("REFUSED", "unit is not ready for canonical composition")
        validate_lock(doc, args.unit_id, args.lock_token)
        validate_dependencies_ready(doc, unit)
        validate_wave_order(doc, unit)
        validate_wave_collisions(doc, unit)
        if scope_expansion_pending(unit):
            raise Operational("BLOCKED", "worker requested scope expansion")
        snapshot = semantic_snapshot(info["toplevel"])
        allowed = set(unit.get("wave", {}).get("allowed_changes", [])) | set(args.allowed_change)
        if snapshot["change_id"] not in allowed:
            raise Operational("BLOCKED", "canonical working-copy change advanced outside recorded allowances")
        if snapshot["changed_paths"]:
            raise Operational("BLOCKED", "canonical working-copy change is not empty at preflight")
        expected_paths = sorted(unit["transport"]["changed_paths"])
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        unit["composition"]["pre_fold"] = snapshot
        unit["composition"]["expected_paths"] = expected_paths
        event(doc, "composition-intent", args.unit_id, {"transport_change": unit["transport"]["change_id"]})
    return "PREFLIGHT_OK", {"unit_id": args.unit_id, "pre_fold": snapshot, "expected_paths": expected_paths}


def matches_expected_composition(repo: str, unit: dict) -> bool:
    snap = semantic_snapshot(repo)
    pre = unit.get("composition", {}).get("pre_fold")
    return bool(pre) and snap["change_id"] == pre["change_id"] and snap["parents"] == pre["parents"] and snap["bookmark_digest"] == pre["bookmark_digest"] and set(snap["changed_paths"]) == set(unit["composition"]["expected_paths"])


def cmd_mark_composed(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        repo = validate_repo(doc)["toplevel"]
        if not matches_expected_composition(repo, unit):
            raise Operational("BLOCKED", "canonical change does not match expected transport composition")
        unit["state"] = "composed"
        unit["composition"]["composed"] = semantic_snapshot(repo)
        event(doc, "transport-composed", args.unit_id)
        return "COMPOSED", {"unit_id": args.unit_id, "snapshot": unit["composition"]["composed"]}


def cmd_mark_verified(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        repo = validate_repo(doc)["toplevel"]
        if not matches_expected_composition(repo, unit):
            raise Operational("BLOCKED", "canonical change changed after composition")
        evidence = {"at": now_iso(), "digest": args.evidence_digest, "summary": args.summary}
        if args.untracked_state:
            evidence["untracked_state"] = parse_json_arg(args.untracked_state, "untracked-state")
        unit["composition"]["verification"] = evidence
        unit["state"] = "verified"
        event(doc, "canonical-verification-passed", args.unit_id)
        return "VERIFIED", {"unit_id": args.unit_id, "verification": evidence}


def reconcile_described(doc: dict, unit: dict) -> dict | None:
    repo = doc["repository"]["toplevel"]
    snap = semantic_snapshot(repo)
    pre = unit["composition"]["pre_fold"]
    if snap["change_id"] != pre["change_id"] or set(snap["changed_paths"]) != set(unit["composition"]["expected_paths"]):
        return None
    if not snap["description"].strip():
        return None
    return {"change_id": snap["change_id"], "snapshot_id": snap["snapshot_id"], "description": snap["description"], "at": now_iso()}


def cmd_mark_described(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit["state"] not in {"verified", "described"}:
            raise Operational("REFUSED", "unit has not passed canonical verification")
        accepted = reconcile_described(doc, unit)
        if not accepted:
            raise Operational("BLOCKED", "described canonical change does not match composition evidence")
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        unit["composition"]["canonical_change"] = accepted
        unit["state"] = "described"
        event(doc, "canonical-change-accepted", args.unit_id, {"change_id": accepted["change_id"]})
    return "DESCRIBED", {"unit_id": args.unit_id, "canonical_change": accepted}


def restore(run_id: str, unit_id: str, lock_token: str) -> bool:
    with locked_manifest(run_id) as doc:
        validate_lock(doc, unit_id, lock_token)
        unit = doc["units"][unit_id]
        pre = unit["composition"].get("pre_fold")
        if not pre:
            raise Operational("REFUSED", "unit has no pre-composition snapshot")
        repo = doc["repository"]["toplevel"]
    with locked_manifest(run_id, write=True) as doc:
        doc["units"][unit_id]["state"] = "restoring"
        event(doc, "restore-intent", unit_id)
    jj(repo, "restore", "--from", pre["snapshot_id"], "--into", "@")
    jj(repo, "describe", "-m", pre["description"])
    actual = semantic_snapshot(repo)
    exact = all(actual[k] == pre[k] for k in ("change_id", "parents", "description", "changed_paths", "bookmark_digest"))
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        unit["composition"]["restore"] = {"at": now_iso(), "exact": exact, "snapshot": actual}
        unit["state"] = "preserved" if exact else "restoring"
        event(doc, "canonical-restored" if exact else "restore-blocked", unit_id)
    return exact


def cmd_restore(args) -> tuple[str, dict]:
    if not restore(args.run_id, args.unit_id, args.lock_token):
        raise Operational("BLOCKED", "exact pre-composition restoration could not be proven")
    return "PRESERVED", {"unit_id": args.unit_id}


def cmd_wave_advance(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        accepted = accepted_unit_change(unit)
        if accepted != args.canonical_change:
            raise Operational("BLOCKED", "wave advancement does not match accepted canonical change")
        advanced = []
        for candidate in wave_members(doc, unit):
            if candidate["wave"]["position"] > unit["wave"]["position"]:
                candidate["wave"].setdefault("allowed_changes", []).append(accepted)
                advanced.append(candidate["unit_id"])
        event(doc, "wave-advanced", args.unit_id, {"canonical_change": accepted, "eligible_siblings": advanced})
    return "WAVE_ADVANCED", {"unit_id": args.unit_id, "canonical_change": accepted, "eligible_siblings": advanced}


def cmd_composition_release(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        path = composition_lock_path(doc)
        claim = doc.get("canonical_lock")
        expected = {"unit_id": args.unit_id, "nonce": args.lock_token, "path": path}
        if not isinstance(claim, dict) or any(claim.get(key) != value for key, value in expected.items()):
            raise Operational("BLOCKED", "canonical composition lock identity mismatch")
        unit = doc["units"].get(args.unit_id)
        if not unit or unit["state"] not in {"described", "preserved", "cleaned", "native-completed"}:
            raise Operational("REFUSED", "composition lock releases only after accepted completion or exact preservation")
        if claim.get("state") == "releasing" and not composition_lock_exists(path):
            doc["canonical_lock"] = None
            event(doc, "composition-lock-release-reconciled", args.unit_id)
            return "RELEASED", {"unit_id": args.unit_id}
        validate_lock(doc, args.unit_id, args.lock_token)
        claim["state"] = "releasing"
        event(doc, "composition-lock-release-started", args.unit_id)

    with locked_manifest(args.run_id, write=True) as doc:
        claim = doc.get("canonical_lock")
        expected = {"unit_id": args.unit_id, "nonce": args.lock_token, "path": path, "state": "releasing"}
        if not isinstance(claim, dict) or any(claim.get(key) != value for key, value in expected.items()):
            raise Operational("BLOCKED", "canonical composition release claim changed")
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise Operational("BLOCKED", "canonical composition lock could not be removed") from exc
        doc["canonical_lock"] = None
        event(doc, "composition-lock-released", args.unit_id)
    return "RELEASED", {"unit_id": args.unit_id}
