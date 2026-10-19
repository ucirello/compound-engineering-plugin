#!/usr/bin/env python3
"""Validate solution-document body citations against a JJ workspace.

Usage: python3 validate-doc-claims.py <doc-path>
Exit 0: clean; 1: flags need adjudication; 2: bad arguments/missing file.
Checks repository paths, cited commit identifiers and their reachability,
relative Markdown links, and prose drafting scaffold. Flags are adjudication
input, not hard failures: fix, annotate as historical, or confirm intentional.
Unresolved hex identifiers without commit context are NOTE, not FLAG.
Never fetches: when freshness matters, run a permitted `jj git fetch` first.
Pure stdlib. JJ reference: https://docs.jj-vcs.dev/latest/cli-reference/ .
"""
import os
import re
import subprocess
import sys

PLACEHOLDER_CHARS = set("<>{}*$")
PLACEHOLDER_SUBSTRINGS = ("path/to", "...", "…")
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
COMMIT_WORDS = frozenset(
    "commit commits committed committing revision revisions rev revs "
    "revert reverts reverted cherry-pick cherry-picked rebase rebased "
    "bisect bisected".split()
)
CITATION_VERBS = frozenset(
    "fixed fix fixes landed lands land introduced introduces introduce "
    "shipped ships ship merged merges merge resolved resolves resolve "
    "reverted reverts broke breaks broken caused causes regressed "
    "added adds removed removes released releases".split()
)
CITATION_PREPS = frozenset(("in", "by", "at", "with"))
REPO_PIN_RE = re.compile(r"(?<![\w./@-])[\w.-]+/[\w.-]+@$")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
SCAFFOLD_RES = (re.compile(r"\bLearnings?\s+#?\d"), re.compile(r"\{\{[^}\n]*\}\}"))


def usage_fail(msg: str) -> "NoReturn":
    sys.stderr.write(f"validate-doc-claims: {msg}\n")
    sys.exit(2)


def run(args: list[str], cwd: str, env=None) -> tuple[int, str]:
    try:
        result = subprocess.run(args, cwd=cwd, env=env, capture_output=True,
                                text=True, timeout=30)
        return result.returncode, result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def jj(args: list[str], workspace_root: str) -> tuple[int, str]:
    return run(["jj", *args], os.path.abspath(workspace_root))


def revisions(revset: str, workspace_root: str) -> tuple[int, str]:
    return jj(["log", "--no-graph", "-r", revset, "-T", 'commit_id ++ "\\n"'],
              workspace_root)


def split_body(text: str) -> tuple[str, int]:
    lines = text.split("\n")
    if lines and lines[0].rstrip() == "---":
        for i in range(1, len(lines)):
            if lines[i].rstrip() == "---":
                return "\n".join(lines[i + 1:]), i + 2
    return text, 1


def is_path_candidate(token: str, *, known_path: bool = False) -> bool:
    if any(ch.isspace() for ch in token):
        return False
    if not known_path and "/" not in token:
        return False
    if "://" in token or token.startswith(("http", "#", "/", "~")):
        return False
    if token.startswith(("origin/", "upstream/", "refs/")):
        return False
    if PLACEHOLDER_CHARS & set(token):
        return False
    return not any(sub in token for sub in PLACEHOLDER_SUBSTRINGS)


def is_path_shaped(token: str, base: str) -> bool:
    segments = token.split("/")
    return bool(re.search(r"\.[A-Za-z0-9]{1,8}$", segments[-1])
                or token.endswith("/")
                or os.path.isdir(os.path.join(base, segments[0])))


def mask_code(lines: list[str]) -> list[str]:
    masked: list[str] = []
    fence: str | None = None
    for line in lines:
        m = FENCE_RE.match(line)
        if fence is None and m:
            fence = m.group(1)
            masked.append(" " * len(line))
            continue
        if fence is not None:
            if (m and m.group(1)[0] == fence[0]
                    and len(m.group(1)) >= len(fence) and not m.group(2).strip()):
                fence = None
            masked.append(" " * len(line))
            continue
        masked.append(BACKTICK_RE.sub(lambda x: " " * len(x.group(0)), line))
    return masked


