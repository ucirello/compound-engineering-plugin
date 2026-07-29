#!/usr/bin/env python3
"""Compute fail-closed, deterministic scope signals for ce-code-review."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


CODE_EXTENSIONS = {
    ".rb", ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs",
    ".java", ".swift", ".kt", ".c", ".cc", ".cpp", ".cs", ".php",
    ".ex", ".exs", ".scala",
}

SIGNAL_PATTERNS = {
    "migrations": re.compile(
        r"db/migrate/|schema\.(rb|sql)|/migrations?/|alembic|flyway|liquibase",
        re.I,
    ),
    "frontend": re.compile(
        r"\.(tsx|jsx|vue|svelte|css|scss|html|erb|haml)$|/components?/|stimulus|turbo",
        re.I,
    ),
    "api": re.compile(
        r"/(routes?|controllers?|api|serializers?|graphql)/|\.proto$|openapi|swagger",
        re.I,
    ),
    "swift-ios": re.compile(r"\.(swift|kt|pbxproj|xcconfig|entitlements)$", re.I),
}

TEST_PATTERN = re.compile(
    r"(^|/)(tests?|spec|__tests__)/|(^|/)[^/]+[._-](test|spec)\.[^/]+$",
    re.I,
)
AGENT_SURFACE_PATTERN = re.compile(
    r"(^|/)(skills?|agents?|prompts?|tools?|mcp|commands?)(/|$)|SKILL\.md$|"
    r"(^|/)(AGENTS|CLAUDE|GEMINI)\.md$|\.cursor/|\.codex-plugin/|\.claude-plugin/",
    re.I,
)


def jj(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["jj", "--no-pager", "--color=never", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def valid_revision(ref: str | None) -> bool:
    if not ref:
        return False
    result = jj("log", "--no-graph", "-r", ref, "-T", 'commit_id ++ "\\n"')
    return result.returncode == 0 and len(result.stdout.splitlines()) == 1


def unique_common_ancestor(base: str, head: str) -> str | None:
    result = jj(
        "log",
        "--no-graph",
        "-r",
        f"heads(::{base} & ::{head})",
        "-T",
        'commit_id ++ "\\n"',
    )
    candidates = [line for line in result.stdout.splitlines() if line]
    if result.returncode != 0 or len(candidates) != 1:
        return None
    return candidates[0]


def fail_closed(reason: str) -> dict[str, object]:
    return {
        "status": "unknown",
        "reason": reason,
        "exec_lines": None,
        "uncounted_files": 1,
        "changed_files": [],
        "signals": [],
        "test_files_changed": False,
        "agent_surface": False,
        "has_learnings_corpus": Path("docs/solutions").is_dir(),
        "lite_eligible": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head")
    args = parser.parse_args()

    if not valid_revision(args.base):
        print(json.dumps(fail_closed("invalid base endpoint"), sort_keys=True))
        return 0
    if args.head is not None and not valid_revision(args.head):
        print(json.dumps(fail_closed("invalid head endpoint"), sort_keys=True))
        return 0

    diff_args = ["--from", args.base, "--to", "@"]
    if args.head:
        common_ancestor = unique_common_ancestor(args.base, args.head)
        if common_ancestor is None:
            print(json.dumps(fail_closed("common ancestor unavailable or ambiguous"), sort_keys=True))
            return 0
        diff_args = ["--from", common_ancestor, "--to", args.head]

    names = jj("diff", *diff_args, "--name-only")
    stats = jj("diff", *diff_args, "--stat")
    if names.returncode != 0 or stats.returncode != 0:
        print(json.dumps(fail_closed("jj diff failed"), sort_keys=True))
        return 0

    files = sorted(line for line in names.stdout.splitlines() if line)
    line_counts: dict[str, int] = {}
    for line in stats.stdout.splitlines():
        if " | " not in line:
            continue
        path, summary = line.rsplit(" | ", 1)
        match = re.match(r"\s*(\d+)\b", summary)
        if match:
            line_counts[path.strip()] = int(match.group(1))
    executable_lines = sum(
        line_counts.get(file, 0)
        for file in files
        if Path(file).suffix.lower() in CODE_EXTENSIONS
    )

    uncounted = sum(
        1
        for file in files
        if Path(file).suffix.lower() not in CODE_EXTENSIONS or file not in line_counts
    )
    signals = [
        name
        for name, pattern in SIGNAL_PATTERNS.items()
        if any(pattern.search(file) for file in files)
    ]
    lite = 1 <= executable_lines <= 39 and uncounted == 0 and not signals

    result = {
        "status": "complete",
        "reason": None,
        "exec_lines": executable_lines,
        "uncounted_files": uncounted,
        "changed_files": files,
        "signals": signals,
        "test_files_changed": any(TEST_PATTERN.search(file) for file in files),
        "agent_surface": any(AGENT_SURFACE_PATTERN.search(file) for file in files),
        "has_learnings_corpus": Path("docs/solutions").is_dir(),
        "lite_eligible": lite,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
