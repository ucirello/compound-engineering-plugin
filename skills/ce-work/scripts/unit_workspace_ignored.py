"""Metadata inventory for local ignored artifacts beside a JJ workspace."""

from __future__ import annotations

import os
import stat

from unit_workspace_state import local_tmp_root


def inventory_untracked_state(repo: str) -> dict[str, tuple]:
    """Inventory the workflow-owned local `.tmp/rocketclaw` tree only."""
    root = local_tmp_root(repo)
    inventory: dict[str, tuple] = {}
    if not os.path.isdir(root):
        return inventory
    for current, directories, files in os.walk(root, followlinks=False):
        for name in directories + files:
            path = os.path.join(current, name)
            try:
                entry = os.lstat(path)
            except OSError:
                continue
            rel = os.path.relpath(path, repo)
            inventory[rel] = (stat.S_IFMT(entry.st_mode), entry.st_size, entry.st_mtime_ns)
    return inventory


def diff_untracked_state(before: dict[str, tuple], after: dict[str, tuple], sample_limit: int = 20) -> dict:
    changed = sorted(path for path in before.keys() & after.keys() if before[path] != after[path])
    removed = sorted(before.keys() - after.keys())
    created = sorted(after.keys() - before.keys())
    return {
        "before": len(before), "after": len(after), "changed": len(changed),
        "removed": len(removed), "created": len(created),
        "sample": {"changed": changed[:sample_limit], "removed": removed[:sample_limit], "created": created[:sample_limit]},
        "sample_limit": sample_limit, "restored": False,
    }
