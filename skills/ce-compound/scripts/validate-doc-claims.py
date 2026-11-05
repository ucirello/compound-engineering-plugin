#!/usr/bin/env python3
"""Validate cited claims against the JJ working tree and explicit history anchors.

Usage:
    python3 validate-doc-claims.py <doc-path> --history-head <verified-commit-id>
        [--upstream-head <verified-remote-default-id>]

HEAD in reports means the exact committed-history anchor supplied by the
caller, not JJ's snapshotting @. Resolve it from task/repository evidence,
not an unconditional @ or @- rule. Capture and preserve its ID before edits.
Absent anchors leave ancestry coverage unknown; working-tree paths, commit
resolution, links and scaffold are still checked. Missing/ambiguous recorded
remote HEAD metadata remains unknown; no trunk()/root() or named-branch guess
is substituted. The caller adjudicates coverage before claiming completion.

Exit codes:
    0 — nothing flagged
    1 — one or more flags need adjudication (report on stdout)
    2 — usage error (bad arguments, missing file)

Scope: mechanical grounding checks on a written doc's *body*. Complements
validate-frontmatter.py (parser-safety) — this script checks the body's
citations against the repository:

    1. Cited repo-relative paths (backticked, containing at least one '/')
       exist in the working tree, including already-absolute citations that
       fall inside the repo (rewritten to repo-relative before candidacy).
       Tokens containing '../' resolve from the doc's directory (those
       escaping the repo are skipped). Misses tracked at HEAD or the
       upstream default branch still count as real paths and are classified
       (deleted/uncommitted vs stale checkout). Tokens missing everywhere
       are flagged only when path-shaped; slash-delimited identifiers
       (branch names, git refs, provider/model IDs) and slash-prefixed
       URL routes are skipped.
    2. Cited commit SHAs (7-40 hex chars with at least one digit and one
       a-f letter) resolve to commits, classified by reachability from
       HEAD and the upstream default branch. Session ids, content hashes
       and blob hashes are hex too, so an unresolvable hex word is
       reported in one of two tiers rather than asserted to be fabricated:
       FLAG when the text right before it presents it as a commit (a
       likely fabricated citation), NOTE otherwise (an identifier this
       script cannot classify). Only FLAG affects the exit code. The
       cue vocabulary therefore ranks confidence; it does not decide
       whether an item is surfaced, so a phrasing it misses is reported
       one tier down instead of disappearing.
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
whatever refs exist locally. Run a best-effort `jj git fetch` first
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
# Words that name a commit or a commit operation, so a hex token right after
# one is a commit citation. Words naming some other git object ("blob", "tree"),
# any hash ("sha"), and the bare tool name ("git", which precedes every object
# kind equally) are deliberately absent — they are what the flag used to mistake
# for commits.
COMMIT_WORDS = frozenset(
    "commit commits committed committing revision revisions rev revs "
    "revert reverts reverted cherry-pick cherry-picked rebase rebased "
    "bisect bisected".split()
)
# A hex token is also a citation when the sentence attributes a change landing
# in this repository to it: "landed in <sha>", "resolved by <sha>". Both halves
# are needed. The preposition alone attributes without saying what to, so it
# would read "recorded at <digest>" as a commit; the verb alone does not point
# at the token. Membership below is that condition, not a tally of phrasings
# seen so far: a verb belongs when it says a change landed, and does not when
# it says an identifier was assigned or a value stored.
CITATION_VERBS = frozenset(
    "fixed fix fixes landed lands land introduced introduces introduce "
    "shipped ships ship merged merges merge resolved resolves resolve "
    "reverted reverts broke breaks broken caused causes regressed "
    "added adds removed removes released releases".split()
)
CITATION_PREPS = frozenset(("in", "by", "at", "with"))
# The pin form that names a commit is owner/repo@<sha>. A bare "@" is not it:
# it also prefixes account names and image tags, whose identifiers are hex too.
REPO_PIN_RE = re.compile(r"(?<![\w./@-])[\w.-]+/[\w.-]+@$")
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


def git(args: list[str], cwd: str, history_head: str | None = None) -> tuple[int, str]:
    """Translate internal history queries to native JJ; never execute Git."""
    nonempty = False
    if args == ["rev-parse", "--show-toplevel"]:
        args = ["workspace", "root"]
    elif args == ["rev-parse", "--abbrev-ref", "origin/HEAD"]:
        default = remote_default(cwd)
        return (0, default) if default else (1, "")
    elif args[:3] == ["rev-parse", "--verify", "--quiet"]:
        return 1, ""
    elif args[:2] == ["rev-list", "--count"]:
        if not history_head:
            return 1, ""
        args = ["log", "--no-graph", "-r", args[2].replace("HEAD", history_head), "-T", 'commit_id ++ "\\n"']
        nonempty = "count"
    elif args[:2] == ["cat-file", "-e"]:
        value = args[2]
        if value.endswith("^{commit}"):
            args = ["log", "--no-graph", "-r", value[:-9], "-T", "commit_id"]
        else:
            rev, path = value.split(":", 1)
            if rev == "HEAD":
                if not history_head:
                    return 1, ""
                rev = history_head
            args = ["file", "list", "-r", rev, "--", path]
        nonempty = True
    elif args[:2] == ["merge-base", "--is-ancestor"]:
        head = history_head if args[3] == "HEAD" else args[3]
        if not head:
            return 1, ""
        args = ["log", "--no-graph", "-r", f"{args[2]} & ::{head}", "-T", "commit_id"]
        nonempty = True
    else:
        return 1, ""
    try:
        result = subprocess.run(
            ["jj", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        if nonempty == "count" and result.returncode == 0:
            output = str(len(output.splitlines())) if output else "0"
        return (1 if nonempty is True and not output else result.returncode), output
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def jj(args: list[str], cwd: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(["jj", "--no-pager", *args], cwd=cwd,
                              capture_output=True, text=True, timeout=30)
        return proc.returncode, proc.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def verified_revision(revision: str | None, cwd: str) -> str | None:
    """Capture exactly one real commit; root() is not a history/remote anchor."""
    if not revision:
        return None
    code, output = jj(["log", "--no-graph", "-r", revision, "-T", 'commit_id ++ "\\n"'], cwd)
    ids = output.splitlines()
    if code == 0 and len(ids) == 1 and re.fullmatch(r"[0-9a-f]{40,64}", ids[0]) and set(ids[0]) != {"0"}:
        return ids[0]
    return None


def remote_default(cwd: str) -> str | None:
    """Use a recorded remote HEAD, never trunk()'s synthetic root fallback.

    Local Git-format symbolic-ref data is read as data, without executing Git.
    Missing or ambiguous remote-default metadata remains unknown. A caller can
    instead supply --upstream-head after verifying the remote default via gh.
    """
    code, remotes = jj(["git", "remote", "list"], cwd)
    root_code, git_root = jj(["git", "root"], cwd)
    if code or root_code:
        return None
    candidates = set()
    for line in remotes.splitlines():
        parts = line.split()
        if not parts:
            continue
        remote = parts[0]
        prefix = f"refs/remotes/{remote}/"
        try:
            with open(os.path.join(git_root, prefix, "HEAD")) as stream:
                target = stream.read().strip()
        except OSError:
            continue
        if not target.startswith("ref: " + prefix):
            continue
        branch = target[len("ref: " + prefix):]
        if not branch or branch == "HEAD":
            continue
        # Quote each ref component to prevent revset expression injection.
        import json
        revision = json.dumps(branch) + "@" + json.dumps(remote)
        resolved = verified_revision(revision, cwd)
        if resolved:
            candidates.add(resolved)
    return next(iter(candidates)) if len(candidates) == 1 else None


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


def is_path_candidate(token: str, *, known_path: bool = False) -> bool:
    if any(ch.isspace() for ch in token):
        return False
    if not known_path and "/" not in token:
        return False
    if "://" in token or token.startswith(("http", "#", "/", "~")):
        return False
    if token.startswith(("origin/", "upstream/", "refs/")):
        return False  # git refs, not repo paths
    if PLACEHOLDER_CHARS & set(token):
        return False
    if any(sub in token for sub in PLACEHOLDER_SUBSTRINGS):
        return False
    return True


def is_path_shaped(token: str, base: str) -> bool:
    """Distinguish a path citation from a slash-delimited identifier
    (branch name, provider/model ID) among tokens found nowhere in git."""
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


def cites_a_commit(prefix: str) -> bool:
    """True when the text just before a hex word presents it as a commit.

    Only the last few words on the same line count: a cue further away
    ("the git history shows session 7e6861b4") describes the surroundings,
    not the token. Digits are word characters so a hash named after its
    algorithm ("SHA256") stays one non-cue word, and command flags drop out
    first so `git show --format=%H <sha>` reads like `git show <sha>`.
    """
    if REPO_PIN_RE.search(prefix):
        return True  # owner/repo@<sha> pins a commit
    unflagged = " ".join(w for w in prefix.split() if not w.startswith("-"))
    words = [
        w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9-]*", unflagged)[-3:]
    ]
    if any(word in COMMIT_WORDS for word in words):
        return True
    return (
        len(words) >= 2
        and words[-1] in CITATION_PREPS
        and words[-2] in CITATION_VERBS
    )


def normalize_path(token: str) -> str:
    token = token.strip().rstrip(".,;")
    token = re.sub(r":\d+(-\d+)?$", "", token)  # strip `:line` / `:a-b` refs
    if token.startswith("./"):
        token = token[2:]
    return token


def strip_repo_prefix(token: str, base: str) -> str:
    """Rewrite an already-absolute path inside the repo to repo-relative.

    Relative tokens, URL routes, and out-of-repo absolute paths are
    unchanged so the existing candidacy guard still drops them. Realpath
    both sides so a host where /tmp is a symlink still matches. A
    successful rewrite is slash-normalized so Windows relpath output
    stays a candidate.
    """
    if not os.path.isabs(token):
        return token
    try:
        rel = os.path.relpath(os.path.realpath(token), os.path.realpath(base))
    except ValueError:
        return token
    if rel == ".." or rel.startswith(".." + os.sep):
        return token
    return rel.replace("\\", "/")


def main(argv: list[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("doc_path")
    parser.add_argument("--history-head", help="exact task/repository committed-history anchor, captured before working-copy edits")
    parser.add_argument("--upstream-head", help="verified actual remote-default head; omit when unknown")
    options = parser.parse_args(argv[1:])
    doc_path = options.doc_path
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
    notes: list[str] = []
    flags: list[str] = []

    # --- Repo context -----------------------------------------------------
    code, repo_root = git(["rev-parse", "--show-toplevel"], doc_dir)
    in_git = code == 0 and bool(repo_root)
    upstream: str | None = None
    history_head: str | None = None
    if in_git:
        history_head = verified_revision(options.history_head, repo_root)
        if options.history_head and not history_head:
            usage_fail("--history-head must resolve to exactly one non-root commit")
        if not history_head:
            infos.append("INFO: committed-history anchor unknown — working-tree/path/link/scaffold and SHA resolution checks still run; historical deletion and ancestry classification require --history-head")
        upstream = verified_revision(options.upstream_head, repo_root) if options.upstream_head else remote_default(repo_root)
        if options.upstream_head and not upstream:
            usage_fail("--upstream-head must resolve to exactly one non-root verified remote-default commit")
        if upstream and history_head:
            code, behind = git(
                ["rev-list", "--count", f"HEAD..{upstream}"], repo_root, history_head
            )
            if code == 0 and behind.isdigit() and int(behind) > 0:
                infos.append(
                    f"INFO: worktree is {behind} commits behind {upstream} — "
                    "verify merge-state claims against remote truth (gh pr view), "
                    "not this checkout"
                )
        if not upstream:
            infos.append(
                "INFO: upstream default unknown — no verified remote-default head; "
                "do not infer local-only or merged status from missing remote coverage"
            )
    else:
        infos.append(
            "INFO: not a git repository — path and SHA classification skipped "
            "(scaffold and link checks still apply)"
        )

    def upstream_has_path(path: str) -> bool:
        if not (in_git and upstream):
            return False
        code, _ = git(["cat-file", "-e", f"{upstream}:{path}"], repo_root)
        return code == 0

    def head_has_path(path: str) -> bool:
        if not in_git:
            return False
        code, _ = git(["cat-file", "-e", f"HEAD:{path}"], repo_root, history_head)
        return code == 0

    # --- 1. Cited repo paths ----------------------------------------------
    checked_paths = 0
    seen_paths: set[str] = set()
    base = repo_root if in_git else os.getcwd()
    for raw in BACKTICK_RE.findall(body):
        token = normalize_path(raw)
        rewritten_abs = False
        if in_git:
            before = token
            token = strip_repo_prefix(token, base)
            rewritten_abs = token != before
        if not is_path_candidate(token, known_path=rewritten_abs):
            continue
        check = token
        if token.startswith("../") or "/../" in token:
            # A `../` citation is doc-relative (matching how markdown links
            # resolve), so map it to a repo-root path before checking.
            if not in_git:
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
        tracked_head = head_has_path(check)
        tracked_upstream = upstream_has_path(check)
        if not (tracked_head or tracked_upstream) and not is_path_shaped(
            check, base
        ):
            continue  # branch name / provider ID, not a path citation
        checked_paths += 1
        loc = loc_suffix(raw)
        if tracked_head:
            flags.append(
                f"FLAG path `{token}`{loc} — tracked at HEAD but missing from "
                "the working tree: deleted or uncommitted removal? Annotate as "
                "historical (e.g. removed by this fix) or restore it."
            )
        elif tracked_upstream:
            flags.append(
                f"FLAG path `{token}`{loc} — not in working tree but exists at "
                f"{upstream}: stale checkout? Annotate or verify against upstream."
            )
        else:
            flags.append(
                f"FLAG path `{token}`{loc} — not found under {base}"
                + (f" or {upstream}" if upstream else "")
                + ". Only that location was searched; check other repos or "
                "stores before treating the citation as wrong. Fix the "
                "citation, or annotate it as historical (e.g. removed by "
                "this fix)."
            )

    # --- 2. Cited commit SHAs ----------------------------------------------
    checked_shas = 0
    if in_git:
        # One entry per distinct hex word: the line to report it at, and
        # whether any occurrence of it is presented as a commit. A doc often
        # quotes a token in a transcript before citing it, so a later citing
        # occurrence upgrades the tier and supplies the line.
        seen_shas: dict[str, tuple[int, bool]] = {}
        order: list[str] = []
        for m in SHA_RE.finditer(body):
            sha = m.group(0)
            if not (any(c.isdigit() for c in sha) and any(c in "abcdef" for c in sha)):
                continue  # dates and decimal ids are not SHAs
            line_start = body.rfind("\n", 0, m.start()) + 1
            cited = cites_a_commit(body[line_start : m.start()])
            line_no = body_start + body.count("\n", 0, m.start())
            if sha not in seen_shas:
                seen_shas[sha] = (line_no, cited)
                order.append(sha)
            elif cited and not seen_shas[sha][1]:
                seen_shas[sha] = (line_no, True)
        for sha in order:
            line_no, cited = seen_shas[sha]
            code, _ = git(["cat-file", "-e", f"{sha}^{{commit}}"], repo_root)
            resolved = code == 0
            loc = f" (line {line_no})"
            if not resolved:
                if not cited:
                    # Nothing here says "commit", and hex is also how session
                    # ids and content hashes are written. Surface it without
                    # claiming to know which it is; the reader adjudicates.
                    notes.append(
                        f"NOTE sha {sha}{loc} — an unresolved hex identifier "
                        "with no commit reference around it. This script cannot "
                        "tell a session id or content hash from a commit; verify "
                        "it if it was meant as one."
                    )
                    continue
                checked_shas += 1
                flags.append(
                    f"FLAG sha {sha}{loc} — does not resolve to a commit in this "
                    "repository. Replace with the PR number, or drop it."
                )
                continue
            checked_shas += 1
            if not history_head:
                notes.append(f"NOTE sha {sha}{loc} — resolves, but committed-history anchor unknown; ancestry classification requires --history-head")
                continue
            head_code, head_match = jj(["log", "--no-graph", "-r", f"{sha} & ::{history_head}", "-T", "commit_id"], repo_root)
            up_code, up_match = jj(["log", "--no-graph", "-r", f"{sha} & ::{upstream}", "-T", "commit_id"], repo_root) if upstream else (0, "")
            if head_code or up_code:
                notes.append(f"NOTE sha {sha}{loc} — ancestry query failed; verification degraded, not evidence of local-only or unreachable status")
                continue
            in_head, in_up = bool(head_match), bool(up_match)
            if upstream is None and not in_head:
                notes.append(f"NOTE sha {sha}{loc} — not reachable from the captured history head; upstream default unknown, so remote reachability and rebased-away status are unverified")
                continue
            if in_head and (in_up or upstream is None):
                continue
            if in_head and not in_up:
                flags.append(
                    f"FLAG sha {sha}{loc} — reachable from HEAD but not {upstream}: "
                    "local-only commit whose SHA may be rewritten on merge "
                    "(rebase/squash). Prefer citing the PR number."
                )
            elif in_up:
                flags.append(
                    f"FLAG sha {sha}{loc} — not reachable from HEAD but reachable "
                    f"from {upstream}: this checkout predates the merge. Add a "
                    "temporal qualifier or verify the claim via gh."
                )
            else:
                flags.append(
                    f"FLAG sha {sha}{loc} — exists but unreachable from HEAD"
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
    for note in notes:
        print(note)
    for flag in flags:
        print(flag)
    summary = (
        f"checked {checked_paths} paths, {checked_shas} SHAs, "
        f"{checked_links} links; {len(flags)} flags"
    )
    if notes:
        summary += f", {len(notes)} notes"
    print(summary)
    if flags:
        return 1
    print(f"OK: {doc_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
