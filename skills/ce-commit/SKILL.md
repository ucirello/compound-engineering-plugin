---
name: ce-commit
description: Create a JJ change with a clear, value-communicating description. Use when the user asks to commit/save working-copy changes with a project-appropriate description.
---

# JJ Change

Create well-crafted local change(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is described with an explicit fileset and a description that states the outcome, and `jj status` is clean of those changes. **Stop when:** the working copy has no remaining changes (nothing to describe).

## Context

Gather context with each command as its **own** shell tool call (program + args only). Do **not** join with `;`, `&&`, `||`, pipes, `$(...)`, or redirects — that syntax fails under Windows PowerShell. A non-zero exit is a normal state to interpret, not a failure to suppress.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a JJ repo — stop |
| `jj status` | Working-copy state | Not a JJ repo — stop |
| `jj diff` | Working-copy vs parents | Empty working-copy diff |
| `jj bookmark list -r @` | Bookmarks on the working-copy change | Empty = no bookmark on `@` |
| `jj log -n 10 --no-graph -r ::@` | Recent description style | Empty history |
| `jj bookmark list -r trunk()` | Default bookmark | No `trunk()` — run `jj git root` as its own call, then `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` with `GIT_DIR` set to that path (fill the path from the prior call; do not nest command substitution), else `main` |

Treat this as a snapshot. Re-read bookmarks and the working-copy fileset immediately before describing if anything may have changed.

**Default bookmark name:** strip a remote `@<remote>` suffix (so `trunk@origin` → `trunk`). Use that bare name for all “on the default bookmark?” checks — never compare against `name@origin`.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to describe** — if `jj status` shows no working-copy changes, report that and stop. Do not use `jj diff` alone as cleanliness.

2. **Bookmark first** — if `@` has no bookmark, or carries the default bookmark (`main` / `master` / the bare default name above), create a feature bookmark from the change content (`jj bookmark create <name>`). If `@` carries the default bookmark, also move that bookmark to the parent so the work is not left on the default: `jj bookmark move <default-name> --to @- --allow-backwards`. Then re-read `jj bookmark list -r @`. Do not ask — describe-only still must not leave work only on an unbookmarked working-copy change or the default bookmark. If the derived name exists, pick a non-conflicting suffix.

3. **Convention** — Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repo-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repo-local syntax. Match project commit conventions already in context; else match the recent log pattern. User override wins.

4. **Logical changes** — if changed files clearly split into distinct concerns, make separate changes (file level only, 2–3 max, no `jj commit --interactive`). If ambiguous, one change.

5. **Description** — subject is imperative and names the outcome (what is now possible or fixed), not the file list. Body only when motivation or trade-offs are not obvious from the subject. When a plan Implementation Unit ID is already in hand for this change (conversation, caller, or the files belong to one unit), append that unit's U-ID in parentheses — `(U3)` means unit 3. Do not hunt for a plan. Omit when the change spans units, the unit is unclear, or no plan is in hand.

6. **Describe named filesets** — put **named files only** in the change (never a pathless `jj commit` that snapshots the whole working copy). Honor `exclude:<paths>` when the invocation carries it: those files stay out of the change no matter what else changed; say in the report that they were left out. There is no index: do not stage. Per change group:

```bash
jj commit -m "<message composed from the standards above>" file1 file2 file3
```

Pass `-m` as a single argument so `$`, quotes, backticks, or a multi-line body are not expanded by the shell.

The trailing fileset on `jj commit` is load-bearing: a pathless `jj commit` takes the whole working copy, so anything not named (a caller's `exclude:` paths, or other working-copy files) would ride into the change. Naming the paths describes exactly the group; remaining working-copy changes move to the new working-copy commit on top.

7. **Confirm** — `jj status`; report change_id(s), commit_id(s), and subject(s) of the described change (`@-` after `jj commit`).
