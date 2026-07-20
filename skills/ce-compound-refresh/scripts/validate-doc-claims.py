#!/usr/bin/env python3
"""Validate cited claims in a solution doc against the Jujutsu workspace.

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
       at @ or trunk() still count as real paths and are classified
       (deleted in the working copy vs stale checkout). Tokens
       missing everywhere are flagged only when path-shaped; slash-delimited
       identifiers (bookmark names, revisions, provider/model IDs) are skipped.
    2. Cited commit SHAs (7-40 hex chars with at least one digit and one
       a-f letter) resolve to commits, classified by reachability from
       the working-copy commit and trunk.
    3. Relative markdown link targets resolve from the doc's location.
    4. Dangling drafting scaffold: "Learning(s) N" numbering and
       unresolved {{...}} placeholder tokens.

Flags are adjudication input, NOT hard failures — a doc may legitimately
cite a path deleted by the very fix it documents. The calling agent
decides per flag: fix, annotate as historical, or confirm intentional.
Only the summary exit code distinguishes "clean" from "needs a look".

The script never touches the network (no fetch); classification uses
the local operation store. Run a best-effort `jj git fetch` first
when freshness matters. Pure stdlib (no third-party deps).
"""
import os
import re
import subprocess
import sys

# Tokens containing these are placeholders/examples, not real citations.
PLACEHOLDER_CHARS = set("<>{}*$")
PLACEHOLDER_SUBSTRINGS = ("path/to", "...", "…")

SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
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
    if token.startswith(("origin/", "upstream/", "refs/")):
        return False  # remote bookmarks/revisions, not repo paths
    if PLACEHOLDER_CHARS & set(token):
        return False
    if any(sub in token for sub in PLACEHOLDER_SUBSTRINGS):
        return False
    return True


def is_path_shaped(token: str, base: str) -> bool:
    """Distinguish a path citation from a slash-delimited identifier
    (bookmark name, provider/model ID) among tokens found nowhere in Jujutsu."""
    segments = token.split("/")
    if re.search(r"\.[A-Za-z0-9]{1,8}$", segments[-1]):
        return True
    if token.endswith("/"):
        return True
    return os.path.isdir(os.path.join(base, segments[0]))


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

    # --- Repo context -----------------------------------------------------
    code, repo_root = jj(["workspace", "root"], doc_dir)
    in_jj = code == 0 and bool(repo_root)
    upstream: str | None = None
    if in_jj:
        code, commit_id = jj(
            ["log", "-r", "trunk()", "--no-graph", "-T", "commit_id"], repo_root
        )
        if code == 0 and commit_id:
            upstream = "trunk()"
            code, behind = jj(
                ["log", "-r", "@..trunk()", "--no-graph", "-T", "commit_id ++ '\\n'"],
                repo_root,
            )
            if code == 0 and behind:
                behind_count = len(behind.splitlines())
                infos.append(
                    f"INFO: working copy is behind trunk by {behind_count} changes — "
                    "verify merge-state claims against remote truth (gh pr view), "
                    "not this checkout"
                )
        else:
            infos.append(
                "INFO: trunk() does not resolve — "
                "path/change classification limited to @"
            )
    else:
        infos.append(
            "INFO: not a Jujutsu workspace — path and change classification skipped "
            "(scaffold and link checks still apply)"
        )

    def upstream_has_path(path: str) -> bool:
        if not (in_jj and upstream):
            return False
        code, _ = jj(["file", "show", "-r", upstream, path], repo_root)
        return code == 0

    def current_change_has_path(path: str) -> bool:
        if not in_jj:
            return False
        code, _ = jj(["file", "show", "-r", "@", path], repo_root)
        return code == 0

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
        tracked_current = current_change_has_path(check)
        tracked_upstream = upstream_has_path(check)
        if not (tracked_current or tracked_upstream) and not is_path_shaped(
            check, base
        ):
            continue  # bookmark name / provider ID, not a path citation
        checked_paths += 1
        loc = loc_suffix(raw)
        if tracked_current:
            flags.append(
                f"FLAG path `{token}`{loc} — present at @ but missing from "
                "the working copy: deleted locally? Annotate as "
                "historical (e.g. removed by this fix) or restore it."
            )
        elif tracked_upstream:
            flags.append(
                f"FLAG path `{token}`{loc} — not in the working copy but exists at "
                f"{upstream}: stale checkout? Annotate or verify against upstream."
            )
        else:
            where = f"working copy or {upstream}" if upstream else "working copy"
            flags.append(
                f"FLAG path `{token}`{loc} — not found in {where}. Fix the "
                "citation, or annotate it as historical (e.g. removed by this fix)."
            )

    # --- 2. Cited commit SHAs ----------------------------------------------
    checked_shas = 0
    seen_shas: set[str] = set()
    if in_jj:
        for m in SHA_RE.finditer(body):
            sha = m.group(0)
            if sha in seen_shas:
                continue
            if not (any(c.isdigit() for c in sha) and any(c in "abcdef" for c in sha)):
                continue  # dates and decimal ids are not SHAs
            seen_shas.add(sha)
            checked_shas += 1
            loc = loc_suffix(sha)
            code, _ = jj(["log", "-r", sha, "--no-graph", "-T", "commit_id"], repo_root)
            if code != 0:
                flags.append(
                    f"FLAG sha {sha}{loc} — does not resolve to a commit in this "
                    "repository. Replace with the PR number, or drop it."
                )
                continue
            head_code, head_output = jj(
                ["log", "-r", f"{sha} & ::@", "--no-graph", "-T", "commit_id"],
                repo_root,
            )
            in_head = head_code == 0 and bool(head_output)
            if upstream is not None:
                upstream_code, upstream_output = jj(
                    ["log", "-r", f"{sha} & ::{upstream}", "--no-graph", "-T", "commit_id"],
                    repo_root,
                )
                in_up = upstream_code == 0 and bool(upstream_output)
            else:
                in_up = False
            if in_head and (in_up or upstream is None):
                continue
            if in_head and not in_up:
                flags.append(
                    f"FLAG sha {sha}{loc} — reachable from @ but not {upstream}: "
                    "local-only commit whose SHA may be rewritten on merge "
                    "(rebase/squash). Prefer citing the PR number."
                )
            elif in_up:
                flags.append(
                    f"FLAG sha {sha}{loc} — not reachable from @ but reachable "
                    f"from {upstream}: this checkout predates the merge. Add a "
                    "temporal qualifier or verify the claim via gh."
                )
            else:
                flags.append(
                    f"FLAG sha {sha}{loc} — exists but unreachable from @"
                    + (f" or {upstream}" if upstream else "")
                    + ": likely a rebased-away commit. Prefer citing the PR number."
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
        f"checked {checked_paths} paths, {checked_shas} SHAs, "
        f"{checked_links} links; {len(flags)} flags"
    )
    if flags:
        return 1
    print(f"OK: {doc_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
