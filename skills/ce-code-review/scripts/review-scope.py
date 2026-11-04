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
        ["jj", "--color=never", "--no-pager", *args], cwd=repo_root(),
        capture_output=True, text=True, check=False
    )


def resolve_commit(ref: str | None) -> str | None:
    if not ref:
        return None
    result = jj("log", "--no-graph", "-r", ref, "-T", 'commit_id ++ "\n"')
    lines = result.stdout.splitlines()
    return lines[0] if result.returncode == 0 and len(lines) == 1 else None


def unique_merge_base(base: str, head: str) -> str | None:
    result = jj("log", "--no-graph", "-r", f"heads(::({base}) & ::({head}))", "-T", 'commit_id ++ "\n"')
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
    """Find the absolute enclosing JJ workspace, including from subdirectories."""
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".jj").is_dir():
            return candidate
    raise RuntimeError("not inside a JJ workspace")


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
    """Return the destination path from a `git diff --numstat` rename display name."""
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
    parser.add_argument("--scope-mode", choices=("standalone", "local-aligned", "base", "pr-remote", "branch-remote"))
    parser.add_argument("--docs-root", default="docs")
    args = parser.parse_args()

    # Remote scope (pr-remote / branch-remote) always passes --head, even when a
    # best-effort fetch left it empty; the local config is not that tree's config.
    local_scope = args.scope_mode not in ("pr-remote", "branch-remote") if args.scope_mode else args.head is None
    repo = repo_signals(args.docs_root, local_scope=local_scope)
    repo.update({"base_requested": args.base, "head_requested": args.head if args.head is not None else "@"})

    base_id = resolve_commit(args.base)
    if not base_id:
        print(json.dumps(fail_closed("invalid base endpoint", repo), sort_keys=True))
        return 0
    head_id = resolve_commit(args.head if args.head is not None else "@")
    if not head_id:
        print(json.dumps(fail_closed("invalid head endpoint", repo), sort_keys=True))
        return 0

    diff_args = ["--from", base_id, "--to", head_id]
    patch = jj("diff", "--git", "--context", "0", *diff_args)
    types = jj("diff", "--types", *diff_args)
    if patch.returncode != 0 or types.returncode != 0:
        print(json.dumps(fail_closed("jj diff failed for exact endpoints", repo), sort_keys=True))
        return 0
    if any(line[:2].strip("-F") for line in types.stdout.splitlines()):
        print(json.dumps(fail_closed("conflict, symlink or submodule in exact range", repo), sort_keys=True))
        return 0

    import shlex
    entries = []
    entry = None
    in_hunk = False
    try:
        for line in patch.stdout.splitlines():
            if line.startswith("diff --git "):
                names = shlex.split(line[len("diff --git "):])
                if len(names) != 2:
                    raise ValueError("ambiguous patch path")
                entry = {"name": names[1][2:], "added": 0, "deleted": 0,
                         "mode": "", "removed": False, "binary": False}
                entries.append(entry)
                in_hunk = False
            elif entry is not None:
                if line.startswith("@@ "):
                    in_hunk = True
                elif in_hunk and line.startswith("+"):
                    entry["added"] += 1
                elif in_hunk and line.startswith("-"):
                    entry["deleted"] += 1
                elif not in_hunk:
                    if line.startswith("deleted file mode "):
                        entry["removed"] = True
                        entry["mode"] = line.rsplit(" ", 1)[1]
                    elif line.startswith(("new file mode ", "new mode ", "old mode ")):
                        entry["mode"] = line.rsplit(" ", 1)[1]
                    elif line.startswith("index ") and len(line.split()) == 4:
                        entry["mode"] = line.split()[-1]
                    elif "Binary files " in line or line == "GIT binary patch":
                        entry["binary"] = True
    except ValueError as exc:
        print(json.dumps(fail_closed(str(exc), repo), sort_keys=True))
        return 0
    executable_mode_paths: set[str] = set()
    deleted_paths: set[str] = set()
    for item in entries:
        if item["removed"]:
            deleted_paths.add(item["name"])
        if item["mode"].endswith("755"):
            executable_mode_paths.add(item["name"])

    files: list[str] = []
    executable_lines = 0
    executable_nontest_lines = 0
    unclassified_lines: dict[str, int] = {}
    changed_lines = 0
    uncounted = 0
    deleted_files: list[str] = []
    deleted_exec_nontest_lines = 0
    for item in entries:
        added, deleted = str(item["added"]), str(item["deleted"])
        resolved_name = item["name"]
        files.append(resolved_name)
        ext = Path(resolved_name).suffix.lower()
        is_exec = ext in CODE_EXTENSIONS or resolved_name in executable_mode_paths
        is_test = bool(TEST_PATTERN.search(resolved_name))
        if item["binary"] or item["mode"] in ("120000", "160000"):
            uncounted += 1
            if resolved_name in deleted_paths:
                deleted_files.append(resolved_name)
            continue
        if resolved_name in deleted_paths:
            deleted_files.append(resolved_name)
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

    if len(entries) != len(types.stdout.splitlines()):
        print(json.dumps(fail_closed("patch inventory incomplete for exact endpoints", repo), sort_keys=True))
        return 0
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
        "base_requested": args.base,
        "head_requested": args.head or "@",
        "base_resolved": base_id,
        "head_resolved": head_id,
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
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as exc:
        print(json.dumps(fail_closed(str(exc), {
            "has_learnings_corpus": None, "declared_packs": None, "pack_roots": 0,
        }), sort_keys=True))
