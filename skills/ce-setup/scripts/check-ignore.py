#!/usr/bin/env python3
"""Conservative local ignore-coverage check without invoking Git.

Recognizes explicit path/directory coverage and its negations. Complex glob
rules are deliberately reported as unverified, never as safely ignored.
"""
import os
import sys
from pathlib import Path


def covered(root, target):
    root = Path(root).resolve()
    target = target.replace(os.sep, "/").strip("/")
    parts = target.split("/")
    ignored = False
    for depth in range(len(parts)):
        base = root.joinpath(*parts[:depth])
        rules = base / ".gitignore"
        if not rules.is_file():
            continue
        relative = "/".join(parts[depth:])
        for raw in rules.read_text(errors="replace").splitlines():
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            negative = raw.startswith("!")
            pattern = raw[1:] if negative else raw
            pattern = pattern.lstrip("/").rstrip("/")
            if any(c in pattern for c in "*?[\\"):
                # A later complex negation may undo an earlier explicit rule.
                if negative:
                    ignored = False
                continue
            if relative == pattern or relative.startswith(pattern + "/"):
                ignored = not negative
    return ignored


if __name__ == "__main__":
    root, target = sys.argv[1:3]
    if os.path.isabs(target):
        target = os.path.relpath(target, root)
    sys.exit(0 if covered(root, target) else 1)
