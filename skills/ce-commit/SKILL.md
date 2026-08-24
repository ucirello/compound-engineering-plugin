---
name: ce-commit
description: Create Jujutsu commits with clear, value-communicating descriptions. Use when the user asks to commit or save working-copy changes with repository-appropriate descriptions.
---

# Jujutsu Commit

Create well-crafted local Jujutsu commits from the current working-copy change. Do not push or open a PR; use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is finalized from an explicit fileset with a description that states the outcome, the appropriate feature bookmark points to the resulting stack, and `jj status` no longer lists those paths in the working-copy change. **Stop when:** the working-copy change is empty.

## Context

Gather context with each command as its **own** shell tool call (program plus arguments only). Do not join commands with shell operators, command substitutions, pipes, or redirects. Interpret a non-zero exit as state rather than suppressing it.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj workspace root` | Workspace root and repository check | Not a Jujutsu workspace; stop |
| `jj status` | Working-copy change and conflicts | Empty change means nothing to commit |
| `jj diff` | Current change contents | Empty output means nothing to commit |
| `jj log -r 'heads(::@ & bookmarks())' --no-graph -T 'json(local_bookmarks) ++ "\n"'` | Nearest local bookmarks in the ancestry | No local bookmark anchors the current stack |
| `jj log -r 'heads(::@ & remote_bookmarks())' --no-graph -T 'json(remote_bookmarks) ++ "\n"'` | Nearest remote bookmarks in the ancestry | No remote bookmark anchors the current stack |
| `jj log -r '::@' -n 10 --no-graph` | Recent description style | No usable history to match |
| `jj log -r 'trunk()' --no-graph` | Default base change | `trunk()` is unresolved; do not guess a default |
| `jj log -r 'trunk() & tracked_remote_bookmarks()' --no-graph -T 'json(remote_bookmarks.filter(|b| b.tracked())) ++ "\n"'` | Tracked remote bookmarks at the default base | None or multiple means there is no unique default bookmark |

Treat this as a snapshot. Re-read `jj status`, `jj diff`, and the nearest bookmarks immediately before finalizing if the working copy may have changed.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to commit** — if the working-copy change is empty, report that and stop. Jujutsu snapshots non-ignored working-copy files automatically, so `jj status` is the authoritative check.

2. **Choose the bookmark action** — Jujutsu has no active bookmark. Resolve the default base with `trunk()`; if it does not resolve, stop before changing a bookmark and report the blocker. Recognize its default bookmark only when exactly one tracked remote bookmark points to that change; never infer a name. If exactly one nearest non-default local bookmark identifies the stack, retain it for advancement after finalizing. If only the unique default bookmark or no local bookmark anchors the stack, derive an unused feature bookmark name from the change. If the default or intended feature bookmark remains ambiguous, ask which bookmark to advance. Do not leave completed work reachable only through the default bookmark or an anonymous change.

3. **Description convention** — Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The user's instruction wins, followed by the project's active instructions and conventions, then the established syntax in the current `jj log`. Where those sources are silent, use only compatible Go guidance to improve the description's quality. It does not impose a verb tense, punctuation, line width, or first-line/body shape.

4. **Logical commits** — if changed files clearly split into distinct concerns, finalize separate file-level changes, with two or three as the maximum. Do not split hunks within a file. If the separation is ambiguous, make one commit.

5. **Describe each change** — communicate the outcome rather than enumerate files. When a plan implementation-unit identifier is already in hand and the files belong to exactly that unit, include that identifier using the project's established rendering. Do not search for a plan; omit the identifier when the group spans units, is unclear, or has no known unit.

6. **Finalize explicit filesets** — honor `exclude:<paths>` from the invocation: those paths must remain in the working-copy change and must be named in the report. For each logical group, pass only that group's paths to `jj commit`; this keeps the selected paths in the finalized commit and moves every remaining path into the new working-copy change.

```text
jj commit -m "<description>" <path>...
```

After each command, inspect the finalized parent with `jj log -r @- --no-graph` and verify with `jj status` that the intended paths left the working-copy change while all other paths, especially exclusions, remain.

7. **Place the feature bookmark** — after all groups are finalized, run `jj bookmark create <feature-bookmark> -r @-` for a new bookmark or `jj bookmark advance <feature-bookmark> --to @-` for the retained non-default bookmark. Confirm its target with `jj bookmark list -r @-`. Do not move the default bookmark.

8. **Report** — report each change ID, commit ID, and description, the feature bookmark, and any excluded or otherwise remaining working-copy paths.
