#!/usr/bin/env python3
"""Conservatively prove root .gitignore coverage without launching Git.

Exit 0 only for a supported path/ancestor ignore with no later
potentially applicable negation. Complex patterns are reported as unverified,
never as safely ignored. Also refuse tracked paths.
"""
import os
import re
import subprocess
import sys

root, path = os.path.abspath(sys.argv[1]), sys.argv[2].strip("/")
directory = sys.argv[2].endswith("/") or os.path.isdir(os.path.join(root, path))
tracked = subprocess.run(["jj", "file", "list", path], cwd=root,
                         capture_output=True, text=True)
if tracked.returncode or tracked.stdout.strip():
    raise SystemExit(1)
def matches(pattern, value):
    # Wildmatch stars do not cross separators; ** does. Character classes and
    # escaped patterns remain unverified rather than approximated as safe.
    if any(c in pattern for c in "[\\"):
        return False
    expression = ""
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if pattern[i:i + 3] == "**/":
            expression += "(?:.*/)?"
            i += 3
            continue
        if pattern[i:i + 2] == "**":
            expression += ".*"
            i += 2
            continue
        expression += "[^/]*" if char == "*" else "[^/]" if char == "?" else re.escape(char)
        i += 1
    return re.fullmatch(expression, value) is not None

covered = False
try:
    with open(os.path.join(root, ".gitignore"), encoding="utf-8") as source:
        for raw in source:
            rule = raw.strip()
            if not rule or rule.startswith("#"):
                continue
            if rule.startswith("!"):
                # An uncertain exception must not produce a privacy guarantee.
                covered = False
                continue
            directory_only = rule.endswith("/")
            anchored = rule.startswith("/") or "/" in rule.rstrip("/")
            rule = rule.strip("/")
            parts = path.split("/")
            length = len(parts) if directory or not directory_only else len(parts) - 1
            candidates = ["/".join(parts[:i]) for i in range(1, length + 1)] if anchored else parts[:length]
            if any(matches(rule, candidate) for candidate in candidates):
                covered = True
except OSError:
    pass
raise SystemExit(0 if covered else 1)
