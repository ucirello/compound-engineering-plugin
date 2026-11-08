#!/usr/bin/env python3
"""Conservatively check repository-local ignore coverage without invoking Git.

Understood root patterns can prove coverage; unusual patterns and negations
fail closed so setup can offer an explicit rule rather than claim protection.
"""
import fnmatch
from pathlib import Path
import sys


def covered(root, target):
    root = Path(root).resolve()
    target = target.replace("\\", "/").removeprefix(str(root) + "/").lstrip("/")
    parts = target.rstrip("/").split("/")
    ignored = False
    for depth in range(len(parts)):
        source = root.joinpath(*parts[:depth], ".gitignore")
        if not source.is_file():
            continue
        relative = "/".join(parts[depth:])
        for raw in source.read_text().splitlines():
            pattern = raw.rstrip()
            if not pattern or pattern.startswith("#"):
                continue
            if pattern.startswith("!"):
                # Conservative: a negation may re-include a descendant.
                ignored = False
                continue
            directory = pattern.endswith("/")
            pattern = pattern.rstrip("/")
            anchored = pattern.startswith("/") or "/" in pattern
            pattern = pattern.lstrip("/")
            candidates = [relative] if anchored else relative.split("/")
            if directory:
                candidates += ["/".join(parts[depth:i]) for i in range(depth + 1, len(parts) + 1)]
            if any(fnmatch.fnmatchcase(candidate, pattern) for candidate in candidates):
                ignored = True
    return ignored


if __name__ == "__main__":
    raise SystemExit(0 if covered(sys.argv[1], sys.argv[2]) else 1)
