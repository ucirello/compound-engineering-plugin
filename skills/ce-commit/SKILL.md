---
name: ce-commit
description: Create a JJ change with a clear, value-communicating description. Use when the user asks to commit/save working-copy changes with a project-appropriate description.
---

# JJ Change

Create well-crafted local change(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is recorded with an explicit fileset and a description that states the outcome, and `jj status` is clean of those changes. **Stop when:** the working copy is clean (nothing to record).

## Context

Gather context with each command as its **own** shell tool call (program + args only). Do **not** join those Context commands with `;`, `&&`, `||`, pipes, `$(...)`, or redirects — that syntax fails under Windows PowerShell. A non-zero exit is a normal state to interpret, not a failure to suppress.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Working-copy state | Not a JJ repo — stop |
| `jj diff` | Working-copy file changes | Empty diff is not cleanliness by itself |
| `jj bookmark list -r @` | Bookmarks on the working-copy change | Empty = no bookmark on `@` |
| `jj log -n 10` | Recent description style | Empty history |
| `jj git root` | Colocated git store for `gh` | Not colocated — skip `gh` |

Pair every `gh` invocation with `GIT_DIR=$(jj git root)` in the same shell so gh's underlying git sees the colocated git store. Resolve the remote default bookmark name with `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`; if that is empty or errors, use `main`.

Treat this as a snapshot. Re-read bookmarks and the working-copy fileset immediately before describing or committing if anything may have changed.

**Default bookmark name:** strip a leading `origin/` or a trailing `@origin` (so `origin/trunk` or `trunk@origin` → `trunk`). Use that bare name for all “on the default bookmark?” checks — never compare against `origin/<name>` or `name@origin`.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to record** — if `jj status` shows no modified or untracked files, report that and stop. Do not use `jj diff` alone as cleanliness (it misses untracked files).

2. **Bookmark first** — if `@` has no bookmark, or the working-copy bookmark is the default (`main` / `master` / the bare default name above), create a feature bookmark from the change content (`jj bookmark create <name>`), then re-read `jj bookmark list -r @`. If the default bookmark still points at `@`, move it to the parent with `jj bookmark move <default> --to @- --allow-backwards` so the work is not left on the default. Do not ask — describe-only still must not leave work only on an unnamed working-copy change or only on the default bookmark. If the derived name exists, pick a non-conflicting suffix.

3. **Description** — Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local syntax from project instructions already in context and from `git log` ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to quality, clarity, and structure without replacing local syntax. User override wins. Do not substitute a Conventional Commit type, scope, or prefix template.

The subject is imperative and names the outcome (what is now possible or fixed), not the file list. Body only when motivation or trade-offs are not obvious from the subject. When a plan Implementation Unit ID is already in hand for this change (conversation, caller, or the files belong to one unit), append that unit's U-ID in parentheses — `(U3)` means unit 3. Do not hunt for a plan. Omit when the change spans units, the unit is unclear, or no plan is in hand.

   - Bad: `Update checkout.rb` / `Add tests and fix stuff`
   - Good: `Fix double-submit on checkout`
   - Good: `Add per-subscription mute (U3)`

4. **Logical changes** — if changed files clearly split into distinct concerns, make separate changes (file level only, 2–3 max, no interactive hunk split). If ambiguous, one change. The working copy is already the change; do not stage.

5. **Describe and commit** — include **named files only** (never `.` as a fileset that selects the whole tree). Honor `exclude:<paths>` when the invocation carries it: those files stay unrecorded no matter what else changed; say in the report that they were left out. The working copy is already the change. Per change group, set the description and record the named fileset:

```bash
jj describe -m "<message composed from the standards above>"
```

```bash
jj commit -m "<message composed from the standards above>" file1 file2 file3
```

`jj describe` sets the description of `@`. `jj commit` with a fileset records those files into the current change and leaves everything else in the new working-copy change. A bare `jj commit` takes the whole working copy, so unnamed files (a caller's `exclude:` paths, or work the user did not name) would ride into the change. Naming the filesets records exactly the group and leaves other paths in the working copy.

6. **Confirm** — `jj status`; report change id(s) and subject(s).
