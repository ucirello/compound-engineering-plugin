---
name: ce-commit
description: Create a JJ commit with a clear, value-communication message. Use when the user asks to commit/save working-copy changes with a repo-appropriate, value-communicating message.
---

# JJ Commit

Create a single, well-crafted JJ commit from the current working-copy changes.

## Context

**On platforms other than Claude Code**, skip to the "Context fallback" section below and run the command there to gather context.

**In Claude Code**, the five labeled sections below (JJ status, Working-copy diff, Bookmarks, Recent commits, Remote default branch) contain pre-populated data. Use them directly throughout this skill -- do not re-run these commands.

**JJ status:**
!`jj status`

**Working-copy diff:**
!`jj diff`

**Bookmarks:**
!`jj bookmark list`

**Recent commits:**
!`jj log -r 'latest(::@, 10)' --no-graph --template 'commit_id.short() ++ " " ++ description.first_line() ++ "\n"'`

**Remote default branch:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BRANCH_UNRESOLVED__'`

### Context fallback

**In Claude Code, skip this section — the data above is already available.**

Run this single command to gather all context:

```bash
printf '=== STATUS ===\n'; jj status; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== BOOKMARKS ===\n'; jj bookmark list; printf '\n=== LOG ===\n'; jj log -r 'latest(::@, 10)' --no-graph --template 'commit_id.short() ++ " " ++ description.first_line() ++ "\n"'; printf '\n=== DEFAULT_BRANCH ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BRANCH_UNRESOLVED__'
```

---

## Workflow

### Step 1: Gather context

Use the context above (JJ status, working-copy diff, bookmarks, recent commits, remote default branch). All data needed for this step is already available -- do not re-run those commands.

The remote default branch value returns a branch name like `main`. If it returned `__DEFAULT_BRANCH_UNRESOLVED__`, try:

```bash
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
```

If both fail, fall back to `main`.

If the JJ status from the context above shows a clean working copy, report that there is nothing to commit and stop.

JJ has no active checked-out branch. If no local bookmark points at `@`, explain that a bookmark is required only if the user wants this work attached to a branch-like name for push/PR workflows. Ask whether to create a feature bookmark now. Use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting options in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) — not because a schema load is required. Never silently skip the question.

- If the user chooses to create a bookmark, derive the name from the change content, create it with `jj bookmark create <bookmark-name>` or `jj bookmark set <bookmark-name>`, then treat that bookmark as the feature bookmark for the rest of the workflow.
- If the user declines, continue with the unbookmarked JJ commit.

### Step 2: Determine commit message convention

Follow this priority order:

1. **Repo conventions already in context** -- If project instructions (AGENTS.md, CLAUDE.md, or similar) are already loaded and specify commit message conventions, follow those. Do not re-read these files; they are loaded at session start.
2. **Recent commit history** -- If no explicit convention is documented, examine the 10 most recent commits from Step 1. If a clear pattern emerges (e.g., conventional commits, ticket prefixes, emoji prefixes), match that pattern.
3. **Default: conventional commits** -- If neither source provides a pattern, use conventional commit format: `type(scope): description` where type is one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `style`, `build`.

When using conventional commits, choose the type that most precisely describes the change (the type list above). Where `fix:` and `feat:` both seem to fit, default to `fix:`: a change that remedies broken or missing behavior is `fix:` even when implemented by adding code. Reserve `feat:` for capabilities the user could not previously accomplish. Other types remain primary when they fit better. The user may override for a specific change.

### Step 3: Consider logical commits

Before committing everything together, scan the changed files for naturally distinct concerns. If modified files clearly group into separate logical changes (e.g., a refactor in one directory and a new feature in another, or test files for a different change than source files), create separate commits for each group.

Keep this lightweight:
- Group at the **file level only** -- do not try to split hunks within a file.
- If the separation is obvious (different features, unrelated fixes), split. If it's ambiguous, one commit is fine.
- Two or three logical commits is the sweet spot. Do not over-slice into many tiny commits.

### Step 4: Commit

If a local bookmark pointing at `@` is `main`, `master`, or the resolved default branch from Step 1, automatically create a feature bookmark before committing. Derive the bookmark name from the change content. If the current change already contains the work, create the feature bookmark on `@` with `jj bookmark create <bookmark-name>` or `jj bookmark set <bookmark-name>` so the diff stays with the commit. If the current change is empty and the work has not started yet, run `jj new <base>` where `<base>` is the default bookmark, then create the feature bookmark. Do not ask whether to create a bookmark — committing directly on the default bookmark is not an option here.

Write the commit message:
- **Subject line**: Concise, imperative mood, focused on *why* not *what*. Follow the convention determined in Step 2.
- **Body** (when needed): Add a body separated by a blank line for non-trivial changes. Explain motivation, trade-offs, or anything a future reader would need. Omit the body for obvious single-purpose changes.

For each commit group, commit specific files in a single call. Prefer naming files over committing the whole working copy to avoid accidentally including sensitive files (.env, credentials) or unrelated changes. Use a heredoc to preserve formatting:

```bash
jj commit file1 file2 file3 -m "$(cat <<'EOF'
type(scope): subject line here

Optional body explaining why this change was made,
not just what changed.
EOF
)"
```

### Step 5: Confirm

Run `jj status` after the commit to verify success. Report the commit hash(es) and subject line(s).
