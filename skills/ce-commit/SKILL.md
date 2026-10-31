---
name: ce-commit
description: Create a local JJ commit with a clear, value-communicating message. Use when the user asks to commit/save selected working-copy changes with a repo-appropriate message.
---

# Local Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and `jj status` shows none of those changes remaining. **Stop when:** there are no selected changes to commit.

## Context

Resolve the absolute target workspace root with `jj workspace root`, then run every JJ command with that absolute root as the shell tool's working directory (or subprocess `cwd`). Use separate tool calls for context commands; interpret non-zero exits rather than suppressing them. Never invoke Git directly. JJ has no staging area: preserve all unrelated working-copy changes and any colocated index state.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Working-copy state and conflicts | Not a JJ workspace — stop |
| `jj diff --summary` | Changed paths in the current change | No selected differences |
| `jj bookmark list` | Local and remote bookmark context | No bookmark is valid JJ state |
| `jj log --no-graph -r '@ | @-'` | Identify the working change and its parent | Resolve history before proceeding |

Resolve the actual relevant history head from the task, current change's ancestry, and verified bookmark context. Do not assume a default branch or silently substitute `main@origin`. If remote default-branch information is genuinely needed, run repository-scoped `gh` from the absolute target root with `GIT_DIR=$(jj git root)`; unavailable or ambiguous information is a reason to stop that decision, not guess a branch.

Read several recent **complete subjects and bodies**, not an oneline log. From the absolute target root, substitute the verified history head into:

```bash
jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'
```

Treat context as a snapshot. Re-read status, selected paths, current revision and bookmarks immediately before committing if anything may have changed.

## Workflow

0. **Gather** — collect the context above. Stop for unresolved conflicts or ambiguous ownership rather than including unrelated work.

1. **Nothing to commit** — if no selected changed paths remain, report that and stop. Inspect `jj status`, including untracked-file warnings, rather than relying on diff alone. Never silently force-track ignored files; report selected files that JJ has not tracked.

2. **Bookmark first** — preserve the existing feature bookmark when applicable. If work is on a verified default bookmark, or has no suitable feature bookmark, create a non-conflicting feature bookmark derived from the change content with `jj bookmark create <name> -r @`. Do not move the default bookmark. A bookmark-free change is normal JJ state, not a detached-HEAD error. Verify the resulting bookmark and its target; suffix a conflicting name rather than replacing it. After each commit, explicitly keep the feature bookmark on the intended completed change, never on excluded work.

3. **Convention and message** — before composition, read the full https://go.dev/wiki/CommitMessage and the recent complete messages above. **Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.** Repository-local syntax established by project/user instructions and history ALWAYS wins over differing Go guidance. Compare several messages for package/prefix, casing, tense, subject/body separation, wrapping and issue-reference placement. Apply compatible Go guidance to clarity and structure within that observed pattern. If history is absent, follow explicit project/user instructions and compatible Go guidance without inventing precedent. Do not impose Conventional Commits, fixed types, prefixes or a fixed message template.

   The following are verbatim Go source excerpts, **illustrative guidance subordinate to the runtime repository pattern, not a mandatory repository template**:

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

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive hunk selection). If ambiguous, one commit. Honor `exclude:<paths>`: those paths remain uncommitted and must be called out in the report. Select explicit literal file paths, not broad filesets that could capture excluded work.

5. **Semantic content** — communicate the outcome, adding motivation or trade-offs when useful under the observed message pattern. When an Implementation Unit ID is already in hand and this commit belongs to exactly that unit, include that identity in the repository-appropriate form; do not hunt for a plan or invent a unit. Preserve human authorship credit when carrying someone else's work: use recorded identities exactly, never guess emails, and follow explicit repository/user attribution requirements. Otherwise describe provenance in the body rather than automatically adding trailers contrary to the guide. Do not add assistant/model/harness attribution.

6. **Commit named files** — JJ snapshots tracked work automatically, so do not stage files. To commit exactly one group and leave all other changes in the new working copy, run from the absolute target root:

```bash
jj commit -m "<message composed from the standards above>" -- file1 file2 file3
```

   Pass the full message as a literal tool argument, not shell-interpolated content. If the caller instead requires describing an already-isolated change without creating a child, verify its entire scope first and use:

```bash
jj describe -m "<message composed from the standards above>"
```

   Never use the describe-only path for a mixed change containing exclusions. `jj commit` with named paths keeps selected changes in the completed parent and moves remaining changes to the new working copy; verify both revisions and move only the intended feature bookmark to the completed parent. Never move a default or unrelated bookmark. If a message file is needed by the tool interface, store it under the absolute workspace's ignored `.tmp/` directory, never outside the repository or in an OS-global temporary directory.

7. **Confirm** — run `jj status`, inspect each completed change's full description and changed paths, and verify feature-bookmark targets. Report commit/change IDs and subjects, remaining excluded or unrelated paths, and any untracked-file warnings. Do not claim the entire workspace is clean when intentionally preserved work remains.

Native JJ reference: https://docs.jj-vcs.dev/latest/cli-reference/ (`jj commit`, `jj describe`, `jj bookmark`, `jj log`).
