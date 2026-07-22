---
name: ce-commit
description: Create one or more coherent JJ commits from the working-copy change with repository-appropriate descriptions. Use when the user asks to commit or save current working-copy changes.
---

# JJ Commit

Create one or more coherent commits from the current JJ working-copy change.

## Context

Gather current context with JJ and inspect actual Git history for commit-message style:

```text
jj workspace root
jj workspace list
jj status
jj diff
jj log -r 'ancestors(@, 10)'
jj bookmark list --all-remotes
git log -n 10 --format=full
```

`@` is the working-copy change. Changes are identified by stable change IDs; commit IDs may change when a change is rewritten. Bookmarks are named pointers used for sharing changes, not a prerequisite for committing. Do not treat the detached state of a colocated Git checkout as an error.

If scratch storage is needed, use `$(jj workspace root)/.tmp/rocketclaw`. If the current directory is outside a JJ workspace, use the current directory's `.tmp/rocketclaw` instead. Never use OS-global temporary storage.

## Workflow

### Step 1: Gather context

Use `jj status` to identify the working-copy change, conflicts, and changed paths; use `jj diff` to understand the content. Use `jj log` to understand the surrounding changes and actual `git log` to understand established description syntax. Use `jj workspace list` to confirm which workspace is active and avoid operating on another workspace's working-copy change.

If `jj status` reports that the working copy has no changes, report that there is nothing to commit and stop. If it reports conflicts, do not commit unless the user explicitly asked to preserve a conflicted change.

### Step 2: Determine commit message convention

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active repository-local instructions and message syntax observed in actual `git log` output win over incompatible Go guidance. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.

### Step 3: Consider logical commits

Scan the changed paths for naturally distinct concerns. If files clearly group into separate logical changes, create a commit for each group.

Keep this lightweight:
- Group at the file level only. Pass filesets to `jj commit`; do not split hunks within a file.
- Split only obvious independent concerns. If separation is ambiguous, use one commit.
- Do not over-slice the working-copy change.

JJ snapshots tracked working-copy files automatically; there is no staging step. Before committing, exclude sensitive or unrelated paths rather than relying on an all-path commit.

### Step 4: Commit

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active repository-local instructions and message syntax observed in actual `git log` output win over incompatible Go guidance. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.

For each logical group, direct JJ to commit the explicit filesets with the runtime-composed description. When one logical group contains every working-copy change, the fileset may be omitted only after confirming no sensitive or unrelated path would be included.

With path arguments, JJ keeps the selected paths in the committed change and moves the remaining changes into the new working-copy change. After each commit, inspect `jj status` and `jj diff` before committing the next group.

Do not create or move a bookmark merely to commit. If the user explicitly asks to publish the resulting change, resolve and retain one intended `$REMOTE` and `$BOOKMARK`, then fetch remote state with `jj git fetch --remote "$REMOTE"` first. Create the bookmark at the committed change with `jj bookmark create "$BOOKMARK" -r @-`, or reconcile and move the existing bookmark with `jj bookmark move "$BOOKMARK" --to @-`. Publish only it with `jj git push --remote "$REMOTE" --bookmark "exact:$BOOKMARK"`. `gh` remains allowed for hosting-service operations. Do not fetch or push for a commit-only request.

### Step 5: Confirm

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active repository-local instructions and message syntax observed in actual `git log` output win over incompatible Go guidance. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.

Run `jj status`, `jj diff`, and `jj log -r '@ | @-'` after the final commit. Confirm that intended paths were committed and unrelated paths remain in `@`. Report each committed change ID, commit ID, and description.
