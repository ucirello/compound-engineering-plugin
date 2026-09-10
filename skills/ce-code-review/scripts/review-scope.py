#!/usr/bin/env python3
"""Compute fail-closed, deterministic scope signals for ce-code-review."""

from __future__ import annotations

import argparse
import json
import os
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

_REPO_ROOT: Path | None = None


def jj(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["jj", *args], capture_output=True, text=True, check=False, cwd=cwd
    )


def repo_root() -> Path:
    """The workspace root, matching how docs_root is resolved everywhere else.

    docs_root is repo-relative (``<repo-root>/<docs_root>``), so the corpus
    check must resolve against the JJ workspace root, not the current working
    directory. ce-code-review can run from a subdirectory (``jj diff`` still
    works there), where ``Path.cwd()`` would join docs_root under the subdir and
    wrongly report the corpus absent. Fall back to cwd when jj can't answer.
    Subsequent jj invocations use this path as cwd so file lists stay
    repo-relative (``src/example.py``, not a workspace-prefixed path).
    """
    global _REPO_ROOT
    if _REPO_ROOT is not None:
        return _REPO_ROOT
    result = jj("workspace", "root")
    if result.returncode == 0 and result.stdout.strip():
        _REPO_ROOT = Path(result.stdout.strip()).resolve()
    else:
        _REPO_ROOT = Path.cwd().resolve()
    return _REPO_ROOT


def jj_at(*args: str) -> subprocess.CompletedProcess[str]:
    return jj(*args, cwd=str(repo_root()))


def valid_commit(ref: str | None) -> bool:
    if not ref:
        return False
    result = jj_at("log", "-r", ref, "--no-graph", "-T", "commit_id", "-n", "1")
    return result.returncode == 0 and bool(result.stdout.strip())


def unique_merge_base(base: str, head: str) -> str | None:
    result = jj_at(
        "log",
        "-r",
        f"heads(::{base} & ::{head})",
        "--no-graph",
        "-T",
        'commit_id ++ "\\n"',
    )
    candidates = [line for line in result.stdout.splitlines() if line]
    if result.returncode != 0 or len(candidates) != 1:
        return None
    return candidates[0]


def executable_lines_from_git_diff(diff_text: str) -> int:
    """Count added+deleted lines on code-extension paths from a git-format diff."""
    current: str | None = None
    added = 0
    deleted = 0
    total = 0

    def flush() -> None:
        nonlocal current, added, deleted, total
        if current and Path(current).suffix.lower() in CODE_EXTENSIONS:
            total += added + deleted
        current = None
        added = 0
        deleted = 0

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            flush()
            continue
        if line.startswith("+++ b/"):
            current = line[6:]
            continue
        if line.startswith("+++ /dev/null"):
            current = current or None
            continue
        if line.startswith("--- "):
            continue
        if current is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            deleted += 1
    flush()
    return total


DEFAULT_DOCS_ROOT = "docs"


def normalize_docs_root(docs_root: str | None) -> str:
    """Fall back to the default root for an unset, empty, or unsubstituted value.

    The calling skill substitutes a resolved path for the ``<root>`` placeholder
    before invoking this script. If that substitution is missing — the value is
    empty, or still contains angle brackets (a literal ``<root>``) — treat it as
    unset and use the default ``docs``, which is exactly the block's unset
    behavior. This keeps the common default-config case correct even when the
    caller forgets to substitute.
    """
    if not docs_root or "<" in docs_root or ">" in docs_root:
        return DEFAULT_DOCS_ROOT
    return docs_root


def has_learnings_corpus(docs_root: str | None) -> bool:
    """Whether a `<docs_root>/solutions` learnings corpus exists.

    docs_root is the artifact root resolved by the calling skill (default
    ``docs``). Guard it the way the skill-prose rule does: normalize an
    unset/placeholder value to the default, and treat a value that is absolute
    or escapes the repository as absent rather than probing an out-of-repo path.
    """
    docs_root = normalize_docs_root(docs_root)
    if os.path.isabs(docs_root):
        return False
    repo = repo_root()
    candidate = (repo / docs_root / "solutions").resolve()
    if repo not in candidate.parents and candidate != repo:
        return False
    return candidate.is_dir()


def fail_closed(reason: str, learnings_corpus: bool = False) -> dict[str, object]:
    return {
        "status": "unknown",
        "reason": reason,
        "exec_lines": None,
        "uncounted_files": 1,
        "changed_files": [],
        "signals": [],
        "test_files_changed": False,
        "agent_surface": False,
        "has_learnings_corpus": learnings_corpus,
        "lite_eligible": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head")
    parser.add_argument("--docs-root", default="docs")
    args = parser.parse_args()

    learnings_corpus = has_learnings_corpus(args.docs_root)

    if not valid_commit(args.base):
        print(json.dumps(fail_closed("invalid base endpoint", learnings_corpus), sort_keys=True))
        return 0
    if args.head is not None and not valid_commit(args.head):
        print(json.dumps(fail_closed("invalid head endpoint", learnings_corpus), sort_keys=True))
        return 0

    if args.head:
        merge_base = unique_merge_base(args.base, args.head)
        if merge_base is None:
            print(json.dumps(fail_closed("merge base unavailable or ambiguous", learnings_corpus), sort_keys=True))
            return 0
        diff_from = merge_base
        diff_to = args.head
        name_args = ["diff", "--name-only", "--from", diff_from, "--to", diff_to]
        git_args = ["diff", "--git", "--from", diff_from, "--to", diff_to]
    else:
        name_args = ["diff", "--name-only", "--from", args.base]
        git_args = ["diff", "--git", "--from", args.base]

    names = jj_at(*name_args)
    git_diff = jj_at(*git_args)
    if names.returncode != 0 or git_diff.returncode != 0:
        print(json.dumps(fail_closed("jj diff failed", learnings_corpus), sort_keys=True))
        return 0

    files = sorted(line for line in names.stdout.splitlines() if line)
    executable_lines = executable_lines_from_git_diff(git_diff.stdout)

    uncounted = sum(
        1 for file in files if Path(file).suffix.lower() not in CODE_EXTENSIONS
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
        "has_learnings_corpus": learnings_corpus,
        "lite_eligible": lite,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
