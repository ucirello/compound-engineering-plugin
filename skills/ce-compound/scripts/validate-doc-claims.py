#!/usr/bin/env python3
"""Validate cited claims in a solution doc against the jj workspace.

Checks cited workspace paths, hexadecimal revision IDs, relative links, and
dangling drafting scaffold. Flags require adjudication; they are not automatic
rewrite instructions. The script is pure stdlib and never touches the network.
"""
import os
import re
import subprocess
import sys

PLACEHOLDER_CHARS = set("<>{}*$")
PLACEHOLDER_SUBSTRINGS = ("path/to", "...", "…")
COMMIT_ID_RE = re.compile(r"\b[0-9a-f]{7,64}\b")
CHANGE_ID_RE = re.compile(r"[k-z]{7,64}")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
SCAFFOLD_RES = (
    re.compile(r"\bLearnings?\s+#?\d"),
    re.compile(r"\{\{[^}\n]*\}\}"),
)


def usage_fail(message: str) -> "NoReturn":
    sys.stderr.write(f"validate-doc-claims: {message}\n")
    sys.exit(2)


def jj(args: list[str], cwd: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["jj", *args], cwd=cwd, capture_output=True, text=True, timeout=30
        )
        return result.returncode, result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def split_body(text: str) -> tuple[str, int]:
    lines = text.split("\n")
    if lines and lines[0].rstrip() == "---":
        for index in range(1, len(lines)):
            if lines[index].rstrip() == "---":
                return "\n".join(lines[index + 1 :]), index + 2
    return text, 1


def normalize_path(token: str) -> str:
    token = token.strip().rstrip(".,;")
    token = re.sub(r":\d+(-\d+)?$", "", token)
    return token[2:] if token.startswith("./") else token


def is_path_candidate(token: str) -> bool:
    if any(character.isspace() for character in token) or "/" not in token:
        return False
    if "://" in token or token.startswith(("http", "#", "/", "~")):
        return False
    if PLACEHOLDER_CHARS & set(token):
        return False
    return not any(part in token for part in PLACEHOLDER_SUBSTRINGS)


def is_path_shaped(token: str, base: str) -> bool:
    segments = token.split("/")
    return (
        bool(re.search(r"\.[A-Za-z0-9]{1,8}$", segments[-1]))
        or token.endswith("/")
        or os.path.isdir(os.path.join(base, segments[0]))
    )


