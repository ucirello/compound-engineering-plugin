"""Canonical Jujutsu integration, locking, sequencing, and restoration."""

from __future__ import annotations

import json
import os
import re
import secrets

from unit_workspace_state import *
from unit_workspace_jobs import find_attempt, scope_expansion_pending


def integration_lock_path(doc: dict) -> str:
    identity = doc["repository"]["identity_digest"]
    root = os.path.dirname(locate_run_dir(doc["run_id"]))
    return os.path.join(root, ".locks", f"integration-{digest_bytes(identity.encode())}.json")


def read_integration_lock(path: str) -> dict:
    return read_private_json(path)


def validated_lock_nonce(doc: dict, unit_id: str, lock: dict) -> str:
    expected = {"run_id": doc["run_id"], "unit_id": unit_id, "repository": doc["repository"]["identity_digest"]}
    if any(lock.get(key) != value for key, value in expected.items()):
        raise Operational("BLOCKED", "integration lock identity mismatch")
    nonce = lock.get("nonce")
    if not isinstance(nonce, str) or not re.fullmatch(r"[0-9a-f]{48}", nonce):
        raise TrustFailure("integration lock nonce is malformed")
    return nonce


def validate_lock(doc: dict, unit_id: str, token: str) -> tuple[str, dict]:
    path = integration_lock_path(doc)
    try:
        lock = read_integration_lock(path)
    except TrustFailure as exc:
        if not os.path.lexists(path):
            raise Operational("BLOCKED", "integration lock is missing") from exc
        raise
    if validated_lock_nonce(doc, unit_id, lock) != token:
        raise Operational("BLOCKED", "integration lock token or identity mismatch")
    return path, lock


