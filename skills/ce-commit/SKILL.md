---
name: ce-commit
description: Create a local Jujutsu commit with a clear, value-communicating message. Use when the user asks to commit/save selected changes with a repo-appropriate message.
---

# Jujutsu Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and those changes are absent from the remaining working-copy diff. **Stop when:** there are no eligible changes to commit. Preserve unrelated work.

## Context

Resolve the target workspace's absolute root with `jj workspace root`, then set every JJ command's working directory to that absolute root (shell tool `workdir`, or `subprocess.run(..., cwd=workspace_root)`). `jj -R` alone is insufficient. Run each command as its own tool call; interpret errors rather than suppressing them. Never invoke the Git executable.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Working-copy changes and conflicts | Not a JJ workspace — stop |
| `jj diff -r @` | Current change, including newly tracked files | Empty = no current diff; also inspect status and untracked files |
| `jj log --no-graph -r '@ | @-' -T 'commit_id ++ " " ++ bookmarks ++ "\n" ++ description ++ "\n"'` | Working-copy identity, parent, bookmarks and descriptions | Resolve errors before proceeding |
| `jj bookmark list` | Local and remote-tracking bookmark context | No bookmarks is valid; do not invent a remote/default target |

Use `jj git remote list` when remote identity is needed. Resolve the actual default bookmark from project instructions and verified remote metadata, not an assumed `main`. If GitHub metadata is needed, invoke repository-scoped `gh` from the absolute workspace root with `GIT_DIR=$(jj git root)` (or obtain that value first and pass it in the tool environment). No push or fetch is implied.

Treat this as a snapshot. Re-read status, working-copy identity and bookmarks immediately before committing if anything may have changed. Inspect ignored/untracked content separately where relevant: JJ does not automatically track ignored or otherwise excluded files. Never add unrelated files merely to make status clean.

## Workflow

0. **Gather** — run the Context commands, then continue. Stop for unresolved conflicts or ambiguous ownership instead of discarding work.

1. **Nothing to commit** — if there are no eligible modified, added, deleted or intentionally untracked files, report that and stop. Do not use the diff alone to dismiss untracked work. Explicitly requested new files must be tracked with `jj file track <named-paths>` if necessary; never track everything indiscriminately.

2. **Bookmark first** — JJ does not require a checked-out branch. Ensure the selected commit will have a non-default local feature bookmark, not just the default bookmark or an unreferenced change. Derive its name from the change content, check existing bookmarks, and choose a non-conflicting suffix when necessary. Create a new bookmark at `@` using `jj bookmark create <name> -r @`; do not move an existing default, remote, recovery or unrelated bookmark. Do not ask for this routine commit-only safety step. Before each subsequent logical commit, verify the feature bookmark's current target; advance only this task-owned bookmark to the newly completed commit as needed, preserving all unrelated bookmarks.

3. **Convention and source guidance** — before composing any message, read the full https://go.dev/wiki/CommitMessage at runtime and examine several recent complete subjects AND bodies using JJ from the target workspace's absolute root. Resolve and verify the relevant history head from the actual task and repository: normally the parent/history underlying this work, or the task's verified source head. An empty `@` is not the history anchor merely because it is current. Do not hardcode `main@origin`, substitute a style sample for a reviewed base/head range, or infer a convention from one commit. After resolving the actual head, for example:

   ```text
   jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'
   ```

   Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping and issue-reference placement across several complete descriptions. Repository-local syntax established by project/user instructions and this history ALWAYS wins over conflicting Go guidance. Apply compatible Go guidance to clarity, quality and structure within that observed pattern. If no history exists, use explicit project/user instructions and Go guidance without inventing a precedent.

   **Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.**

   The following are verbatim **source guidance**, not a mandatory repository template or a message to emit:

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

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive hunk selection). If ambiguous, one commit.

5. **Message** — dynamically compose the subject to name the outcome (what is now possible or fixed), not merely the file list, using the standards above. Include a body when motivation or trade-offs are not obvious. When a plan Implementation Unit ID is already in hand (conversation, caller, or the files belong to one unit), record that ID in the repository's observed syntax. Do not hunt for a plan; omit it when the commit spans units, the unit is unclear, or no plan is in hand. When carrying another person's work that will not otherwise land under their name, preserve their exact recorded human authorship credit in the body, consistent with local instructions; never guess identities or email addresses. Do not add creator/model/harness attribution or Co-authored-by/Assisted-by trailers.

6. **Commit named files only** — honor `exclude:<paths>`: those paths remain outside every commit group regardless of other changes, and the report must say they were left out. Review the exact named paths and current diff immediately before each commit. Use root-relative paths such as `src/example.py`, not a workspace-prefixed path. Pass the full dynamically composed message as a single literal tool argument to `--message`, without shell interpolation:

   ```text
   jj commit --message "<message composed from the standards above>" -- file1 file2 file3
   ```

   With explicit filesets, JJ keeps only the selected changes in the completed commit and moves remaining changes into a new working-copy child. There is no Git staging/index operation. Never use a bare `jj commit` or `jj describe` to include unrelated changes. For exact filenames containing fileset syntax, use literal fileset expressions rather than broadening selection. If message scratch storage is needed, use the target workspace's local `.tmp/`, ensure `.tmp/` is ignored, and never include that scratch file in the commit. Preserve existing ignored/untracked content.

   Verify the completed parent's exact file scope and full description with `jj diff -r @-` and `jj log --no-graph -r @- -T 'commit_id ++ "\n" ++ description ++ "\n"'`. Verify unrelated and excluded changes remain in `@`; do not discard them to obtain a clean status. For later groups, move only the task-owned feature bookmark to the verified completed revision with `jj bookmark set <name> -r <verified-completed-revision>` when needed. Stop if concurrent changes make scope or identity uncertain.

7. **Confirm** — run `jj status`; report completed commit IDs and subjects, feature bookmark, and unrelated/excluded remaining work. Do not push or create a PR.

Native command semantics: https://docs.jj-vcs.dev/latest/cli-reference/#jj-commit ; https://docs.jj-vcs.dev/latest/git-command-table/ ; https://docs.jj-vcs.dev/latest/git-experts/ .
