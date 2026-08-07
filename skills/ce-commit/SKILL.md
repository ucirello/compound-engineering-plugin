---
name: ce-commit
description: Record the current work as one or more coherent Jujutsu changes with repository-appropriate descriptions and bookmark placement. Use when the user asks to commit, save, or record the working-copy change.
---

# Record Jujutsu Changes

Record the current working-copy work as well-described local Jujutsu changes. Do not push or open a PR; use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical unit is a described change with an explicit path list, the completed stack has appropriate non-default bookmark placement, and `@` is a fresh empty working-copy change. **Stop when:** there is no working-copy work to record.

## Context

Gather context with each command as its **own** shell tool call (program plus arguments only). Do **not** join commands with shell operators, substitutions, pipes, or redirects; that syntax is not portable across supported shells. Treat non-zero exits as state to interpret.

Inspect at least:

- the repository and working-copy state with `jj root` and `jj status`;
- the complete working-copy diff with `jj diff`;
- the current change and its recent ancestry with `jj log`;
- local and remote bookmark placement with `jj bookmark list --all-remotes`.

Use `jj git` interoperability only when remote Git state must be refreshed or inspected. If remote-default discovery is necessary and the available JJ state does not identify it, use `gh` when that capability is present; otherwise infer it from the project's active context and remote bookmarks, or ask rather than inventing a default.

Treat the inspection as a snapshot. Re-read `jj status`, the relevant diff, and bookmark placement immediately before recording if anything may have changed. If temporary storage is unavoidable, keep it under the current workspace's `.tmp/` directory and remove it before finishing.

## Message Authority

The project's active instructions and message syntax inferred at runtime from current `jj log` always win. Apply user preferences only where they are compatible with those standards.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Apply compatible Go guidance only to message quality, clarity, and structure. Preserve each logical unit's semantic requirements while adapting syntax dynamically. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example that `jj log` and the project's active instructions do not establish; use `<description-composed-from-runtime-conventions>` wherever command syntax or prose would otherwise supply one. Describe the outcome rather than reciting a path list, and include supporting explanation only when it materially helps a future reader understand the change.

Do not add creator, model, or harness branding; generated-by text; attribution; or filesystem paths to change descriptions.

## Workflow

1. **Inspect** - gather all Context evidence before mutating the change.

2. **Handle an empty change** - if `jj status` and `jj diff` show no working-copy work, report that there is nothing to record and stop. Do not treat an existing description alone as work.

3. **Select logical changes** - map every changed or newly tracked path to a logical unit. If the work clearly contains distinct concerns, split it into separate changes, normally no more than three. If the boundary is ambiguous, keep one change.

4. **Split when needed** - use `jj split` on the working-copy change. Prefer explicit filesets when whole paths form a concern; use its interactive selection only when a safe logical boundary crosses paths. After each split, inspect the resulting revisions and diffs so no path or hunk is omitted, duplicated, or assigned to the wrong unit. Supply a description during the split only after deriving it from Message Authority; otherwise describe the resulting revision separately.

5. **Describe** - use `jj describe` for each resulting revision that lacks its final description. Pass the derived message without shell composition, then inspect the revision to confirm that the description and included paths agree.

6. **Place the bookmark** - preserve an existing suitable feature bookmark and move it to the top recorded change when necessary. If the work is detached, unbookmarked, or associated only with the remote default line, derive a non-conflicting bookmark name from the work and create it at the top recorded change. Never move the default bookmark to feature work, and do not invent a fixed default-bookmark name.

7. **Open fresh work** - run `jj new` on top of the recorded change, then confirm with `jj status` that `@` is empty. If `jj new` cannot be completed, report the blocker instead of claiming completion.

8. **Report** - report each recorded change ID, its description, its explicit path list, the resulting bookmark placement, and confirmation that the new working-copy change is empty.
