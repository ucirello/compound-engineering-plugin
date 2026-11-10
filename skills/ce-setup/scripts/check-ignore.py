#!/usr/bin/env python3
"""Conservative, read-only ignore coverage check without invoking Git.

Recognizes literal root/ancestor rules and simple globs. Complex escapes,
negations, or nested policy require manual verification: never report a local
secret safely ignored merely because a parser approximation says so.
"""
import fnmatch
import pathlib
import subprocess
import sys


def covered(root, target):
    root = pathlib.Path(root).resolve()
    target = target.rstrip("/")
    listed = subprocess.run(
        ["jj", "--ignore-working-copy", "file", "list", target],
        cwd=str(root), capture_output=True, text=True, timeout=10,
    )
    if listed.returncode or listed.stdout.strip():
        return False  # Already tracked files are not protected by ignore rules.
    parts = pathlib.PurePosixPath(target).parts
    if not parts or pathlib.PurePosixPath(target).is_absolute() or ".." in parts:
        return False
    matched = False
    for depth in range(len(parts)):
        base = root.joinpath(*parts[:depth])
        policy = base / ".gitignore"
        if not policy.is_file():
            continue
        relative = "/".join(parts[depth:])
        for raw in policy.read_text().splitlines():
            rule = raw.strip()
            if not rule or rule.startswith("#"):
                continue
            if rule.startswith("!") or "\\" in rule or "**" in rule:
                return False
            directory_only = rule.endswith("/")
            anchored = rule.startswith("/")
            rule = rule.lstrip("/").rstrip("/")
            pattern = rule.split("/")
            for end in range(depth + 1, len(parts) + 1):
                candidate = parts[depth:end]
                if len(pattern) == 1 and not anchored:
                    candidate = candidate[-1:]
                if len(candidate) != len(pattern):
                    continue
                if not all(fnmatch.fnmatchcase(item, glob) for item, glob in zip(candidate, pattern)):
                    continue
                location = root.joinpath(*parts[:end])
                if location.is_symlink():
                    return False
                if directory_only and not location.is_dir():
                    continue
                matched = True
    return matched


if __name__ == "__main__":
    sys.exit(0 if covered(sys.argv[1], sys.argv[2]) else 1)
