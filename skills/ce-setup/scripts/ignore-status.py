#!/usr/bin/env python3
"""Conservative local .gitignore coverage check; never invokes Git.

Exit 0 proves coverage for ordinary patterns; exit 1 means no proven coverage.
Unsupported escaped patterns fail closed, so setup can offer an explicit rule.
"""
import pathlib
import re
import sys


def covered(root, relative):
    root = pathlib.Path(root).resolve()
    directory_target = relative.endswith("/")
    relative = relative.strip("/")
    parts = relative.split("/")
    rules = []
    for level in range(len(parts)):
        directory = root.joinpath(*parts[:level])
        rule_file = directory / ".gitignore"
        for raw in rule_file.read_text().splitlines() if rule_file.is_file() else []:
            rule = raw.rstrip()
            if not rule or rule.startswith("#"):
                continue
            if "\\" in rule or "[" in rule:
                return False  # cannot prove coverage for this syntax
            negate = rule.startswith("!")
            rule = rule[1:] if negate else rule
            directory_only = rule.endswith("/")
            anchored = rule.startswith("/")
            rule = rule.strip("/")
            if not rule:
                continue
            regex = re.escape(rule)
            regex = regex.replace(r"\*\*/", "(?:.*/)?").replace(r"\*\*", ".*")
            regex = regex.replace(r"\*", "[^/]*").replace(r"\?", "[^/]")
            prefix = "^" if anchored or "/" in rule else r"(?:^|/)"
            rules.append((level, re.compile(prefix + regex + "$"), negate, directory_only))
        ignored = False
        is_directory = level < len(parts) - 1 or directory_target or root.joinpath(*parts).is_dir()
        for origin, regex, negate, directory_only in rules:
            target = "/".join(parts[origin:level + 1])
            if (not directory_only or is_directory) and regex.search(target):
                ignored = not negate
        # An excluded parent cannot be re-included by a child's ignore file.
        if ignored:
            return True
    return False


if __name__ == "__main__":
    sys.exit(0 if covered(sys.argv[1], sys.argv[2]) else 1)
