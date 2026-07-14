---
name: ce-commit
description: Describe and finalize a JJ change with a clear, value-communicating message. Use when the user asks to describe/finalize/save working-copy changes with a repo-appropriate message.
---

# JJ Describe and Finalize

Create one or more well-described JJ changes from the current working copy.

## Context

**On platforms other than Claude Code**, skip to the "Context fallback" section below and run the command there to gather context.

**In Claude Code**, the five labeled sections below (JJ status, Working-copy diff, Current bookmarks, Recent changes, Remote default branch) contain pre-populated data. Use them directly throughout this skill -- do not re-run these commands.

**JJ status:**
!`jj status`

**Working-copy diff:**
!`jj diff`

**Bookmarks at the current change or its parent:**
!`jj bookmark list -r '@ | @-'`

**Recent changes:**
!`jj log -r 'ancestors(@, 10)' --limit 10`

**Remote default branch:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BRANCH_UNRESOLVED__'`

### Context fallback

**In Claude Code, skip this section — the data above is already available.**

Run this single command to gather all context:

```bash
printf '=== STATUS ===\n'; jj status; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARKS ===\n'; jj bookmark list -r '@ | @-'; printf '\n=== LOG ===\n'; jj log -r 'ancestors(@, 10)' --limit 10; printf '\n=== DEFAULT_BRANCH ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BRANCH_UNRESOLVED__'
```

---

## Workflow

### Step 1: Gather context

Use the context above (JJ status, working-copy diff, current bookmarks, recent changes, remote default branch). All data needed for this step is already available -- do not re-run those commands.

If the remote default branch returned `__DEFAULT_BRANCH_UNRESOLVED__`, try:

```bash
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

If that fails, fall back to `main`.

If the JJ status from the context above shows no working-copy changes, report that there is nothing to describe or finalize and stop.

If neither the current change nor its parent has a bookmark, explain that a bookmark is required only if the user wants this work attached to a name for pushing. Ask whether to create a feature bookmark now. Use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting options in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

- If the user chooses to create a bookmark, derive the name from the change content, create it with `jj bookmark create <bookmark-name> -r @`, then run `jj bookmark list -r @` again and use that result for the rest of the workflow.
- If the user declines, continue with the unbookmarked JJ change.

### Step 2: Determine JJ description convention

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local instructions and the repository's `git log` syntax always win. Apply compatible Go quality guidance: use concise imperative wording focused on intent, with motivation or context for non-trivial changes. Derive any prefix, type, scope, ticket, emoji, subject form, capitalization, punctuation, body structure, or other syntax dynamically from those sources; never impose a fixed template.

### Step 3: Consider logical changes

Before finalizing everything together, scan the changed files for naturally distinct concerns. If modified files clearly group into separate logical changes (e.g., a refactor in one directory and a new feature in another, or test files for a different change than source files), finalize separate changes for each group.

Keep this lightweight:
- Group at the **file level only** -- pass explicit filesets to `jj commit`; do not split hunks within a file.
- If the separation is obvious (different features, unrelated fixes), split. If it's ambiguous, one change is fine.
- Two or three logical changes is the sweet spot. Do not over-slice into many tiny changes.

### Step 4: Describe and finalize

If the current change or its parent carries the resolved default bookmark, automatically create a feature bookmark before finalizing. Derive the name from the change content, create it with `jj bookmark create <bookmark-name> -r @`, run `jj bookmark list -r @` to confirm, and use it for the rest of the workflow. Do not ask whether to create it -- finalizing directly on the default bookmark is not an option here.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local instructions and the repository's `git log` syntax always win. Apply compatible Go quality guidance and the dynamically discovered convention from Step 2. Focus the message on why rather than a file inventory, including non-trivial motivation, trade-offs, or future-reader context in the repository's established form.

For each logical group except the final one, finalize explicit filesets with `jj commit`; this leaves other files in the new working-copy change and avoids including sensitive or unrelated files. For the final group, describe the current change and start a new empty working-copy change:

```bash
jj commit <files> -m "<message composed from the standards above>"
jj describe -m "<message composed from the standards above>" && jj new
```

### Step 5: Confirm

Run `jj status` and `jj log -r 'ancestors(@, 4)' --limit 4` after finalizing the changes to verify success. Report the change ID(s), commit ID(s), and subject line(s).
