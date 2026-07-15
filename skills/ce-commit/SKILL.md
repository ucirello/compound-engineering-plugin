---
name: ce-commit
description: Create a JJ commit with a clear, repository-appropriate message. Use when the user asks to commit or save current working-copy changes.
---

# JJ Commit

Describe and finish one or more coherent JJ changes from the working-copy commit. Done means each intended change has a validated description, the resulting change and commit IDs are reported, and any remainder in `@` is named explicitly.

Jujutsu has no staging area: the working copy is a commit (`@`), and most `jj` commands snapshot file-system changes into it. `jj commit` describes `@` and creates a new working-copy change on top. With filesets, selected changes remain in the commit being finished and unselected changes move to the new working-copy child.

## Context

Run each command as its own shell tool call. Do not join commands with shell operators, pipes, substitutions, or redirects. A non-zero exit is state to interpret, not a failure to hide.

| Command | Purpose | Failure meaning |
| --- | --- | --- |
| `jj workspace root` | Repository root | Not a JJ repository; report and stop |
| `jj status` | Working-copy and conflict state | Repository cannot be read; report and stop |
| `jj diff` | Current content changes | No output means no content change |
| `jj bookmark list -r @` | Bookmarks at the working-copy change | Empty output is normal |
| `jj bookmark list -r @-` | Bookmarks at its parent | Empty output is normal |
| `jj log -r '::@' --limit 10 --no-graph` | Recent local descriptions and topology | No prior history is available |
| `jj log -r '::@' --limit 10 --no-graph -T 'description ++ "\n"'` | Repository message syntax and style | No compatible history is available |

The final command reads JJ description history for the required local message-style check; all VCS mutation remains JJ-native. Re-read `jj status` and `jj diff` immediately before each commit because commands snapshot the working copy and concurrent edits may change it.

## Workflow

### Step 1: Validate the working copy

If `jj status` reports no changes in `@`, report that there is nothing to finish and stop. Do not create an empty change.

If `jj status` reports conflicts, resolve them before finishing the change. Use `jj resolve` for an available merge tool or edit the materialized conflict directly, then rerun `jj status` and `jj diff`. Do not finish a conflicted change.

Bookmarks are named pointers and do not follow the working copy. A working-copy change does not need a bookmark merely to be committed, so do not create or move one in this skill unless the user explicitly asks.

### Step 2: Determine the message standard

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The repository-local instructions and the `git log` syntax dynamically derived from repository history through JJ always win; apply Go guidance only when compatible. Communicate the change's purpose clearly, keep the first line useful in history, and add explanatory context when a future reader needs it. Fixed prefixes, types, scopes, subjects, templates, and examples are prohibited; do not add capitalization, line-length, or body rules without repository-local evidence.

### Step 3: Choose coherent changes

Scan the changed paths for distinct concerns. If file-level groups are clearly independent, finish them separately. If separation is ambiguous, keep one change. Do not use interactive splitting unless the user explicitly requests hunk-level separation.

Each change must preserve one reviewable purpose. Include related tests, generated outputs, and documentation with the behavior they validate or describe unless local conventions require another grouping.

### Step 4: Describe and finish

At each change-description composition site, apply this instruction exactly:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The repository-local instructions and the `git log` syntax dynamically derived from repository history through JJ always win; apply Go guidance only when compatible. Describe the purpose and material effect accurately. Add a body only when it carries motivation, tradeoffs, compatibility notes, or other context not clear from the first line. Fixed prefixes, types, scopes, subjects, templates, and examples are prohibited.

For one change:

```bash
jj commit -m "<repository-derived-message>"
```

For a multiline description, use the available file-writing capability to create `$(jj workspace root)/.tmp/ce-commit/<unique-id>.txt`. If no JJ repository exists, use the local fallback `.tmp/ce-commit/<unique-id>.txt`; this skill otherwise reports the missing repository and stops. Then run:

```bash
jj commit --message-file <workspace-local-message-file>
```

For multiple file-level groups, pass the group's filesets before `-m` or `--message-file`. Each fileset selects changes retained in the change being finished; unselected changes move to the new working-copy child. Re-run `jj status` and `jj diff` after every path-limited commit before selecting the next group. Do not use staging-area or non-JJ commit commands.

Without filesets, `jj commit` is equivalent to describing `@` and creating a new empty working-copy change on top. Do not run an additional `jj new`.

### Step 5: Validate and report

For every completed change, inspect it with `jj log -r @- --no-graph` and, when needed, `jj show -r @-`. Validate its description with this instruction:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The repository-local instructions and the `git log` syntax dynamically derived from repository history through JJ always win; apply Go guidance only when compatible. Fixed prefixes, types, scopes, subjects, templates, and examples are prohibited. If the description does not match the actual change or present repository standard, edit it with `jj describe -r @- -m "<repository-derived-message>"` or `--message-file <workspace-local-message-file>`, then validate it again.

Run `jj status` after the final commit. Report every completed change ID, commit ID, and first line. If `@` is not empty, report the remaining paths rather than claiming all changes were committed.
