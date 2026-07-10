---
name: ce-commit
description: Describe or commit a JJ change with a clear, value-communication message. Use when the user asks to commit/save current working-copy changes with a repo-appropriate, value-communicating message.
---

# JJ Commit

Create a single, well-crafted JJ change description from the current working-copy changes.

## Context

**On platforms other than Claude Code**, skip to the "Context fallback" section below and run the command there to gather context.

**In Claude Code**, the labeled sections below contain pre-populated data. Use them directly throughout this skill -- do not re-run these commands.

**jj status:**
!`jj status`

**Working-copy diff:**
!`jj diff`

**Current bookmarks:**
!`jj bookmark list --revisions @`

**Recent changes:**
!`jj log -r 'ancestors(@, 10)' --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'`

**Remote default bookmark:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`

### Context fallback

**In Claude Code, skip this section -- the data above is already available.**

Run this single command to gather all context:

```bash
printf '=== STATUS ===\n'; jj status; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARKS ===\n'; jj bookmark list --revisions @; printf '\n=== LOG ===\n'; jj log -r 'ancestors(@, 10)' --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'; printf '\n=== DEFAULT_BOOKMARK ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BOOKMARK_UNRESOLVED__'
```

## Workflow

### Step 1: Gather Context

Use the context above (jj status, working-copy diff, current bookmarks, recent changes, remote default bookmark). All data needed for this step is already available -- do not re-run those commands.

If `jj status` shows no changes and `jj diff` is empty, report that there is nothing to describe/commit and stop.

If no bookmark points at `@` and the user expects this work to be pushed or PR'd later, derive a meaningful bookmark name from the change content and set it with `jj bookmark set <bookmark-name> -r @`. Do not create a bookmark for local-only save requests unless the user asks.

If the current bookmark is `main`, `master`, or the resolved default bookmark, create a feature change/bookmark before describing the work: `jj new <default-bookmark>@origin` when available, otherwise `jj new <default-bookmark>`, then `jj bookmark set <derived-name> -r @`. Do not record feature work directly on the default bookmark.

### Step 2: Determine Message Convention

Follow this priority order:

1. **Repo conventions already in context** -- If project instructions already loaded specify commit/change-message conventions, follow those. Do not re-read instruction files.
2. **Recent change history** -- If no explicit convention is documented, examine the 10 most recent descriptions from Step 1. If a clear pattern emerges, match it.
3. **Default: conventional commits** -- If neither source provides a pattern, use `type(scope): description` where type is one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `style`, `build`.

When using conventional commits, choose the type that most precisely describes the change. Where `fix:` and `feat:` both seem to fit, default to `fix:`. Reserve `feat:` for capabilities the user could not previously accomplish. The user may override for a specific change.

### Step 3: Consider Logical Changes

Before describing everything together, scan changed files for naturally distinct concerns. If modified files clearly group into separate logical changes, create separate JJ changes for each group.

Keep this lightweight:

- Group at the **file level only**. Use `jj split <paths>` when a mixed current change must be separated; do not try to split hunks unless the user asks.
- If the separation is obvious, split. If ambiguous, one change is fine.
- Two or three logical changes is the sweet spot. Do not over-slice into many tiny changes.

### Step 4: Describe The Change

Write the message:

- **Subject line**: Concise, imperative mood, focused on *why* not *what*. Follow the convention determined in Step 2.
- **Body** (when needed): Add a body separated by a blank line for non-trivial changes. Explain motivation, trade-offs, or anything a future reader would need. Omit the body for obvious single-purpose changes.

For each logical group, split first if needed, then describe the current JJ change:

```bash
jj split file1 file2 file3
jj describe -m "$(cat <<'EOF'
type(scope): subject line here

Optional body explaining why this change was made,
not just what changed.
EOF
)"
```

If all current paths belong together, skip `jj split` and run only `jj describe -m ...`.

### Step 5: Confirm

Run `jj status` and `jj log -r @ --no-graph` after describing to verify success. Report the change ID/commit ID and subject line(s).
