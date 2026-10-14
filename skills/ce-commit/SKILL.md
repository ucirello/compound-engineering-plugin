---
name: ce-commit
description: Create a local Jujutsu change with a clear, value-communicating description. Use when the user asks to commit/save changes with a repo-appropriate message.
---

# Jujutsu Commit

Create well-crafted local change(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and an outcome-oriented description, and those changes are no longer pending in `jj status`. **Stop when:** nothing remains to commit. Preserve unrelated work.

## Context

Gather context with each command as its own shell tool call. Obtain the absolute target root with `jj workspace root`, then set every command's working directory to that absolute root; `jj -R` alone does not change the working directory. Prefer program-and-argument calls rather than shell composition, including on Windows. Interpret non-zero exits rather than suppressing them.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Working-copy state and conflicts | Not a JJ repository — stop |
| `jj diff` | Pending changes | Also inspect file state |
| `jj bookmark list` | Local and remote bookmarks | No bookmark — choose a feature bookmark |
| `jj log -r 'ancestors(@, 10)'` | Recent change context | No substantive history — use project/user instructions |
| `jj git root` | Read-only Git backend for history and GitHub CLI | Backend unavailable — report the limitation |

Determine the default bookmark from verified repository context. If unknown, use `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` with `GIT_DIR` set to the backend returned by `jj git root` in the target workspace. POSIX example: `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')`. If unavailable, use a project-declared default; do not guess a mutation target. Re-read bookmarks, the working-copy parent, and selected files immediately before committing if anything may have changed. JJ has no Git staging/index step; preserve any pre-existing backend index state by not committing with Git.

## Message standards

**Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.**

Before composing each message, read the full Go guide at that URL and examine several recent commit subjects AND bodies. From the target workspace's absolute root, obtain the read-only backend with `jj git root`, then run `git --git-dir=<verified-backend> log -10 --format=%B` (or `GIT_DIR=$(jj git root) git log -10 --format=%B` from that root). Compare prefixes or package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Do not infer the pattern from a single example or the Go quotation below. Repository-local syntax established by project/user instructions and history always wins when it differs from Go guidance; apply compatible Go guidance to clarity, quality, and structure without replacing that syntax. If no history exists, use explicit project/user instructions and compatible Go guidance without inventing a precedent or imposing Conventional Commits.

These exact excerpts are **Go source guidance, not a mandatory repository template**:

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

> Notably, for the subject (the first line of description):
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).

> For the body (the rest of the description):
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.

Do not add model, harness, or skill authorship attribution.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to commit** — if `jj status` and file state show no pending changes, report that and stop. Inspect untracked/ignored content separately when relevant; do not mistake excluded or ignored files for committed content. Stop and report conflicts before committing.

2. **Bookmark first** — JJ has no checked-out branch or detached HEAD. If no suitable feature bookmark identifies this work, or only the verified default bookmark does, derive a feature bookmark name from the change content and create it with `jj bookmark create <non-conflicting-name> -r @`, then re-read bookmarks. Do not ask again for this routine commit-only step. Do not move the default or unrelated bookmarks. If the derived name exists, choose a non-conflicting suffix.

3. **Convention** — perform the full runtime read-and-compare process in Message standards. User/project instructions take precedence; do not choose a fixed type, scope, prefix, or message syntax in advance.

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate changes (file level only, 2–3 max, no interactive hunk selection). If ambiguous, one change.

5. **Message** — describe the outcome (what is now possible or fixed), not merely the file list, using the dynamically established standards. Include motivation or trade-offs when not obvious from the subject. When a plan Implementation Unit ID is already in hand for this change (conversation, caller, or files belong to one unit), include that U-ID in a position and form compatible with the observed repository conventions. Do not hunt for a plan. Omit when the change spans units, the unit is unclear, or no plan is in hand. No fixed subject/body example prescribes the result.

6. **Commit named files** — honor `exclude:<paths>`: those files stay in the pending working copy no matter what else changed; report that they were left out. Write the full dynamically composed message to a file under `<absolute-workspace-root>/.tmp/`, never OS-global temporary storage. Read it back, then pass its complete contents as one literal `--message` argument using program-and-argument support or safe shell quoting; never evaluate message text as shell code.

```text
jj commit --message "<message composed from the standards above>" -- file1 file2 file3
```

Run from the target workspace's absolute root. Use verified repository-relative paths (for example `src/example.py`), not workspace-prefixed paths. JJ snapshots automatically; there is no staging step. The explicit path list is required because a bare `jj commit` selects all pending changes. Selected files remain in the committed change; other files move to the new working-copy change on top. Verify the resulting diff and selected/excluded files after each group. `jj commit` leaves bookmarks on the committed change; for additional groups, advance only this run's verified feature bookmark to each resulting committed change with `jj bookmark set <verified-feature-name> -r <verified-committed-change-id>`, never the new empty working-copy tip or an unrelated bookmark.

7. **Confirm** — `jj status` and inspect the committed changes; report change/commit IDs and subjects, plus excluded or unrelated pending files. Do not require an unrelated user's work to become clean.

JJ guidance: https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/git-command-table/ ; command contracts: https://docs.jj-vcs.dev/latest/cli-reference/ . Use Git only for read-only historical-message inspection above, not commit or workspace mutations.
