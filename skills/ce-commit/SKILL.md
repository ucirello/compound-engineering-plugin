---
name: ce-commit
description: Create a JJ change with a clear, value-communicating description. Use when the user asks to commit/save working-copy changes with a project-appropriate description.
---

# JJ Commit

Create well-crafted local change(s) from the current JJ working copy. No push, no PR; use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change has an explicit fileset and an outcome-focused description, a fresh empty working-copy change is on top, and `jj status` shows none of the completed work in the new change. **Stop when:** the working-copy change is empty.

## Context

Gather context with each command as its own shell tool call (program and arguments only). Do not join calls with shell operators, pipes, substitutions, or redirects. Treat a non-zero exit as state to interpret.

| Command | Purpose | Non-zero or empty means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a JJ workspace; stop |
| `jj status` | Working-copy state | Not a JJ workspace; stop |
| `jj diff` | Current change | Empty change |
| `jj log -r '@ | @-' --no-graph` | Current and parent change identity | Repository state is unavailable |
| `jj bookmark list -r @` | Bookmarks currently targeting the working-copy change | Empty means no local bookmark targets `@` |
| `jj bookmark list --all-remotes` | Local and remote bookmark state | Remote state is unavailable |
| `jj log -r 'ancestors(@, 10)' --no-graph` | Recent description style | No local JJ history is available |
| `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | Remote default bookmark | Unavailable; inspect tracked remote bookmarks and ask rather than guessing |

Treat this as a snapshot. Re-read the working-copy change and bookmarks immediately before describing or committing if anything may have changed.

## Workflow

1. If `jj status` shows an empty working-copy change, report that there is nothing to commit and stop.
2. If a bookmark for the proposed work already exists, preserve it. Otherwise derive a non-conflicting feature bookmark name from the change content and create it only after the completed change's target is known; JJ changes do not require a bookmark until publication.
3. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Project instructions and runtime `git log` syntax win.
4. If the changed files clearly split into distinct concerns, create separate changes at file level, two or three at most. If ambiguous, keep one change. Use `jj commit <filesets> -m "<message composed from the standards above>"` for each non-final group; it keeps those files in the completed change and moves the remaining files into the new working-copy change.
5. When a plan Implementation Unit ID is already in hand and maps unambiguously to this change, preserve that semantic reference without forcing a fixed syntax. Do not hunt for a plan.
6. Honor `exclude:<paths>` throughout. Excluded files remain in the working-copy change and are never included in a completed fileset. For a single final group, run `jj commit <included-filesets> -m "<message composed from the standards above>"`. For multiple groups, repeat with each group's filesets; never use an unbounded fileset while excluded or unrelated work exists.
7. If the completed work needs a bookmark, run `jj bookmark set <bookmark> -r @-` after `jj commit` creates the fresh empty change. A bookmark does not advance automatically in JJ.
8. Confirm with `jj status`, `jj log -r '@ | @-' --no-graph`, and `jj bookmark list -r @-`. Report change IDs, commit IDs, descriptions, and any excluded paths left in the working-copy change.
