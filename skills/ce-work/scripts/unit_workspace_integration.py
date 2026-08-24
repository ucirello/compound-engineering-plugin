"""JJ integration locking, sequencing, conflict checks, and operation restoration."""

from __future__ import annotations

import json
import os
import re
import secrets

from unit_workspace_state import *
from unit_workspace_jobs import find_attempt, scope_expansion_pending

INTEGRATABLE_STATES = {"integration-pending", "integrating", "verified", "accepted", "preserved", "cleaned", "native-completed"}


def integration_lock_path(doc: dict) -> str:
    root = os.path.dirname(run_dir(doc["run_id"]))
    key = digest_bytes(doc["repository"]["identity_digest"].encode())
    return os.path.join(root, ".locks", f"integration-{key}.json")


def read_integration_lock(path: str) -> dict:
    return read_private_json(path)


def validate_lock(doc: dict, unit_id: str, token: str) -> tuple[str, dict]:
    path = integration_lock_path(doc)
    lock = read_integration_lock(path)
    expected = {"run_id": doc["run_id"], "unit_id": unit_id, "repository": doc["repository"]["identity_digest"]}
    if any(lock.get(key) != value for key, value in expected.items()) or lock.get("nonce") != token:
        raise Operational("BLOCKED", "integration lock identity mismatch")
    return path, lock


