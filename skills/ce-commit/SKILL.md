---
name: ce-commit
description: Create local JJ commits with clear, value-communicating messages. Use when the user asks to commit/save changes with a repo-appropriate message.
---

# Local Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow. Use native JJ only; never invoke the Git executable, including for inspection or helpers.

**Done when:** each requested logical change is committed with an explicit file list and a message stating its outcome, and those changes no longer remain in the working-copy diff. **Stop when:** there are no requested changes to commit. Preserve unrelated work.

## Context

Establish the absolute target workspace root from the invocation or working directory and verify it with `jj root`. Every JJ subprocess must run at that absolute root, including history inspection. In shell calls use `(cd "$workspace_root" && jj ...)`; do not substitute `-R` for the working directory. Run inspection calls separately and interpret non-zero results rather than suppressing them.

Inspect `jj status`, `jj diff`, `jj log -r '@ | @-'`, and `jj bookmark list` at that root. Record the verified current change and its parent(s), conflicts, changed paths, bookmark targets, and any existing description. Inspect repository instructions for message conventions. Determine the task's verified history head from this evidence: normally the current change's parent for a new working-copy change, or the actual task/source head supplied and verified by the caller. Do not substitute a hardcoded default branch. If ambiguous, stop for clarification.

Treat inspection as a snapshot. Re-read the current change, bookmarks, and selected file diff immediately before committing if anything may have changed. JJ has no staging/index workflow; never translate an old staged set into permission to include unrelated files.

## Workflow

1. **Nothing to commit** — inspect both status and diff, including new/untracked or ignored paths. If no requested changes remain, report that and stop. Never silently add ignored files or treat unrelated changes as part of this request. Stop on conflicts or uncertain ownership.

2. **Preserve the task reference** — use an existing verified feature bookmark when appropriate. If the task has none, choose a meaningful non-conflicting feature bookmark derived from the change content. Never move a default, shared, remote, or unrelated bookmark merely to commit local work. Record original targets and preserve existing user descriptions and recovery references. JJ does not require a checkout/branch switch to commit.

3. **Read and compare message standards** — read the full https://go.dev/wiki/CommitMessage before composing, then inspect multiple recent subjects **and bodies** with `jj log` from the absolute target root, anchored to the verified task history head. For example, use a bounded ancestor revision set for that verified head and `--no-graph -T 'description ++ "\n\n"'`; verify the selected revisions belong to the task's history. Compare package/prefix syntax, casing, tense, subject/body structure, wrapping, and issue references. Do not infer conventions from subject-only output.

   Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

   Repository-local syntax always wins. Explicit user requirements and project instructions govern; use compatible Go guidance where they leave room. With no history, state that limitation and use explicit project/user requirements plus compatible Go guidance, without inventing precedent. If the full guide cannot be read, report the blocker rather than claiming that excerpts are the full guide. Do not impose Conventional Commits, package prefixes, a fixed tense, or another fallback template.

   ### Go source guidance — examples, not a repository template

   The following excerpts are source guidance, not mandatory local syntax. Read the full guide as required above; reconcile these examples with the repository's actual conventions.

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

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max). If ambiguous, one commit. Do not split a file's hunks or rewrite existing commits without authorization.

5. **Message semantics** — name the outcome, not just the file list; explain motivation or trade-offs when useful. When a plan Implementation Unit ID is already in hand and clearly applies to this commit, retain that traceability in a form compatible with local conventions. Do not hunt for a plan or impose a fixed suffix; omit the ID if it is unclear or spans units. Preserve real human authorship credit for carried work using verified identities and repository policy; never guess an email. When trailers are inappropriate under the governing standards, credit people in the body instead. Do not add model/harness authorship or attribution.

6. **Commit named files only** — honor `exclude:<paths>`: leave those paths uncommitted and report them. Use explicit literal file selections (for example JJ `file:` filesets, with shell quoting) so broad filesets cannot capture unrelated work. Write the complete composed message with a file-write tool into an owned file under the absolute workspace's `.tmp/`; never use system temporary storage. Keep that message file and all unrelated scratch outside the selected paths, including when the task changes `.tmp/` itself.

   For each group, pass the message file's literal contents and the explicit owned selections as separate arguments through Python (with `message_file`, `explicit_filesets`, and the absolute `workspace_root` already verified):

   ```python
   from pathlib import Path
   import subprocess

   subprocess.run(['jj', 'commit', '--message', Path(message_file).read_text(), *explicit_filesets], cwd=workspace_root, check=True)
   ```

   Do not use a bare commit that sweeps in all changes. This creates the described commit and leaves unselected changes in the new working copy; there is no staging call. Do not use shell interpolation to build message text. Remove only the owned temporary message file on both success and failure, without broad cleanup.

   After verifying the resulting commit, create the chosen feature bookmark at that exact commit, or advance only the verified task-owned bookmark when authorized. Check the actual result rather than assuming bookmark auto-advance behavior. If committing or bookmark placement fails, retain the recorded identifiers and report the partial state; do not reset, discard, or blindly retry.

7. **Confirm** — inspect `jj status`, the remaining working-copy diff, the new commits' full descriptions, selected file changes, and feature bookmark targets from the absolute root. Report commit/change identifiers and subjects, excluded or unrelated paths left behind, and any remaining blockers. Do not claim the whole workspace is clean when only the requested changes were committed.
