#!/usr/bin/env python3
"""Validate cited claims in a solution doc against the JJ tree.

Usage: python3 validate-doc-claims.py <doc-path>
Exit codes: 0 clean, 1 flags requiring adjudication, 2 usage error.

Checks body citations: working-tree/upstream paths, commit IDs and ancestry,
relative links, and dangling drafting scaffold. Unresolved hex identifiers are
NOTE unless context presents them as commits; only FLAG affects the exit code.
Flags require human/agent adjudication, not automatic rewriting. Historical
paths and pre-fix states can be intentional. Frontmatter is checked separately
by validate-frontmatter.py. No network, mutations, or temporary files are used.
Optionally fetch with jj git fetch first when freshness matters.
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
SCAFFOLD_RES = (
    re.compile(r"\bLearnings?\s+#?\d"),
    re.compile(r"\{\{[^}\n]*\}\}"),
)


def usage_fail(msg: str) -> "NoReturn":
    sys.stderr.write(f"validate-doc-claims: {msg}\n")
    sys.exit(2)


def jj(args: list[str], cwd: str) -> tuple[int, str]:
    """Run at the absolute target workspace root, never via repository -R."""
    try:
        result = subprocess.run(
            ["jj", "--ignore-working-copy", *args], cwd=os.path.abspath(cwd), capture_output=True,
            text=True, timeout=30,
        )
        return result.returncode, result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def workspace_root(path: str) -> str | None:
    """Locate workspace metadata before invoking JJ with workspace-root cwd."""
    current = os.path.abspath(path)
    while True:
        if os.path.lexists(os.path.join(current, ".jj")):
            code, root = jj(["workspace", "root"], current)
            return root if code == 0 and root else None
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def revisions(revset: str, root: str) -> tuple[int, str]:
    return jj(["log", "--no-graph", "--revisions", revset,
               "--template", 'commit_id ++ "\n"'], root)


def has_path(revision: str, path: str, root: str) -> bool:
    # Compare literal relative paths; citation text must not become a fileset.
    code, output = jj(["file", "list", "--revision", revision], root)
    if code:
        return False
    path = path.replace(os.sep, "/").rstrip("/")
    return any(item == path or item.startswith(path + "/")
               for item in output.splitlines())


def split_body(text: str) -> tuple[str, int]:
    """Return body and its 1-indexed starting line, skipping frontmatter."""
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
        return False  # Historical ref syntax, not a repo path.
    if PLACEHOLDER_CHARS & set(token):
        return False
    if any(sub in token for sub in PLACEHOLDER_SUBSTRINGS):
        return False
    return True


def is_path_shaped(token: str, base: str) -> bool:
    """Distinguish path citations from branch names and provider/model IDs."""
    segments = token.split("/")
    if re.search(r"\.[A-Za-z0-9]{1,8}$", segments[-1]):
        return True
    if token.endswith("/"):
        return True
    return os.path.isdir(os.path.join(base, segments[0]))


def mask_code(lines: list[str]) -> list[str]:
    """Mask fenced/inline code without changing line counts or lengths."""
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
                    and len(m.group(1)) >= len(fence)
                    and not m.group(2).strip()):
                fence = None
            masked.append(" " * len(line))
            continue
        masked.append(BACKTICK_RE.sub(lambda x: " " * len(x.group(0)), line))
    return masked


def cites_a_commit(prefix: str) -> bool:
    """Classify only nearby commit cues, not arbitrary hex identifiers."""
    if REPO_PIN_RE.search(prefix):
        return True
    unflagged = " ".join(w for w in prefix.split() if not w.startswith("-"))
    words = [w.lower() for w in
             re.findall(r"[A-Za-z][A-Za-z0-9-]*", unflagged)[-3:]]
    if any(word in COMMIT_WORDS for word in words):
        return True
    return (len(words) >= 2 and words[-1] in CITATION_PREPS
            and words[-2] in CITATION_VERBS)


def normalize_path(token: str) -> str:
    token = token.strip().rstrip(".,;")
    token = re.sub(r":\d+(-\d+)?$", "", token)
    if token.startswith("./"):
        token = token[2:]
    return token


def strip_repo_prefix(token: str, base: str) -> str:
    """Normalize in-repository absolute citations, resolving symlinks."""
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
    repo_root = workspace_root(doc_dir)
    in_jj = repo_root is not None
    upstream: str | None = None
    if in_jj:
        # trunk() honors repository-configured default-branch selection. Pin
        # the resulting commit ID so every classification uses the same tree.
        code, ref = revisions("trunk()", repo_root)
        if code == 0 and len(ref.splitlines()) == 1:
            upstream = ref
        if upstream:
            code, behind = revisions(f"ancestors({upstream}) ~ ancestors(@)", repo_root)
            count = len(behind.splitlines())
            if code == 0 and count > 0:
                infos.append(
                    f"INFO: worktree is {count} commits behind {upstream} — "
                    "verify merge-state claims against remote truth (gh pr view), "
                    "not this checkout"
                )
        else:
            infos.append("INFO: no upstream default bookmark found — "
                         "path/SHA classification limited to @")
    else:
        infos.append("INFO: not a JJ repository — path and SHA classification skipped "
                     "(scaffold and link checks still apply)")

    def upstream_has_path(path: str) -> bool:
        return bool(in_jj and upstream and has_path(upstream, path, repo_root))

    def head_has_path(path: str) -> bool:
        return bool(in_jj and has_path("@", path, repo_root))

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
        tracked_head = head_has_path(check)
        tracked_upstream = upstream_has_path(check)
        if not (tracked_head or tracked_upstream) and not is_path_shaped(check, base):
            continue
        checked_paths += 1
        loc = loc_suffix(raw)
        if tracked_head:
            flags.append(
                f"FLAG path `{token}`{loc} — tracked at @ but missing from "
                "the working tree: deleted or uncommitted removal? Annotate as "
                "historical (e.g. removed by this fix) or restore it."
            )
        elif tracked_upstream:
            flags.append(
                f"FLAG path `{token}`{loc} — not in working tree but exists at "
                f"{upstream}: stale checkout? Annotate or verify against upstream."
            )
        else:
            where = f"working tree or {upstream}" if upstream else "working tree"
            flags.append(
                f"FLAG path `{token}`{loc} — not found in {where}. Fix the "
                "citation, or annotate it as historical (e.g. removed by this fix)."
            )

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
            # Explicit commit_id avoids interpreting hex as a JJ change ID.
            code, resolved_ids = revisions(f'commit_id("{sha}")', repo_root)
            ids = resolved_ids.splitlines()
            resolved = code == 0 and len(ids) == 1
            loc = f" (line {line_no})"
            if not resolved:
                if not cited:
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
            commit = ids[0]
            code, found = revisions(f"{commit} & ancestors(@)", repo_root)
            in_head = code == 0 and bool(found)
            in_up = False
            if upstream:
                code, found = revisions(f"{commit} & ancestors({upstream})", repo_root)
                in_up = code == 0 and bool(found)
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

    checked_links = 0
    seen_links: set[str] = set()
    for target in MD_LINK_RE.findall(body):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
            continue
        if target.startswith("#"):
            continue
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
    for i, line_text in enumerate(mask_code(body_lines)):
        for pattern in SCAFFOLD_RES:
            m = pattern.search(line_text)
            if m:
                flags.append(
                    f'FLAG scaffold "{m.group(0)}" (line {body_start + i}) — '
                    "drafting-context reference leaked into the doc. Rewrite it "
                    "as a real path or link."
                )
    for info in infos:
        print(info)
    for note in notes:
        print(note)
    for flag in flags:
        print(flag)
    summary = (f"checked {checked_paths} paths, {checked_shas} SHAs, "
               f"{checked_links} links; {len(flags)} flags")
    if notes:
        summary += f", {len(notes)} notes"
    print(summary)
    if flags:
        return 1
    print(f"OK: {doc_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
