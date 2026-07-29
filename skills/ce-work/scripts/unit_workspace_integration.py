"""Jujutsu canonical squash, locking, sequencing, and exact restoration."""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil

from unit_workspace_state import (
    Operational,
    TrustFailure,
    changed_paths,
    create_private,
    digest_bytes,
    event,
    find_attempt,
    jj,
    jj_text,
    locked_manifest,
    now_iso,
    read_private_json,
    revision,
    revision_contains,
    run_dir,
    runs_root,
    same_repository_state,
    snapshot,
    test_fault,
    unit_accepted_revision,
    validate_repo,
)


INTEGRATABLE_STATES = {
    "integration-pending",
    "integrated",
    "verified",
    "described",
    "preserved",
    "cleaned",
}


def integration_lock_path(doc: dict) -> str:
    ident = doc["repository"]["identity_digest"] + "\0" + doc["canonical"]["initial_commit_id"]
    root = runs_root(doc["repository"]["toplevel"])
    return os.path.join(root, ".locks", f"integration-{digest_bytes(ident.encode())}.json")


def read_integration_lock(path: str) -> dict:
    return read_private_json(path)


def validated_lock_nonce(doc: dict, unit_id: str, lock: dict) -> str:
    expected = {
        "run_id": doc["run_id"],
        "unit_id": unit_id,
        "repository": doc["repository"]["identity_digest"],
        "initial_revision": doc["canonical"]["initial_commit_id"],
    }
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
    nonce = validated_lock_nonce(doc, unit_id, lock)
    if nonce != token:
        raise Operational("BLOCKED", "integration lock token or identity mismatch")
    return path, lock


