"""Canonical jj integration, locking, wave sequencing, and restoration."""

from __future__ import annotations

import json
import os
import re
import secrets

from unit_workspace_state import *
from unit_workspace_jobs import find_attempt, scope_expansion_pending


def integration_lock_path(doc: dict) -> str:
    ident = doc["repository"]["identity_digest"] + "\0" + doc["bookmark"]["name"]
    return os.path.join(os.path.dirname(run_dir(doc["run_id"])), ".locks", f"integration-{digest_bytes(ident.encode())}.json")


def validate_lock(doc: dict, unit_id: str, token: str) -> tuple[str, dict]:
    path = integration_lock_path(doc)
    lock = read_private_json(path)
    expected = {"run_id": doc["run_id"], "unit_id": unit_id, "repository": doc["repository"]["identity_digest"], "bookmark": doc["bookmark"]["name"]}
    if any(lock.get(k) != v for k, v in expected.items()) or lock.get("nonce") != token:
        raise Operational("BLOCKED", "integration lock identity mismatch")
    return path, lock


def cmd_integration_acquire(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_repo(doc)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit["state"] not in INTEGRATABLE_STATES | {"preserved", "accepted", "cleaned", "native-completed"}:
            raise Operational("REFUSED", "unit is not ready for integration")
        if doc.get("integration_lock"):
            if not args.resume:
                raise Operational("REFUSED", "integration claim already exists")
            token = doc["integration_lock"]["nonce"]
            validate_lock(doc, args.unit_id, token)
            return "ACQUIRED", {"lock_token": token, "resumed": True}
        token = secrets.token_hex(24)
        path = integration_lock_path(doc)
        payload = {"run_id": args.run_id, "unit_id": args.unit_id, "nonce": token, "repository": doc["repository"]["identity_digest"], "bookmark": doc["bookmark"]["name"], "created_at": now_iso()}
        try:
            create_private(path, (json.dumps(payload, sort_keys=True) + "\n").encode())
        except FileExistsError:
            existing = read_private_json(path)
            same_claim = all(existing.get(key) == payload[key] for key in ("run_id", "unit_id", "repository", "bookmark"))
            if not args.resume or not same_claim or not isinstance(existing.get("nonce"), str):
                raise Operational("BLOCKED", "canonical integration is locked by another or unreconciled claim")
            token = existing["nonce"]
        doc["integration_lock"] = {"unit_id": args.unit_id, "nonce": token, "path": path}
        event(doc, "integration-lock-acquired", args.unit_id)
        return "ACQUIRED", {"lock_token": token, "resumed": False, "path": path}


def validate_dependencies_ready(doc: dict, unit: dict) -> None:
    missing = [uid for uid in unit.get("dependencies", []) if not unit_accepted_change(doc["units"].get(uid, {}))]
    if missing:
        raise Operational("BLOCKED", "unit dependencies lack accepted jj changes", {"units": missing})


def cmd_preflight(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"].get(args.unit_id)
        if not unit or unit["state"] not in {"integration-pending", "preserved"}:
            raise Operational("REFUSED", "unit is not integration-pending")
        validate_dependencies_ready(doc, unit)
        if scope_expansion_pending(unit):
            raise Operational("BLOCKED", "worker requested scope expansion", {"recovery_path": unit["recovery_path"]})
        repo = validate_repo(doc)["toplevel"]
        snap = semantic_snapshot(repo)
        if not snap["status_empty"] or snap["conflicts"]:
            raise Operational("BLOCKED", "canonical working-copy change is not empty at preflight")
        allowed = set(unit.get("wave", {}).get("allowed_changes", []))
        allowed.update(args.allowed_change or [])
        if snap["change_id"] not in allowed and snap["change_id"] != unit["workspace"]["base"]:
            raise Operational("BLOCKED", "canonical change advanced outside the recorded wave")
        unit.setdefault("integration", {})["pre_fold"] = snap
        unit["state"] = "integration-pending"
        event(doc, "canonical-integrate-intent", args.unit_id, {"transport": unit["transport"]["change_id"]})
        return "PREFLIGHT_OK", {"unit_id": args.unit_id, "pre_fold": snap, "transport": unit["transport"]}


def cmd_mark_applied(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        repo = validate_repo(doc)["toplevel"]
        transport = unit["transport"]["change_id"]
        if change_id(repo) != transport:
            raise Operational("BLOCKED", "canonical workspace is not editing the rebased transport change")
        if jj_text(repo, "resolve", "--list", "-r", transport, check=False):
            raise Operational("BLOCKED", "transport change has conflicts after rebase")
        expected_parent = unit["integration"]["pre_fold"]["commit_id"]
        actual_parents = parent_ids(repo, transport)
        if actual_parents != [expected_parent]:
            raise Operational("BLOCKED", "rebased transport does not have the accepted canonical change as sole parent")
        actual_paths = changed_paths(repo, transport)
        if actual_paths != unit["transport"]["changed_paths"]:
            raise Operational("BLOCKED", "rebased transport scope differs from the terminalized transport")
        unit["state"] = "integrated"
        unit["integration"]["applied"] = {
            "at": now_iso(),
            "transport_change": transport,
            "commit_id": commit_id(repo, transport),
            "parent_ids": actual_parents,
            "changed_paths": actual_paths,
        }
        event(doc, "transport-change-rebased", args.unit_id, {"change_id": transport})
        return "APPLIED", {"unit_id": args.unit_id, "transport_change": transport}


def cmd_mark_verified(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        ignored_state = args.ignored_state
        if isinstance(ignored_state, str):
            try:
                ignored_state = json.loads(ignored_state)
            except ValueError as exc:
                raise Operational("REFUSED", "ignored-state receipt must be valid JSON") from exc
        evidence = {"at": now_iso(), "digest": args.evidence_digest, "summary": args.summary, "ignored_state": ignored_state}
        unit["integration"]["verification"] = evidence
        unit["state"] = "verified"
        event(doc, "canonical-verification-passed", args.unit_id, {"digest": args.evidence_digest})
        return "VERIFIED", {"unit_id": args.unit_id, "verification": evidence}


def reconcile_change(doc: dict, unit: dict) -> dict | None:
    record = unit.get("integration", {}).get("canonical_change")
    if not isinstance(record, dict):
        return None
    repo = doc["repository"]["toplevel"]
    resolved = change_id(repo, record["change_id"])
    return record if resolved == record["change_id"] and not jj_text(repo, "resolve", "--list", "-r", resolved, check=False) else None


def cmd_mark_accepted(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        canonical = reconcile_change(doc, unit)
        if not canonical:
            raise Operational("BLOCKED", "canonical change receipt does not match jj state")
        unit["state"] = "accepted"
        event(doc, "canonical-change-confirmed", args.unit_id, {"change_id": canonical["change_id"]})
        return "ACCEPTED", {"unit_id": args.unit_id, "canonical_change": canonical}


def cmd_wave_advance(args) -> tuple[str, dict]:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, args.unit_id, args.lock_token)
        unit = doc["units"][args.unit_id]
        accepted = unit_accepted_change(unit)
        if accepted != args.canonical_change:
            raise Operational("BLOCKED", "canonical wave change does not match accepted state")
        advanced = []
        for candidate in doc["units"].values():
            if candidate.get("wave", {}).get("id") == unit.get("wave", {}).get("id") and candidate["wave"]["position"] > unit["wave"]["position"]:
                candidate["wave"].setdefault("allowed_changes", []).append(accepted)
                advanced.append(candidate["unit_id"])
        event(doc, "wave-advanced", args.unit_id, {"canonical_change": accepted, "eligible_siblings": advanced})
        return "WAVE_ADVANCED", {"unit_id": args.unit_id, "canonical_change": accepted, "eligible_siblings": advanced}


def restore(run_id: str, unit_id: str, lock_token: str) -> bool:
    with locked_manifest(run_id, write=True) as doc:
        validate_lock(doc, unit_id, lock_token)
        unit = doc["units"][unit_id]
        pre = unit.get("integration", {}).get("pre_fold")
        if not pre:
            raise Operational("REFUSED", "unit has no pre-integration operation snapshot")
        restore_operation(doc["repository"]["toplevel"], pre["operation_id"])
        actual = semantic_snapshot(doc["repository"]["toplevel"])
        exact = all(actual[key] == pre[key] for key in (
            "change_id", "commit_id", "parent_ids", "description", "changed_paths",
            "status_sha256", "status_empty", "conflicts",
        ))
        unit["integration"]["restore"] = {"at": now_iso(), "exact": exact, "snapshot": actual}
        unit["state"] = "preserved" if exact else "restoring"
        event(doc, "canonical-operation-restored" if exact else "restore-blocked", unit_id)
        return exact


def cmd_restore(args) -> tuple[str, dict]:
    if not restore(args.run_id, args.unit_id, args.lock_token):
        raise Operational("BLOCKED", "exact operation restoration could not be proven")
    return "PRESERVED", {"unit_id": args.unit_id, "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id)}


def integration_release(run_id: str, unit_id: str, lock_token: str) -> None:
    with locked_manifest(run_id, write=True) as doc:
        path, _ = validate_lock(doc, unit_id, lock_token)
        with contextlib.suppress(FileNotFoundError):
            os.unlink(path)
        doc["integration_lock"] = None
        event(doc, "integration-lock-released", unit_id)


def cmd_integration_release(args) -> tuple[str, dict]:
    integration_release(args.run_id, args.unit_id, args.lock_token)
    return "RELEASED", {"unit_id": args.unit_id}
