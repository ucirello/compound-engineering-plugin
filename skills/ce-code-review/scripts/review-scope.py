#!/usr/bin/env python3
"""Compute fail-closed, deterministic scope facts for ce-code-review.

The helper never awards lite. It reports counts, path classes, and floors
the skill's Review depth gate reads. `hard_block_full` forces the full
spine: a path class the script can name, a file it could not count, or a
change whose executable non-test lines reach the full floor. Below that
floor, size is a fact the gate reads, never a decision; the agent judges
consequence.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import re
import subprocess
import sys
from pathlib import Path


CODE_EXTENSIONS = {
    ".rb", ".py", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".go", ".rs",
    ".java", ".swift", ".kt", ".c", ".cc", ".cpp", ".cs", ".php",
    ".ex", ".exs", ".scala",
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".pl", ".pm", ".lua", ".dart",
    ".vue", ".svelte",
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

# Classes the script can name from paths alone. These force full; they do not
# award lite.
HARD_BLOCK_PATTERNS = {
    "migrations": SIGNAL_PATTERNS["migrations"],
}

# Silent-pass guards the script can name from paths alone. These forbid lite
# (the change needs the adversarial read the focused path carries) but do not
# force full; consequence still decides focused versus full. Silent-pass guards
# outside these paths are the agent's question.
SILENT_PASS_PATTERNS = {
    "ci": re.compile(
        r"(^|/)\.github/workflows/|(^|/)\.gitlab-ci\.yml$|(^|/)\.gitlab-ci/"
        r"|(^|/)Jenkinsfile$|(^|/)\.circleci/|(^|/)\.buildkite/",
        re.I,
    ),
}

# Executable non-test changed lines at or above this run the full spine; it
# matches the maintainability reviewer's trigger. Below it, consequence decides.
FULL_EXEC_LINE_MIN = 200

# Conventions recognized: tests?/spec/__tests__ directories; a .test./.spec.
# suffix; a test_*.py / conftest.py Python prefix; and a case-sensitive
# Test/Tests/Spec class-file suffix (Java/C#/Scala/Swift/Kotlin), so that
# Contest.java or Manifest.cs stays production code.
TEST_PATTERN = re.compile(
    r"(^|/)(tests?|spec|__tests__)/"
    r"|(^|/)[^/]+[._-](test|spec)\.[^/]+$"
    r"|(^|/)(test_[^/]+|conftest)\.[^/]+$"
    r"|(?-i:(^|/)[^/]+(Test|Tests|Spec)\.(java|kt|scala|swift|cs)$)",
    re.I,
)
AGENT_SURFACE_PATTERN = re.compile(
    r"(^|/)(skills?|agents?|prompts?|tools?|mcp|commands?)(/|$)|SKILL\.md$|"
    r"(^|/)(AGENTS|CLAUDE|GEMINI)\.md$|\.cursor/|\.codex-plugin/|\.claude-plugin/",
    re.I,
)

_DIFF_GIT_HEADER = re.compile(r"^diff --git a/(.*) b/(.*)$")


def workspace_root() -> str:
    proc = subprocess.run(
        ["jj", "--no-pager", "workspace", "root"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError("not a jj workspace")
    return proc.stdout.strip()


def jj(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    root = cwd or workspace_root()
    return subprocess.run(
        ["jj", "--no-pager", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def valid_commit(ref: str | None, root: str) -> bool:
    if not ref:
        return False
    result = jj(
        "log", "-r", ref, "--no-graph", "-T", 'commit_id ++ "\n"', "-n", "1",
        cwd=root,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def unique_merge_base(base: str, head: str, root: str) -> str | None:
    result = jj(
        "log",
        "-r",
        f"heads(::{base} & ::{head})",
        "--no-graph",
        "-T",
        'commit_id ++ "\n"',
        cwd=root,
    )
    candidates = [line for line in result.stdout.splitlines() if line]
    if result.returncode != 0 or len(candidates) != 1:
        return None
    return candidates[0]


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


@functools.lru_cache(maxsize=None)
def repo_root() -> Path:
    """The workspace root, matching how docs_root is resolved everywhere else.

    docs_root is workspace-relative (``<workspace-root>/<docs_root>``), so the
    corpus check must resolve against ``jj workspace root``, not the current
    working directory. ce-code-review can run from a subdirectory or from
    another directory inside a linked workspace; ``jj diff`` still works once
    commands use cwd=workspace root, where ``Path.cwd()`` would join docs_root
    under the subdir and wrongly report the corpus absent.
    """
    return Path(workspace_root()).resolve()


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
    try:
        repo = repo_root()
    except RuntimeError:
        return False
    candidate = (repo / docs_root / "solutions").resolve()
    if repo not in candidate.parents and candidate != repo:
        return False
    return candidate.is_dir()


PACKS_RESOLVER = Path(__file__).resolve().parent / "packs-resolve.py"
# Parse-only mode does no clone or cache work, so this bound only guards against a
# wedged interpreter; the helper is meant to be cheap and must never hang scope.
PACKS_RESOLVER_TIMEOUT = 30.0


def declared_packs() -> tuple[bool | None, int]:
    """Whether the local RocketClaw config declares Packs, from the config alone.

    Runs the sibling resolver in `--declared-only` mode, which parses the
    `packs:` list from both RocketClaw config layers and shape-checks each
    entry with no clone or cache work. Its `declared` is true when any entry
    parsed or the block is malformed -- a broken declaration is still one the
    learnings pass must surface in Coverage. ``None`` means the helper could
    not tell (resolver missing, crashed, timed out, or answered without
    `declared`); the caller then falls closed to reading the config's `packs:`
    key itself. The second value keeps the `pack_roots` output slot and is
    always 0: nothing resolves here.
    """
    if not PACKS_RESOLVER.is_file():
        return None, 0
    try:
        root = str(repo_root())
        proc = subprocess.run(
            [sys.executable, str(PACKS_RESOLVER), "--declared-only"],
            capture_output=True,
            text=True,
            check=False,
            cwd=root,
            timeout=PACKS_RESOLVER_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired, RuntimeError):
        return None, 0
    if proc.returncode != 0:
        return None, 0
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        return None, 0
    declared = data.get("declared") if isinstance(data, dict) else None
    if not isinstance(declared, bool):
        return None, 0
    return declared, 0


def repo_signals(docs_root: str | None, local_scope: bool) -> dict[str, object]:
    """Facts about the repo, not the diff: present in every result shape.

    `declared_packs` describes the local checkout's config, which is not the
    reviewed tree's config in remote scope, so it is evaluated only when
    `local_scope` is true and reported as ``None`` otherwise.
    """
    learnings_corpus = has_learnings_corpus(docs_root)
    declared, pack_roots = declared_packs() if local_scope else (None, 0)
    return {
        "has_learnings_corpus": learnings_corpus,
        "declared_packs": declared,
        "pack_roots": pack_roots,
    }


def fail_closed(reason: str, signals: dict[str, object]) -> dict[str, object]:
    return {
        "status": "unknown",
        "reason": reason,
        "exec_lines": None,
        "exec_nontest_lines": None,
        "unclassified_lines": {},
        "changed_lines": None,
        "uncounted_files": 1,
        "changed_files": [],
        "signals": [],
        "hard_block_classes": ["unknown-scope"],
        "hard_block_full": True,
        "silent_pass_classes": [],
        "size_band": "unknown",
        "test_files_changed": False,
        "agent_surface": False,
        **signals,
    }


def size_band_for(exec_nontest_lines: int | None) -> str:
    """Band the executable non-test lines: `large` is a full-spine floor.

    Sources the extension list cannot name are not banded; they are reported
    in `unclassified_lines` for the gate's consequence judgment.
    """
    if exec_nontest_lines is None:
        return "unknown"
    if exec_nontest_lines >= FULL_EXEC_LINE_MIN:
        return "large"
    return "small"


def matching_classes(
    files: list[str], patterns: dict[str, re.Pattern[str]]
) -> list[str]:
    return [
        name
        for name, pattern in patterns.items()
        if any(pattern.search(file) for file in files)
    ]


def parse_git_format_diff(diff_text: str) -> tuple[dict[str, int | None], set[str], int]:
    """Per-path added+deleted counts and executable-mode paths from `jj diff --git`.

    ``None`` means the path is binary or otherwise uncounted. The third return
    is how many such uncounted paths were seen. Executable-mode paths are those
    whose resulting mode ends in 755 (new mode, else deleted-file old mode).
    """
    counts: dict[str, int | None] = {}
    executable_mode_paths: set[str] = set()
    current: str | None = None
    added = 0
    deleted = 0
    uncounted = 0
    in_hunk = False
    binary = False
    new_mode: str | None = None
    old_mode: str | None = None
    deleted_mode: str | None = None

    def flush() -> None:
        nonlocal current, added, deleted, uncounted, in_hunk, binary
        nonlocal new_mode, old_mode, deleted_mode
        if current is None:
            return
        if binary:
            counts[current] = None
            uncounted += 1
        else:
            counts[current] = added + deleted
        mode = deleted_mode if deleted_mode is not None else (
            new_mode if new_mode is not None else old_mode
        )
        if mode is not None and mode.endswith("755"):
            executable_mode_paths.add(current)
        current = None
        added = 0
        deleted = 0
        in_hunk = False
        binary = False
        new_mode = None
        old_mode = None
        deleted_mode = None

    for line in diff_text.splitlines():
        header = _DIFF_GIT_HEADER.match(line)
        if header:
            flush()
            current = header.group(2)
            continue
        if current is None:
            continue
        if line.startswith("Binary files ") or line.startswith("GIT binary patch"):
            binary = True
            continue
        if line.startswith("new file mode "):
            new_mode = line.rsplit(" ", 1)[-1]
            continue
        if line.startswith("deleted file mode "):
            deleted_mode = line.rsplit(" ", 1)[-1]
            continue
        if line.startswith("new mode "):
            new_mode = line.rsplit(" ", 1)[-1]
            continue
        if line.startswith("old mode "):
            old_mode = line.rsplit(" ", 1)[-1]
            continue
        if line.startswith("@@"):
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            deleted += 1
    flush()
    return counts, executable_mode_paths, uncounted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head")
    parser.add_argument("--docs-root", default="docs")
    args = parser.parse_args()

    try:
        root = workspace_root()
    except RuntimeError:
        print(json.dumps(fail_closed("not a jj workspace", {
            "has_learnings_corpus": False,
            "declared_packs": None,
            "pack_roots": 0,
        }), sort_keys=True))
        return 0

    # Remote scope (pr-remote / branch-remote) always passes --head, even when a
    # best-effort fetch left it empty; the local config is not that tree's config.
    repo = repo_signals(args.docs_root, local_scope=args.head is None)

    if not valid_commit(args.base, root):
        print(json.dumps(fail_closed("invalid base endpoint", repo), sort_keys=True))
        return 0
    if args.head is not None and not valid_commit(args.head, root):
        print(json.dumps(fail_closed("invalid head endpoint", repo), sort_keys=True))
        return 0

    if args.head:
        merge_base = unique_merge_base(args.base, args.head, root)
        if merge_base is None:
            print(json.dumps(fail_closed("merge base unavailable or ambiguous", repo), sort_keys=True))
            return 0
        diff_from, diff_to = merge_base, args.head
        names = jj("diff", "--from", diff_from, "--to", diff_to, "--name-only", cwd=root)
        git_diff = jj("diff", "--from", diff_from, "--to", diff_to, "--git", cwd=root)
    else:
        names = jj("diff", "--from", args.base, "--name-only", cwd=root)
        git_diff = jj("diff", "--from", args.base, "--git", cwd=root)

    if names.returncode != 0 or git_diff.returncode != 0:
        print(json.dumps(fail_closed("jj diff failed", repo), sort_keys=True))
        return 0

    files = sorted(line for line in names.stdout.splitlines() if line)
    counts, executable_mode_paths, uncounted = parse_git_format_diff(git_diff.stdout)
    executable_lines = 0
    executable_nontest_lines = 0
    unclassified_lines: dict[str, int] = {}
    changed_lines = 0
    for name in files:
        total = counts.get(name)
        if total is None:
            # Name-only listed it but git-format did not count it (rename-only,
            # binary, or empty). Treat unknown counts as uncounted.
            if name not in counts:
                uncounted += 1
            continue
        changed_lines += total
        if Path(name).suffix.lower() in CODE_EXTENSIONS or name in executable_mode_paths:
            executable_lines += total
            if not TEST_PATTERN.search(name):
                executable_nontest_lines += total
        elif not TEST_PATTERN.search(name):
            ext = Path(name).suffix.lower()
            unclassified_lines[ext] = unclassified_lines.get(ext, 0) + total

    signals = matching_classes(files, SIGNAL_PATTERNS)
    hard_block_classes = matching_classes(files, HARD_BLOCK_PATTERNS)
    silent_pass_classes = matching_classes(files, SILENT_PASS_PATTERNS)
    if uncounted:
        hard_block_classes.append("uncounted")
    band = size_band_for(executable_nontest_lines)

    result = {
        "status": "complete",
        "reason": None,
        "exec_lines": executable_lines,
        "exec_nontest_lines": executable_nontest_lines,
        "unclassified_lines": unclassified_lines,
        "changed_lines": changed_lines,
        "uncounted_files": uncounted,
        "changed_files": files,
        "signals": signals,
        "hard_block_classes": hard_block_classes,
        "hard_block_full": bool(hard_block_classes) or band != "small",
        "silent_pass_classes": silent_pass_classes,
        "size_band": band,
        "test_files_changed": any(TEST_PATTERN.search(file) for file in files),
        "agent_surface": any(AGENT_SURFACE_PATTERN.search(file) for file in files),
        **repo,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
