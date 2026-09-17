---
name: ce-commit
description: Create a JJ change with a clear, value-communicating description. Use when the user asks to commit/save working-copy changes with a project-appropriate description.
---

# JJ Commit

Create well-crafted local change(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a description that states the outcome, and `jj status` is clean of those changes. **Stop when:** the tree is clean (nothing to commit).

## Context

Gather context with each command as its **own** shell tool call (program + args only). Do **not** join with `;`, `&&`, `||`, pipes, `$(...)`, or redirects — that syntax fails under Windows PowerShell. A non-zero exit is a normal state to interpret, not a failure to suppress.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj workspace root` | Workspace / repo presence | Not a JJ repo — stop |
| `jj status` | Working-copy state | Not a JJ repo — stop |
| `jj diff` | Working-copy changes | Empty = no content changes (ignored/untracked may still exist) |
| `jj bookmark list -r @` | Bookmarks at working copy | Empty = no bookmark (detached HEAD analog) |
| `jj log -n 10` | Recent description style | Little history to match |
| `jj git root` | Underlying Git dir for `gh` | No Git backend — skip `gh` |
| `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | Remote default bookmark | No GitHub remote / command fails — else `main` |

Pair the `gh` invocation with `GIT_DIR` set to the `jj git root` output and `GIT_WORK_TREE` set to the `jj workspace root` output, using the host's env-for-one-call mechanism (values from those prior own calls). Do not nest `$(...)` into the `gh` command.

Treat this as a snapshot. Re-read bookmarks and the working-copy file set immediately before committing if anything may have changed.

**Default bookmark name:** strip a leading `origin/` or a trailing `@origin` from the remote default (so `origin/trunk` or `trunk@origin` → `trunk`). Use that bare name for all “on the default bookmark?” checks — never compare against `origin/<name>` or `<name>@origin`.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to commit** — if `jj status` shows no working-copy changes (and no untracked files that belong in the change), report that and stop. Do not use `jj diff` alone as cleanliness (it misses untracked files).

2. **Bookmark first** — if there is no bookmark at `@` (detached HEAD analog), or a default bookmark (`main` / `master` / the bare default name above) is at `@`, create a feature bookmark from the change content (`jj bookmark create <name> -r @`). If the default bookmark is at `@`, move it off the work (`jj bookmark move <default> --to @- --allow-backwards`). Then re-read `jj bookmark list -r @`. Do not ask — commit-only still must not leave work only with no bookmark or only on the default bookmark. If the derived name exists, pick a non-conflicting suffix.

3. **Convention** — Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local commit-message syntax from project instructions and `git log` ALWAYS wins when it differs from the Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repository-local syntax. User override wins.

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive hunk split: never `jj commit --interactive`, never `git add -p`). If ambiguous, one commit.

5. **Message** — compose the description from the Convention step. The first line names the outcome (what is now possible or fixed), not the file list. Body only when motivation or trade-offs are not obvious from the first line; when a body is needed, use first line, blank line, then body. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or the files belong to one unit), append that unit's U-ID in parentheses — `(U3)` means unit 3. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand.

6. **Commit** — working copy is the current change; do not `git add`. Honor `exclude:<paths>` when the invocation carries it: those files stay out of the change no matter what else changed; say in the report that they were left out. Name files. Never `git add -A` or `git add .`. Never `jj file track` without named paths. If named files are untracked and belong in the change, `jj file track` those paths as its own call. `jj describe -m "<message composed from the standards above>"` updates the working-copy description without finishing. This workflow finishes a change and starts a new one with `jj commit`. Per commit group:

```bash
jj commit -m "<message composed from the standards above>" file1 file2 file3
```

The trailing fileset on `jj commit` is required: a bare `jj commit` takes the whole working copy, so anything else in `@` (a caller's `exclude:` paths, or work the user did not name) would ride into the change. Naming the paths commits exactly the group and leaves other working-copy paths in the new change on top.

7. **Confirm** — `jj status`; report change id(s) and subject(s).
