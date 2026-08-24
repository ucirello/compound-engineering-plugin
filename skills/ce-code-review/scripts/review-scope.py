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


def jj(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["jj", "--no-pager", *args], capture_output=True, text=True, check=False
    )


def valid_revision(ref: str | None) -> bool:
    if not ref:
        return False
    result = jj("log", "-r", ref, "--no-graph", "-T", 'commit_id ++ "\\n"')
    return result.returncode == 0 and len(result.stdout.splitlines()) == 1


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


def workspace_root() -> Path:
    """The workspace root, matching how docs_root is resolved everywhere else.

    docs_root is workspace-relative (``<workspace-root>/<docs_root>``), so the corpus
    check must resolve against the Jujutsu workspace root, not the current working
    directory. ce-code-review can run from a subdirectory (``jj diff`` still
    works there), where ``Path.cwd()`` would join docs_root under the subdir and
    wrongly report the corpus absent. Fall back to cwd when Jujutsu cannot answer.
    """
    result = jj("workspace", "root")
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return Path.cwd().resolve()


def has_learnings_corpus(docs_root: str | None) -> bool:
    """Whether a `<docs_root>/solutions` learnings corpus exists.

    docs_root is the artifact root resolved by the calling skill (default
    ``docs``). Guard it the way the skill-prose rule does: normalize an
    unset/placeholder value to the default, and treat a value that is absolute
    or escapes the workspace as absent rather than probing an external path.
    """
    docs_root = normalize_docs_root(docs_root)
    if os.path.isabs(docs_root):
        return False
    workspace = workspace_root()
    candidate = (workspace / docs_root / "solutions").resolve()
    if workspace not in candidate.parents and candidate != workspace:
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
    parser.add_argument("--to")
    parser.add_argument("--docs-root", default="docs")
    args = parser.parse_args()

    learnings_corpus = has_learnings_corpus(args.docs_root)

    if not valid_revision(args.base):
        print(json.dumps(fail_closed("invalid base endpoint", learnings_corpus), sort_keys=True))
        return 0
    if args.to is not None and not valid_revision(args.to):
        print(json.dumps(fail_closed("invalid destination revision", learnings_corpus), sort_keys=True))
        return 0

    diff_args = ["--from", args.base, "--to", args.to or "@"]
    names = jj("diff", *diff_args, "--name-only")
    patch = jj("diff", *diff_args, "--git")
    if names.returncode != 0 or patch.returncode != 0:
        print(json.dumps(fail_closed("jj diff failed", learnings_corpus), sort_keys=True))
        return 0

    files = sorted(line for line in names.stdout.splitlines() if line)
    executable_lines = 0
    current_path: str | None = None
    old_path: str | None = None
    for line in patch.stdout.splitlines():
        if line.startswith("--- a/"):
            old_path = line[6:]
        elif line.startswith("+++ b/"):
            current_path = line[6:]
        elif line == "+++ /dev/null":
            current_path = old_path
        elif current_path and Path(current_path).suffix.lower() in CODE_EXTENSIONS:
            if (line.startswith("+") and not line.startswith("+++")) or (
                line.startswith("-") and not line.startswith("---")
            ):
                executable_lines += 1

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
