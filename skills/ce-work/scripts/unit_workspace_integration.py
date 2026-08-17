"""Jujutsu integration, locking, wave sequencing, and exact restoration."""

from __future__ import annotations

import os
import re
import secrets

from unit_workspace_state import (
    DESCRIPTION_STANDARD,
    Operational,
    TrustFailure,
    cmd_integrate as _atomic_integrate,
    cmd_verify_run as _atomic_verify_run,
    create_private,
    digest_bytes,
    event,
    jj,
    locked_manifest,
    now_iso,
    read_private_json,
    run_dir,
    snapshot,
    validate_repo,
)


def integration_lock_path(doc: dict) -> str:
    identity = doc["repository"]["identity_digest"]
    return os.path.join(run_dir(doc["run_id"]), ".locks", f"integration-{digest_bytes(identity.encode())}.json")


def read_integration_lock(path: str) -> dict:
    return read_private_json(path)


def validated_lock_nonce(doc: dict, unit_id: str, lock: dict) -> str:
    expected = {
        "run_id": doc["run_id"],
        "unit_id": unit_id,
        "repository": doc["repository"]["identity_digest"],
    }
    if any(lock.get(key) != value for key, value in expected.items()):
        raise Operational("BLOCKED", "integration lock identity mismatch")
    nonce = lock.get("nonce")
    if not isinstance(nonce, str) or not re.fullmatch(r"[0-9a-f]{48}", nonce):
        raise TrustFailure("integration lock nonce is malformed")
    return nonce


def validate_lock(doc: dict, unit_id: str, token: str) -> tuple[str, dict]:
    path = integration_lock_path(doc)
    lock = read_integration_lock(path)
    if validated_lock_nonce(doc, unit_id, lock) != token:
        raise Operational("BLOCKED", "integration lock token mismatch")
    held = doc.get("integration_lock")
    if not isinstance(held, dict) or held.get("nonce") != token or held.get("unit_id") != unit_id:
        raise Operational("BLOCKED", "manifest integration claim mismatch")
    return path, lock


