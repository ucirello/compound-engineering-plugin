---
name: ce-commit
description: Create a JJ change with a clear, value-communicating description. Use when the user asks to commit/save current changes with a repo-appropriate, value-communicating message.
---

# JJ Commit

Create a single, well-crafted JJ change from the current working tree changes, then start a new empty change when appropriate.

## Context

**On platforms other than Claude Code**, skip to the "Context fallback" section below and run the command there to gather context.

**In Claude Code**, the five labeled sections below (JJ status, working tree diff, current bookmark/change, recent changes, remote default bookmark) contain pre-populated data. Use them directly throughout this skill -- do not re-run these commands.

**JJ status:**
!`jj status`

**Working tree diff:**
!`jj diff`

**Current bookmark/change:**
!`jj bookmark list --revisions @ 2>/dev/null || jj log -r @ --no-graph --template 'change_id.short()'`

**Recent changes:**
!`jj log -r '::@' --limit 10`

**Remote default bookmark:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BOOKMARK_UNRESOLVED__'`

### Context fallback

**In Claude Code, skip this section — the data above is already available.**

Run this single command to gather all context:

```bash
printf '=== STATUS ===\n'; jj status; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARKS ===\n'; jj bookmark list --revisions @; printf '\n=== LOG ===\n'; jj log -r '::@' --limit 10; printf '\n=== DEFAULT_BOOKMARK ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BOOKMARK_UNRESOLVED__'
```

---

## Workflow

### Step 1: Gather context

Use the context above (JJ status, working tree diff, current bookmark/change, recent changes, remote default bookmark). All data needed for this step is already available -- do not re-run those commands.

If the remote default bookmark value returned `__DEFAULT_BOOKMARK_UNRESOLVED__`, try:

```bash
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

If both fail, fall back to `main`.

If the JJ status from the context above shows a clean working copy, report that there are no changes to describe and stop.

If the current change has no bookmark and the user wants this work named for later push/PR, ask whether to create a bookmark now. Use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting options in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

- If the user chooses to create a bookmark, derive the name from the change content, create it with `jj bookmark create <bookmark-name> -r @`, then use that bookmark for the rest of the workflow.
- If the user declines, continue with the unbookmarked JJ change.

### Step 2: Determine change description convention

Follow this priority order:

1. **Repo conventions already in context** -- If project instructions already loaded specify change-description conventions, follow those. Do not re-read these files; they are loaded at session start.
2. **Recent change history** -- If no explicit convention is documented, examine the 10 most recent changes from Step 1. If a clear pattern emerges (e.g., conventional descriptions, ticket prefixes, emoji prefixes), match that pattern.
3. **Default: conventional descriptions** -- If neither source provides a pattern, use conventional format: `type(scope): description` where type is one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `style`, `build`.

When using conventional descriptions, choose the type that most precisely describes the change. Where `fix:` and `feat:` both seem to fit, default to `fix:`: a change that remedies broken or missing behavior is `fix:` even when implemented by adding code. Reserve `feat:` for capabilities the user could not previously accomplish. Other types remain primary when they fit better. The user may override for a specific change.

### Step 3: Consider logical changes

Before describing everything together, scan the changed files for naturally distinct concerns. If modified files clearly group into separate logical changes (e.g., a refactor in one directory and a new feature in another, or test files for a different change than source files), create separate JJ changes for each group.

Keep this lightweight:
- Group at the **file level only** -- do not attempt hunk-level splitting unless the user explicitly asks.
- If the separation is obvious (different features, unrelated fixes), split with `jj split`. If it's ambiguous, one JJ change is fine.
- Two or three logical changes is the sweet spot. Do not over-slice into many tiny changes.

### Step 4: Describe the change and start a new change

If the current bookmark from the context above is `main`, `master`, or the resolved default bookmark from Step 1, automatically create a feature bookmark before describing the current change. Derive the bookmark name from the change content, create it with `jj bookmark create <bookmark-name> -r @`, and use the new bookmark for the rest of the workflow. Do not ask whether to bookmark — describing work on the default bookmark is not an option here.

Write the change description:
- **Subject line**: Concise, imperative mood, focused on *why* not *what*. Follow the convention determined in Step 2.
- **Body** (when needed): Add a body separated by a blank line for non-trivial changes. Explain motivation, trade-offs, or anything a future reader would need. Omit the body for obvious single-purpose changes.

For a single logical change, describe the current change, then start a new empty change:

```bash
jj describe -m "$(cat <<'EOF'
type(scope): subject line here

Optional body explaining why this change was made,
not just what changed.
EOF
)"
jj new
```

For separate logical changes, use `jj split` at file granularity first, then `jj describe` each resulting change.

### Step 5: Confirm

Run `jj status` after the operation to verify success. Report the change ID(s), commit ID(s), and subject line(s).