def cites_a_commit(prefix: str) -> bool:
    if REPO_PIN_RE.search(prefix):
        return True
    unflagged = " ".join(w for w in prefix.split() if not w.startswith("-"))
    words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9-]*", unflagged)[-3:]]
    if any(word in COMMIT_WORDS for word in words):
        return True
    return (len(words) >= 2 and words[-1] in CITATION_PREPS
            and words[-2] in CITATION_VERBS)


def normalize_path(token: str) -> str:
    token = re.sub(r":\d+(-\d+)?$", "", token.strip().rstrip(".,;"))
    return token[2:] if token.startswith("./") else token


def strip_repo_prefix(token: str, base: str) -> str:
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
    notes: list[str] = []
    flags: list[str] = []
    # Discovery starts in the document's absolute directory. Every subsequent
    # JJ invocation runs in the resolved absolute workspace root, not via -R.
    code, repo_root = jj(["workspace", "root"], doc_dir)
    in_jj = code == 0 and bool(repo_root)
    upstream: str | None = None
    if in_jj:
        repo_root = os.path.abspath(repo_root)
        # JJ has no symbolic remote-HEAD query. Read only that Git backend
        # metadata; all revision, tree, and ancestry operations below use JJ.
        code, git_dir = jj(["git", "root"], repo_root)
        if code == 0:
            env = dict(os.environ, GIT_DIR=git_dir)
            code, ref = run(["git", "symbolic-ref", "--quiet",
                             "refs/remotes/origin/HEAD"], repo_root, env)
            if code == 0 and ref.startswith("refs/remotes/origin/"):
                name = ref.removeprefix("refs/remotes/origin/")
                candidate = 'remote_bookmarks(exact:"' + name.replace('"', '\\"') + '", exact:"origin")'
                status, value = revisions(candidate, repo_root)
                if status == 0 and value:
                    upstream = candidate
        if upstream is None:
            for name in ("main", "master"):
                candidate = f'remote_bookmarks(exact:"{name}", exact:"origin")'
                status, value = revisions(candidate, repo_root)
                if status == 0 and value:
                    upstream = candidate
                    break
        if upstream:
            code, behind = revisions(f"@..({upstream})", repo_root)
            if code == 0 and behind:
                infos.append(f"INFO: workspace is {len(behind.splitlines())} commits behind {upstream} — "
                             "verify merge-state claims against remote truth, not this checkout; "
                             "scope gh with GIT_DIR=$(jj git root) from this workspace root")
        else:
            infos.append("INFO: no upstream default bookmark found — path/SHA classification limited to @")
    else:
        infos.append("INFO: not a JJ repository — path and SHA classification skipped "
                     "(scaffold and link checks still apply)")

    # Read complete revision file lists so path matching remains literal and
    # workspace-relative even for names with JJ fileset metacharacters.
    def file_set(revision: str) -> set[str]:
        code, output = jj(["file", "list", "-r", revision], repo_root)
        if code:
            infos.append(f"INFO: could not read files at {revision}; path classification is incomplete")
            return set()
        return set(output.splitlines())

    head_paths = file_set("@") if in_jj else set()
    upstream_paths = file_set(upstream) if in_jj and upstream else set()

    def has_path(paths: set[str], path: str) -> bool:
        return path in paths or any(p.startswith(path.rstrip("/") + "/") for p in paths)

    checked_paths = 0
    seen_paths: set[str] = set()
    base = repo_root if in_jj else os.getcwd()
    for raw in BACKTICK_RE.findall(body):
        token = normalize_path(raw)
        rewritten_abs = False
        if in_jj:
            before = token
            token = strip_repo_prefix(token, base)
            rewritten_abs = token != before
        if not is_path_candidate(token, known_path=rewritten_abs):
            continue
        check = token
        if token.startswith("../") or "/../" in token:
            if not in_jj:
                continue
            resolved = os.path.realpath(os.path.join(doc_dir, token))
            check = os.path.relpath(resolved, os.path.realpath(base))
            if check.startswith(".."):
                continue
        if check in seen_paths:
            continue
        seen_paths.add(check)
        if os.path.exists(os.path.join(base, check)):
            checked_paths += 1
            continue
        tracked_head = has_path(head_paths, check)
        tracked_upstream = has_path(upstream_paths, check)
        if not (tracked_head or tracked_upstream) and not is_path_shaped(check, base):
            continue
        checked_paths += 1
        loc = loc_suffix(raw)
        if tracked_head:
            flags.append(f"FLAG path `{token}`{loc} — tracked at @ but missing from the working tree: "
                         "deleted or uncommitted removal? Annotate as historical (e.g. removed by this fix) or restore it.")
        elif tracked_upstream:
            flags.append(f"FLAG path `{token}`{loc} — not in working tree but exists at {upstream}: "
                         "stale checkout? Annotate or verify against upstream.")
        else:
            where = f"working tree or {upstream}" if upstream else "working tree"
            flags.append(f"FLAG path `{token}`{loc} — not found in {where}. Fix the citation, "
                         "or annotate it as historical (e.g. removed by this fix).")

    checked_shas = 0
    if in_jj:
        seen_shas: dict[str, tuple[int, bool]] = {}
        order: list[str] = []
        for m in SHA_RE.finditer(body):
            sha = m.group(0)
            if not (any(c.isdigit() for c in sha) and any(c in "abcdef" for c in sha)):
                continue
            line_start = body.rfind("\n", 0, m.start()) + 1
            cited = cites_a_commit(body[line_start:m.start()])
            line_no = body_start + body.count("\n", 0, m.start())
            if sha not in seen_shas:
                seen_shas[sha] = (line_no, cited)
                order.append(sha)
            elif cited and not seen_shas[sha][1]:
                seen_shas[sha] = (line_no, True)
        for sha in order:
            line_no, cited = seen_shas[sha]
            # Explicit commit_id avoids interpreting a hex word as a change ID.
            revision = f'commit_id("{sha}")'
            code, resolved = revisions(revision, repo_root)
            loc = f" (line {line_no})"
            if code or not resolved:
                if not cited:
                    notes.append(f"NOTE sha {sha}{loc} — an unresolved hex identifier with no commit reference around it. "
                                 "This script cannot tell a session id or content hash from a commit; verify it if it was meant as one.")
                    continue
                checked_shas += 1
                flags.append(f"FLAG sha {sha}{loc} — does not resolve to a commit in this repository. "
                             "Replace with the PR number, or drop it.")
                continue
            checked_shas += 1
            code, value = revisions(f"({revision}) & ancestors(@)", repo_root)
            in_head = code == 0 and bool(value)
            in_up = False
            if upstream:
                code, value = revisions(f"({revision}) & ancestors({upstream})", repo_root)
                in_up = code == 0 and bool(value)
            if in_head and (in_up or upstream is None):
                continue
            if in_head and not in_up:
                flags.append(f"FLAG sha {sha}{loc} — reachable from @ but not {upstream}: local-only commit "
                             "whose SHA may be rewritten on merge (rebase/squash). Prefer citing the PR number.")
            elif in_up:
                flags.append(f"FLAG sha {sha}{loc} — not reachable from @ but reachable from {upstream}: "
                             "this checkout predates the merge. Add a temporal qualifier or verify the claim via gh "
                             "with GIT_DIR=$(jj git root) from the workspace root.")
            else:
                flags.append(f"FLAG sha {sha}{loc} — exists but unreachable from @"
                             + (f" or {upstream}" if upstream else "")
                             + ": likely a rebased-away commit. Prefer citing the PR number.")

    checked_links = 0
    seen_links: set[str] = set()
    for target in MD_LINK_RE.findall(body):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE) or target.startswith("#"):
            continue
        bare = target.split("#", 1)[0]
        if not bare or bare in seen_links:
            continue
        seen_links.add(bare)
        checked_links += 1
        if not os.path.exists(os.path.normpath(os.path.join(doc_dir, bare))):
            flags.append(f"FLAG link ({target}){loc_suffix(target)} — relative target does not resolve "
                         "from the doc's location. Fix the path.")
    for i, line_text in enumerate(mask_code(body_lines)):
        for pattern in SCAFFOLD_RES:
            m = pattern.search(line_text)
            if m:
                flags.append(f'FLAG scaffold "{m.group(0)}" (line {body_start + i}) — '
                             "drafting-context reference leaked into the doc. Rewrite it as a real path or link.")
    for item in [*infos, *notes, *flags]:
        print(item)
    summary = f"checked {checked_paths} paths, {checked_shas} SHAs, {checked_links} links; {len(flags)} flags"
    if notes:
        summary += f", {len(notes)} notes"
    print(summary)
    if flags:
        return 1
    print(f"OK: {doc_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
