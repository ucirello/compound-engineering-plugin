---
name: ce-commit
description: Create a JJ commit with a clear, value-communicating description. Use when the user asks to commit or save current working-copy changes with a repository-appropriate description.
---

# JJ Commit

Create one or more well-crafted JJ commits from the current working-copy changes.

## Context

If the labeled sections below were pre-populated, use them directly throughout this skill and do not re-run their commands. Otherwise, use the "Context fallback" section.

**Workspace root:**
!`jj workspace root`

**Workspace status:**
!`jj status`

**Working-copy diff:**
!`jj diff`

**Current and parent bookmarks:**
!`jj bookmark list -r '@ | @-'`

**Workspaces:**
!`jj workspace list`

**Recent JJ revisions:**
!`jj log -n 10 --no-graph`

**Past commit messages:**
!`git log -n 10 --format=full`

**Remote default bookmark:**
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || printf '__DEFAULT_BOOKMARK_UNRESOLVED__\n'`

### Context fallback

Skip this section when the data above is already available.

Run this single command to gather all context:

```bash
printf '=== WORKSPACE ROOT ===\n'; jj workspace root; printf '\n=== STATUS ===\n'; jj status; printf '\n=== DIFF ===\n'; jj diff; printf '\n=== CURRENT AND PARENT BOOKMARKS ===\n'; jj bookmark list -r '@ | @-'; printf '\n=== WORKSPACES ===\n'; jj workspace list; printf '\n=== JJ REVISIONS ===\n'; jj log -n 10 --no-graph; printf '\n=== PAST COMMIT MESSAGES ===\n'; git log -n 10 --format=full; printf '\n=== DEFAULT BOOKMARK ===\n'; gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || printf '__DEFAULT_BOOKMARK_UNRESOLVED__\n'
```

---

## Workflow

### Step 1: Gather context

Use the context above (workspace root, status, working-copy diff, bookmarks at `@` and `@-`, workspace list, JJ revisions, past commit messages from `git log`, and remote default bookmark). All data needed for this step is already available -- do not re-run those commands.

If the remote default bookmark returned `__DEFAULT_BOOKMARK_UNRESOLVED__`, infer it from tracked remote bookmarks shown by `jj bookmark list --all-remotes`. If that is inconclusive, use `trunk()` only when `trunk() & ~root()` resolves to exactly one commit; otherwise ask the user or report the ambiguity. Never guess `main` or accept `root()` as the default line.

If `jj status` shows no working-copy changes, report that there is nothing to commit and stop. JJ automatically snapshots working-copy changes and has no staging step; do not use or emulate a staging area.

JJ has no active or checked-out bookmark. Treat a unique non-default local bookmark at `@` or `@-` as the working bookmark. If several bookmarks make the intent ambiguous, ask which one should identify the work. If neither revision has a suitable bookmark, explain that JJ supports anonymous changes but a bookmark is needed to identify the work for a later `jj git push`; ask whether to create one now. Use the available blocking question tool, falling back to options in chat only when no blocking tool exists or the call errors. Never silently skip the question.

- If the user chooses to create a bookmark, derive its name from the change content, create it at `@` with `jj bookmark create <bookmark-name> -r @`, then use it as the working bookmark for the rest of the workflow.
- If the user declines, continue with an anonymous JJ change.

Use `jj file annotate <path>` only when line provenance is needed to understand an otherwise unclear change. This skill creates local commits only: do not run `jj git fetch` or `jj git push`.

### Step 2: Compose change descriptions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Determine the syntax at runtime. Local instructions and actual `git log` syntax win; use only compatible Go guidance. Do not choose syntax independently. Each description must accurately communicate the logical change and its value.

### Step 3: Consider logical commits

Scan the changed files for naturally distinct concerns. If modified files clearly group into separate logical changes, create separate commits for each group.

Keep this lightweight:
- Group at the **file level only** -- pass filesets directly to `jj commit`; do not split hunks within a file.
- If the separation is obvious (different features, unrelated fixes), split. If it's ambiguous, one commit is fine.
- Two or three logical commits is the sweet spot. Do not over-slice into many tiny commits.

### Step 4: Commit

If the working-copy change is based directly on the default bookmark and no suitable non-default working bookmark was selected in Step 1, automatically derive and create a feature bookmark at `@` before committing. Do not move the default bookmark. Committing work identified only by the default bookmark is not an option here.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Local instructions and actual `git log` syntax win; use only compatible Go guidance and do not choose syntax independently.

Use the description composed under Step 2 for each logical group. Review each selected fileset against `jj diff` so sensitive or unrelated files are not included. There is no staging step. For a group containing only selected files, pass those filesets to `jj commit -m "$description"`; for a single group containing all working-copy changes, omit the filesets. Supply the composed description without prescribing a repository-independent format or subject/body shape.

After the final commit, move the selected working bookmark to the newest completed commit with `jj bookmark set <bookmark-name> -r @-` when it does not already point there. Never move the default bookmark as part of this workflow.

### Step 5: Confirm

Run `jj status` and inspect the newly created revisions with `jj log` to verify success. Confirm the workspace with `jj workspace root` if command output indicates a workspace mismatch. Report the change ID(s), commit ID(s), and description first line(s).
