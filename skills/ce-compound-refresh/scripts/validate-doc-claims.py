#!/usr/bin/env python3
"""Validate cited claims in a solution doc against the JJ tree.

Usage:
    python3 validate-doc-claims.py <doc-path>

Exit codes:
    0 — nothing flagged
    1 — one or more flags need adjudication (report on stdout)
    2 — usage error (bad arguments, missing file)

Scope: mechanical grounding checks on a written doc's *body*. Complements
validate-frontmatter.py (parser-safety) — this script checks the body's
citations against the repository:

    1. Cited repo-relative paths (backticked, containing at least one '/')
       exist in the working copy; tokens containing '../' resolve from the
       doc's directory (those escaping the repo are skipped). Misses tracked
       in @, its parent(s), or trunk() still count as
       real paths and are classified (sparse/stale workspace vs removed in
       the current change vs a line that differs from trunk). Tokens
       missing everywhere are flagged only when path-shaped; slash-delimited
         identifiers (bookmark names, revision selectors, provider/model IDs) are skipped.
    2. Cited commit IDs (7-40 hex chars with at least one digit and one
       a-f letter) resolve to commits, classified by reachability from
         @ and trunk().
    3. Relative markdown link targets resolve from the doc's location.
    4. Dangling drafting scaffold: "Learning(s) N" numbering and
       unresolved {{...}} placeholder tokens.

Flags are adjudication input, NOT hard failures — a doc may legitimately
cite a path deleted by the very fix it documents. The calling agent
decides per flag: fix, annotate as historical, or confirm intentional.
Only the summary exit code distinguishes "clean" from "needs a look".

The script never touches the network (no fetch); classification uses
whatever revision references exist locally. Run a best-effort `jj git fetch --all-remotes` first
when freshness matters. Pure stdlib (no third-party deps).
"""
import os
import re
import subprocess
import sys

# Tokens containing these are placeholders/examples, not real citations.
PLACEHOLDER_CHARS = set("<>{}*$")
PLACEHOLDER_SUBSTRINGS = ("path/to", "...", "…")

COMMIT_ID_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
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
            ["jj", *args],
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
    if token.startswith(("bookmarks/", "remote-bookmarks/")):
        return False  # JJ revision selectors, not repo paths
    if PLACEHOLDER_CHARS & set(token):
        return False
    if any(sub in token for sub in PLACEHOLDER_SUBSTRINGS):
        return False
    return True


def is_path_shaped(token: str, base: str) -> bool:
    """Distinguish a path citation from a slash-delimited identifier
    (bookmark name, provider/model ID) among tokens found nowhere in JJ."""
    segments = token.split("/")
    if re.search(r"\.[A-Za-z0-9]{1,8}$", segments[-1]):
        return True
    if token.endswith("/"):
        return True
    return os.path.isdir(os.path.join(base, segments[0]))


