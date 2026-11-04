---
name: ce-commit
description: Create a local Jujutsu commit with a clear, value-communicating message. Use when the user asks to commit/save selected changes with a repo-appropriate message.
---

# Local Commit

Create well-crafted local commit(s) from the current working tree. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and `jj status` shows none of those changes remaining in the working-copy change. **Stop when:** there are no selected changes to commit.

## Context

Resolve the absolute target workspace root with `jj workspace root` from the target directory. Run every subsequent JJ command with the shell tool's working directory set to that absolute root (or Python `subprocess.run([...], cwd=workspace_root)`). Gather each command as its own tool call; interpret empty or non-zero results rather than hiding failures. Never invoke the Git executable. JJ has no staging index; inspect the working-copy change and explicitly select paths instead.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Changes, conflicts, and untracked-file notices | Not a JJ workspace — stop |
| `jj diff --summary` | Working-copy file changes | No tracked changes; still inspect untracked/ignored content |
| `jj log --no-graph -r '@'` | Current change and associated bookmarks | Resolve errors before proceeding |
| `jj bookmark list` | Local/remote bookmark context | No bookmark is normal in JJ |

Resolve the default branch from verified repository configuration or remote-bookmark context; do not guess `main`. If GitHub is needed, run `GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` from the absolute target root. That environment is required for repository-scoped `gh`; it does not authorize direct Git commands. If the default cannot be resolved, report uncertainty before changing bookmarks.

Treat this as a snapshot. Re-read the working-copy revision, bookmarks, selected paths, and exclusions immediately before committing if anything may have changed. JJ guidance: https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/git-command-table/ .

## Workflow

0. **Gather** — run the Context commands, inspect the actual diff, and resolve the task's history anchor before composing a message. Use the verified current change when it contains relevant existing history, or its verified parent/head when `@` is an empty tip; for task-specific work use the verified task head. Do not substitute an unrelated default branch or replace a reviewed base/head range with a style sample.

1. **Nothing to commit** — inspect `jj status`, the diff, and untracked-file notices. If no selected changes exist, report that and stop. Ignored or untracked files are not proven safe by an empty diff. Do not start tracking unrelated content.

2. **Bookmark first** — JJ does not require a branch or have a detached-HEAD problem. Still preserve this workflow's feature-reference safeguard: if the work lacks a task bookmark or is associated only with the default bookmark, create a non-conflicting feature bookmark derived from the change content using `jj bookmark create <name> -r @`. Do not move the default or existing unrelated bookmarks. Re-read the bookmark state. Stop on ambiguous ownership rather than rewriting another person's reference.

3. **Convention and source guidance** — before composing, read the full https://go.dev/wiki/CommitMessage guide and inspect several recent subjects **and bodies**, not just one-line summaries, from the verified history head:

   `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`

   Run this from the absolute target workspace root. Compare several messages for prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Repository-local instructions and the observed repository syntax always win over Go guidance. Apply compatible Go guidance to clarity, outcome, motivation, and structure without imposing Go or Conventional Commit syntax. If there is no history, use explicit project/user instructions and Go guidance without inventing a repository precedent.

   **Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.**

   The following are verbatim source excerpts. The Go example is illustrative source guidance, **not a mandatory repository template**:

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

4. **Logical commits** — if selected files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive hunk selection). If ambiguous, one commit.

5. **Message** — communicate the outcome, not merely a file list; explain motivation or trade-offs when needed. When a plan Implementation Unit ID is already in hand and the files belong to that unit, include that unit's ID in the repository-appropriate form determined above. Do not hunt for a plan; omit the ID for mixed or unclear units. Preserve human authorship credit when carrying someone else's work: copy recorded identities exactly and never guess an email. Follow explicit repository attribution policy where it differs from the Go guidance; otherwise record necessary human credit in the body rather than adding prohibited trailers. Do not add model, harness, or skill authorship attribution.

6. **Commit named paths** — never commit the entire working-copy change implicitly. Honor `exclude:<paths>`: those files stay outside these commits, and the report must say they were left out. Check that each selected path belongs to this logical group, and that there are no unresolved conflicts. Explicitly track only authorized untracked files if needed with `jj file track <named-paths>`; do not override ignore rules without authorization.

   Write the full dynamically composed message with the file-write tool to a unique file under `<absolute-workspace-root>/.tmp/`; ensure `.tmp/` is ignored in `.gitignore`. Use argument-based process execution to avoid shell interpolation of quotes, dollar signs, backticks, or multiline text. For example, a shell-launched Python process can read the message file and call:

   ```python
   message = Path(message_file).read_text()
   subprocess.run(["jj", "commit", "-m", message, "--", *selected_paths],
                  cwd=workspace_root, check=True)
   ```

   Here `workspace_root` and `message_file` are verified absolute paths, `selected_paths` contains explicit repository-relative file paths, and the message is composed from the standards above. Supply paths as literal filesets when filenames contain fileset syntax. Latest JJ's path-scoped `commit` keeps selected changes in the committed revision and moves the remaining changes to a new working-copy change. It does not move bookmarks forward: after each group, verify the resulting committed revision and feature bookmark; advance only the owned feature bookmark when needed, never the default or unrelated references. Reinspect remaining changes before the next group. This preserves excluded and unrelated work without a staging index.

7. **Confirm** — run `jj status` and inspect each created revision's full description and file diff. Verify only the selected paths landed and excluded/unrelated changes remain intact. Report commit IDs and subjects, remaining work, and exclusions. No push or PR.
