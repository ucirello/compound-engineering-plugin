---
name: ce-commit
description: Create one or more coherent JJ commits from the working-copy change with repository-appropriate descriptions. Use when the user asks to commit or save current working-copy changes.
---

# JJ Commit

Finish one or more coherent changes from JJ's working-copy commit (`@`). Done means every intended change has a validated description, completed change and commit IDs are reported, and any remainder in `@` is named explicitly.

The working copy is already a change. Most JJ commands snapshot file-system edits into `@`; `jj commit` finishes that change and creates a new working-copy change on top. When given filesets, it finishes the selected content while moving unselected content into the new working-copy child.

## Command Discipline

Run each command as a separate shell-tool call. Do not combine commands with shell operators, pipes, substitutions, or redirects. Interpret non-zero exits and report unrecoverable failures rather than hiding them.

Use only JJ for repository inspection and mutation. There is no staging area, index, detached-head condition, or branch gate in this workflow. Bookmarks are named pointers that do not automatically follow the working copy; do not create or move one unless the user explicitly asks.

## Workflow

### Step 1: Inspect the working-copy change

Run:

```bash
jj workspace root
jj status
jj diff
jj log -r '::@' --limit 10 --no-graph
jj log -r '::@' --limit 10 --no-graph -T 'description ++ "\n"'
```

`jj workspace root` must identify a repository. If it does not, report that and stop. If `jj status` and `jj diff` show no content changes in `@`, report that there is nothing to finish and stop; do not create an empty change.

If `@` contains conflicts, resolve them with the available merge tool through `jj resolve` or by editing the materialized conflict, then rerun `jj status` and `jj diff`. Do not finish a conflicted change.

Re-run `jj status` and `jj diff` immediately before every `jj commit`. JJ snapshots the file system, so concurrent edits can alter `@` after the initial inspection.

### Step 2: Derive the description standard

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and description syntax inferred at runtime from `jj log` always win. Apply compatible Go guidance for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example, including in command-message examples; use any such form only when the active project instructions or `jj log` establish it.

Infer the active standard from the nearest relevant history, not from a universal fallback. If history is sparse or inconsistent, use a clear description of the change's purpose and material effect without inventing syntax.

### Step 3: Select coherent changes

Inspect every changed path reported by `jj status` and its content in `jj diff`. Group changes only when distinct reviewable purposes are clear. Keep related implementation, tests, generated output, and documentation together unless repository-local conventions indicate otherwise.

Use JJ filesets for file-level groups. Do not perform interactive or hunk-level splitting unless the user explicitly requests it. If separation is ambiguous, finish one coherent change rather than guessing.

Before each path-limited commit, derive a fileset from the current `jj status`; do not reuse a stale path list. Treat fileset expressions as repository inputs requiring careful quoting, especially when paths contain spaces or fileset operators.

### Step 4: Compose and finish each change

For every description, apply this instruction exactly:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and description syntax inferred at runtime from `jj log` always win. Apply compatible Go guidance for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example, including in command-message examples; use any such form only when the active project instructions or `jj log` establish it.

Describe the purpose and material effect accurately; include further context only when it helps a future reader understand motivation, constraints, or trade-offs.

For the whole working-copy change, invoke `jj commit` with the dynamically composed description. For a file-level group, pass the dynamically derived fileset arguments to `jj commit` before the description option. The conceptual forms are:

```text
jj commit -m <description-composed-from-runtime-conventions>
jj commit <dynamically-derived-fileset> -m <description-composed-from-runtime-conventions>
```

The placeholders are runtime values, not literal examples. Pass the description as one argument through the shell tool's argument handling. Do not interpolate repository content into a compound shell command.

If a multiline-description handoff requires a file, resolve `<workspace-root>` by running `jj workspace root`; if that root is unavailable at handoff time, use the current project directory. Use `<workspace-root>/.tmp/rocketclaw/commit/<run-id>/message.txt`. First verify the resolved root, then create the parent directory in a separate shell call with `mkdir -p "<workspace-root>/.tmp/rocketclaw/commit/<run-id>"`; the quoted placeholders must be replaced with the runtime values. Write the message with the available file-writing capability, read it with the available file-reading capability, and pass the resulting content as the description argument. Do not combine root resolution, directory creation, file writing, or committing in one shell command.

After a fileset-limited commit, run `jj status` and `jj diff` again. Selected content belongs to the completed parent; unselected content remains in the new `@`. Recompute the next fileset from that state. Do not run `jj new` after `jj commit` because the latter already creates the new working-copy change.

### Step 5: Validate and report

Inspect each completed parent with:

```text
jj log -r <completed-revision> --no-graph
jj show -r <completed-revision>
```

Immediately after each commit, `<completed-revision>` is normally `@-`; retain its reported change ID before finishing another change so validation and reporting remain unambiguous.

Validate every completed description with this instruction:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Active project instructions and description syntax inferred at runtime from `jj log` always win. Apply compatible Go guidance for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example, including in command-message examples; use any such form only when the active project instructions or `jj log` establish it.

If the description is inaccurate or violates the observed repository standard, invoke `jj describe -r <completed-revision> -m <description-composed-from-runtime-conventions>`, then inspect it again with `jj log` and `jj show`. The placeholders must be replaced with the revision and description derived at runtime.

Run `jj status` after the final commit. Report each completed change ID, commit ID, and description first line. If `@` still contains content or conflicts, report the remaining paths and state rather than claiming that all changes were committed.
