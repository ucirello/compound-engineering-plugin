#!/usr/bin/env python3
"""Validate cited claims in a solution doc against a Jujutsu workspace.

Usage:
    python3 validate-doc-claims.py <doc-path>

Exit codes:
    0 — nothing flagged
    1 — one or more flags need adjudication (report on stdout)
    2 — usage error (bad arguments, missing file)

Scope: mechanical grounding checks on a written doc's *body*. Complements
validate-frontmatter.py (parser-safety) — this script checks the body's
citations against the repository:

    1. Cited workspace-relative paths (backticked, containing at least one '/')
       exist in the working copy; tokens containing '../' resolve from the
       doc's directory (those escaping the workspace are skipped). Misses in
       the working-copy parent or trunk still count as real paths and are
       classified (removed in the current change vs stale workspace). Tokens
       missing everywhere are flagged only when path-shaped; slash-delimited
       identifiers (bookmark names, revision expressions, provider/model IDs) are skipped.
    2. Cited hexadecimal revision IDs (7-64 characters with at least one
       digit and one a-f letter) resolve to revisions, classified by
       reachability from the working-copy change and trunk.
    3. Relative markdown link targets resolve from the doc's location.
    4. Dangling drafting scaffold: "Learning(s) N" numbering and
       unresolved {{...}} placeholder tokens. Inline code spans and fenced
       code blocks are masked first, so a {{...}} shown as documented syntax
       (Handlebars, a CI variable, a GitHub ruleset placeholder) is not
       mistaken for a leaked scaffold; only a bare token in prose is flagged.

Flags are adjudication input, NOT hard failures — a doc may legitimately
cite a path deleted by the very fix it documents. The calling agent
decides per flag: fix, annotate as historical, or confirm intentional.
Only the summary exit code distinguishes "clean" from "needs a look".

The script never touches the network (no fetch); classification uses
whatever remote bookmarks exist locally. Run a best-effort `jj git fetch` first
when freshness matters. Pure stdlib (no third-party deps).
"""
import os
import re
import subprocess
import sys

# Tokens containing these are placeholders/examples, not real citations.
PLACEHOLDER_CHARS = set("<>{}*$")
PLACEHOLDER_SUBSTRINGS = ("path/to", "...", "…")

REVISION_ID_RE = re.compile(r"\b[0-9a-f]{7,64}\b")
TRUNK_REVSET = "trunk() ~ root()"
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
SCAFFOLD_RES = (
    re.compile(r"\bLearnings?\s+#?\d"),
    re.compile(r"\{\{[^}\n]*\}\}"),
)


def usage_fail(msg: str) -> "NoReturn":
    sys.stderr.write(f"validate-doc-claims: {msg}\n")
    sys.exit(2)


