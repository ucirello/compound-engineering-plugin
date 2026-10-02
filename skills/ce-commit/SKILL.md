---
name: ce-commit
description: Create a Jujutsu change with a clear, value-communicating description. Use when the user asks to commit/save changes with a repo-appropriate message.
---

# Commit Changes

Create well-crafted local change(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is recorded with an explicit file list and an outcome-oriented description, and none of those changes remain in the working-copy diff. **Stop when:** the working-copy change is empty (nothing to commit).

## Context

Run each command as its own shell tool call with its working directory set to the target workspace's **absolute root**. `jj -R` alone does not change cwd. Do not join commands with shell syntax where the shell is Windows PowerShell. A non-zero exit is a normal state to interpret, not a failure to suppress.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj workspace root` | Resolve the absolute workspace root | Not a JJ repo — stop |
| `jj status` | Working-copy state, including newly tracked files | Resolve errors before continuing |
| `jj diff --summary` | Changed files in `@` | Empty working-copy change |
| `jj log --no-graph -r '@ | @-'` | Current change, parent, and bookmarks | A bookmark need not be attached to `@` |
| `jj bookmark list` | Local and remote bookmarks | No bookmarks yet |
| `jj git root` | Backend for read-only history and GitHub calls | No Git backend — use JJ history and report the limitation |
| `git log -10 --format=%B` | Recent subjects AND bodies | No history — do not invent precedent |
| `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | Remote default branch | Unavailable — use project configuration, else `main` |

For history and repository-scoped GitHub calls, obtain the backend with `jj git root` in the target workspace and set `GIT_DIR` to that returned path in the tool's environment. POSIX equivalents are `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)` and `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')`. Git is only a read-only history fallback here, never a staging or commit tool.

Treat this as a snapshot. Re-read bookmarks and changed files immediately before recording if anything may have changed. Compare against the bare default bookmark name, not a remote-qualified name. Inspect both `@` and `@-`: an empty working-copy tip can sit above a bookmarked parent.

JJ references: https://docs.jj-vcs.dev/latest/git-experts/ , https://docs.jj-vcs.dev/latest/git-command-table/ , https://docs.jj-vcs.dev/latest/cli-reference/ , https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace . Consult targeted `jj help` for installed command syntax.

## Workflow

0. **Gather** — run every Context command above (own tool call each), then continue.

1. **Nothing to commit** — if the working-copy change is empty, report that and stop. Inspect `jj status` as well as the diff: ignored files are not recorded automatically, and conflicts must be resolved before continuing.

2. **Bookmark first** — if no feature bookmark identifies this work, or the relevant bookmark is the default branch, create a feature bookmark derived from the change content with `jj bookmark create <name> -r @`, then re-read it. Do not ask — commit-only must not leave work identified only by the default bookmark or without a feature bookmark. If the derived name exists, pick a non-conflicting suffix. Do not move the default bookmark.

3. **Convention and message** — before composing any description, read the **full** https://go.dev/wiki/CommitMessage and compare several recent commit subjects **and bodies** from the Context history call. Establish the actual repository pattern for prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement, not just a single example.

   **Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.**

   Repository-local syntax established by project/user instructions and history **always wins** when it differs from Go guidance. Apply compatible Go guidance to clarity, quality, and structure within that pattern; do not impose Go package prefixes or a Conventional Commit template. With no history, follow explicit project/user instructions and compatible Go guidance without inventing a repository precedent.

   The following verbatim excerpts are **Go source guidance, not a mandatory repository template**:

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

   Communicate the outcome (what is now possible or fixed), not merely the file list. Include a body when motivation or trade-offs are not obvious from the subject. When a plan Implementation Unit ID is already in hand for this change (conversation, caller, or files belonging to one unit), include that U-ID in the repository-appropriate form. Do not hunt for a plan. Omit when the change spans units, the unit is unclear, or no plan is in hand. Do not add model/harness authorship or attribution.

4. **Logical changes** — if changed files clearly split into distinct concerns, record separate changes (file level only, 2–3 max, no interactive hunk selection). If ambiguous, one change.

5. **Record named files only** — honor `exclude:<paths>` when the invocation carries it: those files remain in the working-copy change no matter what else changed; say in the report that they were left out. JJ snapshots files without an index, so select the exact named file group using `jj split`, never all files implicitly. Write each full runtime-composed message with the file-write tool under `<absolute-workspace-root>/.tmp/` (create that directory and ensure `.tmp/` is ignored; outside a JJ repo use local `.tmp/`, never OS temporary storage). Read that file as literal text and pass it as one argument:

   ```text
   jj split -r @ --message <full message composed from the standards above> -- file1 file2 file3
   ```

   The placeholder is one literal argument, not shell-expanded text or a fixed message to emit. Do not interpolate a message containing `$`, quotes, backticks, or newlines into shell source. Use safe argument passing; when unavailable, use the local `.tmp/` message file and a small shell/Python invocation that reads it and calls `subprocess.run(["jj", "split", "-r", "@", "--message", message, "--", ...named_files], cwd=workspace_root, check=True)`.

   The explicit file list is required: splitting the selected files records only that group and leaves excluded and unrelated work in the remaining `@`. Re-read revision IDs after every split; do not assume they remain unchanged. Move the feature bookmark to the last recorded group using `jj bookmark set <name> -r <recorded-change-id>`, leaving the remaining working-copy change above it. Do not discard unrelated changes or describe them as committed.

6. **Confirm** — run `jj status`, inspect the remaining `jj diff --summary`, and inspect recorded changes with `jj log`. Report commit/change IDs and subjects, named files recorded, and excluded or unrelated work left over. An empty working-copy tip after recording is normal in JJ.
