#!/usr/bin/env python3
"""Conservatively prove local ignore coverage without invoking Git.

Evaluate root and nested .gitignore rules, including negation and directory
patterns. Unknown global excludes are not counted as proof: a missing result
asks setup to offer an explicit local rule, never claims content is protected.
"""
import os
import re
import subprocess
import sys


def pattern_regex(pattern):
    out = ""
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "\\" and i + 1 < len(pattern):
            i += 1
            out += re.escape(pattern[i])
        elif c == "*":
            if pattern[i:i + 2] == "**":
                i += 1
                if pattern[i + 1:i + 2] == "/":
                    i += 1
                    out += "(?:.*/)?"
                else:
                    out += ".*"
            else:
                out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        elif c == "[":
            end = pattern.find("]", i + 1)
            if end < 0:
                out += r"\["
            else:
                content = pattern[i + 1:end]
                if content.startswith("!"):
                    content = "^" + content[1:]
                out += "[" + content + "]"
                i = end
        else:
            out += re.escape(c)
        i += 1
    return re.compile("^" + out + "$")


def ignored(root, target):
    target = target.replace(os.sep, "/")
    directory = target.endswith("/")
    target = target.rstrip("/")
    tracked = subprocess.run(["jj", "--ignore-working-copy", "file", "list", target],
                             cwd=root, capture_output=True, text=True)
    if tracked.returncode or tracked.stdout.strip():
        return False
    rules = []
    parts = target.split("/")
    for index, part in enumerate(parts):
        parent = "/".join(parts[:index])
        path = os.path.join(root, parent, ".gitignore")
        try:
            with open(path, encoding="utf-8") as stream:
                for raw in stream:
                    line = raw.rstrip("\r\n")
                    while line.endswith(" ") and not line.endswith("\\ "):
                        line = line[:-1]
                    if not line or line.startswith("#"):
                        continue
                    negate = line.startswith("!")
                    if negate:
                        line = line[1:]
                    only_dir = line.endswith("/")
                    line = line.rstrip("/")
                    anchored = line.startswith("/") or "/" in line
                    line = line.lstrip("/")
                    rules.append((parent, pattern_regex(line), anchored, only_dir, negate))
        except FileNotFoundError:
            pass
        current = "/".join(parts[:index + 1])
        is_dir = index < len(parts) - 1 or directory or os.path.isdir(os.path.join(root, current))
        state = False
        for base, matcher, anchored, only_dir, negate in rules:
            relative = current[len(base) + 1:] if base else current
            if only_dir and not is_dir:
                continue
            if matcher.fullmatch(relative if anchored else part):
                state = not negate
        # An excluded parent cannot be re-included by descendant rules.
        if state:
            return True
    return False


if __name__ == "__main__":
    try:
        sys.exit(0 if ignored(os.path.abspath(sys.argv[1]), sys.argv[2]) else 1)
    except (OSError, ValueError, re.error):
        sys.exit(2)
