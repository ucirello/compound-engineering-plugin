"""Metadata inventory of files outside Jujutsu's tracked-file inventory.

Verification runs in the canonical workspace. State outside the tracked
inventory is disclosed but never copied, restored, or deleted.
"""

from __future__ import annotations

import os
import stat

from unit_workspace_state import Operational, jj


def tracked_paths(repo: str) -> set[str]:
    raw = jj(repo, "file", "list", "-T", 'path ++ "\\0"')
    return {part.decode("utf-8", "surrogateescape") for part in raw.split(b"\0") if part}


def ignored_paths(repo: str) -> set[str]:
    repo = os.path.abspath(repo)
    tracked = tracked_paths(repo)
    paths: set[str] = set()
    for current_root, directories, files in os.walk(repo, topdown=True, followlinks=False):
        relative_root = os.path.relpath(current_root, repo)
        if relative_root == os.path.join(".tmp", "rocketclaw", "ce-work") or relative_root.startswith(os.path.join(".tmp", "rocketclaw", "ce-work") + os.sep):
            directories[:] = []
            continue
        directories[:] = [name for name in directories if name != ".jj"]
        symlink_directories = [name for name in directories if os.path.islink(os.path.join(current_root, name))]
        directories[:] = [name for name in directories if name not in symlink_directories]
        for name in [*symlink_directories, *files]:
            absolute = os.path.join(current_root, name)
            relative = os.path.normpath(os.path.join(relative_root, name)) if relative_root != "." else name
            if relative not in tracked and relative != ".jj" and not relative.startswith(f".jj{os.sep}"):
                paths.add(relative)
    return paths


def artifact_path(repo: str, relative: str) -> str:
    repo = os.path.abspath(repo)
    target = os.path.abspath(os.path.join(repo, relative))
    if target == repo or os.path.commonpath([repo, target]) != repo:
        raise Operational("BLOCKED", "ignored artifact path escaped canonical repository")
    return target


def _entry_type(mode: int) -> str:
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISREG(mode):
        return "file"
    return "other"


def inventory_ignored_state(repo: str) -> dict[str, tuple]:
    inventory: dict[str, tuple] = {}
    for relative in ignored_paths(repo):
        try:
            entry = os.lstat(artifact_path(repo, relative))
        except OSError:
            inventory[relative] = ("uninspectable",)
            continue
        inventory[relative] = (
            _entry_type(entry.st_mode), entry.st_size, entry.st_mtime_ns,
            entry.st_ino, entry.st_dev, entry.st_nlink, stat.S_IMODE(entry.st_mode),
            entry.st_ctime_ns,
        )
    return inventory


def _comparable(record: tuple) -> tuple:
    return record if os.name != "nt" else record[:-1]


def diff_ignored_state(before: dict[str, tuple], after: dict[str, tuple], sample_limit: int = 20) -> dict:
    changed: list[str] = []
    uninspectable = 0
    for relative in before.keys() & after.keys():
        old, new = before[relative], after[relative]
        if old[0] == "uninspectable" or new[0] == "uninspectable":
            uninspectable += 1
        elif _comparable(old) != _comparable(new):
            changed.append(relative)
    removed = sorted(before.keys() - after.keys())
    created = sorted(after.keys() - before.keys())
    changed.sort()
    return {
        "before": len(before), "after": len(after), "changed": len(changed),
        "removed": len(removed), "created": len(created), "uninspectable": uninspectable,
        "sample": {"changed": changed[:sample_limit], "removed": removed[:sample_limit], "created": created[:sample_limit]},
        "sample_limit": sample_limit, "restored": False,
    }
