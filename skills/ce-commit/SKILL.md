---
name: ce-commit
description: Create a JJ change with a clear, value-communicating description. Use when the user asks to commit/save working-copy changes with a repo-appropriate, value-communicating message.
---

# JJ Change

Describe the current Jujutsu working-copy change, then advance to a new empty change.

## Context

**On platforms other than Claude Code**, skip to the "Context fallback" section below and run the command there to gather context.

**In Claude Code**, the five labeled sections below (JJ status, Working-copy diff, Current bookmark, Recent changes, Default bookmark) contain pre-populated data. Use them directly throughout this skill -- do not re-run these commands.

**JJ status:**
!`jj st`

**Working-copy diff:**
!`jj diff`

**Current bookmark:**
!`jj log -r @ --no-graph --template 'bookmarks' 2>/dev/null || true`

**Recent changes:**
!`jj log -r 'ancestors(@, 10)' --no-pager`

**Default bookmark:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BOOKMARK_UNRESOLVED__'`

### Context fallback

**In Claude Code, skip this section — the data above is already available.**

Run this single command to gather all context:

```bash
printf '=== STATUS ===\n'; jj st; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARKS ===\n'; jj log -r @ --no-graph --template 'bookmarks'; printf '\n=== LOG ===\n'; jj log -r 'ancestors(@, 10)' --no-pager; printf '\n=== DEFAULT_BOOKMARK ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BOOKMARK_UNRESOLVED__'
```

---

## Workflow

### Step 1: Gather context

Use the context above (JJ status, working-copy diff, current bookmark, recent changes, default bookmark). All data needed for this step is already available -- do not re-run those commands.

The default bookmark value is usually `main`. If it returned `__DEFAULT_BOOKMARK_UNRESOLVED__`, try:

```bash
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

If both fail, fall back to `main`.

If `jj st` from the context above shows no changes, report that there is nothing to describe and stop.

If the current bookmark from the context above is empty and the user wants this work pushed or PR-backed later, ask whether to create a feature bookmark now. Use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting options in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

- If the user chooses to create a bookmark, derive the name from the change content, create it with `jj bookmark set <bookmark-name> -r @`, then use that bookmark for the rest of the workflow.
- If the user declines, continue with an unbookmarked local change.

### Step 2: Determine change-description convention

Follow this priority order:

1. **Repo conventions already in context** -- If project instructions already specify change-description conventions, follow those. Do not re-read these files; they are loaded at session start.
2. **Recent JJ history** -- If no explicit convention is documented, examine the 10 most recent change descriptions from Step 1. If a clear pattern emerges (e.g., conventional changes, ticket prefixes, emoji prefixes), match that pattern.
3. **Default: conventional changes** -- If neither source provides a pattern, use conventional change format for the JJ change description: `type(scope): description` where type is one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `style`, `build`.

When using conventional changes, choose the type that most precisely describes the change (the type list above). Where `fix:` and `feat:` both seem to fit, default to `fix:`: a change that remedies broken or missing behavior is `fix:` even when implemented by adding code. Reserve `feat:` for capabilities the user could not previously accomplish. Other types remain primary when they fit better. The user may override for a specific change.

### Step 3: Consider logical changes

Before describing everything together, scan the changed files for naturally distinct concerns. If modified files clearly group into separate logical changes (e.g., a refactor in one directory and a new feature in another, or test files for a different change than source files), split them into separate JJ changes.

Keep this lightweight:
- Group at the **file level only** -- use `jj split` only when separation is obvious; do not try to split hunks within a file.
- If the separation is obvious (different features, unrelated fixes), split. If it's ambiguous, one change is fine.
- Two or three logical changes is the sweet spot. Do not over-slice into many tiny changes.

### Step 4: Describe and advance

If the current bookmark from the context above is `main`, `master`, or the resolved default bookmark from Step 1, automatically create a feature bookmark before describing the change. Derive the bookmark name from the change content and run `jj bookmark set <bookmark-name> -r @`. Do not ask whether to bookmark — describing work directly on the default bookmark is not an option here.

Write the change description:
- **Subject line**: Concise, imperative mood, focused on *why* not *what*. Follow the convention determined in Step 2.
- **Body** (when needed): Add a body separated by a blank line for non-trivial changes. Explain motivation, trade-offs, or anything a future reader would need. Omit the body for obvious single-purpose changes.

For each change group, ensure the working-copy change contains only that group (`jj split` first if needed), then describe it and advance to a new empty change. Use a heredoc to preserve formatting:

```bash
jj describe -m "$(cat <<'EOF'
type(scope): subject line here

Optional body explaining why this change was made,
not just what changed.
EOF
)" && jj new
```

### Step 5: Confirm

Run `jj st` and `jj log -r 'ancestors(@, 3)'` after describing the change to verify success. Report the change ID(s), change ID(s), and subject line(s).
