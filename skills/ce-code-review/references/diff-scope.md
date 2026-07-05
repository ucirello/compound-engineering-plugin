# Diff Scope Rules

These rules apply to every reviewer. They define what is "your code to review" versus pre-existing context.

## Scope Discovery

Determine the diff to review using this priority order:

1. **User-specified scope.** If the caller passed `BASE:`, `FILES:`, or `DIFF:` markers, use that scope exactly.
2. **Working copy changes.** If there are unstaged or staged changes (`jj diff` is non-empty), review those.
3. **Unpublished changes vs base bookmark.** If the working copy is clean, review `jj diff --from <common-ancestor> --to @`, where `<common-ancestor>` is the latest shared ancestor of `@` and the default bookmark.

The scope step in the SKILL.md handles discovery and passes you the resolved diff. You do not need to run JJ commands yourself unless PR scope mode requires it (below).

## Remote scope (`pr-remote` and `bookmark-remote`)

When the review context includes `<pr-scope-mode>pr-remote</pr-scope-mode>` or `<pr-scope-mode>bookmark-remote</pr-scope-mode>`, the working tree is **not** the reviewed head. Do **not** use Read/Grep on workspace paths for files in the changed-file list — they may not match the branch or PR under review.

Instead:

- Prefer `jj file show -r <remote-head-ref> <path>` when `<pr-head-ref>` or `<bookmark-head-ref>` is provided in context.
- Otherwise rely on diff hunks in the provided `<diff>` only.
- Do not treat local workspace contents as evidence for findings on changed files.

## Finding Classification Tiers

Every finding you report falls into one of three tiers based on its relationship to the diff:

### Primary (directly changed code)

Lines added or modified in the diff. This is your main focus. Report findings against these lines at full confidence.

### Secondary (immediately surrounding code)

Unchanged code within the same function, method, or block as a changed line. If a change introduces a bug that's only visible by reading the surrounding context, report it -- but note that the issue exists in the interaction between new and existing code.

### Pre-existing (unrelated to this diff)

Issues in unchanged code that the diff didn't touch and doesn't interact with. Mark these as `"pre_existing": true` in your output. They're reported separately and don't count toward the review verdict.

**The rule:** If you'd flag the same issue on an identical diff that didn't include the surrounding file, it's pre-existing. If the diff makes the issue *newly relevant* (e.g., a new caller hits an existing buggy function), it's secondary.
