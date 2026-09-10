---
name: ce-commit
description: Create a JJ change with a clear, value-communicating description. Use when the user asks to commit/save working-copy changes with a project-appropriate description.
---

# JJ Commit

Create well-crafted local change(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit fileset and a description that states the outcome, and `jj status` is clean of those changes. **Stop when:** the working-copy change is empty (nothing to commit).

## Context

Gather context with each command as its **own** shell tool call (program + args only). Do **not** join with `;`, `&&`, `||`, pipes, `$(...)`, or redirects — that syntax fails under Windows PowerShell. A non-zero exit is a normal state to interpret, not a failure to suppress.

Run every `jj` command with process cwd set to the workspace root from `jj workspace root`. Do not use `jj -R` as a cwd substitute. Filesets are workspace-relative (`src/example.py`), never a path that includes `.tmp/` or another checkout prefix.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj workspace root` | Workspace root | Not a JJ repo — stop |
| `jj status` | Working-copy state | Not a JJ repo — stop |
| `jj diff` | Working-copy changes | Empty change |
| `jj bookmark list -r @` | Bookmarks on the working-copy change | Empty = no local bookmark on `@` |
| `jj log -n 10 --no-graph` | Recent description style | No history |
| `jj bookmark list -r trunk()` | Default bookmark (trunk) | No `trunk()` — try `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`, else `main` |
| `jj git root` | Underlying Git dir for `gh` | No Git backend — skip `gh`; do not guess a default bookmark |

Treat this as a snapshot. Re-read bookmarks and working-copy state immediately before committing if anything may have changed.

**Default bookmark name:** strip a trailing `@origin` (or other remote) from a remote bookmark (so `main@origin` → `main`). Use that bare name for all “on the default bookmark?” checks — never compare against `name@origin`.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to commit** — if `jj status` shows no working-copy changes, report that and stop. Do not use `jj diff` alone as cleanliness.

2. **Bookmark first** — if `@` has no local bookmark, or a bookmark on `@` is the default (`main` / `master` / the bare trunk name above), create a feature bookmark from the change content (`jj bookmark create <name>`), then re-read `jj bookmark list -r @`. If the default bookmark itself points at `@`, move it to `@-` (`jj bookmark move <default> --to @- --allow-backwards`) so the work is not left on the default. Do not ask — commit-only still must not leave work only with no bookmark or only on the default bookmark. If the derived name exists, pick a non-conflicting suffix.

3. **Compose the description.** Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in git log, compose commit messages adherent to the present standards.

   Repository-local commit-message syntax from project commit conventions already in context and `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality/clarity/structure without replacing repository-local syntax. Do not choose a fixed type, scope, prefix, subject form, or body template.

   Semantic constraints on the composed message: the subject names the outcome (what is now possible or fixed), not the file list. Body only when motivation or trade-offs are not obvious from the subject. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or the files belong to one unit), append that unit's U-ID in parentheses — `(U3)` means unit 3. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand.

   - Bad: `Update checkout.rb` / `Add tests and fix stuff`
   - Good: `Fix double-submit on checkout`
   - Good: `Add per-subscription mute (U3)`

4. **Logical changes** — if changed files clearly split into distinct concerns, make separate changes (file level only, 2–3 max, no `jj commit --interactive` / `jj split`). If ambiguous, one change.

5. **Commit named files** — there is no staging area; the working copy is the change. Honor `exclude:<paths>` when the invocation carries it: those files stay in the working-copy change no matter what else changed; say in the report that they were left out. Commit **named files only** (never `jj commit` with no filesets — that takes the whole working copy). For each group:

```
jj commit -m "<message composed from the standards above>" file1 file2 file3
```

The fileset list is load-bearing: a bare `jj commit` takes the whole working copy, so `exclude:` paths or work the user did not name would ride into the change. Naming the paths keeps exactly that group in the completed change and moves other working-copy paths into the new empty change on top.

`jj commit` does not move bookmarks forward. After the last group, if the feature bookmark is not on the completed tip, run `jj bookmark set <name> -r @-`.

6. **Confirm** — `jj status`; report change id(s) and subject(s).
