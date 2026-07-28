"""Fail-stop Jujutsu squash, verification, describe, and run verification transactions."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

from unit_workspace_state import (
    O_NOFOLLOW,
    Operational,
    TrustFailure,
    changed_paths,
    digest_bytes,
    event,
    ignored_snapshot,
    jj,
    jj_text,
    locked_manifest,
    now_iso,
    revision_contains,
    run_dir,
    same_repository_state,
    test_fault,
    unit_accepted_revision,
    validate_private_dir,
    validate_repo,
)
from unit_workspace_integration import (
    cmd_integration_acquire,
    cmd_integration_release,
    cmd_mark_applied,
    cmd_mark_described,
    cmd_mark_verified,
    cmd_preflight,
    cmd_restore,
    cmd_wave_advance,
    matches_expected_apply,
    remove_introduced_paths,
    semantic_snapshot,
    validate_lock,
)
from unit_workspace_lifecycle import (
    cmd_cleanup,
    pending_plan_wide_verification,
    plan_wide_verification_attempts,
    receipted_plan_wide_verification,
)

MAX_IGNORED_SNAPSHOT_ENTRIES = 512
MAX_IGNORED_SNAPSHOT_BYTES = 64 * 1024 * 1024
DESCRIPTION_RULE = "Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards."
DESCRIPTION_CONTEXT = (
    "The project's active runtime instructions and conventions are required input. "
    "Inspect descriptions with `jj log`; syntax observed there takes precedence over generic guidance "
    "and over the wording of the sentence above. Apply the linked Go guidance only where it is "
    "compatible with those project instructions and the repository's `jj log` history. Do not use "
    "fixed types, scopes, templates, examples, or identity footers."
)


def _args(**values):
    return SimpleNamespace(**values)


def _verification_command(args, operation: str = "integrate") -> list[str]:
    command = list(args.verification_command)
    if command and command[0] == "--":
        command.pop(0)
    if not command or any(not value or "\0" in value for value in command):
        raise Operational("REFUSED", f"{operation} requires a non-empty verification command after --")
    return command


def _change_description(args) -> str:
    description = (args.description or "").strip()
    if not description or "\0" in description or len(description.encode()) > 1024:
        raise Operational(
            "REFUSED",
            f"change description must be non-empty, NUL-free, and at most 1024 bytes. "
            f"{DESCRIPTION_RULE} {DESCRIPTION_CONTEXT}",
        )
    return description


def _verification_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("JJ_WORKSPACE", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _remove_owned_new_paths(repo: str, paths: set[str], pre_revision: str) -> None:
    tracked = set(filter(None, jj_text(repo, "file", "list", "-r", pre_revision).splitlines()))
    for rel in sorted(paths, key=lambda value: (value.count("/"), value), reverse=True):
        if rel in tracked or any(path.startswith(f"{rel}/") for path in tracked):
            continue
        target = os.path.abspath(os.path.join(repo, rel))
        if os.path.commonpath([repo, target]) != repo:
            raise Operational("BLOCKED", "verification artifact path escaped canonical workspace")
        if os.path.islink(target) or os.path.isfile(target):
            os.unlink(target)
        elif os.path.isdir(target):
            shutil.rmtree(target)


def _directory_paths(repo: str) -> set[str]:
    """Snapshot workspace directories without traversing VCS or private runtime metadata."""
    return set(_directory_snapshot(repo))


def _directory_snapshot(repo: str) -> dict[str, int]:
    """Snapshot workspace directory paths and modes without traversing private metadata."""
    repo = os.path.abspath(repo)
    directories: dict[str, int] = {}
    test_fault("directory-snapshot-before-walk")

    def fail(error: OSError) -> None:
        raise Operational("BLOCKED", f"could not inspect workspace directories: {error}")

    for parent, names, _files in os.walk(repo, topdown=True, onerror=fail, followlinks=False):
        names[:] = [name for name in names if name not in {".jj", ".git", ".tmp"}]
        for name in names:
            path = os.path.join(parent, name)
            try:
                entry = os.lstat(path)
            except OSError as exc:
                raise Operational("BLOCKED", f"could not inspect workspace directory {path}: {exc}") from exc
            if stat.S_ISDIR(entry.st_mode) and not stat.S_ISLNK(entry.st_mode):
                directories[os.path.relpath(path, repo)] = stat.S_IMODE(entry.st_mode)
    return directories


def _restore_directory_snapshot(repo: str, snapshot_state: dict[str, int]) -> set[str]:
    """Restore only preexisting directory entries; never remove an obstruction."""
    restored: set[str] = set()
    for rel, mode in sorted(snapshot_state.items(), key=lambda item: (item[0].count("/"), item[0])):
        target = _artifact_path(repo, rel)
        try:
            entry = os.lstat(target)
        except FileNotFoundError:
            try:
                os.mkdir(target, mode)
                os.chmod(target, mode, follow_symlinks=False)
            except OSError as exc:
                raise Operational("BLOCKED", f"could not restore pre-verification directory {rel}: {exc}") from exc
            restored.add(rel)
            continue
        if not stat.S_ISDIR(entry.st_mode) or stat.S_ISLNK(entry.st_mode):
            raise Operational("BLOCKED", f"pre-verification directory is obstructed: {rel}")
        if stat.S_IMODE(entry.st_mode) != mode:
            try:
                os.chmod(target, mode, follow_symlinks=False)
            except OSError as exc:
                raise Operational("BLOCKED", f"could not restore pre-verification directory mode {rel}: {exc}") from exc
            restored.add(rel)
    return restored


def _new_parent_directories(paths: set[str], before: set[str]) -> set[str]:
    directories: set[str] = set()
    for path in paths:
        parent = os.path.dirname(path)
        while parent and parent != "." and parent not in before:
            directories.add(parent)
            parent = os.path.dirname(parent)
    return directories


def _ignored_paths(repo: str) -> set[str]:
    """Return ignored files without changing ordinary clean-state rules."""
    return set(ignored_snapshot(repo))


def _artifact_path(repo: str, rel: str) -> str:
    repo = os.path.abspath(repo)
    target = os.path.abspath(os.path.join(repo, rel))
    if target == repo or os.path.commonpath([repo, target]) != repo:
        raise Operational("BLOCKED", "ignored artifact path escaped canonical workspace")
    return target


def _preflight_ignored_artifacts(repo: str, paths: set[str]) -> tuple[list[dict], dict[str, int]]:
    if len(paths) > MAX_IGNORED_SNAPSHOT_ENTRIES:
        raise Operational(
            "REFUSED",
            f"ignored artifact snapshot exceeds {MAX_IGNORED_SNAPSHOT_ENTRIES} entries",
            {"entries": len(paths), "max_entries": MAX_IGNORED_SNAPSHOT_ENTRIES},
        )

    planned: list[dict] = []
    directories: dict[str, int] = {}
    total_bytes = 0
    repo = os.path.abspath(repo)
    for rel in sorted(paths):
        target = _artifact_path(repo, rel)
        parent = os.path.dirname(target)
        ancestors: list[str] = []
        while parent != repo:
            ancestors.append(parent)
            parent = os.path.dirname(parent)
        for directory in reversed(ancestors):
            directory_rel = os.path.relpath(directory, repo)
            entry = os.lstat(directory)
            if not stat.S_ISDIR(entry.st_mode) or stat.S_ISLNK(entry.st_mode):
                raise Operational("REFUSED", f"ignored artifact parent is not a real directory: {directory_rel}")
            directories[directory_rel] = stat.S_IMODE(entry.st_mode)

        before = os.lstat(target)
        if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode) or before.st_nlink != 1:
            raise Operational("REFUSED", f"cannot safely snapshot ignored artifact: {rel}")
        uid_getter = getattr(os, "geteuid", None) or getattr(os, "getuid", None)
        effective_uid = uid_getter() if uid_getter is not None else None
        if effective_uid is not None and before.st_uid != effective_uid:
            raise Operational("REFUSED", f"ignored artifact is not owned by the current user: {rel}")
        total_bytes += before.st_size
        if total_bytes > MAX_IGNORED_SNAPSHOT_BYTES:
            raise Operational(
                "REFUSED",
                f"ignored artifact snapshot exceeds {MAX_IGNORED_SNAPSHOT_BYTES} bytes",
                {"bytes": total_bytes, "max_bytes": MAX_IGNORED_SNAPSHOT_BYTES},
            )
        planned.append({"rel": rel, "target": target, "before": before})
    return planned, directories


def _snapshot_ignored_artifacts(repo: str, paths: set[str], private_parent: str) -> dict:
    """Copy bounded ignored regular files to private state without following symlinks."""
    validate_private_dir(private_parent)
    planned, directories = _preflight_ignored_artifacts(repo, paths)
    backup_root = os.path.join(private_parent, f"ignored-snapshot-{secrets.token_hex(8)}")
    os.mkdir(backup_root, 0o700)
    validate_private_dir(backup_root)
    files: dict[str, dict] = {}
    try:
        for index, plan in enumerate(planned):
            rel = plan["rel"]
            target = plan["target"]
            before = plan["before"]
            source_fd = os.open(target, os.O_RDONLY | O_NOFOLLOW)
            backup = os.path.join(backup_root, f"{index:08d}")
            backup_fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
            digest = hashlib.sha256()
            try:
                opened = os.fstat(source_fd)
                if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino) or not stat.S_ISREG(opened.st_mode):
                    raise Operational("BLOCKED", f"ignored artifact changed while being snapshotted: {rel}")
                remaining = before.st_size
                while remaining:
                    chunk = os.read(source_fd, min(1024 * 1024, remaining))
                    if not chunk:
                        raise Operational("BLOCKED", f"ignored artifact changed while being snapshotted: {rel}")
                    remaining -= len(chunk)
                    digest.update(chunk)
                    view = memoryview(chunk)
                    while view:
                        written = os.write(backup_fd, view)
                        view = view[written:]
                if os.read(source_fd, 1):
                    raise Operational("BLOCKED", f"ignored artifact changed while being snapshotted: {rel}")
                finished = os.fstat(source_fd)
                if (
                    finished.st_size != before.st_size
                    or finished.st_mtime_ns != before.st_mtime_ns
                    or finished.st_ctime_ns != before.st_ctime_ns
                ):
                    raise Operational("BLOCKED", f"ignored artifact changed while being snapshotted: {rel}")
            finally:
                os.close(source_fd)
                os.close(backup_fd)
            files[rel] = {
                "backup": backup,
                "digest": digest.hexdigest(),
                "mode": stat.S_IMODE(before.st_mode),
                "size": before.st_size,
            }
    except Exception:
        shutil.rmtree(backup_root)
        raise
    return {"root": backup_root, "files": files, "directories": directories}


def _artifact_matches(target: str, record: dict) -> bool:
    try:
        before = os.lstat(target)
        if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
            return False
        fd = os.open(target, os.O_RDONLY | O_NOFOLLOW)
    except (FileNotFoundError, OSError):
        return False
    digest = hashlib.sha256()
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino) or not stat.S_ISREG(opened.st_mode):
            return False
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        os.close(fd)
    return (
        before.st_size == record["size"]
        and stat.S_IMODE(before.st_mode) == record["mode"]
        and digest.hexdigest() == record["digest"]
    )


def _remove_artifact_entry(path: str) -> None:
    try:
        entry = os.lstat(path)
    except FileNotFoundError:
        return
    if stat.S_ISDIR(entry.st_mode) and not stat.S_ISLNK(entry.st_mode):
        shutil.rmtree(path)
    else:
        os.unlink(path)


def _restore_ignored_artifacts(repo: str, snapshot_state: dict) -> set[str]:
    """Restore snapshotted ignored files and parent directory modes exactly."""
    repo = os.path.abspath(repo)
    restored: set[str] = set()
    for rel, mode in sorted(snapshot_state["directories"].items(), key=lambda item: item[0].count("/")):
        directory = _artifact_path(repo, rel)
        try:
            entry = os.lstat(directory)
        except FileNotFoundError:
            entry = None
        if entry is not None and (not stat.S_ISDIR(entry.st_mode) or stat.S_ISLNK(entry.st_mode)):
            _remove_artifact_entry(directory)
            entry = None
        if entry is None:
            os.mkdir(directory, mode)
        os.chmod(directory, mode, follow_symlinks=False)

    for rel, record in sorted(snapshot_state["files"].items()):
        target = _artifact_path(repo, rel)
        if _artifact_matches(target, record):
            continue
        restored.add(rel)
        _remove_artifact_entry(target)
        parent = os.path.dirname(target)
        temporary = os.path.join(parent, f".rocketclaw-restore-{secrets.token_hex(8)}")
        source_fd = os.open(record["backup"], os.O_RDONLY | O_NOFOLLOW)
        target_fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, record["mode"])
        try:
            while True:
                chunk = os.read(source_fd, 1024 * 1024)
                if not chunk:
                    break
                view = memoryview(chunk)
                while view:
                    written = os.write(target_fd, view)
                    view = view[written:]
            os.fchmod(target_fd, record["mode"])
        finally:
            os.close(source_fd)
            os.close(target_fd)
        os.replace(temporary, target)
        if not _artifact_matches(target, record):
            raise Operational("BLOCKED", f"ignored artifact restoration could not be proven: {rel}")
    shutil.rmtree(snapshot_state["root"])
    return restored


def _restore_owned_verification(
    run_id: str,
    unit_id: str,
    token: str,
    before: dict,
    before_paths: set[str],
    after_paths: set[str],
) -> None:
    with locked_manifest(run_id) as doc:
        validate_repo(doc)
        unit = doc["units"].get(unit_id)
        if not unit or not unit.get("integration", {}).get("pre_fold"):
            raise Operational("BLOCKED", "owned verification restoration lacks pre-squash evidence")
        repo = doc["repository"]["toplevel"]
        pre = dict(unit["integration"]["pre_fold"])
        if not matches_expected_apply(repo, unit, before):
            raise Operational("BLOCKED", "owned verification did not start from the expected transport squash")
        current = semantic_snapshot(repo)
        if current["change_id"] != before["change_id"]:
            raise Operational("BLOCKED", "verification changed the canonical Jujutsu change; refusing automatic restoration")
        verification_paths = after_paths - before_paths
    with locked_manifest(run_id, write=True) as doc:
        doc["units"][unit_id]["state"] = "restoring"
        event(doc, "restore-intent", unit_id, {"source": "controller-owned-verification"})
    cmd_restore(_args(run_id=run_id, unit_id=unit_id, lock_token=token))
    with locked_manifest(run_id) as doc:
        remove_introduced_paths(repo, doc["units"][unit_id])
    _remove_owned_new_paths(repo, verification_paths, pre["commit_id"])
    actual = semantic_snapshot(repo)
    exact = same_repository_state(actual, pre)
    if not exact:
        with locked_manifest(run_id, write=True) as doc:
            blocker = {"at": now_iso(), "unit_id": unit_id, "reason": "exact pre-squash restoration could not be proven"}
            doc["blockers"].append(blocker)
            event(doc, "restore-blocked", unit_id, {"source": "controller-owned-verification"})
        raise Operational("BLOCKED", "exact pre-squash restoration could not be proven", {"retain_integration_lock": True})


def _verification_log(run_id: str, unit_id: str) -> tuple[str, object]:
    parent = os.path.join(run_dir(run_id), "units", unit_id, "result")
    validate_private_dir(parent)
    path = os.path.join(parent, f"host-verification-{secrets.token_hex(6)}.log")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
    return path, os.fdopen(fd, "wb")


def _run_verification_log(run_id: str) -> tuple[str, object]:
    parent = os.path.join(run_dir(run_id), "jobs")
    validate_private_dir(parent)
    path = os.path.join(parent, f"run-verification-{secrets.token_hex(6)}.log")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW, 0o600)
    return path, os.fdopen(fd, "wb")


def _validate_accepted_run_revision(repo: str, units: dict, current_revision: str) -> None:
    """Require the canonical revision to contain every completed unit revision."""
    revisions: set[str] = set()
    for unit in units.values():
        accepted = unit_accepted_revision(unit)
        if accepted is None:
            raise Operational("BLOCKED", "unit completion evidence changed before plan-wide verification")
        base = unit.get("workspace", {}).get("base")
        if not isinstance(base, str) or not revision_contains(repo, base, accepted):
            raise Operational(
                "BLOCKED",
                "controller-accepted unit revision does not descend from its recorded base",
                {"unit_id": unit.get("unit_id"), "base": base, "accepted_revision": accepted},
            )
        if accepted in revisions:
            raise Operational("BLOCKED", "unit completion evidence contains duplicate accepted revisions")
        revisions.add(accepted)

    if any(not revision_contains(repo, accepted, current_revision) for accepted in revisions):
        raise Operational(
            "BLOCKED",
            "canonical revision does not contain every controller-accepted unit",
            {"accepted_revisions": sorted(revisions), "actual_revision": current_revision},
        )


def _accepted_unit_revision_snapshot(units: dict) -> dict[str, str] | None:
    accepted = {unit_id: unit_accepted_revision(unit) for unit_id, unit in units.items()}
    if any(revision_id is None for revision_id in accepted.values()):
        return None
    return accepted


def _record_run_verification_attempt(
    args,
    attempt_id: str,
    lock_unit: str,
    lock_token: str,
    command: list[str],
    before: dict,
    verification_log: str,
) -> None:
    with locked_manifest(args.run_id, write=True) as doc:
        validate_lock(doc, lock_unit, lock_token)
        attempts = plan_wide_verification_attempts(doc)
        if any(attempt.get("attempt_id") == attempt_id for attempt in attempts):
            raise TrustFailure("plan-wide verification attempt identity is duplicated")
        attempts.append({
            "attempt_id": attempt_id,
            "started_at": now_iso(),
            "status": "pending",
            "integration_lock_nonce": lock_token,
            "lock_unit_id": lock_unit,
            "argv": command,
            "summary": args.verification_summary,
            "canonical_snapshot": before,
            "verification_log": verification_log,
        })
        event(doc, "run-verification-started", None, {"attempt_id": attempt_id})


def _record_run_verification_receipt(args, attempt_id: str, lock_token: str, receipt: dict) -> None:
    with locked_manifest(args.run_id, write=True) as doc:
        attempts = plan_wide_verification_attempts(doc)
        matches = [attempt for attempt in attempts if attempt.get("attempt_id") == attempt_id]
        if len(matches) != 1:
            raise TrustFailure("plan-wide verification attempt identity is missing or duplicated")
        attempt = matches[0]
        if attempt.get("status") != "pending" or attempt.get("integration_lock_nonce") != lock_token:
            raise TrustFailure("plan-wide verification attempt state or lock identity changed")
        validate_lock(doc, attempt["lock_unit_id"], lock_token)
        doc.setdefault("verifications", []).append(receipt)
        attempt.update({
            "status": "receipt-recorded",
            "completed_at": now_iso(),
            "evidence_digest": receipt["evidence_digest"],
        })
        event(doc, "run-verification-passed" if receipt["verification_exit"] == 0 else "run-verification-failed", None, {
            "attempt_id": attempt_id,
            "evidence_digest": receipt["evidence_digest"],
            "verification_exit": receipt["verification_exit"],
        })
        if receipt["verification_exit"] != 0:
            doc["blockers"].append({
                "at": now_iso(),
                "unit_id": None,
                "reason": "plan-wide verification failed",
                "evidence_digest": receipt["evidence_digest"],
            })


def _verify_run_locked(
    args,
    repo: str,
    command: list[str],
    units: dict,
    attempt_id: str,
    lock_unit: str,
    lock_token: str,
) -> tuple[str, dict]:
    before = semantic_snapshot(repo)
    before_paths = set(changed_paths(repo))
    before_ignored = _ignored_paths(repo)
    if not before["working_copy_empty"] or before_paths or before["conflicted"]:
        raise Operational("BLOCKED", "verify-run requires a clean canonical Jujutsu working-copy change")
    _validate_accepted_run_revision(repo, units, before["commit_id"])
    accepted_units = _accepted_unit_revision_snapshot(units)
    if accepted_units is None:
        raise Operational("BLOCKED", "unit completion evidence changed before plan-wide verification")
    _preflight_ignored_artifacts(repo, before_ignored)
    before_directory_snapshot = _directory_snapshot(repo)
    before_directories = set(before_directory_snapshot)
    ignored_artifacts = _snapshot_ignored_artifacts(
        repo,
        before_ignored,
        os.path.join(run_dir(args.run_id), "jobs"),
    )

    verification_log, stream = _run_verification_log(args.run_id)
    with stream:
        _record_run_verification_attempt(
            args,
            attempt_id,
            lock_unit,
            lock_token,
            command,
            before,
            verification_log,
        )
        try:
            proc = subprocess.run(
                command,
                cwd=repo,
                stdin=subprocess.DEVNULL,
                stdout=stream,
                stderr=subprocess.STDOUT,
                env=_verification_environment(),
                check=False,
            )
            verification_exit = proc.returncode
        except OSError as exc:
            stream.write(f"verification launch failed: {exc}\n".encode("utf-8", "replace"))
            verification_exit = 127
    test_fault("verify-run-before-receipt")

    after = semantic_snapshot(repo)
    after_paths = set(changed_paths(repo))
    new_ignored = _ignored_paths(repo) - before_ignored
    after_directory_snapshot = _directory_snapshot(repo)
    new_directories = set(after_directory_snapshot) - before_directories
    directory_state_changed = after_directory_snapshot != before_directory_snapshot
    ignored_directories = _new_parent_directories(new_ignored, before_directories)
    _remove_owned_new_paths(repo, new_ignored | new_directories | ignored_directories, before["commit_id"])
    restored_ignored = _restore_ignored_artifacts(repo, ignored_artifacts)
    cleaned_paths = sorted(new_ignored | new_directories | restored_ignored)
    if not same_repository_state(after, before):
        if after["change_id"] != before["change_id"] or after["bookmark_state_sha256"] != before["bookmark_state_sha256"]:
            with locked_manifest(args.run_id, write=True) as doc:
                lock = doc.get("integration_lock") or {}
                blocker = {
                    "at": now_iso(),
                    "unit_id": None,
                    "reason": "plan-wide verification changed canonical change or bookmarks",
                    "retain_integration_lock": True,
                    "integration_lock_nonce": lock.get("nonce"),
                }
                doc["blockers"].append(blocker)
                event(doc, "run-verification-restore-blocked", None, {"verification_exit": verification_exit})
            raise Operational(
                "BLOCKED",
                "plan-wide verification changed canonical change or bookmarks; automatic restoration refused",
                {
                    "verification_exit": verification_exit,
                    "verification_log": verification_log,
                    "cleaned_paths": cleaned_paths,
                    "retain_integration_lock": True,
                },
            )
        deletion_paths = (after_paths - before_paths) | new_ignored | new_directories
        cleaned_paths = sorted(deletion_paths | restored_ignored)
        jj(repo, "op", "restore", before["operation_id"])
        created_directories = _new_parent_directories(deletion_paths, before_directories)
        _remove_owned_new_paths(repo, deletion_paths | created_directories, before["commit_id"])
    directory_restore_error = None
    try:
        restored_directories = _restore_directory_snapshot(repo, before_directory_snapshot)
    except Operational as exc:
        restored_directories = set()
        directory_restore_error = str(exc)
    cleaned_paths = sorted(set(cleaned_paths) | restored_directories)
    restored = semantic_snapshot(repo)
    restored_directory_snapshot = _directory_snapshot(repo)
    if not same_repository_state(restored, before) or restored_directory_snapshot != before_directory_snapshot or directory_restore_error:
        with locked_manifest(args.run_id, write=True) as doc:
            lock = doc.get("integration_lock") or {}
            blocker = {
                "at": now_iso(),
                "unit_id": None,
                "reason": "plan-wide verification restoration could not be proven",
                "retain_integration_lock": True,
                "integration_lock_nonce": lock.get("nonce"),
            }
            doc["blockers"].append(blocker)
            event(doc, "run-verification-restore-blocked", None, {"verification_exit": verification_exit})
        raise Operational(
            "BLOCKED",
            "plan-wide verification restoration could not be proven",
            {
                "verification_exit": verification_exit,
                "verification_log": verification_log,
                "cleaned_paths": cleaned_paths,
                "directory_restore_error": directory_restore_error,
                "retain_integration_lock": True,
            },
        )

    log_digest = hashlib.sha256(Path(verification_log).read_bytes()).hexdigest()
    receipt = {
        "attempt_id": attempt_id,
        "at": now_iso(),
        "argv": command,
        "summary": args.verification_summary,
        "verification_exit": verification_exit,
        "log_sha256": log_digest,
        "canonical_revision_id": before["commit_id"],
        "accepted_units": accepted_units,
        "canonical_state_changed": not same_repository_state(after, before) or directory_state_changed,
        "cleaned_paths": cleaned_paths,
        "verification_log": verification_log if verification_exit != 0 else None,
        "verification_log_retained": verification_exit != 0,
    }
    receipt["evidence_digest"] = digest_bytes(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode())
    _record_run_verification_receipt(args, attempt_id, lock_token, receipt)
    if verification_exit != 0:
        raise Operational(
            "BLOCKED",
            "plan-wide authoritative verification failed",
            {
                "verification_exit": verification_exit,
                "verification_log": verification_log,
                "evidence_digest": receipt["evidence_digest"],
                "cleaned_paths": cleaned_paths,
            },
        )
    os.unlink(verification_log)
    return "RUN_VERIFIED", {
        "verification_exit": 0,
        "evidence_digest": receipt["evidence_digest"],
        "canonical_revision_id": before["commit_id"],
        "cleaned_paths": cleaned_paths,
        "verification_log_retained": False,
    }


def cmd_verify_run(args) -> tuple[str, dict]:
    """Run a plan-wide gate while holding the canonical integration lock."""
    command = _verification_command(args, "verify-run")
    with locked_manifest(args.run_id) as doc:
        info = validate_repo(doc)
        units = doc.get("units", {})
        if not units or any(unit_accepted_revision(unit) is None for unit in units.values()):
            raise Operational(
                "REFUSED",
                "verify-run requires every unit to be terminal with an accepted canonical revision",
            )
        if doc.get("integration_lock") is not None:
            raise Operational("BLOCKED", "verify-run requires no active integration lock")
        repo = info["toplevel"]
        lock_unit = sorted(units)[-1]
    acquired = cmd_integration_acquire(_args(
        run_id=args.run_id,
        unit_id=lock_unit,
        resume=False,
        plan_verification=True,
    ))[1]
    token = acquired["lock_token"]
    attempt_id = secrets.token_hex(16)
    try:
        with locked_manifest(args.run_id) as doc:
            validate_repo(doc)
            units = doc.get("units", {})
            if not units or any(unit_accepted_revision(unit) is None for unit in units.values()):
                raise Operational("BLOCKED", "external unit completion evidence changed before plan-wide verification")
            accepted_units = dict(units)
        result = _verify_run_locked(
            args,
            repo,
            command,
            accepted_units,
            attempt_id,
            lock_unit,
            token,
        )
    except Operational as exc:
        with locked_manifest(args.run_id) as doc:
            lock = doc.get("integration_lock")
            pending = pending_plan_wide_verification(doc, lock) if isinstance(lock, dict) else None
            receipted = receipted_plan_wide_verification(doc, lock) if isinstance(lock, dict) else None
        if not exc.detail.get("retain_integration_lock") and not (
            pending and pending.get("attempt_id") == attempt_id
        ):
            if receipted and receipted.get("attempt_id") == attempt_id:
                test_fault("verify-run-after-receipt")
            cmd_integration_release(_args(run_id=args.run_id, unit_id=lock_unit, lock_token=token))
        raise
    test_fault("verify-run-after-receipt")
    cmd_integration_release(_args(run_id=args.run_id, unit_id=lock_unit, lock_token=token))
    return result


def _integration_recovery_failure(args, original: Operational, failure: Operational, phase: str) -> Operational:
    if phase == "restore":
        reason = "integration failed and exact restoration could not be proven"
        event_name = "integration-restore-blocked"
    else:
        reason = "integration failed after exact restoration but lock release failed"
        event_name = "integration-release-blocked"
    detail = {
        "reason": reason,
        "unit_id": args.unit_id,
        "original_failure": str(original),
        "original_word": original.word,
        f"{phase}_failure": str(failure),
        f"{phase}_word": failure.word,
        "retain_integration_lock": True,
        "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id),
    }
    with locked_manifest(args.run_id, write=True) as doc:
        doc["blockers"].append({"at": now_iso(), **detail})
        event(doc, event_name, args.unit_id, {
            "original_word": original.word,
            f"{phase}_word": failure.word,
        })
    return Operational("BLOCKED", reason, detail)


def cmd_integrate(args) -> tuple[str, dict]:
    command = _verification_command(args)
    description = _change_description(args)

    token = None
    verification_log = None
    described = False
    canonical_change = None
    try:
        acquired = cmd_integration_acquire(_args(run_id=args.run_id, unit_id=args.unit_id, resume=False))[1]
        token = acquired["lock_token"]
        cmd_preflight(_args(
            run_id=args.run_id,
            unit_id=args.unit_id,
            lock_token=token,
            allowed_revision=args.allowed_revision,
        ))
        with locked_manifest(args.run_id, write=True) as doc:
            repo = doc["repository"]["toplevel"]
            transport = doc["units"][args.unit_id]["transport"]["commit_id"]
            doc["units"][args.unit_id]["integration"]["pending_description"] = description
        _preflight_ignored_artifacts(repo, _ignored_paths(repo))
        pre_squash_directory_snapshot = _directory_snapshot(repo)
        jj(repo, "squash", "--from", transport, "--into", "@")
        cmd_mark_applied(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        with locked_manifest(args.run_id) as doc:
            unit = doc["units"][args.unit_id]
            applied = unit["integration"].get("applied") or {}
        before = semantic_snapshot(repo)
        before_paths = set(changed_paths(repo))
        if not matches_expected_apply(repo, unit, before) or before["commit_id"] != applied.get("commit_id"):
            raise Operational("BLOCKED", "canonical squash changed before verification")
        before_ignored = _ignored_paths(repo)
        _preflight_ignored_artifacts(repo, before_ignored)
        before_directory_snapshot = _directory_snapshot(repo)
        before_directories = set(before_directory_snapshot)
        ignored_artifacts = _snapshot_ignored_artifacts(
            repo,
            before_ignored,
            os.path.join(run_dir(args.run_id), "units", args.unit_id, "result"),
        )

        verification_log, stream = _verification_log(args.run_id, args.unit_id)
        with stream:
            try:
                proc = subprocess.run(
                    command,
                    cwd=repo,
                    stdin=subprocess.DEVNULL,
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    env=_verification_environment(),
                    check=False,
                )
                verification_exit = proc.returncode
            except OSError as exc:
                stream.write(f"verification launch failed: {exc}\n".encode("utf-8", "replace"))
                verification_exit = 127
        after = semantic_snapshot(repo)
        after_paths = set(changed_paths(repo))
        new_ignored = _ignored_paths(repo) - before_ignored
        after_directory_snapshot = _directory_snapshot(repo)
        new_directories = set(after_directory_snapshot) - before_directories
        directory_state_changed = after_directory_snapshot != before_directory_snapshot
        ignored_directories = _new_parent_directories(new_ignored, before_directories)
        _remove_owned_new_paths(repo, new_ignored | new_directories | ignored_directories, before["commit_id"])
        restored_ignored = _restore_ignored_artifacts(repo, ignored_artifacts)
        verification_failed = verification_exit != 0 or not same_repository_state(after, before)
        target_directory_snapshot = before_directory_snapshot
        rollback_directories: set[str] = set()
        if verification_failed:
            rollback_directories = set(before_directory_snapshot) - set(pre_squash_directory_snapshot)
            _restore_owned_verification(args.run_id, args.unit_id, token, before, before_paths, after_paths)
            target_directory_snapshot = pre_squash_directory_snapshot
            rollback_directories |= set(_directory_snapshot(repo)) - set(target_directory_snapshot)
            _remove_owned_new_paths(repo, rollback_directories, before["commit_id"])
        directory_restore_error = None
        try:
            test_fault("unit-verification-before-directory-restore")
            restored_directories = _restore_directory_snapshot(repo, target_directory_snapshot)
        except Operational as exc:
            restored_directories = set()
            directory_restore_error = str(exc)
        cleaned_paths = sorted(
            (after_paths - before_paths)
            | new_ignored
            | new_directories
            | rollback_directories
            | restored_ignored
            | restored_directories
        )
        restored_directory_snapshot = _directory_snapshot(repo)
        directory_restoration_unproven = (
            restored_directory_snapshot != target_directory_snapshot or directory_restore_error
        )
        log_digest = hashlib.sha256(Path(verification_log).read_bytes()).hexdigest()
        if directory_restoration_unproven:
            detail = {
                "unit_id": args.unit_id,
                "verification_exit": verification_exit,
                "verification_log": verification_log,
                "cleaned_paths": cleaned_paths,
                "directory_restore_error": directory_restore_error,
                "retain_integration_lock": True,
            }
            with locked_manifest(args.run_id, write=True) as doc:
                lock = doc.get("integration_lock") or {}
                doc["blockers"].append({
                    "at": now_iso(),
                    "unit_id": args.unit_id,
                    "reason": "unit verification directory restoration could not be proven",
                    "retain_integration_lock": True,
                    "integration_lock_nonce": lock.get("nonce"),
                })
                event(doc, "unit-verification-restore-blocked", args.unit_id, {
                    "verification_exit": verification_exit,
                })
            raise Operational(
                "BLOCKED",
                "unit verification directory restoration could not be proven",
                detail,
            )
        if verification_failed:
            cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
            token = None
            raise Operational(
                "BLOCKED",
                "authoritative verification failed or changed canonical state",
                {
                    "unit_id": args.unit_id,
                    "verification_exit": verification_exit,
                    "verification_log": verification_log,
                    "canonical_state_changed": not same_repository_state(after, before),
                    "cleaned_paths": cleaned_paths,
                },
            )
        evidence = digest_bytes(json.dumps({
            "argv": command,
            "exit": verification_exit,
            "log_sha256": log_digest,
            "before": before,
            "after": after,
            "directory_state_changed": directory_state_changed,
            "cleaned_paths": cleaned_paths,
        }, sort_keys=True, separators=(",", ":")).encode())
        cmd_mark_verified(_args(
            run_id=args.run_id,
            unit_id=args.unit_id,
            lock_token=token,
            evidence_digest=evidence,
            summary=args.verification_summary,
        ))
        test_fault("before-canonical-describe")
        jj(repo, "describe", "-m", description)
        jj(repo, "new")
        described_body = cmd_mark_described(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))[1]
        described = True
        canonical_change = described_body["canonical_change"]
        canonical_revision = canonical_change["commit_id"]
        test_fault("after-canonical-describe-confirmed")
        with locked_manifest(args.run_id) as doc:
            wave_id = doc["units"][args.unit_id].get("wave", {}).get("id")
        if wave_id:
            cmd_wave_advance(_args(
                run_id=args.run_id,
                unit_id=args.unit_id,
                lock_token=token,
                canonical_revision=canonical_revision,
            ))
        cmd_cleanup(_args(
            run_id=args.run_id,
            unit_id=args.unit_id,
            abandon=False,
            expect_transport=None,
            expect_job=None,
        ))
        cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
        token = None
        os.unlink(verification_log)
        return "UNIT_DESCRIBED", {
            "unit_id": args.unit_id,
            "canonical_change": canonical_change,
            "verification_digest": evidence,
            "verification_log_retained": False,
            "cleaned_paths": cleaned_paths,
            "cleaned": True,
        }
    except (Operational, TrustFailure) as original:
        if token is not None and described:
            detail = {
                "reason": "canonical change accepted but post-description finalization is incomplete",
                "unit_id": args.unit_id,
                "canonical_change": canonical_change,
                "original_failure": str(original),
                "original_word": original.word,
                "retain_integration_lock": True,
                "recovery_path": os.path.join(run_dir(args.run_id), "units", args.unit_id),
            }
            with locked_manifest(args.run_id, write=True) as doc:
                doc["blockers"].append({"at": now_iso(), **detail})
                event(doc, "post-description-finalization-blocked", args.unit_id, {
                    "canonical_change": canonical_change,
                    "original_word": original.word,
                })
            raise Operational(
                "BLOCKED",
                "canonical change accepted but post-description finalization is incomplete",
                detail,
            ) from original
        if token is not None and original.detail.get("retain_integration_lock"):
            raise
        if token is not None:
            with locked_manifest(args.run_id) as doc:
                unit = doc["units"].get(args.unit_id)
                pre_fold = unit.get("integration", {}).get("pre_fold") if unit else None
            if not pre_fold:
                cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
                token = None
                raise
            try:
                cmd_restore(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
            except (Operational, TrustFailure) as restore_failure:
                raise _integration_recovery_failure(args, original, restore_failure, "restore") from restore_failure
            try:
                cmd_integration_release(_args(run_id=args.run_id, unit_id=args.unit_id, lock_token=token))
                token = None
            except (Operational, TrustFailure) as release_failure:
                raise _integration_recovery_failure(args, original, release_failure, "release") from release_failure
        raise