def cmd_integration_acquire(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        unit = doc.get("units", {}).get(args.unit_id)
        if not unit or unit.get("state") not in {"integration-pending", "accepted", "cleaned"}:
            raise Operational("REFUSED", "unit is not ready for integration locking")
        existing = doc.get("integration_lock")
        if existing:
            if not getattr(args, "resume", False):
                raise Operational("REFUSED", "integration claim already exists")
            path, _ = validate_lock(doc, args.unit_id, existing["nonce"])
            return "ACQUIRED", {"lock_token": existing["nonce"], "resumed": True, "path": path}
        token = secrets.token_hex(24)
        path = integration_lock_path(doc)
        payload = {
            "run_id": args.run_id,
            "unit_id": args.unit_id,
            "nonce": token,
            "repository": doc["repository"]["identity_digest"],
            "operation_id": info["snapshot"]["operation_id"],
            "created_at": now_iso(),
        }
        create_private(path, (json_bytes(payload)))
        doc["integration_lock"] = {
            "unit_id": args.unit_id,
            "nonce": token,
            "path": path,
            "operation_id": info["snapshot"]["operation_id"],
        }
        event(doc, "integration-lock-acquired", args.unit_id)
    return "ACQUIRED", {"lock_token": token, "resumed": False, "path": path}


def json_bytes(value: dict) -> bytes:
    import json

    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def semantic_snapshot(repo: str) -> dict:
    return snapshot(repo)


def expected_apply_snapshot(_repo: str, _pre_change: str, unit: dict) -> dict:
    transport = unit.get("transport")
    if not isinstance(transport, dict):
        raise Operational("BLOCKED", "unit has no terminalized Jujutsu change")
    return {
        "change_id": transport["change_id"],
        "commit_id": transport["commit_id"],
        "parent_commit_ids": list(transport["parent_commit_ids"]),
        "changed_paths": list(transport["changed_paths"]),
        "delta_sha256": transport["delta_sha256"],
    }


def matches_expected_apply(repo: str, unit: dict, observed: dict | None = None) -> bool:
    observed = observed or semantic_snapshot(repo)
    integration = unit.get("integration") or {}
    expected = integration.get("expected_apply") or integration.get("applied")
    if not isinstance(expected, dict):
        return False
    return (
        observed.get("conflict") is False
        and observed.get("changed_paths") == expected.get("changed_paths")
        and observed.get("delta_sha256") == expected.get("delta_sha256")
    )


def wave_members(doc: dict, unit: dict) -> list[dict]:
    wave = unit.get("wave", {})
    wave_id = wave.get("id")
    if not wave_id:
        return []
    members = [candidate for candidate in doc.get("units", {}).values() if candidate.get("wave", {}).get("id") == wave_id]
    if any(candidate.get("wave", {}).get("base") != wave.get("base") for candidate in members):
        raise Operational("BLOCKED", "wave members do not share one recorded base")
    positions = [candidate.get("wave", {}).get("position") for candidate in members]
    if len(positions) != len(set(positions)):
        raise Operational("BLOCKED", "wave positions are not unique")
    return sorted(members, key=lambda candidate: candidate["wave"]["position"])


def wave_member_changed_paths(unit: dict) -> set[str] | None:
    transport = unit.get("transport")
    if not isinstance(transport, dict):
        return None
    paths = transport.get("changed_paths")
    if not isinstance(paths, list) or any(not isinstance(path, str) for path in paths):
        raise TrustFailure("wave changed-path inventory is malformed")
    return set(paths)


def validate_wave_order(doc: dict, unit: dict) -> None:
    unresolved = [
        candidate["unit_id"]
        for candidate in wave_members(doc, unit)
        if candidate["wave"]["position"] < unit["wave"]["position"] and candidate.get("state") != "cleaned"
    ]
    if unresolved:
        raise Operational("BLOCKED", "earlier wave changes must be accepted first", {"units": unresolved})


def validate_wave_collisions(
    doc: dict,
    unit: dict,
    overrides: dict[str, set[str]] | None = None,
    require_complete: bool = True,
) -> None:
    overrides = overrides or {}
    changed: dict[str, set[str]] = {}
    missing: list[str] = []
    for candidate in wave_members(doc, unit):
        unit_id = candidate["unit_id"]
        paths = overrides.get(unit_id)
        if paths is None:
            paths = wave_member_changed_paths(candidate)
        if paths is None:
            missing.append(unit_id)
        else:
            changed[unit_id] = paths
    if require_complete and missing:
        raise Operational("BLOCKED", "every wave worker must terminalize before integration", {"units": missing})
    collisions = {
        f"{left}:{right}": sorted(changed[left] & changed[right])
        for index, left in enumerate(changed)
        for right in list(changed)[index + 1:]
        if changed[left] & changed[right]
    }
    if collisions:
        raise Operational("BLOCKED", "wave changes have a changed-path collision", {"collisions": collisions})


def validate_wave_ready(doc: dict, unit: dict) -> None:
    validate_wave_order(doc, unit)
    validate_wave_collisions(doc, unit)


def validate_dependencies_ready(doc: dict, unit: dict) -> None:
    missing = [dependency for dependency in unit.get("dependencies", []) if dependency not in doc.get("units", {})]
    unresolved = [
        dependency
        for dependency in unit.get("dependencies", [])
        if dependency in doc.get("units", {}) and doc["units"][dependency].get("state") != "cleaned"
    ]
    if missing or unresolved:
        raise Operational("BLOCKED", "unit dependencies lack accepted canonical changes", {"missing": missing, "unresolved": unresolved})


def cmd_preflight(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        unit = doc.get("units", {}).get(args.unit_id)
        if not unit or unit.get("state") != "integration-pending":
            raise Operational("REFUSED", "unit is not integration-pending")
        validate_lock(doc, args.unit_id, args.lock_token)
        validate_dependencies_ready(doc, unit)
        validate_wave_ready(doc, unit)
        current = info["snapshot"]
        if not current["empty"] or current["conflict"]:
            raise Operational("BLOCKED", "canonical working-copy change is not empty and conflict-free")
        expected = expected_apply_snapshot(info["workspace_root"], current["change_id"], unit)
        unit["integration"] = {
            "pre": current,
            "expected_apply": expected,
            "description_rule": DESCRIPTION_STANDARD,
        }
        event(doc, "integration-preflight", args.unit_id, {"operation_id": current["operation_id"]})
    return "PREFLIGHT_OK", {"unit_id": args.unit_id, "pre": current, "expected_apply": expected}


def cmd_mark_applied(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc.get("units", {}).get(args.unit_id)
        if not unit or not unit.get("integration", {}).get("expected_apply"):
            raise Operational("REFUSED", "unit has no recorded Jujutsu preflight")
        observed = semantic_snapshot(validate_repo(doc)["workspace_root"])
        if not matches_expected_apply(doc["repository"]["workspace_root"], unit, observed):
            raise Operational("BLOCKED", "canonical change does not match the expected isolated delta")
        unit["integration"]["applied"] = observed
        event(doc, "isolated-change-applied", args.unit_id, {"change_id": observed["change_id"]})
    return "APPLIED", {"unit_id": args.unit_id, "snapshot": observed}


def cmd_mark_verified(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc.get("units", {}).get(args.unit_id)
        observed = semantic_snapshot(validate_repo(doc)["workspace_root"])
        if not unit or not matches_expected_apply(doc["repository"]["workspace_root"], unit, observed):
            raise Operational("BLOCKED", "canonical change moved after integration")
        unit["integration"]["verification"] = {
            "at": now_iso(),
            "digest": args.evidence_digest,
            "summary": args.summary,
        }
        event(doc, "canonical-verification-passed", args.unit_id, {"digest": args.evidence_digest})
    return "VERIFIED", {"unit_id": args.unit_id, "verification": unit["integration"]["verification"]}


def reconcile_change(doc: dict, unit: dict) -> dict | None:
    canonical = unit.get("integration", {}).get("canonical")
    if not isinstance(canonical, dict):
        return None
    observed = semantic_snapshot(doc["repository"]["workspace_root"])
    if observed["change_id"] == canonical["change_id"] and observed["commit_id"] == canonical["commit_id"]:
        return canonical
    return None


def restore(run_id: str, unit_id: str, lock_token: str) -> bool:
    from unit_workspace_state import _restore_operation

    with locked_manifest(run_id) as doc:
        validate_lock(doc, unit_id, lock_token)
        unit = doc.get("units", {}).get(unit_id)
        expected = unit.get("integration", {}).get("pre") if unit else None
        if not isinstance(expected, dict):
            raise Operational("REFUSED", "unit has no pre-integration operation snapshot")
        repo = doc["repository"]["workspace_root"]
    actual = _restore_operation(repo, expected["operation_id"])
    exact = (
        actual["change_id"] == expected["change_id"]
        and actual["commit_id"] == expected["commit_id"]
        and actual["delta_sha256"] == expected["delta_sha256"]
    )
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        unit["integration"]["restore"] = {"at": now_iso(), "exact": exact, "snapshot": actual}
        event(doc, "integration-operation-restored" if exact else "integration-restore-blocked", unit_id)
    return exact


def cmd_restore(args) -> tuple[str, dict]:
    if not restore(args.run_id, args.unit_id, args.lock_token):
        raise Operational("BLOCKED", "exact Jujutsu operation restoration could not be proven")
    return "PRESERVED", {"unit_id": args.unit_id, "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id)}


def integration_release(run_id: str, unit_id: str, lock_token: str) -> None:
    with locked_manifest(run_id, write=True) as doc:
        path, _ = validate_lock(doc, unit_id, lock_token)
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        doc["integration_lock"] = None
        event(doc, "integration-lock-released", unit_id)


def cmd_integration_release(args) -> tuple[str, dict]:
    integration_release(args.run_id, args.unit_id, args.lock_token)
    return "RELEASED", {"unit_id": args.unit_id}


def cmd_wave_advance(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc.get("units", {}).get(args.unit_id)
        if not unit or unit.get("state") not in {"accepted", "cleaned"}:
            raise Operational("REFUSED", "only an accepted wave change can advance siblings")
        members = wave_members(doc, unit)
        canonical = unit.get("integration", {}).get("canonical")
        if not canonical or args.canonical_change not in {canonical["change_id"], canonical["commit_id"]}:
            raise Operational("BLOCKED", "canonical wave identity does not match the accepted Jujutsu change")
        advanced = [candidate["unit_id"] for candidate in members if candidate["wave"]["position"] > unit["wave"]["position"]]
    return "WAVE_ADVANCED", {"unit_id": args.unit_id, "canonical_change": canonical, "eligible_siblings": advanced}


def cmd_integrate(args) -> tuple[str, dict]:
    """Run the atomic Jujutsu integration transaction.

    Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
    """
    return _atomic_integrate(args)


def cmd_verify_run(args) -> tuple[str, dict]:
    return _atomic_verify_run(args)
