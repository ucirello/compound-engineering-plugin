"""Metadata inventory of untracked cache and asset entries in a Jujutsu workspace."""

import os
import stat

from unit_workspace_state import Operational, jj_text


def _entry_type(mode: int) -> str:
    if stat.S_ISLNK(mode): return "symlink"
    if stat.S_ISDIR(mode): return "directory"
    if stat.S_ISREG(mode): return "file"
    return "other"


def inventory_untracked_state(repo: str) -> dict[str, tuple]:
    tracked = set(jj_text(repo, "file", "list").splitlines())
    inventory = {}
    for root, dirs, files in os.walk(repo, topdown=True, followlinks=False):
        rel_root = os.path.relpath(root, repo)
        if rel_root == ".":
            dirs[:] = [d for d in dirs if d not in {".jj", ".tmp"}]
        for name in [*dirs, *files]:
            rel = os.path.normpath(os.path.join(rel_root, name))
            if rel.startswith((".jj" + os.sep, ".tmp" + os.sep)) or rel in tracked:
                continue
            target = os.path.abspath(os.path.join(repo, rel))
            if os.path.commonpath([repo, target]) != repo:
                raise Operational("BLOCKED", "untracked artifact escaped canonical workspace")
            try:
                entry = os.lstat(target)
                inventory[rel] = (_entry_type(entry.st_mode), entry.st_size, entry.st_mtime_ns, entry.st_ino, entry.st_dev, stat.S_IMODE(entry.st_mode))
            except OSError:
                inventory[rel] = ("uninspectable",)
    return inventory


def diff_untracked_state(before: dict[str, tuple], after: dict[str, tuple], sample_limit: int = 20) -> dict:
    changed = sorted(k for k in before.keys() & after.keys() if before[k] != after[k])
    removed = sorted(before.keys() - after.keys())
    created = sorted(after.keys() - before.keys())
    return {
        "before": len(before), "after": len(after), "changed": len(changed),
        "removed": len(removed), "created": len(created),
        "sample": {"changed": changed[:sample_limit], "removed": removed[:sample_limit], "created": created[:sample_limit]},
        "sample_limit": sample_limit, "restored": False,
    }
