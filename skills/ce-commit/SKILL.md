---
name: ce-commit
description: Create a JJ commit with a clear, value-communicating description. Use when the user asks to commit or save current working-copy changes with a repository-appropriate message.
---

# JJ Commit

Create one or more well-crafted JJ commits from the current working-copy change.

## Context

**On platforms other than Claude Code**, skip to the "Context fallback" section below and run the command there to gather context.

**In Claude Code**, the five labeled sections below (JJ status, Working-copy diff, Nearby bookmarks, Recent commits, Remote default bookmark) contain pre-populated data. Use them directly throughout this skill -- do not re-run these commands.

**JJ status:**
!`jj status`

**Working-copy diff:**
!`jj diff`

**Bookmarks at the working-copy change and its parent:**
!`jj bookmark list -r '@ | @-'`

**Recent commits:**
!`jj log -r '::@-' -n 10 --no-graph`

**Remote default bookmark:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BOOKMARK_UNRESOLVED__'`

### Context fallback

**In Claude Code, skip this section -- the data above is already available.**

Run this single command to gather all context:

```bash
printf '=== STATUS ===\n'; jj status; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== NEARBY BOOKMARKS ===\n'; jj bookmark list -r '@ | @-'; printf '\n=== LOG ===\n'; jj log -r '::@-' -n 10 --no-graph; printf '\n=== DEFAULT BOOKMARK ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo '__DEFAULT_BOOKMARK_UNRESOLVED__'
```

---

## Workflow

### Step 1: Gather context

Use the context above (JJ status, working-copy diff, nearby bookmarks, recent commits, remote default bookmark). All data needed for this step is already available -- do not re-run those commands.

If the remote default bookmark returned `__DEFAULT_BOOKMARK_UNRESOLVED__`, fall back to `main`.

If the JJ status and diff show that the working-copy change is empty, report that there is nothing to commit and stop. An empty change description alone does not make the change empty.

JJ has no detached-HEAD state and does not require a bookmark to commit. Treat a local non-default bookmark at `@` or `@-` as the active feature bookmark. If multiple nearby non-default bookmarks make the intended one ambiguous, ask which bookmark to advance. Use the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension). Fall back to presenting options in chat only when no blocking tool exists in the harness or the call errors (e.g., Codex edit modes) -- not because a schema load is required. Never silently skip the question.

If the only nearby bookmark is the default bookmark, derive a feature-bookmark name from the change content and create it at `@`. If the default bookmark itself points to `@`, first move it back to `@-` so the new work does not advance the default line:

```bash
jj bookmark move <default-bookmark> --to @- --allow-backwards
jj bookmark create <feature-bookmark> -r @
```

If the default bookmark already points to `@-`, only create the feature bookmark. If there is no nearby bookmark, continue without one; that is a normal JJ workflow.

### Step 2: Determine commit message convention

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Derive the syntax at runtime in this priority order:

1. **Repository-local instructions** -- Inspect the repository's active instructions and conventions at runtime, including any scoped instructions governing the changed files.
2. **Repository-preferred history** -- Run the repository-preferred `git log` command at runtime and inspect its recent commit messages. If no invocation is prescribed, inspect at least the 10 most recent messages with `git log`.
3. **Compatible Go guidance** -- Only where the stronger sources do not conflict, keep the summary concise and explain motivation when it is not evident from the change.

Repository-local instructions and the syntax demonstrated by `git log` override the Go guidance. Do not use or prescribe fixed messages, prefixes, types, scopes, subjects, bodies, templates, placeholders, or examples.

### Step 3: Consider logical commits

Before committing everything together, scan the changed files for naturally distinct concerns. If modified files clearly group into separate logical changes (for example, an unrelated refactor and behavior change), create separate commits for each group.

Keep this lightweight:
- Group at the **file level only** -- pass explicit filesets to `jj commit`; do not split hunks interactively.
- If the separation is obvious, split. If it is ambiguous, one commit is fine.
- Two or three logical commits is the sweet spot. Do not over-slice into many tiny commits.

### Step 4: Describe and commit

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

At runtime, repository-local instructions take precedence, followed by the syntax demonstrated by the repository-preferred `git log`; apply compatible Go guidance only where those sources leave room. For each commit description, preserve the semantic facts needed to explain purpose, motivation, trade-offs, and context, but do not turn those facts into a prescribed subject, body, format, template, placeholder, or example.

JJ has no staging area. For each logical group, pass only that group's intended files to `jj commit` so unrelated or sensitive files remain in the new working-copy change. Supply the runtime-composed description without using a fixed command template or message placeholder.

After each commit, if an active feature bookmark was identified or created in Step 1, advance it to the new commit:

```bash
jj bookmark move <feature-bookmark> --to @-
```

### Step 5: Confirm

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Before correcting any description, reapply Step 2's runtime repository-local instruction and repository-preferred `git log` precedence; use Go guidance only when compatible, and do not introduce fixed messages, prefixes, types, scopes, subjects, bodies, templates, placeholders, or examples. Run `jj status` after all commits to verify success. Inspect each newly created commit with `jj log` and confirm that its description follows the runtime-derived convention; if it does not, correct it with `jj describe` before reporting success. Report each change ID, commit ID, and the first line of its description. Do not treat an intentionally retained working-copy change containing unrelated files as a failed commit.
