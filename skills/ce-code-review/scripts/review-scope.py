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
# Whole-file deletions never count toward it: they band separately, and that
# band can forbid lite but never forces full.
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


def jj(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["jj", "--color=never", *args], cwd=repo_root(), capture_output=True, text=True, check=False
    )


def resolve_commit(ref: str | None) -> str | None:
    if not ref:
        return None
    result = jj("log", "--no-graph", "-r", ref, "-T", 'commit_id ++ "\\n"')
    ids = result.stdout.splitlines()
    return ids[0] if result.returncode == 0 and len(ids) == 1 else None


def unique_merge_base(base: str, head: str) -> str | None:
    result = jj("log", "--no-graph", "-r", f"heads(::{base} & ::{head})", "-T", 'commit_id ++ "\\n"')
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
    """The repository root, matching how docs_root is resolved everywhere else.

    docs_root is repo-relative (``<repo-root>/<docs_root>``), so the corpus
    check resolves against the absolute JJ workspace root, not an invocation
    subdirectory. Fall back to local cwd only when no workspace is available.
    """
    result = subprocess.run(["jj", "workspace", "root"], cwd=Path.cwd().resolve(), capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return Path.cwd().resolve()


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


def numstat_path(name: str) -> str:
    """Return the destination path from a legacy rename display name."""
    if " => " not in name:
        return name
    if "{" in name and "}" in name:
        prefix, rest = name.split("{", 1)
        old_new, suffix = rest.split("}", 1)
        _, new = old_new.split(" => ", 1)
        # A collapsed segment (`a/{b => }/c`) leaves an empty side, so the
        # rebuilt path would carry `//` and miss every path-class pattern.
        return re.sub(r"/{2,}", "/", f"{prefix}{new}{suffix}")
    _, new = name.split(" => ", 1)
    return new


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head")
    parser.add_argument("--local-scope", action="store_true", help="captured head belongs to this workspace; inspect local config")
    parser.add_argument("--docs-root", default="docs")
    args = parser.parse_args()

    # Remote scope (pr-remote / branch-remote) always passes --head, even when a
    # best-effort fetch left it empty; the local config is not that tree's config.
    repo = repo_signals(args.docs_root, local_scope=args.local_scope or args.head is None)

    base = resolve_commit(args.base)
    head = resolve_commit(args.head if args.head is not None else "@")
    if base is None:
        print(json.dumps(fail_closed("invalid base endpoint", repo), sort_keys=True))
        return 0
    if head is None:
        print(json.dumps(fail_closed("invalid head endpoint", repo), sort_keys=True))
        return 0

    # Callers capture the base (including any merge-base resolution) once.
    # Never replace that exact range with a parent-relative or newly resolved range.
    diff_args = ["--from", base, "--to", head]
    types = jj("diff", "--types", *diff_args)
    if types.returncode != 0 or any("C" in line[:2] or "G" in line[:2] for line in types.stdout.splitlines()):
        print(json.dumps(fail_closed("conflicted, submodule, or unavailable scope", repo), sort_keys=True))
        return 0
    patch = jj("diff", "--git", "--context", "0", *diff_args)
    if patch.returncode != 0:
        print(json.dumps(fail_closed("jj diff failed", repo), sort_keys=True))
        return 0
    entries = []
    entry = None
    in_hunk = False
    executable_mode_paths: set[str] = set()
    deleted_paths: set[str] = set()
    for line in patch.stdout.splitlines():
        if line.startswith("diff --git "):
            in_hunk = False
            if entry is not None:
                entries.append(entry)
            # JJ emits Git-format quoted paths; decode JSON-compatible quoting.
            match = re.match(r'diff --git ("(?:[^"\\]|\\.)*"|a/.*?) ("(?:[^"\\]|\\.)*"|b/.*)$', line)
            if not match:
                print(json.dumps(fail_closed("unparseable diff path", repo), sort_keys=True))
                return 0
            name = match.group(2)
            name = json.loads(name) if name.startswith('"') else name
            entry = ["0", "0", name[2:]]
            continue
        if entry is None:
            continue
        if line.startswith("@@ "):
            in_hunk = True
            continue
        if not in_hunk and line.startswith("rename to "):
            name = line[len("rename to "):]
            entry[2] = json.loads(name) if name.startswith('"') else name
        if not in_hunk and line.startswith("+++ ") and line != "+++ /dev/null":
            name = line[4:]
            name = json.loads(name) if name.startswith('"') else name
            entry[2] = name[2:]
        if line.startswith("deleted file mode "):
            deleted_paths.add(entry[2])
        if line.startswith(("old mode ", "new mode ", "new file mode ", "deleted file mode ")) and line.endswith("755"):
            executable_mode_paths.add(entry[2])
        if line.startswith(("Binary files ", "GIT binary patch")):
            entry[:2] = ["-", "-"]
        elif in_hunk and entry[0] != "-" and line.startswith("+"):
            entry[0] = str(int(entry[0]) + 1)
        elif in_hunk and entry[1] != "-" and line.startswith("-"):
            entry[1] = str(int(entry[1]) + 1)
    if entry is not None:
        entries.append(entry)

    files: list[str] = []
    executable_lines = 0
    executable_nontest_lines = 0
    unclassified_lines: dict[str, int] = {}
    changed_lines = 0
    uncounted = 0
    deleted_files: list[str] = []
    deleted_exec_nontest_lines = 0
    for added, deleted, name in entries:
        resolved_name = name
        files.append(resolved_name)
        ext = Path(resolved_name).suffix.lower()
        is_exec = ext in CODE_EXTENSIONS or resolved_name in executable_mode_paths
        is_test = bool(TEST_PATTERN.search(resolved_name))
        if resolved_name in deleted_paths:
            deleted_files.append(resolved_name)
            if deleted == "-":
                uncounted += 1
            if deleted.isdigit():
                changed_lines += int(deleted)
                if is_exec and not is_test:
                    deleted_exec_nontest_lines += int(deleted)
            continue
        if added == "-" or deleted == "-":
            uncounted += 1
            continue
        try:
            total = int(added) + int(deleted)
        except ValueError:
            uncounted += 1
            continue
        changed_lines += total
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
