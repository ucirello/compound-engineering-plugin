# Diff Scope Rules

These rules apply to every reviewer. They define what is "your code to review" versus pre-existing context.

## Scope Discovery

Determine the diff to review using this priority order:

1. **User-specified scope.** If the caller passed `BASE:`, `FILES:`, or `DIFF:` markers, use that scope exactly.
2. **Working-copy change.** If `jj diff -r @` is non-empty, include the current working-copy commit.
3. **Bookmark history vs base.** Review `jj diff --from 'fork_point(@ | <base>)' --to @`, where `<base>` is the resolved default remote bookmark.

The scope step in SKILL.md passes the resolved diff. Use only read-only JJ commands for additional inspection.

## Remote scope (`pr-remote` and `bookmark-remote`)

When review context is remote, the working copy is not the reviewed revision. Do not use Read/Grep on workspace paths for changed files.

Instead:

- Prefer `jj file show -r <remote-head-rev> <path>` when `<pr-head-rev>` or `<bookmark-head-rev>` is provided.
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
