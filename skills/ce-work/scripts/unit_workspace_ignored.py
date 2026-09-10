"""Metadata inventory of the canonical checkout's ignored entries.

Verification runs in the canonical checkout; ignored state is never copied or
restored. Two inventories taken before and after verification diff into a
disclosure of changed, removed, and created ignored paths.

JJ has no public ignored-file listing command. Paths present on disk that are
not in `jj file list` (the working-copy revision) are treated as ignored
untracked entries. VCS metadata directories are skipped and never parsed.
"""

from __future__ import annotations

import os
import stat

from unit_workspace_state import Operational, jj_text


_SKIP_DIR_NAMES = {".jj", ".git"}


def ignored_paths(repo: str) -> set[str]:
    repo = os.path.abspath(repo)
    tracked = set()
    listed = jj_text(repo, "file", "list", "-r", "@")
    for line in listed.splitlines():
        if line:
            tracked.add(line)
    ignored: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(repo, followlinks=False):
        dirnames[:] = [name for name in dirnames if name not in _SKIP_DIR_NAMES]
        rel_dir = os.path.relpath(dirpath, repo)
        if rel_dir == ".":
            rel_dir = ""
        for name in filenames:
            rel = name if not rel_dir else f"{rel_dir}/{name}".replace("\\", "/")
            if rel not in tracked:
                ignored.add(rel)
        for name in dirnames:
            rel = name if not rel_dir else f"{rel_dir}/{name}".replace("\\", "/")
            # Directories themselves are not in `jj file list`; only files are.
            # Empty ignored directories are not inventoried.
            del rel
    return ignored


def artifact_path(repo: str, rel: str) -> str:
    repo = os.path.abspath(repo)
    target = os.path.abspath(os.path.join(repo, rel))
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
    """lstat every ignored entry; an entry that cannot be inspected is recorded, not refused."""
    repo = os.path.abspath(repo)
    inventory: dict[str, tuple] = {}
    for rel in ignored_paths(repo):
        try:
            entry = os.lstat(artifact_path(repo, rel))
        except OSError:
            inventory[rel] = ("uninspectable",)
            continue
        inventory[rel] = (
            _entry_type(entry.st_mode),
            entry.st_size,
            entry.st_mtime_ns,
            entry.st_ino,
            entry.st_dev,
            entry.st_nlink,
            stat.S_IMODE(entry.st_mode),
            entry.st_ctime_ns,
        )
    return inventory


def _comparable(record: tuple) -> tuple:
    # Windows ctime is creation time, so it cannot signal an in-place mutation there.
    return record if os.name != "nt" else record[:-1]


def diff_ignored_state(before: dict[str, tuple], after: dict[str, tuple], sample_limit: int = 20) -> dict:
    changed: list[str] = []
    uninspectable = 0
    for rel in before.keys() & after.keys():
        old, new = before[rel], after[rel]
        if old[0] == "uninspectable" or new[0] == "uninspectable":
            uninspectable += 1
        elif _comparable(old) != _comparable(new):
            changed.append(rel)
    removed = sorted(before.keys() - after.keys())
    created = sorted(after.keys() - before.keys())
    changed.sort()
    return {
        "before": len(before),
        "after": len(after),
        "changed": len(changed),
        "removed": len(removed),
        "created": len(created),
        "uninspectable": uninspectable,
        "sample": {
            "changed": changed[:sample_limit],
            "removed": removed[:sample_limit],
            "created": created[:sample_limit],
        },
        "sample_limit": sample_limit,
        "restored": False,
    }
