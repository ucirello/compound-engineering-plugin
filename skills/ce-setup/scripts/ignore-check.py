#!/usr/bin/env python3
"""Check repository-local ignore rules without executing Git.

Exit 0 only for ignored, untracked paths. Supports ordered negation, nested
.gitignore files, anchored patterns, directory rules, and glob wildcards.
"""
import os
import re
import subprocess
import sys


def ignored(root, path):
    root = os.path.abspath(root)
    requested_directory = path.endswith("/")
    path = path.replace(os.sep, "/").rstrip("/")
    if path.startswith("/") or ".." in path.split("/"):
        return False
    tracked = subprocess.run(["jj", "--ignore-working-copy", "file", "list", path],
                             cwd=root, capture_output=True, text=True)
    if tracked.returncode or tracked.stdout.strip():
        return False
    parts = path.split("/")
    rules = []
    for depth in range(len(parts)):
        base = "/".join(parts[:depth])
        try:
            with open(os.path.join(root, base, ".gitignore"), encoding="utf-8") as f:
                lines = f.read().splitlines()
        except OSError:
            lines = []
        for raw in lines:
            line = raw.rstrip()
            if not line or line.startswith("#"):
                continue
            negate = line.startswith("!")
            if negate:
                line = line[1:]
            directory = line.endswith("/")
            line = line.rstrip("/")
            anchored = line.startswith("/") or "/" in line
            line = line.lstrip("/")
            # Translate wildmatch without making '*' cross a slash.
            regex = ""
            i = 0
            while i < len(line):
                c = line[i]
                if c == "\\" and i + 1 < len(line):
                    i += 1
                    regex += re.escape(line[i])
                elif line[i:i+3] == "**/":
                    regex += "(?:.*/)?"
                    i += 2
                elif line[i:i+2] == "**":
                    regex += ".*"
                    i += 1
                elif c == "*":
                    regex += "[^/]*"
                elif c == "?":
                    regex += "[^/]"
                elif c == "[" and "]" in line[i+1:]:
                    end = line.index("]", i+1)
                    group = line[i+1:end]
                    regex += "[" + ("^" + group[1:] if group.startswith("!") else group) + "]"
                    i = end
                else:
                    regex += re.escape(c)
                i += 1
            rules.append((base, re.compile(("^" if anchored else "(?:^|/)") + regex + "$"), negate, directory))
        # An excluded parent cannot be re-included by a child's rules.
        candidate = "/".join(parts[:depth+1])
        is_dir = depth < len(parts)-1 or requested_directory or os.path.isdir(os.path.join(root, path))
        excluded = False
        for base, pattern, negate, directory in rules:
            relative = candidate[len(base)+1:] if base else candidate
            if (not directory or is_dir) and pattern.search(relative):
                excluded = not negate
        if excluded:
            return True
    return False


if __name__ == "__main__":
    sys.exit(0 if ignored(sys.argv[1], sys.argv[2]) else 1)