def mask_code(lines: list[str]) -> list[str]:
    masked: list[str] = []
    fence: str | None = None
    for line in lines:
        match = FENCE_RE.match(line)
        if fence is None and match:
            fence = match.group(1)
            masked.append(" " * len(line))
            continue
        if fence is not None:
            if (
                match
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
                and not match.group(2).strip()
            ):
                fence = None
            masked.append(" " * len(line))
            continue
        masked.append(BACKTICK_RE.sub(lambda item: " " * len(item.group(0)), line))
    return masked


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        usage_fail(f"usage: {os.path.basename(argv[0])} <doc-path>")
    doc_path = argv[1]
    if not os.path.isfile(doc_path):
        usage_fail(f"file not found: {doc_path}")

    with open(doc_path, encoding="utf-8") as doc_file:
        body, body_start = split_body(doc_file.read())
    body_lines = body.split("\n")

    def location(needle: str) -> str:
        for index, line in enumerate(body_lines):
            if needle in line:
                return f" (line {body_start + index})"
        return ""

    infos: list[str] = []
    flags: list[str] = []
    code, workspace_root = jj(["root"], os.path.dirname(os.path.abspath(doc_path)))
    in_workspace = code == 0 and bool(workspace_root)
    trunk_available = False
    if in_workspace:
        trunk_available = jj(
            ["log", "-r", "trunk()", "--no-graph", "-T", 'change_id ++ "\\n"'],
            workspace_root,
        )[0] == 0
        if not trunk_available:
            infos.append("INFO: trunk() does not resolve; checks are limited to @")
    else:
        infos.append(
            "INFO: not a jj workspace; path and revision checks skipped "
            "(scaffold and link checks still apply)"
        )

    def revision_has_path(revision: str, path: str) -> bool:
        return in_workspace and jj(
            ["file", "show", "-r", revision, path], workspace_root
        )[0] == 0

    def revset_has(revset: str) -> bool:
        code, output = jj(
            ["log", "-r", revset, "--no-graph", "-T", 'change_id ++ "\\n"'],
            workspace_root,
        )
        return code == 0 and bool(output)

    checked_paths = 0
    seen_paths: set[str] = set()
    base = workspace_root if in_workspace else os.getcwd()
    doc_dir = os.path.dirname(os.path.abspath(doc_path))
    for raw in BACKTICK_RE.findall(body):
        token = normalize_path(raw)
        if not is_path_candidate(token):
            continue
        check = token
        if token.startswith("../") or "/../" in token:
            if not in_workspace:
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
        present_at = revision_has_path("@", check)
        present_trunk = trunk_available and revision_has_path("trunk()", check)
        if not (present_at or present_trunk) and not is_path_shaped(check, base):
            continue
        checked_paths += 1
        loc = location(raw)
        if present_at:
            flags.append(
                f"FLAG path `{token}`{loc} — present at @ but missing from the "
                "working copy. Annotate as historical or restore it."
            )
        elif present_trunk:
            flags.append(
                f"FLAG path `{token}`{loc} — absent from the working copy but "
                "present at trunk(). Annotate or verify against remote truth."
            )
        else:
            where = "working copy or trunk()" if trunk_available else "working copy"
            flags.append(
                f"FLAG path `{token}`{loc} — not found in {where}. Fix the "
                "citation or annotate it as historical."
            )

    checked_revisions = 0
    seen_revisions: set[str] = set()
    if in_workspace:
        candidates = [(match.group(0), "commit") for match in COMMIT_ID_RE.finditer(body)]
        candidates.extend(
            (token, "change")
            for token in BACKTICK_RE.findall(body)
            if CHANGE_ID_RE.fullmatch(token)
        )
        for revision, id_kind in candidates:
            if revision in seen_revisions:
                continue
            if id_kind == "commit" and not (any(c.isdigit() for c in revision) and any(c in "abcdef" for c in revision)):
                continue
            seen_revisions.add(revision)
            checked_revisions += 1
            loc = location(revision)
            if not revset_has(revision):
                flags.append(
                    f"FLAG {id_kind} ID {revision}{loc} — does not resolve in this "
                    "workspace. Replace it with the PR number or drop it."
                )
                continue
            in_at = revset_has(f"{revision} & ::@")
            in_trunk = trunk_available and revset_has(f"{revision} & ::trunk()")
            if in_at and not in_trunk:
                flags.append(
                    f"FLAG {id_kind} ID {revision}{loc} — reachable from @ but not trunk(): "
                    + ("the commit ID may be rewritten. Prefer citing the stable change ID or PR number." if id_kind == "commit" else "local-only change. Prefer citing the PR number.")
                )
            elif in_trunk and not in_at:
                flags.append(
                    f"FLAG {id_kind} ID {revision}{loc} — reachable from trunk() but "
                    "not @. Add a temporal qualifier or verify via gh."
                )
            elif not in_at and not in_trunk:
                flags.append(
                    f"FLAG {id_kind} ID {revision}{loc} — resolves but is unreachable "
                    "from @ or trunk(). Prefer citing the PR number."
                )

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
            flags.append(
                f"FLAG link ({target}){location(target)} — relative target does "
                "not resolve from the doc's location. Fix the path."
            )

    for index, line in enumerate(mask_code(body_lines)):
        for pattern in SCAFFOLD_RES:
            match = pattern.search(line)
            if match:
                flags.append(
                    f'FLAG scaffold "{match.group(0)}" (line {body_start + index}) — '
                    "drafting context leaked into the doc. Rewrite it as a real path or link."
                )

    for info in infos:
        print(info)
    for flag in flags:
        print(flag)
    print(
        f"checked {checked_paths} paths, {checked_revisions} revisions, "
        f"{checked_links} links; {len(flags)} flags"
    )
    if flags:
        return 1
    print(f"OK: {doc_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
