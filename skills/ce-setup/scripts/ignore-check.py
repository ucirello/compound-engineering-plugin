#!/usr/bin/env python3
"""Conservative local ignore safety check; no Git executable or file creation.

Return success only when a repository .gitignore rule demonstrably covers the
path. Global excludes are not team safety evidence. Negation wins in order;
unsupported escaped patterns fail closed rather than claiming protection.
"""
import fnmatch
from pathlib import Path
import sys


def covered(root, relative):
    parts = relative.strip("/").split("/")
    ignored = False
    for depth in range(len(parts)):
        base = root.joinpath(*parts[:depth])
        config = base / ".gitignore"
        if not config.is_file():
            continue
        target = "/".join(parts[depth:])
        for raw in config.read_text().splitlines():
            rule = raw.rstrip()
            if not rule or rule.startswith("#"):
                continue
            if "\\" in rule:
                return False
            negate = rule.startswith("!")
            rule = rule[1:] if negate else rule
            directory = rule.endswith("/")
            rule = rule.rstrip("/")
            anchored = rule.startswith("/") or "/" in rule
            rule = rule.lstrip("/")
            prefixes = ["/".join(parts[depth:stop]) for stop in range(depth + 1, len(parts) + 1)]
            if directory and not relative.endswith("/"):
                prefixes = prefixes[:-1]
            candidates = prefixes if anchored else [p.rsplit("/", 1)[-1] for p in prefixes]
            # fnmatch * crosses /; avoid claiming coverage for that difference.
            matches = any(fnmatch.fnmatchcase(p, rule) and ("**" in rule or p.count("/") == rule.count("/")) for p in candidates)
            if matches:
                ignored = not negate
    return ignored


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve()
    relative = sys.argv[2]
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        sys.exit(2)
    sys.exit(0 if covered(root, relative) else 1)