def cmd_integration_acquire(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        plan_verification = bool(getattr(args, "plan_verification", False))
        recover_only = bool(getattr(args, "recover_only", False))
        allowed_states = INTEGRATABLE_STATES | {"native-completed"}
        if not unit or unit["state"] not in allowed_states:
            raise Operational("REFUSED", "unit is not ready for integration")
        if not plan_verification and unit["state"] != "native-completed":
            validate_wave_order(doc, unit)
        path = integration_lock_path(doc)
        existing = doc.get("integration_lock")
        if existing:
            if not args.resume:
                raise Operational("REFUSED", "integration claim already exists; pass --resume to recover the same claim")
            if existing.get("phase", "held") != "held":
                raise Operational("REFUSED", "integration claim is releasing; resume or retry release before acquisition")
            validate_lock(doc, args.unit_id, existing["nonce"])
            return "ACQUIRED", {"lock_token": existing["nonce"], "resumed": True, "path": path}
        nonce = secrets.token_hex(24)
        resumed = False
        if recover_only:
            lock = read_integration_lock(path)
            nonce = validated_lock_nonce(doc, args.unit_id, lock)
            resumed = True
        else:
            payload = {
                "run_id": args.run_id,
                "unit_id": args.unit_id,
                "nonce": nonce,
                "repository": doc["repository"]["identity_digest"],
                "initial_revision": doc["canonical"]["initial_commit_id"],
                "created_at": now_iso(),
            }
            try:
                create_private(path, (json.dumps(payload, sort_keys=True) + "\n").encode())
                test_fault("integration-lock-after-create")
            except Operational as exc:
                if exc.word == "INTERRUPTED":
                    raise
                lock = read_integration_lock(path)
                if lock.get("run_id") == args.run_id and lock.get("unit_id") == args.unit_id:
                    if not args.resume:
                        raise Operational("REFUSED", "integration lock file already exists; pass --resume to recover its claim")
                    nonce = validated_lock_nonce(doc, args.unit_id, lock)
                    resumed = True
                else:
                    raise Operational(
                        "BLOCKED",
                        "another run/unit owns canonical integration",
                        {"owner_run": lock.get("run_id"), "owner_unit": lock.get("unit_id")},
                    )
    with locked_manifest(args.run_id, write=True) as doc:
        doc["integration_lock"] = {"unit_id": args.unit_id, "nonce": nonce, "path": path, "phase": "held"}
        event(doc, "integration-lock-acquired", args.unit_id, {"resumed": resumed})
    return "ACQUIRED", {"lock_token": nonce, "resumed": resumed, "path": path}


def semantic_snapshot(repo: str) -> dict:
    return snapshot(repo)


def expected_apply_snapshot(repo: str, pre_revision: str, unit: dict) -> dict:
    transport = unit["transport"]
    worker = revision(unit["workspace"]["path"])
    if worker["change_id"] != transport["change_id"] or worker["commit_id"] != transport["commit_id"]:
        raise Operational("BLOCKED", "pinned worker change moved before canonical preflight")
    paths = changed_paths(unit["workspace"]["path"], transport["base"], transport["commit_id"])
    if paths != sorted(transport["changed_paths"]):
        raise Operational("BLOCKED", "pinned worker paths differ from the transport receipt")
    return {"change_id": revision(repo, pre_revision)["change_id"], "changed_paths": paths}


def matches_expected_apply(repo: str, unit: dict, snap: dict | None = None) -> bool:
    snap = snap or semantic_snapshot(repo)
    pre = unit.get("integration", {}).get("pre_fold")
    expected = unit.get("integration", {}).get("expected_apply")
    if not pre or not expected:
        return False
    return (
        snap["change_id"] == pre["change_id"] == expected["change_id"]
        and not snap["conflicted"]
        and sorted(changed_paths(repo)) == sorted(expected["changed_paths"])
    )


def wave_members(doc: dict, unit: dict) -> list[dict]:
    wave = unit.get("wave", {})
    wave_id = wave.get("id")
    if not wave_id:
        return []
    base = wave.get("base")
    members = [
        candidate
        for candidate in doc.get("units", {}).values()
        if candidate.get("wave", {}).get("id") == wave_id
    ]
    positions = [candidate.get("wave", {}).get("position") for candidate in members]
    if any(candidate.get("wave", {}).get("base") != base for candidate in members):
        raise Operational("BLOCKED", "wave members do not share one recorded base")
    if len(set(positions)) != len(positions):
        raise Operational("BLOCKED", "wave positions are not unique")
    return sorted(members, key=lambda candidate: candidate["wave"]["position"])


def validate_wave_order(doc: dict, unit: dict) -> None:
    members = wave_members(doc, unit)
    earlier_unresolved = [
        candidate["unit_id"]
        for candidate in members
        if candidate["wave"]["position"] < unit["wave"]["position"]
        and unit_accepted_revision(candidate) is None
    ]
    if earlier_unresolved:
        raise Operational(
            "BLOCKED",
            "earlier wave units must be described or preserved before this squash",
            {"reason": "earlier wave unit not resolved", "units": earlier_unresolved},
        )


def wave_member_changed_paths(candidate: dict) -> set[str] | None:
    transport = candidate.get("transport") or {}
    if transport.get("commit_id"):
        paths = transport.get("changed_paths")
    elif candidate.get("state") == "native-completed":
        completion = find_attempt(candidate).get("fallback", {}).get("completed")
        paths = completion.get("changed_paths") if isinstance(completion, dict) else None
    else:
        return None
    if not isinstance(paths, list) or any(not isinstance(path, str) for path in paths):
        raise TrustFailure("wave member changed paths are malformed")
    return set(paths)


def validate_wave_collisions(
    doc: dict,
    unit: dict,
    overrides: dict[str, set[str]] | None = None,
    require_complete: bool = True,
) -> None:
    members = wave_members(doc, unit)
    if not members:
        return
    overrides = overrides or {}
    changed_by_unit: dict[str, set[str]] = {}
    unterminated: list[str] = []
    for candidate in members:
        unit_id = candidate["unit_id"]
        paths = overrides.get(unit_id)
        if paths is None:
            paths = wave_member_changed_paths(candidate)
        if paths is None:
            unterminated.append(unit_id)
        else:
            changed_by_unit[unit_id] = paths
    if unterminated and require_complete:
        raise Operational(
            "BLOCKED",
            "every wave worker must terminalize before the first squash",
            {"reason": "wave not fully terminalized", "units": unterminated},
        )
    collisions: dict[str, list[str]] = {}
    for index, left in enumerate(members):
        for right in members[index + 1 :]:
            left_paths = changed_by_unit.get(left["unit_id"])
            right_paths = changed_by_unit.get(right["unit_id"])
            if left_paths is None or right_paths is None:
                continue
            overlap = sorted(left_paths & right_paths)
            if overlap:
                collisions[f'{left["unit_id"]}:{right["unit_id"]}'] = overlap
    if collisions:
        raise Operational(
            "BLOCKED",
            "wave changes have a changed-path collision",
            {"reason": "changed-path collision", "collisions": collisions},
        )


def validate_wave_ready(doc: dict, unit: dict) -> None:
    if not wave_members(doc, unit):
        return
    validate_wave_order(doc, unit)
    validate_wave_collisions(doc, unit)


def validate_wave_advancement(members: list[dict], unit: dict, parent: str, canonical: str) -> list[str]:
    position = unit["wave"]["position"]
    targets = [candidate for candidate in members if candidate["wave"]["position"] > position]
    for candidate in targets:
        allowed = candidate["wave"].get("allowed_revisions", [])
        if canonical in allowed:
            continue
        if not allowed or allowed[-1] != parent:
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
    missing: list[str] = []
    unaccepted: list[str] = []
    for dependency_id in unit.get("dependencies", []):
        dependency = doc.get("units", {}).get(dependency_id)
        if dependency is None:
            missing.append(dependency_id)
        elif unit_accepted_revision(dependency) is None:
            unaccepted.append(dependency_id)
    if missing or unaccepted:
        raise Operational(
            "BLOCKED",
            "unit dependencies must have controller-accepted canonical revisions before preflight",
            {
                "unit_id": unit["unit_id"],
                "missing_dependencies": missing,
                "unaccepted_dependencies": unaccepted,
            },
        )


def dependency_advanced_revision(doc: dict, unit: dict, revision_id: str) -> bool:
    dependency_revisions = [
        unit_accepted_revision(doc["units"][dependency_id])
        for dependency_id in unit.get("dependencies", [])
    ]
    if any(value is None for value in dependency_revisions):
        return False
    accepted = {
        value
        for unit_id, candidate in doc.get("units", {}).items()
        if unit_id != unit.get("unit_id")
        if (value := unit_accepted_revision(candidate)) is not None
    }
    if revision_id not in accepted:
        return False
    required = {*accepted, *dependency_revisions, *unit.get("wave", {}).get("allowed_revisions", [])}
    required.discard(None)
    repo = doc["repository"]["toplevel"]
    return all(revision_contains(repo, ancestor, revision_id) for ancestor in required)


def validate_preflight_ancestry(doc: dict, unit: dict, revisions: set[str]) -> None:
    required = {
        value
        for unit_id, candidate in doc.get("units", {}).items()
        if unit_id != unit["unit_id"]
        if (value := unit_accepted_revision(candidate)) is not None
    }
    wave = unit.get("wave", {})
    required.update(value for value in wave.get("allowed_revisions", []) if value != wave.get("base"))
    repo = doc["repository"]["toplevel"]
    missing = {
        current: sorted(ancestor for ancestor in required if not revision_contains(repo, ancestor, current))
        for current in sorted(revisions)
    }
    missing = {current: values for current, values in missing.items() if values}
    if missing:
        raise Operational(
            "BLOCKED",
            "preflight revision omits controller-accepted prerequisites",
            {"unit_id": unit["unit_id"], "missing_ancestry": missing},
        )


def scope_expansion_pending(unit: dict) -> bool:
    receipt = find_attempt(unit).get("terminal_receipt")
    return isinstance(receipt, dict) and receipt.get("terminal_status") == "scope_expansion"


def cmd_preflight(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit["state"] not in {"integration-pending", "preserved"}:
            raise Operational("REFUSED", "unit is not integration-pending")
        validate_lock(doc, args.unit_id, args.lock_token)
        validate_dependencies_ready(doc, unit)
        if scope_expansion_pending(unit):
            raise Operational(
                "BLOCKED",
                "worker requested scope expansion; inspect the retained result and change, then resolve or re-dispatch explicitly",
                {
                    "unit_id": args.unit_id,
                    "terminal_status": "scope_expansion",
                    "transport": unit["transport"],
                    "recovery_path": unit["recovery_path"],
                },
            )
        validate_wave_ready(doc, unit)
        allowed = set(unit["wave"].get("allowed_revisions", []))
        requested = set(getattr(args, "allowed_revision", []) or [])
        if any(value not in allowed and not dependency_advanced_revision(doc, unit, value) for value in requested):
            raise Operational("BLOCKED", "unrecorded same-wave revision allowance")
        if info["commit_id"] not in allowed and not dependency_advanced_revision(doc, unit, info["commit_id"]):
            raise Operational("BLOCKED", "canonical revision advanced outside the recorded wave")
        validate_preflight_ancestry(doc, unit, requested | {info["commit_id"]})
        snap = semantic_snapshot(info["toplevel"])
        if not snap["working_copy_empty"] or snap["conflicted"]:
            raise Operational("BLOCKED", "canonical working-copy change is not empty and conflict-free at preflight")
        expected = expected_apply_snapshot(info["toplevel"], "@", unit)
        intent_revision = doc["revision"] + 1
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        unit["state"] = "integration-pending"
        unit["integration"] = {
            "intent_revision": intent_revision,
            "pre_fold": snap,
            "expected_apply": expected,
            "applied": None,
            "verification": None,
            "canonical_change": None,
            "restore": None,
        }
        event(doc, "canonical-squash-intent", args.unit_id, {"transport": unit["transport"]["commit_id"], "pre_revision": snap["commit_id"]})
    return "PREFLIGHT_OK", {"unit_id": args.unit_id, "pre_fold": snap, "transport": unit["transport"]}


def cmd_mark_applied(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit["state"] not in {"integration-pending", "integrated"} or not unit["integration"].get("pre_fold"):
            raise Operational("REFUSED", "no recorded preflight intent")
        repo = validate_repo(doc)["toplevel"]
        snap = semantic_snapshot(repo)
        if not matches_expected_apply(repo, unit, snap):
            raise Operational("BLOCKED", "canonical state does not match the expected Jujutsu squash")
    test_fault("after-apply-observed")
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        unit["state"] = "integrated"
        unit["integration"]["applied"] = snap
        event(doc, "transport-squashed", args.unit_id, {"commit_id": snap["commit_id"]})
    return "APPLIED", {"unit_id": args.unit_id, "commit_id": snap["commit_id"]}


def cmd_mark_verified(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit["state"] not in {"integrated", "verified"}:
            raise Operational("REFUSED", "unit is not squashed")
        repo = validate_repo(doc)["toplevel"]
        if not matches_expected_apply(repo, unit):
            raise Operational(
                "BLOCKED",
                "canonical state changed after the recorded squash",
                {"unit_id": args.unit_id, "reason": "canonical state no longer matches the expected squash"},
            )
        evidence = {"at": now_iso(), "digest": args.evidence_digest, "summary": args.summary}
        unit["integration"]["verification"] = evidence
        unit["state"] = "verified"
        event(doc, "canonical-verification-passed", args.unit_id, {"digest": args.evidence_digest})
    return "VERIFIED", {"unit_id": args.unit_id, "verification": evidence}


def reconcile_description(doc: dict, unit: dict) -> dict | None:
    repo = doc["repository"]["toplevel"]
    accepted = revision(repo, "@-")
    current = semantic_snapshot(repo)
    expected_change = unit["integration"]["pre_fold"]["change_id"]
    if (
        accepted["change_id"] == expected_change
        and accepted["description"].strip()
        and current["change_id"] != accepted["change_id"]
        and current["working_copy_empty"]
        and not current["conflicted"]
        and revision_contains(repo, accepted["commit_id"], current["commit_id"])
    ):
        return {**accepted, "tip_commit_id": current["commit_id"], "at": now_iso()}
    return None


def cmd_mark_described(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit["state"] not in {"verified", "described"}:
            raise Operational("REFUSED", "unit has not passed canonical verification")
        described = reconcile_description(doc, unit)
        if not described:
            raise Operational("BLOCKED", "canonical description/change/cleanliness do not match recorded integration")
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        unit["integration"]["canonical_change"] = described
        unit["state"] = "described"
        current = semantic_snapshot(doc["repository"]["toplevel"])
        doc["canonical"]["change_id"] = current["change_id"]
        doc["canonical"]["bookmark_state_sha256"] = current["bookmark_state_sha256"]
        event(doc, "canonical-change-confirmed", args.unit_id, {"change_id": described["change_id"]})
    return "DESCRIBED", {"unit_id": args.unit_id, "canonical_change": described}


def cmd_wave_advance(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit.get("state") != "described":
            raise Operational("REFUSED", "only a described wave unit can advance its siblings")
        validate_lock(doc, args.unit_id, args.lock_token)
        members = wave_members(doc, unit)
        if not members:
            raise Operational("REFUSED", "unit does not belong to a parallel wave")
        validate_wave_ready(doc, unit)
        canonical = getattr(args, "canonical_revision", None)
        recorded = unit.get("integration", {}).get("canonical_change", {})
        if recorded.get("commit_id") != canonical or not revision_contains(info["toplevel"], canonical, info["commit_id"]):
            raise Operational("BLOCKED", "canonical wave revision does not match manifest and current revset")
        parent = unit.get("integration", {}).get("pre_fold", {}).get("commit_id")
        validate_wave_advancement(members, unit, parent, canonical)
    with locked_manifest(args.run_id, write=True) as doc:
        unit = doc["units"][args.unit_id]
        position = unit["wave"]["position"]
        advanced = advance_wave_allowed_revisions(wave_members(doc, unit), position, canonical)
        event(doc, "wave-advanced", args.unit_id, {"canonical_revision": canonical, "eligible_siblings": advanced})
    return "WAVE_ADVANCED", {"unit_id": args.unit_id, "canonical_revision": canonical, "eligible_siblings": advanced}


def path_in_revision(repo: str, revision_id: str, relative: str) -> bool:
    listed = jj_text(repo, "file", "list", "-r", revision_id, relative, check=False)
    return relative in listed.splitlines()


def remove_introduced_paths(repo: str, unit: dict) -> None:
    pre = unit["integration"]["pre_fold"]["commit_id"]
    for relative in unit["transport"]["changed_paths"]:
        if path_in_revision(repo, pre, relative):
            continue
        target = os.path.abspath(os.path.join(repo, relative))
        if os.path.commonpath([repo, target]) != repo:
            raise Operational("BLOCKED", "change path escaped canonical workspace")
        if os.path.islink(target) or os.path.isfile(target):
            os.unlink(target)
        elif os.path.isdir(target):
            shutil.rmtree(target)
        parent = os.path.dirname(target)
        while parent != repo and os.path.commonpath([repo, parent]) == repo:
            try:
                os.rmdir(parent)
            except OSError:
                break
            parent = os.path.dirname(parent)


def restore(run_id: str, unit_id: str, lock_token: str) -> bool:
    with locked_manifest(run_id) as doc:
        validate_lock(doc, unit_id, lock_token)
        unit = doc["units"].get(unit_id)
        if not unit or not unit.get("integration", {}).get("pre_fold"):
            raise Operational("REFUSED", "unit has no pre-squash snapshot")
        repo = doc["repository"]["toplevel"]
        pre = dict(unit["integration"]["pre_fold"])
        current = semantic_snapshot(repo)
        already_exact = same_repository_state(current, pre)
        expected_apply = matches_expected_apply(repo, unit, current)
        if not (already_exact or expected_apply or unit.get("state") == "restoring"):
            raise Operational("BLOCKED", "canonical state is not a proven in-flight squash; refusing restoration")
    with locked_manifest(run_id, write=True) as doc:
        doc["units"][unit_id]["state"] = "restoring"
        event(doc, "restore-intent", unit_id)
    if not already_exact:
        jj(repo, "op", "restore", pre["operation_id"])
        test_fault("restore-after-operation")
        with locked_manifest(run_id) as doc:
            remove_introduced_paths(repo, doc["units"][unit_id])
    test_fault("restore-after-path-removal")
    actual = semantic_snapshot(repo)
    exact = same_repository_state(actual, pre)
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        unit["integration"]["restore"] = {
            "at": now_iso(),
            "exact": exact,
            "already_exact": already_exact,
            "snapshot": actual,
        }
        if exact:
            unit["state"] = "preserved"
            event(doc, "canonical-restored", unit_id)
        else:
            blocker = {"at": now_iso(), "unit_id": unit_id, "reason": "exact pre-squash restoration could not be proven"}
            doc["blockers"].append(blocker)
            event(doc, "restore-blocked", unit_id)
    return exact


def cmd_restore(args) -> tuple[str, dict]:
    exact = restore(args.run_id, args.unit_id, args.lock_token)
    if not exact:
        raise Operational("BLOCKED", "exact pre-squash restoration could not be proven", {"retain_integration_lock": True})
    return "PRESERVED", {"unit_id": args.unit_id, "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id)}


def release_lock_is_owned(doc: dict, unit_id: str, lock_token: str, lock: dict) -> bool:
    expected = {
        "run_id": doc["run_id"],
        "unit_id": unit_id,
        "repository": doc["repository"]["identity_digest"],
        "initial_revision": doc["canonical"]["initial_commit_id"],
    }
    if any(lock.get(key) != value for key, value in expected.items()):
        return False
    nonce = lock.get("nonce")
    return isinstance(nonce, str) and bool(re.fullmatch(r"[0-9a-f]{48}", nonce)) and nonce == lock_token


def integration_release(run_id: str, unit_id: str, lock_token: str) -> None:
    with locked_manifest(run_id, write=True) as doc:
        held = doc.get("integration_lock")
        if not held or held.get("unit_id") != unit_id or held.get("nonce") != lock_token:
            raise Operational("REFUSED", "integration lock token or identity mismatch")
        unit = doc["units"].get(unit_id)
        pre_apply = bool(unit and unit.get("state") == "integration-pending" and not unit.get("integration"))
        if not unit or (unit["state"] not in {"described", "preserved", "cleaned", "native-completed"} and not pre_apply):
            raise Operational("REFUSED", "integration lock releases only before preflight or after accepted completion")
        path = held.get("path")
        if path != integration_lock_path(doc):
            raise Operational("BLOCKED", "manifest integration lock path changed")
        phase = held.get("phase", "held")
        if phase == "held":
            validate_lock(doc, unit_id, lock_token)
            held["phase"] = "releasing"
            held["release_started_at"] = now_iso()
            event(doc, "integration-lock-release-intent", unit_id)
        elif phase != "releasing":
            raise Operational("BLOCKED", "manifest integration claim has an unknown phase")
    with locked_manifest(run_id, write=True) as doc:
        held = doc.get("integration_lock")
        if not held or held.get("unit_id") != unit_id or held.get("nonce") != lock_token or held.get("phase") != "releasing":
            raise Operational("BLOCKED", "manifest integration claim changed")
        if held.get("path") != path or path != integration_lock_path(doc):
            raise Operational("BLOCKED", "manifest integration lock path changed")
        current = None
        try:
            current = read_integration_lock(path)
        except TrustFailure:
            if os.path.lexists(path):
                raise
        if current is not None and release_lock_is_owned(doc, unit_id, lock_token, current):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
        test_fault("integration-release-after-unlink")
        if os.path.lexists(path):
            current = read_integration_lock(path)
            if release_lock_is_owned(doc, unit_id, lock_token, current):
                raise Operational("BLOCKED", "integration lock file remained after release")
        doc["integration_lock"] = None
        event(doc, "integration-lock-released", unit_id)


def cmd_integration_release(args) -> tuple[str, dict]:
    integration_release(args.run_id, args.unit_id, args.lock_token)
    return "RELEASED", {"unit_id": args.unit_id}