def cmd_integration_acquire(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit.get("state") not in INTEGRATABLE_STATES:
            raise Operational("REFUSED", "unit is not ready for integration")
        existing = doc.get("integration_lock")
        path = integration_lock_path(doc)
        if existing:
            if not getattr(args, "resume", False):
                raise Operational("REFUSED", "integration lock already exists")
            validate_lock(doc, args.unit_id, existing["nonce"])
            return "ACQUIRED", {"lock_token": existing["nonce"], "resumed": True, "path": path}
        nonce = secrets.token_hex(24)
        payload = {"run_id": args.run_id, "unit_id": args.unit_id, "repository": doc["repository"]["identity_digest"], "nonce": nonce, "created_at": now_iso()}
        create_private(path, (json.dumps(payload, sort_keys=True) + "\n").encode())
    with locked_manifest(args.run_id, write=True) as doc:
        doc["integration_lock"] = {"unit_id": args.unit_id, "nonce": nonce, "path": path, "phase": "held"}
        event(doc, "integration-lock-acquired", args.unit_id)
    return "ACQUIRED", {"lock_token": nonce, "resumed": False, "path": path}


def validate_dependencies_ready(doc: dict, unit: dict) -> None:
    missing = [dep for dep in unit.get("dependencies", []) if not unit_accepted_change(doc.get("units", {}).get(dep, {}))]
    if missing:
        raise Operational("BLOCKED", "unit dependencies are not accepted", {"dependencies": missing})


def wave_members(doc: dict, unit: dict) -> list[dict]:
    wave_id = unit.get("wave", {}).get("id")
    if not wave_id:
        return []
    members = [row for row in doc.get("units", {}).values() if row.get("wave", {}).get("id") == wave_id]
    base = unit.get("wave", {}).get("base")
    if any(row.get("wave", {}).get("base") != base for row in members):
        raise Operational("BLOCKED", "wave members do not share one recorded base")
    positions = [row.get("wave", {}).get("position") for row in members]
    if any(not isinstance(position, int) or isinstance(position, bool) or position < 0 for position in positions):
        raise Operational("BLOCKED", "wave positions are malformed")
    if sorted(positions) != list(range(len(positions))):
        raise Operational("BLOCKED", "wave positions are not unique and complete")
    return sorted(members, key=lambda row: row["wave"]["position"])


def validate_wave_order(doc: dict, unit: dict) -> None:
    unresolved = [
        row["unit_id"] for row in wave_members(doc, unit)
        if row["wave"]["position"] < unit["wave"]["position"] and not unit_accepted_change(row)
    ]
    if unresolved:
        raise Operational("BLOCKED", "earlier wave changes are not accepted", {"units": unresolved})


def validate_wave_collisions(doc: dict, unit: dict) -> None:
    members = wave_members(doc, unit)
    missing = [row["unit_id"] for row in members if not isinstance(row.get("transport"), dict)]
    if missing:
        raise Operational("BLOCKED", "every wave worker must terminalize before the first integration", {"units": missing})
    for index, left in enumerate(members):
        left_paths = set((left.get("transport") or {}).get("changed_paths", []))
        for right in members[index + 1:]:
            right_paths = set((right.get("transport") or {}).get("changed_paths", []))
            overlap = sorted(left_paths & right_paths)
            if overlap:
                raise Operational("BLOCKED", "wave changes have a fileset collision", {"units": [left["unit_id"], right["unit_id"]], "paths": overlap})


def cmd_preflight(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit.get("state") not in {"integration-pending", "preserved"}:
            raise Operational("REFUSED", "unit is not integration-pending")
        validate_lock(doc, args.unit_id, args.lock_token)
        validate_dependencies_ready(doc, unit)
        validate_wave_order(doc, unit)
        validate_wave_collisions(doc, unit)
        if scope_expansion_pending(unit):
            raise Operational("BLOCKED", "worker requested scope expansion", {"recovery_path": unit["recovery_path"]})
        repo = info["workspace_root"]
        snap = semantic_snapshot(repo)
        if not snap["empty"] or snap["conflicted"]:
            raise Operational("BLOCKED", "canonical working-copy change is not empty and conflict-free")
        accepted = [unit_accepted_change(row) for row in doc["units"].values() if unit_accepted_change(row)]
        expected_parent = accepted[-1] if accepted else revision_info(repo, "@-")["change_id"]
        requested = list(getattr(args, "allowed_change", []) or [])
        if requested and expected_parent not in requested:
            raise Operational("BLOCKED", "canonical accepted change is outside the recorded wave allowance")
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        unit["state"] = "integrating"
        unit["integration"]["pre_operation"] = snap["operation_id"]
        unit["integration"]["pre_snapshot"] = snap
        unit["integration"]["transport_pre_snapshot"] = revision_info(repo, unit["transport"]["change_id"])
        unit["integration"]["destination_change"] = expected_parent
        event(doc, "integration-intent", args.unit_id, {"operation_id": snap["operation_id"], "destination_change": expected_parent})
    return "PREFLIGHT_OK", {"unit_id": args.unit_id, "pre_operation": snap["operation_id"], "destination_change": expected_parent, "transport": unit["transport"]}


def cmd_mark_applied(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        change = unit["transport"]["change_id"]
        repo = doc["repository"]["workspace_root"]
        if has_conflicts(repo, change):
            raise Operational("BLOCKED", "integrated JJ change contains conflicts")
        unit["integration"]["rebased"] = {**revision_info(repo, change), "at": now_iso()}
        event(doc, "change-rebased", args.unit_id, {"change_id": change})
    return "APPLIED", {"unit_id": args.unit_id, "change": unit["integration"]["rebased"]}


def cmd_mark_verified(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        if unit.get("state") not in {"integrating", "verified"}:
            raise Operational("REFUSED", "unit is not integrating")
        unit["state"] = "verified"
        unit["integration"]["verification"] = {"at": now_iso(), "digest": args.evidence_digest, "summary": args.summary, "ignored_state": getattr(args, "ignored_state", None)}
        event(doc, "authoritative-verification-passed", args.unit_id, {"digest": args.evidence_digest})
    return "VERIFIED", {"unit_id": args.unit_id, "verification": unit["integration"]["verification"]}


def cmd_mark_accepted(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        if unit.get("state") != "verified":
            raise Operational("REFUSED", "unit has not passed authoritative verification")
        repo = doc["repository"]["workspace_root"]
        accepted = revision_info(repo, unit["transport"]["change_id"])
        if has_conflicts(repo, accepted["change_id"]):
            raise Operational("BLOCKED", "accepted change contains conflicts")
        record = {**accepted, "at": now_iso()}
        unit["integration"]["accepted_change"] = record
        unit["state"] = "accepted"
        event(doc, "change-accepted", args.unit_id, {"change_id": record["change_id"], "commit_id": record["commit_id"]})
    return "ACCEPTED", {"unit_id": args.unit_id, "accepted_change": record}


def cmd_wave_advance(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        accepted = unit.get("integration", {}).get("accepted_change")
        if not accepted or accepted["change_id"] != args.canonical_change:
            raise Operational("BLOCKED", "wave advance does not match the accepted change")
        advanced = []
        for sibling in wave_members(doc, unit):
            if sibling["wave"]["position"] > unit["wave"]["position"]:
                sibling["wave"].setdefault("accepted", []).append(accepted["change_id"])
                advanced.append(sibling["unit_id"])
        event(doc, "wave-advanced", args.unit_id, {"change_id": accepted["change_id"], "eligible_siblings": advanced})
    return "WAVE_ADVANCED", {"unit_id": args.unit_id, "canonical_change": accepted["change_id"], "eligible_siblings": advanced}


def restore(run_id: str, unit_id: str, lock_token: str) -> bool:
    with locked_manifest(run_id) as doc:
        validate_lock(doc, unit_id, lock_token)
        unit = doc["units"][unit_id]
        expected = unit.get("integration", {}).get("pre_snapshot")
        transport_before = unit.get("integration", {}).get("transport_pre_snapshot")
        transport = unit.get("transport", {}).get("change_id")
        repo = doc["repository"]["workspace_root"]
        if not expected or not transport_before or not transport:
            raise Operational("REFUSED", "unit has no complete pre-integration restoration receipt")
        current = semantic_snapshot(repo)
        current_transport = revision_info(repo, transport)
        verification_child = (
            current.get("empty") is True
            and not current.get("conflicted")
            and current.get("parents") == [current_transport["commit_id"]]
        )
        if current.get("change_id") != expected.get("change_id") and not verification_child:
            raise Operational("BLOCKED", "canonical state is not a proven controller-owned integration state")
        original_parents = transport_before.get("parents")
        if not isinstance(original_parents, list) or len(original_parents) != 1:
            raise Operational("BLOCKED", "transport restoration requires one recorded original parent")
    if verification_child:
        jj(repo, "abandon", current["change_id"])
    jj(repo, "edit", expected["change_id"])
    current_transport = revision_info(repo, transport)
    if current_transport.get("parents") != original_parents:
        jj(repo, "rebase", "-r", transport, "-o", original_parents[0])
    restored_transport = revision_info(repo, transport)
    if (
        restored_transport.get("change_id") != transport_before.get("change_id")
        or restored_transport.get("parents") != original_parents
        or has_conflicts(repo, transport)
        or changed_paths(repo, transport) != unit["transport"].get("changed_paths")
    ):
        raise Operational("BLOCKED", "scoped transport restoration could not be proven")
    actual = semantic_snapshot(repo)
    exact = all(actual.get(key) == expected.get(key) for key in ("commit_id", "change_id", "parents", "changed_paths", "diff_sha256", "empty", "conflicted"))
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        unit["integration"]["restore"] = {"at": now_iso(), "operation": expected.get("operation_id"), "exact": exact, "snapshot": actual, "scoped": True}
        unit["state"] = "preserved"
        event(doc, "operation-restored" if exact else "operation-restore-blocked", unit_id, {"operation": expected.get("operation_id"), "scoped": True})
        if not exact:
            doc["blockers"].append({"at": now_iso(), "unit_id": unit_id, "reason": "exact JJ operation restoration could not be proven", "retain_integration_lock": True})
    return exact


def cmd_restore(args) -> tuple[str, dict]:
    if not restore(args.run_id, args.unit_id, args.lock_token):
        raise Operational("BLOCKED", "exact JJ operation restoration could not be proven")
    return "PRESERVED", {"unit_id": args.unit_id, "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id)}


def integration_release(run_id: str, unit_id: str, lock_token: str) -> None:
    with locked_manifest(run_id, write=True) as doc:
        path, _ = validate_lock(doc, unit_id, lock_token)
        pending = [
            attempt for attempt in doc.get("verification_attempts", [])
            if isinstance(attempt, dict)
            and attempt.get("status") == "pending"
            and attempt.get("integration_lock_nonce") == lock_token
        ]
        if pending:
            raise Operational("BLOCKED", "pending plan-wide verification retains the integration lock", {"retain_integration_lock": True})
        unit = doc["units"].get(unit_id)
        if not unit or unit.get("state") not in {"accepted", "cleaned", "preserved", "native-completed"}:
            raise Operational("REFUSED", "integration lock can release only after acceptance or restoration")
        os.unlink(path)
        doc["integration_lock"] = None
        event(doc, "integration-lock-released", unit_id)


def cmd_integration_release(args) -> tuple[str, dict]:
    integration_release(args.run_id, args.unit_id, args.lock_token)
    return "RELEASED", {"unit_id": args.unit_id}
