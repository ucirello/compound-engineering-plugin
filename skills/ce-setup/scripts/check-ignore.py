#!/usr/bin/env python3
"""Check setup's fixed ignore targets using JJ's snapshot engine, without snapshotting the caller."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from uuid import uuid4


TARGETS = {
    ".rocketclaw/config.local.yaml": ".rocketclaw/config.local.yaml",
    ".context/": ".context/",
    ".tmp/": ".tmp/",
}


def jj(cwd, *args, required=True):
    return subprocess.run(["jj", "--no-pager", "--color=never", *args], cwd=cwd,
                          timeout=10, capture_output=True, text=True, check=required)


def copy_if_file(source, target):
    if source.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def main(repo):
    scratch = repo / ".tmp"
    scratch.mkdir(exist_ok=True)
    if scratch.is_symlink():
        raise OSError("workspace .tmp/ is a symlink; refusing ignore probe")
    with tempfile.TemporaryDirectory(prefix="setup-ignore-", dir=scratch) as path:
        mirror = Path(path)
        targets = {
            key: value + f"ignore-probe-{uuid4().hex}" if value.endswith("/") else value
            for key, value in TARGETS.items()
        }
        jj(mirror, "git", "init", "--colocate")
        copy_if_file(repo / ".gitignore", mirror / ".gitignore")
        copy_if_file(repo / ".rocketclaw/.gitignore", mirror / ".rocketclaw/.gitignore")
        git_root = jj(repo, "git", "root", required=False)
        if git_root.returncode == 0:
            store = Path(git_root.stdout.strip())
            common_file = store / "commondir"
            if common_file.is_file():
                store /= common_file.read_text().strip()
            copy_if_file(store / "info/exclude", mirror / ".git/info/exclude")
        for probe in targets.values():
            target = mirror / probe
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch()
        for target, probe in targets.items():
            present = jj(mirror, "--config", 'snapshot.auto-track="all()"', "file", "list",
                         "-T", 'path ++ "\\n"', "--", probe).stdout.strip()
            tracked = jj(repo, "--ignore-working-copy", "file", "list",
                         "-T", 'path ++ "\\n"', "--", target.rstrip("/")).stdout.strip()
            if not present and not tracked:
                print(target)


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2 or not Path(sys.argv[1]).is_absolute():
            raise ValueError("expected an absolute JJ workspace root")
        main(Path(sys.argv[1]).resolve())
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        sys.exit(f"ignore coverage could not be verified: {exc}")
