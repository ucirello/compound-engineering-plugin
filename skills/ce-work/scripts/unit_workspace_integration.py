"""Canonical Jujutsu integration, locking, sequencing, and restoration."""

from __future__ import annotations

import json
import os
import re
import secrets

from unit_workspace_state import *
from unit_workspace_jobs import find_attempt


def integration_lock_path(doc: dict) -> str:
    ident = doc["repository"]["identity_digest"] + "\0" + doc["workspace"]["name"]
    return os.path.join(os.path.dirname(run_dir(doc["run_id"])), ".locks", f"integration-{digest_bytes(ident.encode())}.json")


def read_integration_lock(path: str) -> dict:
    return read_private_json(path)


def validated_lock_nonce(doc: dict, unit_id: str, lock: dict) -> str:
    expected = {
        "run_id": doc["run_id"],
        "unit_id": unit_id,
        "repository": doc["repository"]["identity_digest"],
        "workspace_name": doc["workspace"]["name"],
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
    if validated_lock_nonce(doc, unit_id, lock) != token:
        raise Operational("BLOCKED", "integration lock token or identity mismatch")
    return path, lock


def cmd_integration_acquire(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        plan_verification = bool(getattr(args, "plan_verification", False))
        recover_only = bool(getattr(args, "recover_only", False))
        allowed = INTEGRATABLE_STATES | {"preserved", "accepted", "cleaned"}
        if plan_verification or (recover_only and unit and unit.get("state") == "native-completed"):
            allowed.add("native-completed")
        if not unit or unit.get("state") not in allowed:
            raise Operational("REFUSED", "unit is not ready for integration")
        if not plan_verification and unit.get("state") != "native-completed":
            validate_wave_order(doc, unit)
        path = integration_lock_path(doc)
        existing = doc.get("integration_lock")
        if existing:
            if not args.resume:
                raise Operational("REFUSED", "integration claim already exists; pass --resume to recover it")
            validate_lock(doc, args.unit_id, existing["nonce"])
            return "ACQUIRED", {"lock_token": existing["nonce"], "resumed": True, "path": path}
        nonce = secrets.token_hex(24)
        payload = {
            "run_id": args.run_id,
            "unit_id": args.unit_id,
            "nonce": nonce,
            "repository": doc["repository"]["identity_digest"],
            "workspace_name": doc["workspace"]["name"],
            "created_at": now_iso(),
        }
        if recover_only:
            nonce = validated_lock_nonce(doc, args.unit_id, read_integration_lock(path))
            resumed = True
        else:
            try:
                create_private(path, (json.dumps(payload, sort_keys=True) + "\n").encode())
                test_fault("integration-lock-after-create")
                resumed = False
            except Operational as exc:
                if exc.word == "INTERRUPTED":
                    raise
                lock = read_integration_lock(path)
                if not args.resume:
                    raise Operational("REFUSED", "integration lock exists; pass --resume to recover it") from exc
                nonce = validated_lock_nonce(doc, args.unit_id, lock)
                resumed = True
    with locked_manifest(args.run_id, write=True) as doc:
        doc["integration_lock"] = {"unit_id": args.unit_id, "nonce": nonce, "path": path, "phase": "held"}
        event(doc, "integration-lock-acquired", args.unit_id, {"resumed": resumed})
    return "ACQUIRED", {"lock_token": nonce, "resumed": resumed, "path": path}


def semantic_snapshot(repo: str) -> dict:
    revision = revision_info(repo)
    paths = sorted(status_paths(repo))
    diff = jj(repo, "diff", "-r", "@")
    return {
        **revision,
        "changed_paths": paths,
        "diff_sha256": digest_bytes(diff),
        "empty": not paths,
    }


def expected_apply_snapshot(repo: str, pre_revision: str, unit: dict) -> dict:
    transport = unit["transport"]
    current = revision_info(repo, transport["commit_id"])
    if current["change_id"] != transport["change_id"] or current["parent_commit_ids"] != [transport["base"]]:
        raise Operational("BLOCKED", "pinned worker revision changed after terminalization")
    return {
        "source_revision": transport["commit_id"],
        "changed_paths": list(transport["changed_paths"]),
        "canonical_revision": pre_revision,
    }


def matches_expected_apply(repo: str, unit: dict, snap: dict | None = None) -> bool:
    snap = snap or semantic_snapshot(repo)
    pre = unit.get("integration", {}).get("pre_fold")
    expected = unit.get("integration", {}).get("expected_apply")
    return bool(
        pre
        and expected
        and snap["change_id"] == pre["change_id"]
        and set(snap["changed_paths"]) == set(expected["changed_paths"])
    )


def wave_members(doc: dict, unit: dict) -> list[dict]:
    wave = unit.get("wave", {})
    if not wave.get("id"):
        return []
    members = [candidate for candidate in doc.get("units", {}).values() if candidate.get("wave", {}).get("id") == wave["id"]]
    positions = [candidate.get("wave", {}).get("position") for candidate in members]
    if any(candidate.get("wave", {}).get("base") != wave.get("base") for candidate in members):
        raise Operational("BLOCKED", "wave members do not share one recorded base")
    if len(positions) != len(set(positions)):
        raise Operational("BLOCKED", "wave positions are not unique")
    return sorted(members, key=lambda candidate: candidate["wave"]["position"])


def validate_wave_order(doc: dict, unit: dict) -> None:
    unresolved = [
        candidate["unit_id"]
        for candidate in wave_members(doc, unit)
        if candidate["wave"]["position"] < unit["wave"]["position"]
        and unit_accepted_revision(candidate) is None
    ]
    if unresolved:
        raise Operational("BLOCKED", "earlier wave units must be resolved before this integration", {"units": unresolved})


def wave_member_changed_paths(candidate: dict) -> set[str] | None:
    transport = candidate.get("transport", {})
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


def validate_wave_collisions(doc: dict, unit: dict, overrides: dict[str, set[str]] | None = None, require_complete: bool = True) -> None:
    overrides = overrides or {}
    changed: dict[str, set[str]] = {}
    missing = []
    for candidate in wave_members(doc, unit):
        paths = overrides.get(candidate["unit_id"])
        if paths is None:
            paths = wave_member_changed_paths(candidate)
        if paths is None:
            missing.append(candidate["unit_id"])
        else:
            changed[candidate["unit_id"]] = paths
    if missing and require_complete:
        raise Operational("BLOCKED", "every wave member must terminalize before integration", {"units": missing})
    ids = sorted(changed)
    for index, left in enumerate(ids):
        for right in ids[index + 1:]:
            collision = sorted(changed[left] & changed[right])
            if collision:
                raise Operational("BLOCKED", "wave revisions have a changed-path collision", {"left": left, "right": right, "paths": collision})


def validate_wave_ready(doc: dict, unit: dict) -> None:
    validate_wave_order(doc, unit)
    validate_wave_collisions(doc, unit)


def validate_wave_advancement(members: list[dict], unit: dict, parent: str, canonical: str) -> list[str]:
    if not revision_is_ancestor(unit["workspace"]["path"], parent, canonical):
        raise Operational("BLOCKED", "canonical revision does not descend from the recorded pre-integration revision")
    return [canonical]


def advance_wave_allowed_revisions(members: list[dict], position: int, canonical: str) -> list[str]:
    advanced = []
    for candidate in members:
        if candidate["wave"]["position"] > position:
            allowed = candidate["wave"].setdefault("allowed_revisions", [])
            if canonical not in allowed:
                allowed.append(canonical)
            advanced.append(candidate["unit_id"])
    return advanced


def validate_dependencies_ready(doc: dict, unit: dict) -> None:
    unresolved = [dependency for dependency in unit.get("dependencies", []) if unit_accepted_revision(doc["units"].get(dependency, {})) is None]
    if unresolved:
        raise Operational("BLOCKED", "unit dependencies are not integrated", {"dependencies": unresolved})


def cmd_preflight(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        info = validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit.get("state") != "integration-pending":
            raise Operational("REFUSED", "unit is not integration-pending")
        validate_lock(doc, args.unit_id, args.lock_token)
        validate_dependencies_ready(doc, unit)
        validate_wave_ready(doc, unit)
        allowed = set(unit.get("wave", {}).get("allowed_revisions", []))
        allowed.update(getattr(args, "allowed_revision", []) or [])
        if info["commit_id"] not in allowed:
            raise Operational("BLOCKED", "canonical revision advanced outside the recorded unit contract")
        if status_paths(info["toplevel"]):
            raise Operational("BLOCKED", "canonical working-copy change is not empty")
        expected = expected_apply_snapshot(info["toplevel"], info["commit_id"], unit)
        unit["integration"]["intent_revision"] = doc["revision"] + 1
        unit["integration"]["pre_fold"] = semantic_snapshot(info["toplevel"])
        unit["integration"]["expected_apply"] = expected
        event(doc, "canonical-apply-intent", args.unit_id, {"source_revision": expected["source_revision"], "canonical_revision": info["commit_id"]})
        return "PREFLIGHT_OK", {"pre_fold": unit["integration"]["pre_fold"], "expected_apply": expected}


def cmd_mark_applied(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"].get(args.unit_id)
        if not unit or not matches_expected_apply(doc["repository"]["toplevel"], unit):
            raise Operational("BLOCKED", "canonical state does not match the expected Jujutsu fileset application")
        snap = semantic_snapshot(doc["repository"]["toplevel"])
        unit["integration"]["applied"] = {"at": now_iso(), "snapshot": snap}
        event(doc, "canonical-applied", args.unit_id, {"revision": snap["commit_id"]})
        return "APPLIED", {"snapshot": snap}


def cmd_mark_verified(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"].get(args.unit_id)
        if not unit or not matches_expected_apply(doc["repository"]["toplevel"], unit):
            raise Operational("BLOCKED", "canonical state changed before verification was recorded")
        receipt = {
            "at": now_iso(),
            "evidence_digest": args.evidence_digest,
            "summary": args.summary,
            "ignored_state": json.loads(args.ignored_state) if args.ignored_state else None,
        }
        unit["integration"]["verification"] = receipt
        unit["state"] = "verified"
        event(doc, "canonical-verified", args.unit_id)
        return "VERIFIED", {"verification": receipt}


def reconcile_revision(doc: dict, unit: dict) -> dict | None:
    canonical = unit.get("integration", {}).get("canonical_revision")
    if canonical and revision_info(doc["repository"]["toplevel"], canonical["commit_id"])["change_id"] == canonical["change_id"]:
        return canonical
    return None


def cmd_mark_accepted(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit.get("state") not in {"verified", "accepted"}:
            raise Operational("REFUSED", "unit is not verified")
        if unit.get("state") == "accepted":
            canonical = reconcile_revision(doc, unit)
            if canonical:
                return "ACCEPTED", {"canonical_revision": canonical, "resumed": True}
        repo = doc["repository"]["toplevel"]
        current_snapshot = semantic_snapshot(repo)
        current = current_snapshot
        pre = unit["integration"]["pre_fold"]
        verified_snapshot = unit.get("integration", {}).get("applied", {}).get("snapshot")
        if (
            not isinstance(verified_snapshot, dict)
            or current["change_id"] != pre["change_id"]
            or current["parent_commit_ids"] != pre["parent_commit_ids"]
            or current["changed_paths"] != verified_snapshot.get("changed_paths")
            or current["diff_sha256"] != verified_snapshot.get("diff_sha256")
        ):
            raise Operational("BLOCKED", "described canonical revision no longer matches the integrated fileset")
        canonical = {
            "change_id": current["change_id"],
            "commit_id": current["commit_id"],
            "parent_commit_ids": list(current["parent_commit_ids"]),
            "at": now_iso(),
        }
        unit["integration"]["canonical_revision"] = canonical
        unit["state"] = "accepted"
        event(doc, "canonical-revision-recorded", args.unit_id, canonical)
        return "ACCEPTED", {"canonical_revision": canonical, "resumed": False}


def cmd_wave_advance(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"].get(args.unit_id)
        recorded = unit.get("integration", {}).get("canonical_revision") if unit else None
        canonical = recorded.get("commit_id") if isinstance(recorded, dict) else None
        if canonical != args.canonical_revision:
            raise Operational("BLOCKED", "wave advancement revision is not the controller-accepted revision")
        current = revision_info(doc["repository"]["toplevel"])
        if current["parent_commit_ids"] != [canonical]:
            raise Operational("BLOCKED", "canonical workspace did not advance to an empty child of the accepted revision")
        members = wave_members(doc, unit)
        advanced = advance_wave_allowed_revisions(members, unit["wave"]["position"], current["commit_id"])
        event(doc, "wave-advanced", args.unit_id, {"canonical_revision": canonical, "next_revision": current["commit_id"], "units": advanced})
        return "WAVE_ADVANCED", {"canonical_revision": canonical, "next_revision": current["commit_id"], "units": advanced}


def remove_introduced_paths(repo: str, unit: dict) -> None:
    return None


def restore(run_id: str, unit_id: str, lock_token: str) -> bool:
    with locked_manifest(run_id) as doc:
        validate_lock(doc, unit_id, lock_token)
        unit = doc["units"].get(unit_id)
        pre = unit.get("integration", {}).get("pre_fold") if unit else None
        if not pre:
            return False
        repo = doc["repository"]["toplevel"]
        paths = unit.get("transport", {}).get("changed_paths", [])
    with locked_manifest(run_id, write=True) as doc:
        doc["units"][unit_id]["state"] = "restoring"
        event(doc, "restore-intent", unit_id)
    if paths:
        jj(repo, "restore", "--from", pre["commit_id"], "--into", "@", *root_file_filesets(paths))
    jj(repo, "describe", "-r", "@", "-m", pre["description"])
    actual = semantic_snapshot(repo)
    exact = (
        actual["change_id"] == pre["change_id"]
        and actual["parent_commit_ids"] == pre["parent_commit_ids"]
        and actual["changed_paths"] == pre["changed_paths"]
        and actual["diff_sha256"] == pre["diff_sha256"]
        and actual["description"] == pre["description"]
    )
    with locked_manifest(run_id, write=True) as doc:
        unit = doc["units"][unit_id]
        unit["integration"]["restore"] = {"at": now_iso(), "exact": exact, "snapshot": actual}
        unit["state"] = "preserved" if exact else "restoring"
        event(doc, "canonical-restored" if exact else "restore-blocked", unit_id)
    if not exact:
        raise Operational("BLOCKED", "exact pre-integration restoration could not be proven")
    return True


def cmd_restore(args) -> tuple[str, dict]:
    exact = restore(args.run_id, args.unit_id, args.lock_token)
    return "RESTORED" if exact else "NOOP", {"unit_id": args.unit_id, "exact": exact}


def release_lock_is_owned(doc: dict, unit_id: str, lock_token: str, lock: dict) -> bool:
    try:
        return validated_lock_nonce(doc, unit_id, lock) == lock_token
    except Operational:
        return False


def integration_release(run_id: str, unit_id: str, lock_token: str) -> None:
    with locked_manifest(run_id, write=True) as doc:
        path, _ = validate_lock(doc, unit_id, lock_token)
        doc["integration_lock"] = None
        event(doc, "integration-lock-release-intent", unit_id)
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    with locked_manifest(run_id, write=True) as doc:
        event(doc, "integration-lock-released", unit_id)


def cmd_integration_release(args) -> tuple[str, dict]:
    integration_release(args.run_id, args.unit_id, args.lock_token)
    return "RELEASED", {"unit_id": args.unit_id}
