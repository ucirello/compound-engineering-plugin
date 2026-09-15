---
name: ce-commit
description: Create a JJ change with a clear, value-communicating description. Use when the user asks to commit/save working-copy changes with a repo-appropriate description.
---

# JJ Commit

Create well-crafted local change(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit fileset and a description that states the outcome, and `jj status` is clean of those changes. **Stop when:** the working copy is clean (nothing to commit).

## Context

Gather context with each command as its **own** shell tool call (program + args only). Do **not** join with `;`, `&&`, `||`, pipes, `$(...)`, or redirects — that syntax fails under Windows PowerShell. A non-zero exit is a normal state to interpret, not a failure to suppress.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Working-copy state | Not a jj workspace — stop |
| `jj diff` | Current change vs parent | Empty = no content changes (still check `jj status`) |
| `jj log -r @ --no-graph -T bookmarks` | Bookmarks on `@` | Empty = no bookmark on `@` |
| `jj log -n 10 --no-graph` | Recent description style | Empty history |
| `jj bookmark list` | Local and remote bookmarks; trunk | No bookmarks listed |
| `jj git root` | Git dir for `gh` | No colocated Git repo — skip `gh`, use bookmarks |
| `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name` | GitHub default branch (fallback) | No GitHub remote / auth — use the trunk bookmark, else `main` |

When invoking `gh`, set `GIT_DIR` for that call to the path from `jj git root` (fill the path from that prior call; do not nest `$(...)`).

Treat this as a snapshot. Re-read bookmarks on `@` and the changed fileset immediately before committing if anything may have changed.

**Default bookmark name:** from `jj bookmark list` / remote bookmarks, take the trunk name and strip a trailing `@origin` (so `main@origin` → `main`). Fall back to the `gh` default branch, else `main`. Use that bare name for all “on the default bookmark?” checks — never compare against `<name>@origin`.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to commit** — if `jj status` shows no working-copy changes, report that and stop. Do not use `jj diff` alone as cleanliness. There is no staging area; the working copy is the change.

2. **Bookmark first** — if `@` has no bookmark, or it carries the default bookmark (`main` / `master` / the bare default name above), create a feature bookmark from the change content (`jj bookmark create <name>`). If the default bookmark is on `@`, move it to `@-` so the default stays at the parent. Then re-read `jj log -r @ --no-graph -T bookmarks`. Do not ask — commit-only still must not leave work only on a bookmark-less `@` or the default bookmark. If the derived name exists, pick a non-conflicting suffix.

3. **Description** —

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local syntax from project instructions and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality, clarity, and structure without replacing repo-local syntax. Determine the syntax at runtime from those sources. User override wins.

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive hunk split). If ambiguous, one commit. `jj commit` with a fileset puts those paths in the current change and leaves the rest in the working copy.

5. **Message** — first line names the outcome (what is now possible or fixed), not the file list. Body only when motivation or trade-offs are not obvious from the first line. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or the files belong to one unit), append that unit's U-ID in parentheses — `(U3)` means unit 3. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand.

6. **Commit** — no staging. Named filesets only. Honor `exclude:<paths>` when the invocation carries it: omit those paths from the fileset so they stay in the working copy no matter what else changed; say in the report that they were left out.

Resolve the workspace root with `jj workspace root` as its own call. Write the full message — first line, blank line, optional body — to a file under `<workspace-root>/.tmp/ce-commit/` with your file-write tool, then commit each group:

```bash
jj commit -m "<message composed from the standards above>" file1 file2 file3
```

`jj commit` has no `-F`; do not feed the message through a shell redirect. A fileset-less `jj commit` takes the whole working copy, so `exclude:` paths or files belonging to a later logical group would ride into the change. Naming the paths commits exactly the group and leaves other working-copy paths alone.

7. **Confirm** — `jj status`; report change id(s) and subject(s).
