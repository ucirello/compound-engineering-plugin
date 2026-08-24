"""Metadata inventory of workspace files not present in the selected JJ revision."""

from __future__ import annotations

import os
import stat

from unit_workspace_state import Operational, jj_text


def ignored_paths(repo: str) -> set[str]:
    tracked = set(filter(None, jj_text(repo, "file", "list", "-r", "@").splitlines()))
    result: set[str] = set()
    for current, dirs, files in os.walk(repo):
        dirs[:] = [name for name in dirs if name not in {".jj", ".tmp"}]
        for name in files:
            absolute = os.path.join(current, name)
            relative = os.path.relpath(absolute, repo)
            if relative not in tracked:
                result.add(relative)
    return result


def artifact_path(repo: str, rel: str) -> str:
    target = os.path.abspath(os.path.join(repo, rel))
    if target == repo or os.path.commonpath([repo, target]) != os.path.abspath(repo):
        raise Operational("BLOCKED", "artifact path escaped canonical workspace")
    return target


def inventory_ignored_state(repo: str) -> dict[str, tuple]:
    inventory = {}
    for rel in ignored_paths(repo):
        try:
            info = os.lstat(artifact_path(repo, rel))
        except OSError:
            inventory[rel] = ("uninspectable",)
            continue
        kind = "symlink" if stat.S_ISLNK(info.st_mode) else "file" if stat.S_ISREG(info.st_mode) else "other"
        inventory[rel] = (kind, info.st_size, info.st_mtime_ns, info.st_ino, info.st_dev, stat.S_IMODE(info.st_mode))
    return inventory


def diff_ignored_state(before: dict[str, tuple], after: dict[str, tuple], sample_limit: int = 20) -> dict:
    changed = sorted(path for path in before.keys() & after.keys() if before[path] != after[path])
    removed = sorted(before.keys() - after.keys())
    created = sorted(after.keys() - before.keys())
    return {
        "before": len(before), "after": len(after), "changed": len(changed),
        "removed": len(removed), "created": len(created),
        "sample": {"changed": changed[:sample_limit], "removed": removed[:sample_limit], "created": created[:sample_limit]},
        "sample_limit": sample_limit, "restored": False,
    }
