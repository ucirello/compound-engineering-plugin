---
name: ce-commit
description: Create a Jujutsu commit with a clear, value-communicating description. Use when the user asks to commit or save working-copy changes with a repo-appropriate description.
---

# Commit

Create well-crafted local commit(s) from the current Jujutsu working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed from an explicit file list with a description that states the outcome, its current-line bookmark points to the latest created commit, and `jj status` is clean of those changes. **Stop when:** the working-copy commit has no changes to commit.

## Context

Gather context with each command as its **own** shell tool call (program + args only). Do **not** join with `;`, `&&`, `||`, pipes, `$(...)`, or redirects — that syntax fails under Windows PowerShell. A non-zero exit is a normal state to interpret, not a failure to suppress.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj workspace root` | Workspace root; place any temporary files under `<workspace-root>/.tmp`, or `<current-directory>/.tmp` if this fails | Not a Jujutsu workspace; use the current directory only for temporary paths, then stop the commit workflow |
| `jj status` | Working-copy state | Not a Jujutsu repository — stop |
| `jj diff` | Current change | Empty = no content changes |
| `jj bookmark list -r 'heads(::@ & bookmarks())'` | Closest current-line local bookmark(s) | Empty = the working copy has no local bookmark on its line |
| `jj log -r :: -n 10` | Recent description style and repository history | No usable local history |
| `jj bookmark list --all-remotes` | Local and remote bookmark context | No usable bookmark context |
| `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | GitHub default bookmark name | GitHub metadata unavailable; infer from active project conventions and remote bookmark context, or ask if still ambiguous |

Treat this as a snapshot. Re-read status, diff, and current-line bookmarks immediately before committing if anything may have changed.

Use the bare default bookmark name for current-line checks, without a remote suffix.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to commit** — if `jj status` and `jj diff` show that the working-copy commit has no content changes, report that and stop.

2. **Bookmark first** — if the working copy has no current-line local bookmark, or its closest current-line bookmark is the default bookmark, create a feature bookmark at `@` with `jj bookmark create <derived-name> -r @`, then re-read the current-line bookmarks. Do not ask — commit-only still must not leave work without a feature bookmark or only on the default bookmark's line. If the derived name exists, choose a non-conflicting suffix. Record the feature bookmark that must advance with the commits; if multiple current-line feature bookmarks make that choice ambiguous, ask before moving one.

3. **Convention and description** — project instructions already in context and patterns observed in `jj log` take precedence; user overrides win. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply compatible Go guidance only to quality, clarity, and structure without imposing a fixed prefix, type, scope, subject, body, layout, template, example, or message. Preserve any Implementation Unit traceability required by the active project conventions without prescribing where or how it appears.

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits at file level only, 2–3 maximum, without interactive selection. If ambiguous, make one commit.

5. **Commit named files** — commit each group with `jj commit -m <description> <path>...`. Honor `exclude:<paths>` when the invocation carries it: those files stay in the new working-copy commit no matter what else changed; say in the report that they were left out. Never omit the filesets: without path arguments, `jj commit` commits every change in the working-copy commit. After each commit, advance the recorded feature bookmark to the created commit with `jj bookmark move <bookmark> --to @-`, then verify its target before continuing.

6. **Confirm** — run `jj status`, inspect each created commit with `jj log -r <created-revisions>`, and verify the recorded feature bookmark targets the latest one. Report commit IDs, change IDs, and description summaries, plus any excluded or otherwise remaining working-copy changes.
