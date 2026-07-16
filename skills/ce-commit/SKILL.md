---
name: ce-commit
description: Create a JJ commit with a clear, repository-appropriate message. Use when the user asks to commit or save current working-copy changes.
---

# JJ Commit

Create one or more well-described JJ changes from the current working-copy change.

## Workflow

### Step 1: Gather context

Run these commands from the workspace:

```bash
jj status
jj diff --git
jj log -r '::@' -n 10
git log -10
jj bookmark list --all-remotes
```

Use `jj status` and `jj diff` to inspect the working-copy change `@`. JJ snapshots working-copy files automatically, so operate directly on the change and select content with filesets. Treat untracked files reported by JJ deliberately, and do not include ignored files, credentials, or unrelated changes.

If `@` has no content changes, report that there is nothing to commit and stop. Do not create an empty change.

If `jj status` reports conflicts, stop and explain them instead of committing unresolved content unless the user explicitly requested that result.

### Step 2: Determine the message convention

Follow the project's active repository-local instructions first. Do not re-read instructions already present in context.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. Derive the message syntax dynamically while capturing motivation, effects, trade-offs, or relevant context that are not evident from the change itself. Do not impose a fixed prefix, type, scope, subject, body structure, template, or example.

### Step 3: Determine logical changes

Inspect the changed paths for naturally distinct concerns before committing:

- Group at the file level only; do not split hunks within a file.
- Split clearly unrelated work into separate changes.
- Keep one change when separation is ambiguous.
- Preserve dependency order when multiple changes build on each other.

Use JJ filesets to select each group. Quote fileset expressions so the shell does not interpret them. Prefer explicit workspace-relative paths or filesets over selecting every path, which reduces the risk of including unrelated or sensitive files.

### Step 4: Handle bookmarks

JJ has no active or current bookmark. Use `jj bookmark list` and the revision graph to identify bookmarks at or immediately behind `@`; do not infer an active bookmark from the working copy.

If the working-copy change is already directly targeted by the repository's default bookmark, do not leave that bookmark on the new work. Move the default bookmark back to the unchanged parent with `jj bookmark move`, using `--allow-backwards` only when JJ requires it. Create a descriptive feature bookmark for the committed work if the repository workflow uses bookmarks or the work will be pushed. Otherwise, a local change does not require a bookmark.

If a feature bookmark already identifies the current line of work, preserve it. Because `jj commit` does not advance bookmarks to the new empty working-copy change, leave the feature bookmark on the committed change or move it there explicitly when needed. Never move unrelated bookmarks.

Use neutral arguments appropriate to the discovered repository state:

```bash
jj bookmark move <bookmark> --to <revision>
jj bookmark create <bookmark> --revision <revision>
```

### Step 5: Describe and commit

For a single change containing all of `@`, update its description and create a new empty working-copy change on top:

```bash
jj commit --message <message>
```

For each file-level group, pass its filesets to `jj commit`. The selected paths remain in the described commit, and the remaining paths move to the new working-copy change on top:

```bash
jj commit --message <message> <filesets>
```

If the user explicitly wants to describe `@` without creating a new working-copy change, use:

```bash
jj describe --message <message>
```

Before each command, verify that its filesets select exactly the intended paths with `jj diff <filesets>`. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. Derive the message syntax dynamically; do not impose a fixed prefix, type, scope, subject, body structure, template, or example. Compose the message from that selected diff, not from unrelated remaining work.

For multiple groups, commit them in dependency order and reassess `jj status` and `jj diff` after each commit because `@` changes. Use only the JJ change workflow described here.

### Step 6: Confirm

Run:

```bash
jj status
jj log -r '@- | @' -n 2
jj bookmark list
```

Verify that each intended change has the expected description and content, that remaining working-copy changes are intentional, and that bookmarks point to the intended revisions. When validating a description, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. Validate against the dynamically derived repository standard, not a fixed prefix, type, scope, subject, body structure, template, or example. Report the committed change ID or commit ID and first line for each created change, plus any remaining working-copy changes.
