---
name: ce-commit
description: Create a local Jujutsu commit with a clear, repository-appropriate message. Use when the user asks to commit or save working-copy changes.
---

# Jujutsu Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, the topic bookmark identifies the last finalized change, and `jj status` confirms that only intentionally omitted changes remain in the working copy. **Stop when:** there is no eligible change to commit.

## Context

Resolve the target's absolute root with `jj workspace root`; if not in a JJ workspace, stop. Set the shell tool's working directory to that absolute root for all subsequent commands. Gather context with each command as its **own** shell tool call (program + args only). Do not chain commands or use shell substitution, pipes, or redirects. Interpret failures rather than suppressing them. See the [JJ command reference](https://docs.jj-vcs.dev/latest/cli-reference/) and [Git-to-JJ command table](https://docs.jj-vcs.dev/latest/git-command-table/) for the native equivalents.

| Command | Purpose |
| --- | --- |
| `jj --ignore-working-copy log -r '@ \| @- \| trunk()'` | Establish the recorded working-copy change, its parent(s), and the configured or inferred trunk before snapshotting. |
| `jj --ignore-working-copy bookmark list -r '@ \| @-'` | Identify local bookmarks that would be affected and any unambiguous topic bookmark at the current change or its parent. |
| `jj status` | After the bookmark safety check, snapshot normal file changes and check for conflicts, snapshot warnings, or no work. |
| `jj diff --summary` and `jj diff` | Inspect changed paths and content; record the owned scope and distinguish unrelated changes. |

JJ has no index or checked-out branch. Protect `main`, `master`, and the verified repository default bookmark by local name. Use project instructions and local JJ evidence to identify the default; `trunk()` is a candidate, not proof of an otherwise unknown remote default. If needed, in the target root run `jj git root` and set `GIT_DIR` to that result for `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. If the default cannot be verified and it is unclear whether a bookmark is safe to update, do not update it. If a protected or unrelated bookmark points directly at `@`, a snapshot or commit can rewrite its target; stop before snapshotting rather than modifying it. A default bookmark on `@-` is normal and is not moved by this workflow.

## Workflow

0. **Gather** — use the Context checks to identify the workspace, pending work, and bookmark state.

1. **Nothing to commit** — if `jj status` and the diff show no eligible changes, report that and stop. JJ normally snapshots new non-ignored files; don't assume a clean diff proves there were no intentionally untracked files or snapshot failures. Address snapshot warnings and conflicts before committing; do not silently include ignored or unrelated files.

2. **Select a topic bookmark first** — reuse only an unambiguous, editable local topic bookmark at `@` or `@-` that belongs to this work. Otherwise choose an unused topic name from the change content, checking for local and remote collisions with `jj bookmark list --all-remotes "exact:<topic>"` and choosing a non-conflicting suffix if needed. Do not move a default, remote, or unrelated bookmark. Normal topic creation is part of the commit-only request; do not ask again. Record the intended bookmark and its initial state so the final update can be verified.

3. **Learn the repository's message standard** — before composing a message, read the full [Go CommitMessage guide](https://go.dev/wiki/CommitMessage) and compare several recent full commit subjects **and** bodies from the verified history head for this task. Resolve that head from the actual work: normally the parent of the pending change, or an explicitly relevant verified task/topic head. Use its exact revision rather than an assumed default branch, and don't use a style sample as a substitute for a reviewed base/head range. From the absolute target root, run `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'commit_id ++ "\n" ++ description ++ "\n"'` with the resolved revision substituted. If the first sample is mostly subject-only, extend it on the same ancestry to compare multiple bodies when available. Compare prefixes or package names, casing, verb tense, subject/body separation, wrapping, issue references, and trailers. If no usable history exists, follow explicit user/project instructions and compatible Go guidance without inventing precedent.

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max; no hunk splitting). If ambiguous, make one commit. Honor `exclude:<paths>`: those paths stay out of every finalized commit, and report that they were left out. Keep unrelated changes out of the explicit path list even if JJ already snapshotted them.

5. **Message** — Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

   Repository-local syntax established by project instructions and history always wins over the Go guidance. Honor an explicit user override. Apply compatible Go guidance to clarity and structure: state what is now possible or fixed rather than listing files, and explain motivation or trade-offs when they are not obvious. If a single plan Implementation Unit ID is already known for this commit, include it using the repository's style; do not hunt for a plan. Omit it when no unit is known or the change spans units. Credit people whose ported or applied work would otherwise land without their name, including human co-authors identified in the source. Use the repository's convention for credit and copy recorded identities exactly. Never guess an email; use names in prose if necessary.

   **Source guidance from the Go wiki, not a repository template:**

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

6. **Commit exactly the named files** — recheck status, bookmark targets, and the intended diff immediately before committing each group. Stop if the scope changed or if finalizing `@` would overwrite an unrelated existing description or change a protected bookmark. Preview the exact filesets with `jj diff --summary -- <exact-file-filesets>`, then run `jj commit -m "<message composed from the standards above>" -- <exact-file-filesets>`. Use one literal [`file:"path"` fileset](https://docs.jj-vcs.dev/latest/filesets/) per named, workspace-relative file, including both sides of a rename when intended. Never use a broad pattern or omit the filesets: bare `jj commit` would take all of `@`. With filesets, JJ finalizes the selected changes and leaves the remaining changes in a new working-copy change. Verify each finalized change and its path list before proceeding.

   Pass the full message as one literal argument without shell interpolation. If the tool only accepts shell text, write the message with the file tool under the target workspace's ignored `.tmp/` and use a local Python `subprocess.run` argument list (no shell, `cwd` set to the absolute root) to read the file as UTF-8 and pass its contents to `-m`. This preserves multiline content, quotes, dollar signs, and backticks.

7. **Confirm** — point the selected topic bookmark at the verified last finalized commit, not at the new `@`: use `jj bookmark create <topic> -r <verified-final-id>` for a new topic or `jj bookmark move <topic> --to <verified-final-id>` for a previously selected topic if its checked target has not moved unexpectedly and the move is a fast-forward. Skip the move if already correct. Verify the bookmark target and `jj status`; report each finalized commit's hash and subject, the topic bookmark, and any intentionally excluded paths or unresolved blockers.