def jj(args: list[str], cwd: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["jj", "--no-pager", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def split_body(text: str) -> tuple[str, int]:
    """Return (body, 1-indexed line number the body starts on).

    Skips YAML frontmatter when present so frontmatter fields are not
    scanned as body citations.
    """
    lines = text.split("\n")
    if lines and lines[0].rstrip() == "---":
        for i in range(1, len(lines)):
            if lines[i].rstrip() == "---":
                return "\n".join(lines[i + 1 :]), i + 2
    return text, 1


def is_path_candidate(token: str) -> bool:
    if any(ch.isspace() for ch in token):
        return False
    if "/" not in token:
        return False
    if "://" in token or token.startswith(("http", "#", "/", "~")):
        return False
    if token.startswith(("origin/", "upstream/", "refs/")):
        return False  # revision names, not workspace paths
    if PLACEHOLDER_CHARS & set(token):
        return False
    if any(sub in token for sub in PLACEHOLDER_SUBSTRINGS):
        return False
    return True


def is_path_shaped(token: str, base: str) -> bool:
    """Distinguish a path citation from a slash-delimited identifier
    (bookmark name, provider/model ID) among tokens found nowhere in the workspace."""
    segments = token.split("/")
    if re.search(r"\.[A-Za-z0-9]{1,8}$", segments[-1]):
        return True
    if token.endswith("/"):
        return True
    return os.path.isdir(os.path.join(base, segments[0]))


def mask_code(lines: list[str]) -> list[str]:
    """Blank out fenced code blocks and inline code spans, preserving line
    count and length. Illustrative {{...}} in quoted code must not read as a
    leaked drafting scaffold; only bare tokens in prose should."""
    masked: list[str] = []
    fence: str | None = None  # active fence run (e.g. "```"), or None
    for line in lines:
        m = FENCE_RE.match(line)
        if fence is None and m:
            fence = m.group(1)
            masked.append(" " * len(line))
            continue
        if fence is not None:
            # CommonMark: a closing fence is the same char, at least as long,
            # and followed only by whitespace — an info string (```json) opens
            # but never closes, so it stays block content.
            if (
                m
                and m.group(1)[0] == fence[0]
                and len(m.group(1)) >= len(fence)
                and not m.group(2).strip()
            ):
                fence = None
            masked.append(" " * len(line))
            continue
        masked.append(BACKTICK_RE.sub(lambda x: " " * len(x.group(0)), line))
    return masked


def normalize_path(token: str) -> str:
    token = token.strip().rstrip(".,;")
    token = re.sub(r":\d+(-\d+)?$", "", token)  # strip `:line` / `:a-b` refs
    if token.startswith("./"):
        token = token[2:]
    return token


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        usage_fail(f"usage: {os.path.basename(argv[0])} <doc-path>")

    doc_path = argv[1]
    if not os.path.isfile(doc_path):
        usage_fail(f"file not found: {doc_path}")

    with open(doc_path) as f:
        text = f.read()

    doc_dir = os.path.dirname(os.path.abspath(doc_path))
    body, body_start = split_body(text)
    body_lines = body.split("\n")

    def loc_suffix(needle: str) -> str:
        for i, line in enumerate(body_lines):
            if needle in line:
                return f" (line {body_start + i})"
        return ""

    infos: list[str] = []
    flags: list[str] = []

    # --- Workspace context ------------------------------------------------
    code, workspace_root = jj(["workspace", "root"], doc_dir)
    in_jj = code == 0 and bool(workspace_root)
    trunk: str | None = None
    if in_jj:
        code, trunk_ids = jj(
            [
                "log",
                "--no-graph",
                "-r",
                TRUNK_REVSET,
                "-T",
                'commit_id ++ "\\n"',
            ],
            workspace_root,
        )
        trunk_matches = [line for line in trunk_ids.splitlines() if line]
        if code == 0 and len(trunk_matches) == 1:
            trunk = TRUNK_REVSET
            code, behind = jj(
                [
                    "log",
                    "--no-graph",
                    "-r",
                    f"@..({trunk})",
                    "-T",
                    'commit_id ++ "\\n"',
                ],
                workspace_root,
            )
            if code == 0:
                behind_count = len(behind.splitlines()) if behind else 0
                if behind_count > 0:
                    infos.append(
                        f"INFO: workspace is {behind_count} revisions behind trunk() — "
                        "verify merge-state claims against remote truth (gh pr view), "
                        "not this workspace"
                    )
        else:
            infos.append(
                "INFO: trunk() does not uniquely resolve to a non-root revision — "
                "path/revision classification "
                "is limited to the working-copy change and its parent"
            )
    else:
        infos.append(
            "INFO: not a Jujutsu workspace — path and revision classification skipped "
            "(scaffold and link checks still apply)"
        )

    def trunk_has_path(path: str) -> bool:
        if not (in_jj and trunk):
            return False
        code, _ = jj(["file", "show", "-r", trunk, path], workspace_root)
        return code == 0

    def parent_has_path(path: str) -> bool:
        if not in_jj:
            return False
        code, _ = jj(["file", "show", "-r", "@-", path], workspace_root)
        return code == 0

    # --- 1. Cited workspace paths -----------------------------------------
    checked_paths = 0
    seen_paths: set[str] = set()
    base = workspace_root if in_jj else os.getcwd()
    for raw in BACKTICK_RE.findall(body):
        token = normalize_path(raw)
        if not is_path_candidate(token):
            continue
        check = token
        if token.startswith("../") or "/../" in token:
            # A `../` citation is doc-relative (matching how markdown links
            # resolve), so map it to a workspace-root path before checking.
            if not in_jj:
                continue
            resolved = os.path.realpath(os.path.join(doc_dir, token))
            check = os.path.relpath(resolved, os.path.realpath(base))
            if check.startswith(".."):
                continue  # escapes the workspace and cannot be checked
        if check in seen_paths:
            continue
        seen_paths.add(check)
        if os.path.exists(os.path.join(base, check)):
            checked_paths += 1
            continue
        tracked_parent = parent_has_path(check)
        tracked_trunk = trunk_has_path(check)
        if not (tracked_parent or tracked_trunk) and not is_path_shaped(
            check, base
        ):
            continue  # bookmark name / provider ID, not a path citation
        checked_paths += 1
        loc = loc_suffix(raw)
        if tracked_parent:
            flags.append(
                f"FLAG path `{token}`{loc} — present in the working-copy parent "
                "but missing now: removed by the current change? Annotate as "
                "historical (e.g. removed by this fix) or restore it."
            )
        elif tracked_trunk:
            flags.append(
                f"FLAG path `{token}`{loc} — not in the working copy but exists at "
                "trunk(): stale workspace? Annotate or verify against trunk."
            )
        else:
            where = (
                "working copy or trunk()" if trunk else "working copy"
            )
            flags.append(
                f"FLAG path `{token}`{loc} — not found in {where}. Fix the "
                "citation, or annotate it as historical (e.g. removed by this fix)."
            )

    # --- 2. Cited revision IDs ---------------------------------------------
    checked_revision_ids = 0
    seen_revision_ids: set[str] = set()
    if in_jj:
        for m in REVISION_ID_RE.finditer(body):
            revision_id = m.group(0)
            if revision_id in seen_revision_ids:
                continue
            if not (
                any(c.isdigit() for c in revision_id)
                and any(c in "abcdef" for c in revision_id)
            ):
                continue  # dates and decimal ids are not revision IDs
            seen_revision_ids.add(revision_id)
            checked_revision_ids += 1
            loc = loc_suffix(revision_id)
            revision = f"commit_id({revision_id})"
            code, resolved = jj(
                ["log", "--no-graph", "-r", revision, "-T", "commit_id"],
                workspace_root,
            )
            if code != 0 or not resolved:
                flags.append(
                    f"FLAG revision {revision_id}{loc} — does not resolve in this "
                    "workspace. Replace it with the PR number or drop it."
                )
                continue
            code, in_working_copy_output = jj(
                ["log", "--no-graph", "-r", f"{revision} & ::@", "-T", "commit_id"],
                workspace_root,
            )
            in_working_copy = code == 0 and bool(in_working_copy_output)
            in_trunk = False
            if trunk:
                code, in_trunk_output = jj(
                    [
                        "log",
                        "--no-graph",
                        "-r",
                        f"{revision} & ::({trunk})",
                        "-T",
                        "commit_id",
                    ],
                    workspace_root,
                )
                in_trunk = code == 0 and bool(in_trunk_output)
            if in_working_copy and (in_trunk or trunk is None):
                continue
            if in_working_copy and not in_trunk:
                flags.append(
                    f"FLAG revision {revision_id}{loc} — reachable from @ but not "
                    "trunk(): local-only revision whose commit ID may be rewritten. "
                    "Prefer citing the PR number."
                )
            elif in_trunk:
                flags.append(
                    f"FLAG revision {revision_id}{loc} — not reachable from @ but "
                    "reachable "
                    "from trunk(): this workspace predates the merge. Add a "
                    "temporal qualifier or verify the claim via gh."
                )
            else:
                flags.append(
                    f"FLAG revision {revision_id}{loc} — exists but unreachable from @"
                    + (" or trunk()" if trunk else "")
                    + ": likely a rewritten-away revision. Prefer citing the PR number."
                )

    # --- 3. Relative markdown links -----------------------------------------
    checked_links = 0
    seen_links: set[str] = set()
    for target in MD_LINK_RE.findall(body):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
            continue  # URL scheme
        if target.startswith("#"):
            continue  # intra-doc anchor
        bare = target.split("#", 1)[0]
        if not bare or bare in seen_links:
            continue
        seen_links.add(bare)
        checked_links += 1
        if not os.path.exists(os.path.normpath(os.path.join(doc_dir, bare))):
            loc = loc_suffix(target)
            flags.append(
                f"FLAG link ({target}){loc} — relative target does not resolve "
                "from the doc's location. Fix the path."
            )

    # --- 4. Dangling drafting scaffold ---------------------------------------
    for i, line_text in enumerate(mask_code(body_lines)):
        for pattern in SCAFFOLD_RES:
            m = pattern.search(line_text)
            if m:
                flags.append(
                    f'FLAG scaffold "{m.group(0)}" (line {body_start + i}) — '
                    "drafting-context reference leaked into the doc. Rewrite it "
                    "as a real path or link."
                )

    # --- Report ---------------------------------------------------------------
    for info in infos:
        print(info)
    for flag in flags:
        print(flag)
    print(
        f"checked {checked_paths} paths, {checked_revision_ids} revision IDs, "
        f"{checked_links} links; {len(flags)} flags"
    )
    if flags:
        return 1
    print(f"OK: {doc_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
