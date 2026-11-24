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
}

# Classes the script can name from paths alone. These force full; they do not
# award lite.
HARD_BLOCK_PATTERNS = {
    "migrations": SIGNAL_PATTERNS["migrations"],
}

# Potential silent-pass guards identified by path. The agent assesses what
# they protect; these signals do not force a depth or select a reviewer.
SILENT_PASS_PATTERNS = {
    "ci": re.compile(
        r"(^|/)\.github/workflows/|(^|/)\.gitlab-ci\.yml$|(^|/)\.gitlab-ci/"
        r"|(^|/)Jenkinsfile$|(^|/)\.circleci/|(^|/)\.buildkite/",
        re.I,
    ),
}

# Executable non-test changed lines at or above this run the full spine; it
# matches the maintainability reviewer's trigger. Below it, consequence decides.
# Whole-file deletions never count toward it; their separate band is an
# inspection cue, not a depth floor.
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


def jj(*args: str, snapshot: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["jj", "--color=never", "--no-pager",
         *([] if snapshot else ["--ignore-working-copy"]), *args],
        cwd=repo_root(),
        capture_output=True,
        encoding="utf-8",
        errors="surrogateescape",
        check=False,
    )


def resolve_commit(ref: str | None, *, snapshot: bool = False) -> str | None:
    if not ref:
        return None
    result = jj("log", "--no-graph", "-r", ref, "-T", 'commit_id ++ "\\n"', snapshot=snapshot)
    value = result.stdout.strip()
    return value if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value) else None


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
    """Find the workspace root even when the caller starts in a subdirectory."""
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / ".jj").is_dir():
            return candidate
    raise ValueError("not inside a JJ workspace")


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


PACKS_RESOLVER = Path(__file__).resolve().parent / "packs-resolve.py"
# Parse-only mode does no git or cache work, so this bound only guards against a
# wedged interpreter; the helper is meant to be cheap and must never hang scope.
PACKS_RESOLVER_TIMEOUT = 30.0


