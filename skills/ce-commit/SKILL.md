---
name: ce-commit
description: Create local Jujutsu changes with clear, value-communicating descriptions. Use when the user asks to save current work as one or more repository-appropriate changes.
---

# Jujutsu Change

Create well-crafted local change(s) from the current working copy. Do not publish or open a review; use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change has an explicit file set, a repository-appropriate description that states its outcome, and an appropriate bookmark, and `jj status` shows none of those files in the new working-copy change. **Stop when:** the working-copy change is empty.

## Context

Gather context with each command as its **own** shell tool call (program + args only). Do **not** join with `;`, `&&`, `||`, pipes, `$(...)`, or redirects; that syntax is not portable across supported shells. Interpret a non-zero exit as state instead of suppressing it.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj root` | Workspace root | Not a Jujutsu workspace; stop |
| `jj status` | Working-copy change, parents, conflicts, and bookmarks | Not a Jujutsu workspace; stop |
| `jj diff --summary -r @` | Changed paths in the working-copy change | No path summary |
| `jj bookmark list -r @` | Local bookmarks currently targeting the working-copy change | No bookmark targets `@` |
| `jj log -r 'trunk()' --no-graph` | Repository default line of development | Default revision cannot be resolved |
| `jj log -n 10 --no-graph -T 'description.first_line() ++ "\n"'` | Recent description style | No useful local history |

Treat this as a snapshot. Re-run `jj status`, `jj diff --summary -r @`, and `jj bookmark list -r @` immediately before each mutation if the working copy may have changed.

If scratch space is necessary, use `<workspace-root>/.tmp/<run-id>/`; if that location cannot be used, fall back to `./.tmp/<run-id>/`. Do not use OS temporary directories, and remove run-only scratch after success.

## Workflow

0. **Gather** - run every Context command above in its own shell call, then continue.

1. **Nothing to save** - if `jj status` says the working-copy change is empty, report that and stop. Use this state rather than the path summary alone so conflicts and working-copy metadata remain visible.

2. **Bookmark first** - ensure the work is represented by a non-default local bookmark derived from its content. If no local bookmark targets `@`, create one with `jj bookmark create <name> -r @`. If `@` is the default revision, create the feature bookmark and move each default bookmark back to `@-` with `jj bookmark move <default-bookmark> --to @- --allow-backwards`. Re-run `jj bookmark list -r @`; do not ask unless a collision or conflicted bookmark prevents a safe transition. Pick a non-conflicting suffix when the derived name exists.

3. **Description authority** - The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; do not impose a fixed syntax. A user override wins.

4. **Logical changes** - if changed files clearly separate into distinct concerns, save separate changes at file granularity, 2-3 maximum. If the separation is ambiguous, use one change. Preserve `exclude:<paths>` exactly: excluded paths remain in the working-copy change and are named in the report.

5. **Compose descriptions** - describe the observable outcome rather than listing files. Include a body only when the governing sources or the change's non-obvious motivation, constraints, or consequences call for one. When a plan Implementation Unit ID is already available from the conversation, caller, or files belonging to one unit, retain that semantic association in the form required by local conventions; do not search for a plan, infer an unclear unit, or associate one description with multiple units.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

6. **Create the changes** - never allow excluded or unrelated paths into a described change. For one group that contains every changed path, describe `@`, then create a fresh working-copy change:

```bash
jj describe -m "<message composed from the standards above>"
jj new
```

When paths must remain out, extract each named group from `@` with `jj split <file1> <file2> -m "<message composed from the standards above>"`. The selected paths become the described parent change and the unselected paths remain in the working-copy child. Move the feature bookmark to that parent with `jj bookmark move <name> --to @- --allow-backwards`, then repeat only for additional groups. This is the Jujutsu-native equivalent of exact file grouping and leaves every excluded path untouched in `@`. Do not use interactive hunk selection.

7. **Validate and report** - run `jj status`, `jj diff --summary -r @`, `jj bookmark list`, and `jj log -r '::@' -n 4 --no-graph`. For each resulting change, run `jj show -r <change-id> --summary`. Verify that every intended path is in the intended described change, every excluded or unrelated path remains in `@`, and the working-copy change is empty unless paths were intentionally left out. Report the resulting change IDs, descriptions, bookmarks, and intentionally retained paths.
