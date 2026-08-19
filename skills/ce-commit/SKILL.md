---
name: ce-commit
description: Describe and commit jj changes with repository-appropriate messages. Use when the user asks to commit or save workspace changes locally.
---

# Commit Changes

Create well-described local jj changes from the current workspace. Do not push or open a PR; use `ce-commit-push-pr` for the full ship flow.

**Done when:** each included logical change has its own description and commit, `jj status` shows those changes are no longer in the working-copy change, and excluded paths remain uncommitted. **Stop when:** there are no workspace changes to commit.

## Context

Run each command as its own shell tool call (program plus arguments only). Do not join commands with shell operators, substitutions, pipes, or redirects. Treat a non-zero exit as state to interpret.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj root` | Workspace root | Not a jj workspace; stop |
| `jj status` | Working-copy change and conflicts | No workspace changes means stop |
| `jj diff` | Content to group and describe | No diff means stop |
| `jj log -r 'ancestors(@, 10)'` | Recent local description style | No useful local history |
| `git log --oneline -10` | Repository message history | Unavailable history; use the jj history |

Treat this context as a snapshot. Re-read `jj status` immediately before each commit if the workspace may have changed.

If temporary files are needed, resolve the workspace with `jj workspace root` and store them under `<jj-workspace-root>/.tmp/ce-commit/`; if the root cannot be resolved, use `./.tmp/ce-commit/`. Do not use OS-global temporary storage.

## Compose And Commit

Repository-local instructions and repository history always win over all other message guidance. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply compatible Go clarity and structure guidance so the description communicates the outcome and any material motivation, behavior, or trade-offs without imposing fixed syntax or content.

Group clearly distinct concerns into separate changes at file level; if the split is ambiguous, keep one change. When a plan Implementation Unit ID is already in hand and one group maps to that unit, preserve the ID in the repository-appropriate location without searching for a plan; omit it when the group spans units or the mapping is unclear.

Honor `exclude:<paths>` throughout: excluded paths remain in the working-copy change and the final report names them. For each included group, pass its explicit paths to jj so unrelated or excluded workspace content cannot enter the commit:

```bash
jj commit --message "<repository-appropriate description>" -- <group-files...>
```

This describes the current change, commits only the named files into it, and moves the remaining workspace changes into a new working-copy change on top. There is no staging step or index. If the command fails or the resulting split is not the intended file set, stop and report the state rather than committing a broader change.

After every commit, run `jj status` and inspect the committed change with `jj log -r @-`. Report each change ID and description, plus any excluded or otherwise uncommitted paths.