def declared_packs() -> tuple[bool | None, int]:
    """Whether the local config declares Compound Packs, from the config alone.

    Runs the sibling resolver in `--declared-only` mode, which parses the
    `packs:` list from both config layers and shape-checks each entry with no
    git or cache work. Its `declared` is true when any entry parsed or the block
    is malformed -- a broken declaration is still one the learnings pass must
    surface in Coverage. ``None`` means the helper could not tell (resolver
    missing, crashed, timed out, or answered without `declared`); the caller
    then falls closed to reading the config's `packs:` key itself. The second
    value keeps the `pack_roots` output slot and is always 0: nothing resolves
    here.
    """
    if not PACKS_RESOLVER.is_file():
        return None, 0
    try:
        proc = subprocess.run(
            [sys.executable, str(PACKS_RESOLVER), "--declared-only"],
            capture_output=True,
            text=True,
            check=False,
            cwd=repo_root(),
            timeout=PACKS_RESOLVER_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
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
    learnings_corpus = has_learnings_corpus(docs_root) if local_scope else None
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
        "deleted_files": [],
        "deleted_exec_nontest_lines": None,
        "deleted_band": "unknown",
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


def deleted_band_for(deleted_files: list[str], deleted_exec_nontest_lines: int) -> str:
    if not deleted_files:
        return "none"
    if deleted_exec_nontest_lines >= FULL_EXEC_LINE_MIN:
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


DIFF_ENTRY_TEMPLATE = (
    'json({"path" => path, "source" => source.path(), "status" => status, '
    '"old_exec" => source.executable(), "new_exec" => target.executable(), '
    '"old_type" => source.file_type(), "new_type" => target.file_type()}) ++ "\\n"'
)


def exact_diff(base: str, head: str) -> list[tuple[dict, int | None]]:
    """Pair JJ's exact-range path/type metadata with zero-context patch counts.

    Parent-relative log statistics are not range statistics. Git-format hunks
    count real additions/removals and distinguish binary edits from mode-only
    and pure rename entries; native metadata supplies unambiguous paths.
    """
    endpoints = ("--from", base, "--to", head)
    metadata = jj("diff", *endpoints, "-T", DIFF_ENTRY_TEMPLATE)
    patch = jj("diff", *endpoints, "--git", "--context", "0",
               "--config", "diff.git.show-path-prefix=true")
    if metadata.returncode or patch.returncode:
        raise ValueError("JJ range diff failed")
    entries = [json.loads(line) for line in metadata.stdout.split("\n") if line]
    sections = patch.stdout.split("\ndiff --git ")
    if patch.stdout.startswith("diff --git "):
        sections[0] = sections[0].removeprefix("diff --git ")
    elif patch.stdout:
        raise ValueError("unrecognized JJ patch header")
    else:
        sections = []
    if len(entries) != len(sections):
        raise ValueError("JJ metadata and patch inventory differ")
    result = []
    for entry, section in zip(entries, sections):
        header, *lines = section.split("\n")
        if header != f'a/{entry["source"]} b/{entry["path"]}':
            raise ValueError("cannot associate JJ patch section with its path")
        total = 0
        in_hunk = False
        for line in lines:
            if line.startswith("Binary files ") or line == "GIT binary patch":
                total = None
                break
            if line.startswith("@@ "):
                in_hunk = True
            elif in_hunk and line.startswith(("+", "-")):
                total += 1
        if any(entry[key] in ("conflict", "git-submodule", "tree") for key in ("old_type", "new_type")):
            total = None
        result.append((entry, total))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head")
    parser.add_argument("--local-scope", action="store_true",
                        help="inspect local config even when an explicit captured head is supplied")
    parser.add_argument("--docs-root", default="docs")
    args = parser.parse_args()

    # Remote scope (pr-remote / branch-remote) always passes --head, even when a
    # best-effort fetch left it empty; the local config is not that tree's config.
    repo = {"has_learnings_corpus": False, "declared_packs": None, "pack_roots": 0}
    try:
        repo = repo_signals(args.docs_root, local_scope=args.head is None or args.local_scope)
        head = resolve_commit("@" if args.head is None else args.head, snapshot=args.head is None)
        base = resolve_commit(args.base)
        if base is None or head is None:
            raise ValueError(f"invalid {'base' if base is None else 'head'} endpoint")
        entries = exact_diff(base, head)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps(fail_closed(str(exc), repo), sort_keys=True))
        return 0

    files: list[str] = []
    executable_lines = 0
    executable_nontest_lines = 0
    unclassified_lines: dict[str, int] = {}
    changed_lines = 0
    uncounted = 0
    deleted_files: list[str] = []
    deleted_exec_nontest_lines = 0
    for entry, total in entries:
        resolved_name = entry["path"]
        files.append(resolved_name)
        ext = Path(resolved_name).suffix.lower()
        is_exec = ext in CODE_EXTENSIONS or entry["old_exec"] or entry["new_exec"]
        is_test = bool(TEST_PATTERN.search(resolved_name))
        if entry["status"] == "removed":
            deleted_files.append(resolved_name)
        if total is None:
            uncounted += 1
            continue
        changed_lines += total
        if entry["status"] == "removed":
            if is_exec and not is_test:
                deleted_exec_nontest_lines += total
            continue
        if is_exec:
            executable_lines += total
            if not is_test:
                executable_nontest_lines += total
        elif not is_test:
            unclassified_lines[ext] = unclassified_lines.get(ext, 0) + total

    files.sort()
    deleted_files.sort()
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
        "deleted_files": deleted_files,
        "deleted_exec_nontest_lines": deleted_exec_nontest_lines,
        "deleted_band": deleted_band_for(deleted_files, deleted_exec_nontest_lines),
        "test_files_changed": any(TEST_PATTERN.search(file) for file in files),
        "agent_surface": any(AGENT_SURFACE_PATTERN.search(file) for file in files),
        **repo,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
