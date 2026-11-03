#!/usr/bin/env python3
"""Check repo-local ignore safety for setup's two fixed targets, without Git.

No files are created and JJ snapshotting is disabled. This intentionally checks
repository .gitignore rules, not machine-global exclusions: local secrets and
scratch should remain protected for other contributors too.
"""

import fnmatch
import os
from pathlib import Path
import re
import subprocess
import sys


def pattern_regex(pattern):
    """Translate slash-separated wildmatch, including ** and escaped literals."""
    if any(token in pattern for token in ("[[:", "[[.", "[[=")):
        raise ValueError("unsupported locale-dependent character class")
    out, i = "", 0
    while i < len(pattern):
        char = pattern[i]
        if char == "\\":
            i += 1
            if i == len(pattern):
                raise ValueError("dangling pattern escape")
            out += re.escape(pattern[i])
        elif char == "*":
            end = i
            while end < len(pattern) and pattern[end] == "*":
                end += 1
            if end - i >= 2 and (i == 0 or pattern[i - 1] == "/") and (end == len(pattern) or pattern[end] == "/"):
                if end < len(pattern):
                    out += "(?:[^/]+/)*"
                    end += 1
                else:
                    out += ".*"
            else:
                out += "[^/]*"
            i = end - 1
        elif char == "?":
            out += "[^/]"
        elif char == "[":
            end = i + 1
            if end < len(pattern) and pattern[end] in "!^":
                end += 1
            if end < len(pattern) and pattern[end] == "]":
                end += 1
            end = pattern.find("]", end)
            if end < 0:
                out += r"\["
            else:
                # fnmatch handles ranges and negated classes, but a class may
                # never consume a path separator in ignore wildmatch.
                out += "(?!/)" + fnmatch.translate(pattern[i:end + 1])[4:-3]
                i = end
        else:
            out += re.escape(char)
        i += 1
    return re.compile("^(?:" + out + ")$")


def read_rules(path, base):
    if path.is_symlink():
        raise ValueError("symlink ignore file")
    if not path.exists():
        return []
    rules = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        # Only unescaped trailing spaces are discarded.
        while raw.endswith(" "):
            backslashes = len(raw[:-1]) - len(raw[:-1].rstrip("\\"))
            if backslashes % 2:
                break
            raw = raw[:-1]
        if not raw or raw.startswith("#"):
            continue
        negate = raw.startswith("!")
        pattern = raw[1:] if negate else raw
        directory_only = pattern.endswith("/")
        pattern = pattern.rstrip("/")
        anchored = pattern.startswith("/") or "/" in pattern
        pattern = pattern.lstrip("/")
        if pattern:
            rules.append((base, pattern_regex(pattern), anchored, directory_only, negate))
    return rules


def local_ignored(root, target, directory=False):
    """Evaluate each ancestor before descending: excluded parents cannot reopen."""
    rules = []
    parts = target.split("/")
    for index in range(len(parts)):
        base = "/".join(parts[:index])
        if root.joinpath(*parts[:index]).is_symlink():
            raise ValueError("symlink rule directory")
        rules.extend(read_rules(root.joinpath(*parts[:index], ".gitignore"), base))
        candidate = "/".join(parts[:index + 1])
        is_directory = index < len(parts) - 1 or directory
        ignored = False
        for rule_base, regex, anchored, directory_only, negate in rules:
            relative = candidate[len(rule_base) + 1:] if rule_base else candidate
            if directory_only and not is_directory:
                continue
            value = relative if anchored else relative.rsplit("/", 1)[-1]
            if regex.fullmatch(value):
                ignored = not negate
        if ignored:
            return True
    return False


def check(root, target, directory=False):
    try:
        env = {key: value for key, value in os.environ.items()
               if not key.startswith("GIT_") and key not in ("JJ_REPO", "JJ_WORKSPACE")}
        listed = subprocess.run(
            ["jj", "--ignore-working-copy", "file", "list", "-r", "@", "--", target],
            cwd=str(root), env=env, capture_output=True, text=True, timeout=15,
        )
        if listed.returncode:
            return "unknown"
        if listed.stdout.strip():
            return "missing"  # Ignore rules do not untrack existing content.
        return "ok" if local_ignored(root, target, directory) else "missing"
    except (OSError, UnicodeError, ValueError, re.error, subprocess.TimeoutExpired):
        return "unknown"


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve()
    target = sys.argv[2]
    if target not in (".rocketclaw/config.local.yaml", ".tmp"):
        raise SystemExit("only setup's fixed targets are supported")
    print(check(root, target, target == ".tmp"))
