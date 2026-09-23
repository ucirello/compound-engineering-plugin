---
name: ce-commit
description: Create a local JJ commit with a clear, value-communicating message. Use when the user asks to commit/save working-copy changes with a repo-appropriate message.
---

# JJ Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, the feature bookmark names the last completed commit, and `jj status` shows only changes intentionally left out. **Stop when:** there are no eligible working-copy changes to commit.

## Context

Gather context with each command as its **own** shell tool call (program + args only). Do **not** join with `;`, `&&`, `||`, pipes, `$(...)`, or redirects — that syntax fails under Windows PowerShell. A non-zero exit is a normal state to interpret, not a failure to suppress.

Use the absolute workspace root as the working directory for every JJ subprocess. Discover it with `jj workspace root` from the known absolute workspace directory; stop if unavailable. Do not substitute `-R` or inspect repository internals. If another workspace is relevant, discover membership and roots through `jj workspace list` and `jj workspace root --name <name>`.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Working-copy state, including untracked files | Not a JJ workspace — stop |
| `jj diff -r @` | Current change contents | Empty = no snapshotted changes |
| `jj bookmark list --all-remotes` | Feature and default bookmark positions | No bookmarks yet; derive a new feature name |
| `jj log -r 'ancestors(@, 10)' --no-graph` | Recent message style and current/parent revisions | No substantive history yet |

Treat this as a snapshot. Re-read status and bookmarks immediately before committing if anything may have changed. JJ has no staging area: the explicit file list defines the commit, and unselected changes remain in the next working-copy change.

**Default bookmark:** use the project's configured default; otherwise query `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`, falling back to `main`. For every `gh` call, first obtain `jj git root` in this workspace, then set the subprocess environment's `GIT_DIR` to that output. Compare bare bookmark names, not remote-qualified names.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to commit** — if there are no eligible changes, report that and stop. Do not use the diff alone as cleanliness: status may report untracked files that were not snapshotted. Resolve any tracking limit for intended files explicitly before committing; do not silently omit them.

2. **Feature bookmark first** — use an unambiguous task feature bookmark at `@` or its parent `@-`. If none exists, create one from the change content with `jj bookmark create <name> -r @`, choosing a non-conflicting suffix when needed. Do not move the default bookmark. Stop rather than rewrite a published or protected current revision. Re-read bookmark positions after creation. JJ has no checked-out branch or detached HEAD; bookmark selection must come from these positions and task context, not a guessed current branch.

3. **Convention** — read https://go.dev/wiki/CommitMessage before composing the message.

   Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

   The history command named in that policy refers to history inspected using `jj log` in this JJ workflow; never execute Git. Runtime project instructions and history syntax override the Go guidance; an explicit user override wins. If history is absent, use the Go guidance without imposing a fixed prefix or template.

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive hunk selection). If ambiguous, one commit.

5. **Message** — communicate the outcome, not just the file list, and explain motivation or trade-offs when they are not obvious. Preserve relevant issue/PR references. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or the files belong to one unit), include that unit's U-ID using the applicable message standards. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand.

6. **Commit named files** — honor `exclude:<paths>` when the invocation carries it: those files remain outside the completed commits no matter what else changed; say in the report that they were left out. Never omit the explicit file list or select the entire workspace. Write `<message composed from the standards above>` with your file-write tool to a unique file under the absolute workspace root's `.tmp/commit/`. Exclude that scratch directory from the commit. Run `scripts/commit.py` from this skill using its absolute path, the absolute workspace root, the absolute message-file path, and the named workspace-relative files:

```bash
python3 "<absolute-skill-directory>/scripts/commit.py" "<absolute-workspace-root>" "<absolute-message-file>" "<selected-file>" "<another-selected-file>"
```

The helper passes the message as a literal subprocess argument without a shell, preserving dollar signs, quotes, backticks, and multi-line bodies. It supplies exact file filesets to `jj commit`; selected changes stay in the completed commit, while unselected changes move to the new `@`. After each successful commit, move only the selected feature bookmark with `jj bookmark set <name> -r @-`. The completed commit is `@-`, even when the new `@` is empty. Stop on failure before attempting another group.

7. **Confirm** — run `jj status`, inspect each completed commit's diff against its named file list and exclusions, and check the feature bookmark position. Report commit IDs and subjects, plus any changes left out.
