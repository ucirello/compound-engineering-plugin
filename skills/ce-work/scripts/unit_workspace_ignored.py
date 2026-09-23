"""Read-only ignored-path metadata inventory for verification receipts.

The sole authorized Git operation is ls-files --others --ignored
--exclude-standard -z --, with GIT_DIR from the public jj git root API.
Inventories never copy contents, restore files, or delete files.
"""

from __future__ import annotations

import os
import stat
import subprocess

from unit_workspace_state import Operational, jj_text, sanitized_process_environment


def inventory_ignored_state(repo: str) -> dict:
    root = os.path.abspath(repo)
    try:
        git_dir = jj_text(root, "git", "root")
        if not git_dir:
            return {"available": False, "reason": "jj git root returned no Git directory"}
        proc = subprocess.run(
            ["git", "ls-files", "--others", "--ignored", "--exclude-standard", "-z", "--"],
            cwd=root,
            env=sanitized_process_environment({"GIT_DIR": git_dir, "GIT_WORK_TREE": root}),
            capture_output=True,
            check=False,
        )
        if proc.returncode:
            return {"available": False, "reason": proc.stderr.decode("utf-8", "replace").strip()}
    except (OSError, Operational) as exc:
        return {"available": False, "reason": str(exc)}
    entries = {}
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        relative = os.fsdecode(raw)
        if os.path.isabs(relative) or ".." in relative.split("/"):
            return {"available": False, "reason": "ignored inventory contained an unsafe path"}
        try:
            info = os.lstat(os.path.join(root, relative))
            entries[relative] = {
                "mode": info.st_mode,
                "size": info.st_size,
                "mtime_ns": info.st_mtime_ns,
                "ctime_ns": info.st_ctime_ns,
                "symlink": stat.S_ISLNK(info.st_mode),
            }
        except OSError as exc:
            entries[relative] = {"uninspectable": True, "reason": str(exc)}
    return {"available": True, "entries": entries}


def diff_ignored_state(before: dict, after: dict, sample_limit: int = 20) -> dict:
    available = before.get("available", False) and after.get("available", False)
    old = before.get("entries", {})
    new = after.get("entries", {})
    changed = sorted(path for path in old.keys() & new.keys() if old[path] != new[path]) if available else []
    removed = sorted(old.keys() - new.keys()) if available else []
    created = sorted(new.keys() - old.keys()) if available else []
    uninspectable = {path for entries in (old, new) for path, metadata in entries.items() if metadata.get("uninspectable")}
    return {
        "available": bool(available),
        "reason": None if available else before.get("reason") or after.get("reason"),
        "before": len(old) if before.get("available") else None,
        "after": len(new) if after.get("available") else None,
        "changed": len(changed) if available else None,
        "removed": len(removed) if available else None,
        "created": len(created) if available else None,
        "uninspectable": len(uninspectable),
        "sample": {"changed": changed[:sample_limit], "removed": removed[:sample_limit], "created": created[:sample_limit]},
        "sample_limit": sample_limit,
        "restored": False,
    }
