---
name: ce-commit
description: Create a JJ change with a clear, value-communicating description. Use when the user asks to describe/save current changes as a JJ change with a repo-appropriate, value-communicating change description.
---

# JJ Change

Create a single, well-crafted JJ change from the current working-copy changes.

## Context

**On platforms other than Claude Code**, skip to the "Context fallback" section below and run the command there to gather context.

**In Claude Code**, the five labeled sections below (JJ status, working-copy diff, bookmarks at `@`, recent JJ changes, remote default bookmark) contain pre-populated data. Use them directly throughout this skill -- do not re-run these commands.

**JJ status:**
!`jj st`

**Working-copy diff:**
!`jj diff`

**Bookmarks at `@`:**
!`jj bookmark list --revisions @ --tracked`

**Recent JJ changes:**
!`jj log --limit 10 --no-graph`

**Remote default bookmark:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BOOKMARK_UNRESOLVED__'`

### Context fallback

**In Claude Code, skip this section — the data above is already available.**

Run this single command to gather all context:

```bash
printf '=== STATUS ===\n'; jj st; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARK ===\n'; jj bookmark list --revisions @ --tracked; printf '\n=== LOG ===\n'; jj log --limit 10 --no-graph; printf '\n=== DEFAULT_BOOKMARK ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BOOKMARK_UNRESOLVED__'
```

---

## Workflow

### Step 1: Gather context

Use the context above (JJ status, working-copy diff, bookmarks at `@`, recent JJ changes, remote default bookmark). All data needed for this step is already available -- do not re-run those commands.

The remote default bookmark value should be the default bookmark name, such as `main`. If it returned `__DEFAULT_BOOKMARK_UNRESOLVED__`, try:

```bash
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

If both fail, fall back to `main`.

If the JJ status from the context above shows a clean working copy (no modified, added, deleted, or untracked files), report that there is nothing to save as a JJ change and stop.

If no bookmark points at `@` in the context above, the current JJ change has no bookmark. Explain that a bookmark is required if the user wants this work attached to a named line of work. Ask whether to create a feature bookmark now. Use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting options in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

- If the user chooses to create a bookmark, derive the name from the change content, create it with `jj bookmark create <bookmark-name> -r @`, then run `jj bookmark list --revisions @ --tracked` again and use that result as the bookmark name for the rest of the workflow.
- If the user declines, continue with the unbookmarked JJ change.

### Step 2: Determine change description convention

Follow this priority order:

1. **Repo conventions already in context** -- If project instructions are already loaded and specify JJ change description conventions, follow those. Do not re-read these files; they are loaded at session start.
2. **Recent JJ change history** -- If no explicit convention is documented, examine the 10 most recent JJ changes from Step 1. If a clear pattern emerges (e.g., conventional change descriptions, ticket prefixes, emoji prefixes), match that pattern.
3. **Default: conventional change descriptions** -- If neither source provides a pattern, use conventional format for the first line: `type(scope): description` where type is one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `style`, `build`.

When using conventional change descriptions, choose the type that most precisely describes the change (the type list above). Where `fix:` and `feat:` both seem to fit, default to `fix:`: a change that remedies broken or missing behavior is `fix:` even when implemented by adding code. Reserve `feat:` for capabilities the user could not previously accomplish. Other types remain primary when they fit better. The user may override for a specific change.

### Step 3: Consider logical JJ changes

Before describing everything together, scan the changed files for naturally distinct concerns. If modified files clearly group into separate logical changes (e.g., a refactor in one directory and a new feature in another, or test files for a different change than source files), create separate JJ changes for each group.

Keep this lightweight:
- Group at the **file level only** -- do not try to split hunks within a file.
- If the separation is obvious (different features, unrelated fixes), split. If it's ambiguous, one JJ change is fine.
- Two or three logical JJ changes is the sweet spot. Do not over-slice into many tiny changes.

### Step 4: Describe and split the JJ change

If a bookmark pointing at `@` from the context above is `main`, `master`, or the resolved default bookmark from Step 1, automatically create a feature bookmark before describing the change. Derive the bookmark name from the change content, create it with `jj bookmark create <bookmark-name> -r @`, run `jj bookmark list --revisions @ --tracked` to confirm, and use the new bookmark as the bookmark for the rest of the workflow. Do not ask whether to create a bookmark — saving work directly on the default bookmark is not an option here.

Write the JJ change description:
- **Subject line**: Concise, imperative mood, focused on *why* not *what*. Follow the convention determined in Step 2.
- **Body** (when needed): Add a body separated by a blank line for non-trivial changes. Explain motivation, trade-offs, or anything a future reader would need. Omit the body for obvious single-purpose changes.

For a single logical change, describe the current JJ change directly. Use a heredoc to preserve formatting:

```bash
jj describe -m "$(cat <<'EOF'
type(scope): subject line here

Optional body explaining why this change was made,
not just what changed.
EOF
)"
```

For multiple logical changes, split by file with `jj split file1 file2 file3` for each group, then run `jj describe -r <change-id> -m ...` for each resulting change. Do not include unrelated files, secrets, `.env`, credentials, build artifacts, or generated files unless they are intentionally part of the user-visible change.

### Step 5: Confirm

Run `jj st` after describing the change to verify success. Report the JJ change ID(s) and subject line(s).
