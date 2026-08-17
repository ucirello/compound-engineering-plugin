"""Metadata-only inventory of files outside the active Jujutsu tree."""

from __future__ import annotations

import os
import stat

from unit_workspace_state import jj_text


def inventory_ignored_state(repo: str) -> dict[str, tuple]:
    tracked = set(jj_text(repo, "file", "list", "-r", "@").splitlines())
    inventory: dict[str, tuple] = {}
    for directory, names, files in os.walk(repo, topdown=True, followlinks=False):
        relative_directory = os.path.relpath(directory, repo)
        if relative_directory == ".":
            # `.git` is colocated-backend metadata, not a working-copy artifact.
            names[:] = [name for name in names if name not in {".jj", ".git", ".tmp"}]
        for name in files:
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, repo)
            if relative in tracked:
                continue
            entry = os.lstat(path)
            inventory[relative] = (
                stat.S_IFMT(entry.st_mode),
                stat.S_IMODE(entry.st_mode),
                entry.st_size,
                entry.st_mtime_ns,
            )
    return inventory


def diff_ignored_state(before: dict[str, tuple], after: dict[str, tuple], sample_limit: int = 20) -> dict:
    created = sorted(after.keys() - before.keys())
    removed = sorted(before.keys() - after.keys())
    changed = sorted(path for path in before.keys() & after.keys() if before[path] != after[path])
    return {
        "created": len(created),
        "removed": len(removed),
        "changed": len(changed),
        "sample": (created + removed + changed)[:sample_limit],
    }
