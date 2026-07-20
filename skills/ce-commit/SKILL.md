---
name: ce-commit
description: Create one or more coherent JJ commits from the working-copy change with repository-appropriate descriptions. Use when the user asks to commit or save current working-copy changes.
---

# JJ Commit

Create one or more coherent commits from the current JJ working-copy change.

## Context

Gather current context with JJ:

```text
jj workspace root
jj workspace list
jj status
jj diff
jj log -r 'ancestors(@, 10)'
jj bookmark list --all-remotes
```

`@` is the working-copy change. Changes are identified by stable change IDs; commit IDs may change when a change is rewritten. Bookmarks are named pointers used for sharing changes, not a prerequisite for committing. Do not treat the detached state of a colocated Git checkout as an error.

If scratch storage is needed, use `$(jj workspace root)/.tmp/rocketclaw`. If the current directory is outside a JJ workspace, use the current directory's `.tmp/rocketclaw` instead. Never use OS-global temporary storage.

## Workflow

### Step 1: Gather context

Use `jj status` to identify the working-copy change, conflicts, and changed paths; use `jj diff` to understand the content. Use `jj log` to understand the surrounding changes and established description syntax. Use `jj workspace list` to confirm which workspace is active and avoid operating on another workspace's working-copy change.

If `jj status` reports that the working copy has no changes, report that there is nothing to commit and stop. If it reports conflicts, do not commit unless the user explicitly asked to preserve a conflicted change.

### Step 2: Determine commit message convention

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Runtime project instructions and established syntax inferred from `jj log` take precedence. Apply compatible Go commit-message quality guidance. Do not impose a fixed syntax, prefix, type list, subject template, or body template when the project does not establish one.

### Step 3: Consider logical commits

Scan the changed paths for naturally distinct concerns. If files clearly group into separate logical changes, create a commit for each group.

Keep this lightweight:
- Group at the file level only. Pass filesets to `jj commit`; do not split hunks within a file.
- Split only obvious independent concerns. If separation is ambiguous, use one commit.
- Do not over-slice the working-copy change.

JJ snapshots tracked working-copy files automatically; there is no staging step. Before committing, exclude sensitive or unrelated paths rather than relying on an all-path commit.

### Step 4: Commit

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

For each logical group, commit explicit filesets with its description:

```bash
jj commit <filesets...> -m "<description-composed-from-runtime-conventions>"
```

With path arguments, JJ keeps the selected paths in the committed change and moves the remaining changes into the new working-copy change. After each commit, inspect `jj status` and `jj diff` before committing the next group.

Do not create or move a bookmark merely to commit. If the user explicitly asks to publish the resulting change, fetch remote state with `jj git fetch` first. Then create a bookmark at the committed change with `jj bookmark create <bookmark> -r @-`, or reconcile and move an existing bookmark with `jj bookmark move <bookmark> --to @-`. Publish only the intended bookmark with `jj git push --bookmark <bookmark>`. `gh` remains allowed for hosting-service operations. Do not fetch or push for a commit-only request.

### Step 5: Confirm

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Run `jj status`, `jj diff`, and `jj log -r '@ | @-'` after the final commit. Confirm that intended paths were committed and unrelated paths remain in `@`. Report each committed change ID, commit ID, and description.
