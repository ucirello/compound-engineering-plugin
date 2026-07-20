---
name: ce-commit
description: Create one or more coherent JJ changes from the working-copy change with repository-appropriate descriptions. Use when the user asks to commit or save current working-copy changes.
---

# Describe JJ Changes

Turn the current Jujutsu working-copy change into one or more coherent, described changes, then start a fresh working-copy change.

## Context

**On platforms other than Claude Code**, skip to "Context fallback" and run the commands there.

**In Claude Code**, the labeled sections below contain pre-populated data. Use them throughout this skill; do not rerun them.

**Working-copy status:**
!`jj status`

**Working-copy diff:**
!`jj diff`

**Recent change history:**
!`jj log -r '::@' --limit 10`

**Workspace root:**
!`jj workspace root`

### Context fallback

**In Claude Code, skip this section because the data above is already available.**

Run these commands to gather the same context:

```bash
jj status
jj diff
jj log -r '::@' --limit 10
jj workspace root
```

## Workflow

### Step 1: Inspect the working-copy change

Use the status, diff, recent history, and workspace root above. If the working-copy change has no file changes, report that there is nothing to save and stop.

Review every changed path before changing descriptions or splitting. Exclude credentials, environment files, unrelated user changes, and local runtime or scratch paths such as `.rocketclaw/`, `.tmp/rocketclaw/`, and `.context/` unless the user explicitly put them in scope and the repository tracks them intentionally. Respect `.gitignore` and the repository's active instructions. Preserve historical records and test fixtures unless changing them is part of the requested behavior.

Jujutsu snapshots files without a staging area. Do not introduce a staging step.

If temporary files are necessary, place them under `$(jj workspace root)/.tmp/rocketclaw/`. If the workspace root cannot be resolved, use `./.tmp/rocketclaw/` as the local fallback. Remove per-run temporary files when finished.

### Step 2: Decide the change boundaries

Scan the diff for naturally distinct concerns. Keep one change when the work is cohesive or separation is ambiguous. Split when file-level groups are clearly independent.

Keep splitting lightweight:

- Use Jujutsu filesets with `jj split`; do not stage files or invoke another VCS.
- Split at the file level only. Do not split hunks within a file.
- Keep tests with the behavior they verify and documentation with the behavior it explains.
- Avoid turning one coherent change into many tiny changes.
- Before each split, use `jj diff` with the intended fileset to verify that it selects exactly the desired paths.
- After each split, inspect the resulting changes with `jj status`, `jj diff`, and `jj log` before continuing. Do not assume which resulting revision contains a group when the output can establish it.

### Step 3: Compose, edit, and validate descriptions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

This policy applies every time a description is composed, edited, or validated. The syntax required by the repository's active local instructions and the syntax visible in `git log` ALWAYS wins. Apply the Go guidance only where it is compatible with those sources. Determine all syntax at runtime; do not impose a message format, type, scope, prefix, or other convention that those sources do not establish.

For each resulting change, use `jj describe` to set its description. Communicate the value or reason for the change rather than a file inventory. Preserve motivation, trade-offs, constraints, or other information a future reader needs, while keeping an obvious single-purpose description brief.

After setting or editing each description, inspect it with `jj log` and compare it with the actual change shown by `jj diff`. Correct descriptions that are empty, misleading, incomplete, or inconsistent with the runtime convention before proceeding.

### Step 4: Finish the operation

Once every intended change has the correct contents and description, run `jj new` to create a fresh empty working-copy change. Do not create or move bookmarks unless the user requested that separately.

Run `jj status` to verify that the new working-copy change is empty, then use `jj log` to collect the completed changes' change IDs, commit IDs, and description first lines. Report those details and mention any paths deliberately left in the working copy.
