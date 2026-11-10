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
import ast
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


def jj(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["jj", *args], cwd=repo_root(), capture_output=True, text=True, check=False
    )


def resolve_commit(ref: str | None) -> str | None:
    if not ref:
        return None
    result = jj("log", "--no-graph", "-r", ref, "-T", 'commit_id ++ "\\n"')
    candidates = result.stdout.splitlines()
    if result.returncode == 0 and len(candidates) == 1:
        return candidates[0]
    return None


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
    """Discover the absolute workspace root, failing closed outside JJ."""
    result = subprocess.run(["jj", "root"], cwd=Path.cwd().resolve(),
                            capture_output=True, text=True, check=False)
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    raise RuntimeError("JJ workspace root unavailable")


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
# Parse-only mode does no fetch or cache work, so this bound only guards against a
# wedged interpreter; the helper is meant to be cheap and must never hang scope.
PACKS_RESOLVER_TIMEOUT = 30.0


def declared_packs() -> tuple[bool | None, int]:
    """Whether local RocketClaw config declares packs, from the config alone.

    Runs the sibling resolver in `--declared-only` mode, which parses the
    `packs:` list from both RocketClaw config layers and shape-checks each entry with no
    fetch or cache work. Its `declared` is true when any entry parsed or the block
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


def patch_path(value: str) -> str:
    """Decode a C-quoted patch path without losing tabs or non-ASCII bytes."""
    if value.startswith('"'):
        try:
            ascii_literal = "".join(
                char if ord(char) < 128 else "".join(f"\\x{byte:02x}" for byte in char.encode("utf-8"))
                for char in value
            )
            return ast.literal_eval('b' + ascii_literal).decode("utf-8", "surrogateescape")
        except (ValueError, SyntaxError, UnicodeError):
            raise ValueError("unreadable quoted diff path")
    return value


def patch_records(text: str) -> list[dict]:
    """Count exact unified hunks, retaining binary, rename and mode facts.

    Mode-only and pure rename sections count as changed files with zero lines.
    Unknown/conflict output must not look like a small, successfully counted diff.
    """
    records = []
    record = None
    in_hunk = False
    old_left = new_left = 0
    for line in text.split("\n"):
        if line.startswith("diff --git "):
            if old_left or new_left:
                raise ValueError("truncated diff hunk")
            # Header paths are ambiguous when unquoted and contain spaces;
            # +++/--- or rename metadata below resolves those sections.
            header = line[len("diff --git "):]
            match = re.match(r'("(?:[^"\\]|\\.)*"|a/.*?) ("(?:[^"\\]|\\.)*"|b/.*)$', header)
            if not match:
                raise ValueError("unreadable diff header")
            same = re.fullmatch(r"a/(.*) b/\1", header)
            old = "a/" + same[1] if same else patch_path(match[1])
            new = "b/" + same[1] if same else patch_path(match[2])
            record = {"path": new[2:], "old_path": old[2:], "added": 0,
                      "removed": 0, "deleted": False, "binary": False,
                      "executable": False}
            records.append(record)
            in_hunk = False
            continue
        if record is None:
            if line.strip():
                raise ValueError("unrecognized diff output")
            continue
        if record["binary"]:
            continue
        if line.startswith("@@ "):
            if old_left or new_left:
                raise ValueError("truncated diff hunk")
            match = re.match(r"@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@", line)
            if not match:
                raise ValueError("unreadable diff hunk")
            old_left = int(match[1]) if match[1] is not None else 1
            new_left = int(match[2]) if match[2] is not None else 1
            in_hunk = True
        elif in_hunk and (old_left or new_left):
            if line.startswith("+"):
                record["added"] += 1
                new_left -= 1
            elif line.startswith("-"):
                record["removed"] += 1
                old_left -= 1
            elif line.startswith(" "):
                old_left -= 1
                new_left -= 1
            elif not line.startswith("\\ No newline"):
                raise ValueError("unrecognized diff hunk line")
            if old_left < 0 or new_left < 0:
                raise ValueError("invalid diff hunk counts")
        elif line.startswith(("rename to ", "copy to ")):
            record["path"] = patch_path(line.split(" to ", 1)[1])
        elif line.startswith(("rename from ", "copy from ")):
            record["old_path"] = patch_path(line.split(" from ", 1)[1])
        elif line.startswith("+++ "):
            if line[4:] != "/dev/null":
                record["path"] = patch_path(line[4:])[2:]
        elif line.startswith("--- "):
            if line[4:] != "/dev/null":
                record["old_path"] = patch_path(line[4:])[2:]
        elif line.startswith("deleted file mode "):
            record["deleted"] = True
            record["path"] = record["old_path"]
            record["executable"] = line.endswith("755")
        elif line.startswith(("new file mode ", "new mode ", "old mode ")):
            record["executable"] = line.endswith("755")
        elif line.startswith("index "):
            record["executable"] |= line.endswith(" 100755")
        elif line.startswith(("Binary files ", "GIT binary patch")):
            record["binary"] = True
        elif line.startswith(("<<<<<<<", "+++++++", "%%%%%%%")):
            raise ValueError("conflicted diff cannot be counted")
        elif not (not line or line.startswith(("similarity index ", "dissimilarity index ", "\\ No newline"))):
            raise ValueError("unrecognized diff metadata")
    if old_left or new_left:
        raise ValueError("truncated diff hunk")
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head")
    parser.add_argument("--scope-mode", choices=("standalone", "base", "local-aligned", "pr-remote", "branch-remote"))
    parser.add_argument("--docs-root", default="docs")
    args = parser.parse_args()

    # Remote scope (pr-remote / branch-remote) always passes --head, even when a
    # best-effort fetch left it empty; the local config is not that tree's config.
    local_scope = (args.scope_mode in {"standalone", "base", "local-aligned"}
                   if args.scope_mode else args.head is None)
    repo = repo_signals(args.docs_root, local_scope=local_scope)

    base_id = resolve_commit(args.base)
    if base_id is None:
        print(json.dumps(fail_closed("invalid base endpoint", repo), sort_keys=True))
        return 0
    head_id = resolve_commit("@" if args.head is None else args.head)
    if head_id is None:
        print(json.dumps(fail_closed("invalid head endpoint", repo), sort_keys=True))
        return 0

    # Scope resolution already chose the exact base; never widen the range.
    conflicts = jj("log", "--no-graph", "-r", f"{base_id} | {head_id}",
                   "-T", 'if(conflict, "conflict\\n", "")')
    if conflicts.returncode != 0 or conflicts.stdout:
        print(json.dumps(fail_closed("conflicted or unreadable endpoint", repo), sort_keys=True))
        return 0
    patch = jj("diff", "--git", "--from", base_id, "--to", head_id)
    if patch.returncode != 0:
        print(json.dumps(fail_closed("jj diff failed", repo), sort_keys=True))
        return 0
    try:
        records = patch_records(patch.stdout)
    except ValueError as exc:
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
    for record in records:
        added, deleted = record["added"], record["removed"]
        resolved_name = record["path"]
        files.append(resolved_name)
        ext = Path(resolved_name).suffix.lower()
        is_exec = ext in CODE_EXTENSIONS or record["executable"]
        is_test = bool(TEST_PATTERN.search(resolved_name))
        if record["binary"]:
            uncounted += 1
            if record["deleted"]:
                deleted_files.append(resolved_name)
            continue
        if record["deleted"]:
            deleted_files.append(resolved_name)
            changed_lines += deleted
            if is_exec and not is_test:
                deleted_exec_nontest_lines += deleted
            continue
        total = added + deleted
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
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as exc:
        print(json.dumps(fail_closed(str(exc), {"has_learnings_corpus": False,
                         "declared_packs": None, "pack_roots": 0}), sort_keys=True))