def cmd_integration_acquire(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        plan_verification = bool(getattr(args, "plan_verification", False))
        recover_only = bool(getattr(args, "recover_only", False))
        allowed = INTEGRATABLE_STATES | {"preserved", "committed", "cleaned"}
        if plan_verification or (recover_only and unit and unit.get("state") == "native-completed"):
            allowed.add("native-completed")
        if not unit or unit.get("state") not in allowed:
            raise Operational("REFUSED", "unit is not ready for integration")
        if not plan_verification and unit.get("state") != "native-completed":
            validate_wave_order(doc, unit)
        path = integration_lock_path(doc)
        existing = doc.get("integration_lock")
        if existing:
            if not getattr(args, "resume", False):
                raise Operational("REFUSED", "integration claim already exists; resume the same claim")
            validate_lock(doc, args.unit_id, existing["nonce"])
            return "ACQUIRED", {"lock_token": existing["nonce"], "resumed": True, "path": path}
        nonce = secrets.token_hex(24)
        resumed = False
        if recover_only:
            nonce = validated_lock_nonce(doc, args.unit_id, read_integration_lock(path))
            resumed = True
        else:
            payload = {"run_id": args.run_id, "unit_id": args.unit_id, "nonce": nonce, "repository": doc["repository"]["identity_digest"], "created_at": now_iso()}
            try:
                create_private(path, (json.dumps(payload, sort_keys=True) + "\n").encode())
                test_fault("integration-lock-after-create")
            except Operational as exc:
                if exc.word == "INTERRUPTED":
                    raise
                observed = read_integration_lock(path)
                if observed.get("run_id") != args.run_id or observed.get("unit_id") != args.unit_id or not getattr(args, "resume", False):
                    raise Operational("BLOCKED", "another run or unit owns canonical integration")
                nonce = validated_lock_nonce(doc, args.unit_id, observed)
                resumed = True
    with locked_manifest(args.run_id, write=True) as doc:
        doc["integration_lock"] = {"unit_id": args.unit_id, "nonce": nonce, "path": path, "phase": "held"}
        event(doc, "integration-lock-acquired", args.unit_id, {"resumed": resumed})
    return "ACQUIRED", {"lock_token": nonce, "resumed": resumed, "path": path}


def semantic_snapshot(repo: str) -> dict:
    jj(repo, "status")
    revision = revision_snapshot(repo)
    paths = changed_paths(repo)
    diff = jj(repo, "diff", "--git", "--color", "never")
    return {
        "operation": operation_id(repo),
        "change_id": revision["change_id"],
        "commit": revision["commit"],
        "parents": revision["parents"],
        "description": revision["description"],
        "paths": paths,
        "diff_sha256": digest_bytes(diff),
        "empty": not paths,
        "conflicted": has_conflicts(repo),
    }


def same_revision_state(left: dict, right: dict) -> bool:
    keys = ("change_id", "parents", "description", "paths", "diff_sha256", "empty", "conflicted")
    return all(left.get(key) == right.get(key) for key in keys)


def same_exact_revision_state(left: dict, right: dict) -> bool:
    keys = ("change_id", "commit", "parents", "description", "paths", "diff_sha256", "empty", "conflicted")
    return isinstance(right, dict) and all(left.get(key) == right.get(key) for key in keys)


def matches_expected_apply(repo: str, unit: dict, snapshot: dict | None = None) -> bool:
    expected = unit.get("integration", {}).get("expected_apply")
    current = snapshot or semantic_snapshot(repo)
    return isinstance(expected, dict) and all(current.get(key) == value for key, value in expected.items() if key != "operation")


def wave_members(doc: dict, unit: dict) -> list[dict]:
    wave = unit.get("wave", {})
    if not wave.get("id"):
        return []
    members = [candidate for candidate in doc.get("units", {}).values() if candidate.get("wave", {}).get("id") == wave["id"]]
    if any(candidate.get("wave", {}).get("base") != wave.get("base") for candidate in members):
        raise Operational("BLOCKED", "wave members do not share one recorded base")
    positions = [candidate.get("wave", {}).get("position") for candidate in members]
    if len(set(positions)) != len(positions):
        raise Operational("BLOCKED", "wave positions are not unique")
    return sorted(members, key=lambda candidate: candidate["wave"]["position"])


def validate_wave_order(doc: dict, unit: dict) -> None:
    unresolved = [
        candidate["unit_id"] for candidate in wave_members(doc, unit)
        if candidate["wave"]["position"] < unit["wave"]["position"]
        and candidate.get("state") not in {"committed", "preserved", "cleaned", "native-completed"}
    ]
    if unresolved:
        raise Operational("BLOCKED", "earlier wave units must be accepted or preserved before this integration", {"units": unresolved})


def wave_member_changed_paths(candidate: dict) -> set[str] | None:
    transport = candidate.get("transport", {})
    if transport.get("commit"):
        paths = transport.get("changed_paths")
    elif candidate.get("state") == "native-completed":
        completion = find_attempt(candidate).get("fallback", {}).get("completed")
        paths = completion.get("changed_paths") if isinstance(completion, dict) else None
    else:
        return None
    if not isinstance(paths, list) or any(not isinstance(path, str) for path in paths):
        raise TrustFailure("wave member changed paths are malformed")
    return set(paths)


def validate_wave_collisions(doc: dict, unit: dict, overrides: dict[str, set[str]] | None = None, require_complete: bool = True) -> None:
    members = wave_members(doc, unit)
    if not members:
        return
    overrides = overrides or {}
    changed: dict[str, set[str]] = {}
    missing: list[str] = []
    for candidate in members:
        paths = overrides.get(candidate["unit_id"])
        if paths is None:
            paths = wave_member_changed_paths(candidate)
        if paths is None:
            missing.append(candidate["unit_id"])
        else:
            changed[candidate["unit_id"]] = paths
    if missing and require_complete:
        raise Operational("BLOCKED", "every wave worker must terminalize before the first integration", {"units": missing})
    collisions: dict[str, list[str]] = {}
    for index, left in enumerate(members):
        for right in members[index + 1:]:
            overlap = sorted(changed.get(left["unit_id"], set()) & changed.get(right["unit_id"], set()))
            if overlap:
                collisions[f'{left["unit_id"]}:{right["unit_id"]}'] = overlap
    if collisions:
        raise Operational("BLOCKED", "wave transports have a changed-path collision", {"collisions": collisions})


def validate_wave_ready(doc: dict, unit: dict) -> None:
    validate_wave_order(doc, unit)
    validate_wave_collisions(doc, unit)


def validate_wave_advancement(members: list[dict], unit: dict, parent: str, canonical: str) -> list[str]:
    targets = [candidate for candidate in members if candidate["wave"]["position"] > unit["wave"]["position"]]
    for candidate in targets:
        allowed = candidate["wave"].get("allowed_revisions", [])
        if canonical not in allowed and (not allowed or allowed[-1] != parent):
            raise Operational("BLOCKED", "wave advancement is not the exact recorded canonical chain")
    return [candidate["unit_id"] for candidate in targets]


def advance_wave_allowed_revisions(members: list[dict], position: int, canonical: str) -> list[str]:
    advanced: list[str] = []
    for candidate in members:
        if candidate["wave"]["position"] <= position:
            continue
        allowed = candidate["wave"].setdefault("allowed_revisions", [])
        if canonical not in allowed:
            allowed.append(canonical)
        advanced.append(candidate["unit_id"])
    return advanced


def validate_dependencies_ready(doc: dict, unit: dict) -> None:
    missing = [dependency for dependency in unit.get("dependencies", []) if dependency not in doc.get("units", {})]
    unaccepted = [dependency for dependency in unit.get("dependencies", []) if dependency in doc.get("units", {}) and unit_accepted_commit(doc["units"][dependency]) is None]
    if missing or unaccepted:
        raise Operational("BLOCKED", "unit dependencies lack accepted canonical changes", {"missing_dependencies": missing, "unaccepted_dependencies": unaccepted})


def dependency_advanced_revision(doc: dict, unit: dict, revision: str) -> bool:
    repo = doc["repository"]["toplevel"]
    required = [unit_accepted_commit(doc["units"][dependency]) for dependency in unit.get("dependencies", [])]
    return bool(required) and all(commit is not None and is_ancestor(repo, commit, revision) for commit in required)


def cmd_preflight(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit.get("state") not in {"integration-pending", "preserved"}:
            raise Operational("REFUSED", "unit is not integration-pending")
        validate_lock(doc, args.unit_id, args.lock_token)
        validate_dependencies_ready(doc, unit)
        if scope_expansion_pending(unit):
            raise Operational("BLOCKED", "worker requested scope expansion", {"unit_id": args.unit_id, "transport": unit["transport"], "recovery_path": unit["recovery_path"]})
        validate_wave_ready(doc, unit)
        snapshot = semantic_snapshot(info["toplevel"])
        allowed = set(unit["wave"].get("allowed_revisions", []))
        requested_values = getattr(args, "allowed_change", None) or []
        requested = {resolve_revision(info["toplevel"], value) for value in requested_values}
        if any(value not in allowed for value in requested):
            raise Operational("BLOCKED", "unrecorded same-wave canonical revision allowance")
        current_allowed = info["commit"] in allowed or (snapshot["empty"] and len(snapshot["parents"]) == 1 and snapshot["parents"][0] in allowed)
        if not current_allowed:
            raise Operational("BLOCKED", "canonical working-copy commit advanced outside the recorded wave")
        dependency_commits = [unit_accepted_commit(doc["units"][dependency]) for dependency in unit.get("dependencies", [])]
        if any(commit is None or not is_ancestor(info["toplevel"], commit, info["commit"]) for commit in dependency_commits):
            raise Operational("BLOCKED", "canonical working-copy change omits an accepted dependency")
        if not snapshot["empty"] or snapshot["conflicted"]:
            raise Operational("BLOCKED", "canonical working-copy change is not empty and conflict-free at preflight")
        intent_revision = doc["revision"] + 1
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        unit["state"] = "integration-pending"
        unit["integration"]["intent_revision"] = intent_revision
        unit["integration"]["pre_fold"] = snapshot
        unit["integration"]["expected_apply"] = None
        event(doc, "canonical-apply-intent", args.unit_id, {"transport_change": unit["transport"].get("change_id"), "pre_change": snapshot["change_id"]})
    return "PREFLIGHT_OK", {"unit_id": args.unit_id, "pre_fold": snapshot, "transport": unit["transport"]}


def apply_transport(run_id: str, unit_id: str, token: str) -> dict:
    with locked_manifest(run_id) as doc:
        validate_lock(doc, unit_id, token)
        unit = doc["units"][unit_id]
        repo = doc["repository"]["toplevel"]
        transport = unit["transport"]["commit"]
        before_ids = all_commit_ids(repo)
    jj(repo, "duplicate", transport, "-o", "@")
    after_ids = all_commit_ids(repo)
    created = sorted(after_ids - before_ids)
    if len(created) != 1:
        raise Operational("BLOCKED", "transport duplication did not create exactly one integration change", {"created": created})
    try:
        jj(repo, "squash", "--from", created[0], "--into", "@")
    except Operational:
        jj(repo, "abandon", created[0], check=False)
        raise
    snapshot = semantic_snapshot(repo)
    if snapshot["conflicted"]:
        raise Operational("BLOCKED", "transport integration produced conflicts", {"changed_paths": snapshot["paths"]})
    expected_paths = set(unit["transport"].get("changed_paths", []))
    if set(snapshot["paths"]) != expected_paths:
        raise Operational("BLOCKED", "integrated paths differ from the terminalized transport", {"expected_paths": sorted(expected_paths), "actual_paths": snapshot["paths"]})
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        unit["state"] = "integrated"
        unit["integration"]["expected_apply"] = snapshot
        unit["integration"]["applied"] = {"at": now_iso(), "snapshot": snapshot, "duplicate": created[0]}
        event(doc, "transport-applied", unit_id, {"change": snapshot["change_id"], "commit": snapshot["commit"]})
    return snapshot


def cmd_mark_applied(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit.get("state") not in {"integration-pending", "integrated", "verified"}:
            raise Operational("REFUSED", "unit has no recorded integration intent")
        snapshot = semantic_snapshot(doc["repository"]["toplevel"])
        if unit["integration"].get("expected_apply") is None:
            pre = unit["integration"].get("pre_fold")
            expected_paths = set(unit.get("transport", {}).get("changed_paths", []))
            if (
                not isinstance(pre, dict)
                or snapshot["change_id"] != pre["change_id"]
                or set(snapshot["paths"]) != expected_paths
                or snapshot["empty"]
                or snapshot["conflicted"]
            ):
                raise Operational("BLOCKED", "canonical state is not a valid applied transport change")
            unit["integration"]["expected_apply"] = snapshot
            unit["integration"]["applied"] = {"at": now_iso(), "snapshot": snapshot, "external_transition": True}
            unit["state"] = "integrated"
            event(doc, "transport-applied", args.unit_id, {"change": snapshot["change_id"], "commit": snapshot["commit"]})
        elif not matches_expected_apply(doc["repository"]["toplevel"], unit, snapshot):
            raise Operational("BLOCKED", "canonical state does not match the recorded Jujutsu integration")
    return "APPLIED", {"unit_id": args.unit_id, "snapshot": snapshot}


def cmd_mark_verified(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit.get("state") not in {"integrated", "verified"} or not matches_expected_apply(doc["repository"]["toplevel"], unit):
            raise Operational("BLOCKED", "canonical state changed after the recorded transport application")
        evidence = {"at": now_iso(), "digest": args.evidence_digest, "summary": args.summary}
        ignored_state = getattr(args, "ignored_state", None)
        if isinstance(ignored_state, str):
            ignored_state = parse_json_arg(ignored_state, "ignored-state")
        if ignored_state is not None:
            evidence["ignored_state"] = ignored_state
        unit["integration"]["verification"] = evidence
        unit["state"] = "verified"
        event(doc, "canonical-verification-passed", args.unit_id, {"digest": args.evidence_digest})
    return "VERIFIED", {"unit_id": args.unit_id, "verification": evidence}


def reconcile_commit(doc: dict, unit: dict) -> dict | None:
    repo = doc["repository"]["toplevel"]
    current = semantic_snapshot(repo)
    expected = unit.get("integration", {}).get("expected_apply")
    if not isinstance(expected, dict):
        return None
    if current["change_id"] != expected["change_id"] or current["paths"] != expected["paths"] or current["conflicted"]:
        return None
    return {"change_id": current["change_id"], "commit": current["commit"], "parents": current["parents"], "description": current["description"], "at": now_iso()}


def cmd_mark_committed(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit.get("state") not in {"verified", "committed"}:
            raise Operational("REFUSED", "unit has not passed canonical verification")
        canonical = reconcile_commit(doc, unit)
        if not canonical:
            raise Operational("BLOCKED", "canonical Jujutsu change does not match recorded integration")
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        unit["integration"]["canonical_change"] = canonical
        unit["state"] = "committed"
        event(doc, "canonical-change-confirmed", args.unit_id, {"change": canonical["change_id"], "commit": canonical["commit"]})
    return "COMMITTED", {"unit_id": args.unit_id, "canonical_change": canonical}


def cmd_wave_advance(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit.get("state") != "committed":
            raise Operational("REFUSED", "only an accepted wave unit can advance siblings")
        validate_lock(doc, args.unit_id, args.lock_token)
        members = wave_members(doc, unit)
        if not members:
            raise Operational("REFUSED", "unit does not belong to a parallel wave")
        value = args.canonical_change
        canonical = resolve_revision(info["toplevel"], value)
        recorded = unit.get("integration", {}).get("canonical_change", {})
        if recorded.get("commit") != canonical:
            raise Operational("BLOCKED", "canonical wave change does not match the manifest")
        parent = unit.get("integration", {}).get("pre_fold", {}).get("commit")
        validate_wave_advancement(members, unit, parent, canonical)
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        advanced = advance_wave_allowed_revisions(wave_members(doc, unit), unit["wave"]["position"], canonical)
        event(doc, "wave-advanced", args.unit_id, {"canonical_change": canonical, "eligible_siblings": advanced})
    return "WAVE_ADVANCED", {"unit_id": args.unit_id, "canonical_change": canonical, "eligible_siblings": advanced}


def restore(run_id: str, unit_id: str, lock_token: str) -> bool:
    with locked_manifest(run_id) as doc:
        validate_lock(doc, unit_id, lock_token)
        unit = doc["units"].get(unit_id)
        if not unit or not unit.get("integration", {}).get("pre_fold"):
            raise Operational("REFUSED", "unit has no pre-integration snapshot")
        repo = doc["repository"]["toplevel"]
        pre = dict(unit["integration"]["pre_fold"])
        integration = unit["integration"]
        allowed = [
            candidate for candidate in (
                integration.get("expected_apply"),
                integration.get("applied", {}).get("snapshot") if isinstance(integration.get("applied"), dict) else None,
            ) if isinstance(candidate, dict)
        ]
    current = semantic_snapshot(repo)
    if same_exact_revision_state(current, pre):
        actual = current
        exact = True
    elif not any(same_exact_revision_state(current, candidate) for candidate in allowed):
        raise Operational(
            "BLOCKED",
            "canonical state is neither the recorded pre-integration snapshot nor an exact controller-recorded applied state; refusing to touch @",
            {"current_snapshot": current, "retain_integration_lock": True},
        )
    else:
        with locked_manifest(run_id, write=True) as doc:
            doc["units"][unit_id]["state"] = "restoring"
            event(doc, "restore-intent", unit_id, {"current_snapshot": current})
        jj(repo, "restore", "--from", pre["commit"], "--to", "@")
        # Restoration reuses recorded bytes and therefore does not compose a new description.
        if revision_snapshot(repo)["description"] != pre["description"]:
            jj(repo, "describe", "-m", pre["description"])
        actual = semantic_snapshot(repo)
        exact = same_exact_revision_state(actual, pre)
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        unit["integration"]["restore"] = {"at": now_iso(), "exact": exact, "snapshot": actual}
        if exact:
            unit["state"] = "preserved"
            event(doc, "canonical-restored", unit_id)
        else:
            doc["blockers"].append({"at": now_iso(), "unit_id": unit_id, "reason": "exact pre-integration restoration could not be proven"})
            event(doc, "restore-blocked", unit_id)
    return exact


def cmd_restore(args) -> tuple[str, dict]:
    if not restore(args.run_id, args.unit_id, args.lock_token):
        raise Operational("BLOCKED", "exact pre-integration restoration could not be proven")
    return "PRESERVED", {"unit_id": args.unit_id, "recovery_path": os.path.join(locate_run_dir(args.run_id), "units", args.unit_id)}


def release_lock_is_owned(doc: dict, unit_id: str, lock_token: str, lock: dict) -> bool:
    try:
        return validated_lock_nonce(doc, unit_id, lock) == lock_token
    except Operational:
        return False


def integration_release(run_id: str, unit_id: str, lock_token: str) -> None:
    with locked_manifest(run_id, write=True) as doc:
        held = doc.get("integration_lock")
        if not held or held.get("unit_id") != unit_id or held.get("nonce") != lock_token:
            raise Operational("REFUSED", "integration lock token or identity mismatch")
        unit = doc["units"].get(unit_id)
        pre_apply = bool(unit and unit.get("state") == "integration-pending" and not unit.get("integration", {}).get("pre_fold"))
        if not unit or (unit.get("state") not in {"committed", "preserved", "cleaned", "native-completed"} and not pre_apply):
            raise Operational("REFUSED", "integration lock releases only before preflight or after accepted completion")
        path = held.get("path")
        if path != integration_lock_path(doc):
            raise Operational("BLOCKED", "manifest integration lock path changed")
        validate_lock(doc, unit_id, lock_token)
        held["phase"] = "releasing"
        event(doc, "integration-lock-release-intent", unit_id)
    with locked_manifest(run_id, write=True) as doc:
        if os.path.lexists(path):
            observed = read_integration_lock(path)
            if release_lock_is_owned(doc, unit_id, lock_token, observed):
                os.unlink(path)
        test_fault("integration-release-after-unlink")
        if os.path.lexists(path):
            raise Operational("BLOCKED", "integration lock file remained after release")
        doc["integration_lock"] = None
        event(doc, "integration-lock-released", unit_id)


def cmd_integration_release(args) -> tuple[str, dict]:
    integration_release(args.run_id, args.unit_id, args.lock_token)
    return "RELEASED", {"unit_id": args.unit_id}
