#!/usr/bin/env python3
"""Conservative local ignore check, without launching Git or changing files.

Recognizes literal directory/file rules and ordinary globs in applicable
.gitignore files. Unknown bracket/escape patterns fail closed (not ignored).
"""
import fnmatch
import os
from pathlib import Path
import subprocess
import sys


def ignored(root, relative):
    root = Path(root).resolve()
    relative = relative.replace(os.sep, "/").rstrip("/")
    if relative.startswith("/") or ".." in relative.split("/"):
        return False
    tracked = subprocess.run(["jj", "file", "list", "--", relative], cwd=root,
                             capture_output=True, text=True)
    if tracked.returncode or tracked.stdout.strip():
        return False
    parts = relative.split("/")
    result = False
    for depth in range(len(parts)):
        scope = root.joinpath(*parts[:depth])
        config = scope / ".gitignore"
        if not config.is_file():
            continue
        local = "/".join(parts[depth:])
        for raw in config.read_text().splitlines():
            rule = raw.rstrip()
            if not rule or rule.startswith("#"):
                continue
            negate = rule.startswith("!")
            rule = rule[1:] if negate else rule
            if "\\" in rule or "[" in rule:
                return False
            directory = rule.endswith("/")
            anchored = rule.startswith("/")
            rule = rule.strip("/")
            candidates = [local] if anchored or "/" in rule else local.split("/")
            if directory or "/" in rule:
                candidates += ["/".join(local.split("/")[:i]) for i in range(1, len(local.split("/")))]
            # Ordinary * does not cross slash; ** intentionally does.
            def matches(candidate):
                if "**" in rule:
                    return fnmatch.fnmatchcase(candidate, rule)
                return len(candidate.split("/")) == len(rule.split("/")) and all(
                    fnmatch.fnmatchcase(c, p) for c, p in zip(candidate.split("/"), rule.split("/")))
            if any(matches(candidate) for candidate in candidates):
                result = not negate
    return result


if __name__ == "__main__":
    sys.exit(0 if ignored(sys.argv[1], sys.argv[2]) else 1)
