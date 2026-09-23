"""Workspace-local scratch shared by the sweep's bundled scripts."""

import os
import subprocess
from pathlib import Path


def workspace_root():
    start = Path.cwd().resolve()
    try:
        result = subprocess.run(
            ["jj", "--ignore-working-copy", "--color=never", "workspace", "root"],
            cwd=start, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return start
    root = Path(result.stdout.strip())
    return root if result.returncode == 0 and root.is_absolute() else start


def scratch_directory():
    """Keep temporary bytes under workspace .tmp, or local .tmp outside JJ."""
    root = workspace_root()
    for name in (".tmp", "sweep"):
        root = root / name
        if root.is_symlink():
            raise OSError(f"unsafe scratch directory symlink: {root}")
        root.mkdir(mode=0o700, exist_ok=True)
        if root.is_symlink() or not root.is_dir():
            raise OSError(f"unsafe scratch directory: {root}")
        if hasattr(os, "geteuid") and root.stat().st_uid != os.geteuid():
            raise OSError(f"scratch directory is not owned by the current user: {root}")
        root.chmod(0o700)
    return root