def normalize_path(token: str) -> str:
    token = token.strip().rstrip(".,;")
    token = re.sub(r":\d+(-\d+)?$", "", token)  # strip `:line` / `:a-b` citations
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

    # --- Repo context -----------------------------------------------------
    code, repo_root = jj(["workspace", "root"], doc_dir)
    in_jj = code == 0 and bool(repo_root)
    trunk: str | None = None
    if in_jj:
        code, trunk_id = jj(
            ["log", "-r", "trunk() ~ root()", "--no-graph", "-T", "commit_id"],
            repo_root,
        )
        if code == 0 and trunk_id:
            trunk = "trunk()"
        if trunk:
            code, behind = jj(["log", "-r", f"@..{trunk}", "--count"], repo_root)
            if code == 0 and behind.isdigit() and int(behind) > 0:
                infos.append(
                    f"INFO: workspace is {behind} changes behind {trunk} — "
                    "verify merge-state claims against remote truth (gh pr view), "
                    "not this workspace state"
                )
        else:
            infos.append(
                "INFO: no non-root trunk() revision found — "
                "path/commit classification limited to @"
            )
    else:
        infos.append(
            "INFO: not a JJ workspace — path and commit classification skipped "
            "(scaffold and link checks still apply)"
        )

    def trunk_has_path(path: str) -> bool:
        if not (in_jj and trunk):
            return False
        code, _ = jj(["file", "show", "-r", trunk, path], repo_root)
        return code == 0

    def revision_has_path(revision: str, path: str) -> bool:
        if not in_jj:
            return False
        code, _ = jj(["file", "show", "-r", revision, path], repo_root)
        return code == 0

    parent_ids: list[str] = []
    if in_jj:
        code, output = jj(
            ["log", "-r", "parents(@)", "--no-graph", "-T", 'commit_id ++ "\\n"'],
            repo_root,
        )
        if code == 0:
            parent_ids = output.splitlines()

    # --- 1. Cited repo paths ----------------------------------------------
    checked_paths = 0
    seen_paths: set[str] = set()
    base = repo_root if in_jj else os.getcwd()
    for raw in BACKTICK_RE.findall(body):
        token = normalize_path(raw)
        if not is_path_candidate(token):
            continue
        check = token
        if token.startswith("../") or "/../" in token:
            # A `../` citation is doc-relative (matching how markdown links
            # resolve), so map it to a repo-root path before checking.
            if not in_jj:
                continue
            resolved = os.path.realpath(os.path.join(doc_dir, token))
            check = os.path.relpath(resolved, os.path.realpath(base))
            if check.startswith(".."):
                continue  # escapes the repo — not checkable as a repo path
        if check in seen_paths:
            continue
        seen_paths.add(check)
        if os.path.exists(os.path.join(base, check)):
            checked_paths += 1
            continue
        tracked_current = revision_has_path("@", check)
        tracked_parent = any(revision_has_path(parent, check) for parent in parent_ids)
        tracked_trunk = trunk_has_path(check)
        known_path = tracked_current or tracked_parent or tracked_trunk
        if not known_path and not is_path_shaped(check, base):
            continue  # bookmark name / provider ID, not a path citation
        checked_paths += 1
        loc = loc_suffix(raw)
        if tracked_current:
            flags.append(
                f"FLAG path `{token}`{loc} — present at @ but absent from the "
                "working copy: sparse or stale workspace? Materialize the path "
                "or verify the claim with `jj file show -r @`."
            )
        elif tracked_parent:
            flags.append(
                f"FLAG path `{token}`{loc} — absent at @ but present in a parent: "
                "removed by the current change. Annotate it as historical "
                "(e.g. removed by this fix) or restore it."
            )
        elif tracked_trunk:
            flags.append(
                f"FLAG path `{token}`{loc} — absent at @ but present at "
                f"{trunk}: this line differs from trunk. Annotate or verify "
                "against trunk."
            )
        else:
            where = (
                f"@, its parents, or {trunk}" if trunk else "@ or its parents"
            )
            flags.append(
                f"FLAG path `{token}`{loc} — not found in {where}. Fix the "
                "citation, or annotate it as historical (e.g. removed by this fix)."
            )

    # --- 2. Cited commit IDs ------------------------------------------------
    checked_commit_ids = 0
    seen_commit_ids: set[str] = set()
    if in_jj:
        for m in COMMIT_ID_RE.finditer(body):
            commit_id = m.group(0)
            if commit_id in seen_commit_ids:
                continue
            if not (
                any(c.isdigit() for c in commit_id)
                and any(c in "abcdef" for c in commit_id)
            ):
                continue  # dates and decimal ids are not commit IDs
            seen_commit_ids.add(commit_id)
            checked_commit_ids += 1
            loc = loc_suffix(commit_id)
            commit_revset = f"commit_id({commit_id})"
            code, resolved = jj(
                ["log", "-r", commit_revset, "--no-graph", "-T", "commit_id"],
                repo_root,
            )
            if code != 0 or not resolved:
                flags.append(
                    f"FLAG commit ID {commit_id}{loc} — does not resolve to a commit in this "
                    "repository. Replace with the PR number, or drop it."
                )
                continue
            in_current = (
                jj(
                    [
                        "log",
                        "-r",
                        f"{commit_revset} & ::@",
                        "--no-graph",
                        "-T",
                        "commit_id",
                    ],
                    repo_root,
                )[1]
                != ""
            )
            in_trunk = (
                trunk is not None
                and jj(
                    [
                        "log",
                        "-r",
                        f"{commit_revset} & ::{trunk}",
                        "--no-graph",
                        "-T",
                        "commit_id",
                    ],
                    repo_root,
                )[1]
                != ""
            )
            if in_current and (in_trunk or trunk is None):
                continue
            if in_current and not in_trunk:
                flags.append(
                    f"FLAG commit ID {commit_id}{loc} — reachable from @ but not {trunk}: "
                    "local-only commit ID that may be rewritten on merge "
                    "or revision rewrite. Prefer citing the PR number."
                )
            elif in_trunk:
                flags.append(
                    f"FLAG commit ID {commit_id}{loc} — not reachable from @ but reachable "
                    f"from {trunk}: this working-copy line predates the merge. Add a "
                    "temporal qualifier or verify the claim via gh."
                )
            else:
                flags.append(
                    f"FLAG commit ID {commit_id}{loc} — exists but unreachable from @"
                    + (f" or {trunk}" if trunk else "")
                    + ": likely a rewritten revision. Prefer citing the PR number."
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
    for i, line_text in enumerate(body_lines):
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
        f"checked {checked_paths} paths, {checked_commit_ids} commit IDs, "
        f"{checked_links} links; {len(flags)} flags"
    )
    if flags:
        return 1
    print(f"OK: {doc_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
