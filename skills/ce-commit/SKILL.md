---
name: ce-commit
description: Create a JJ commit with a clear, value-communicating message. Use when the user asks to commit/save changes with a repo-appropriate message.
---

# JJ Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and `jj status` shows none of those changes remaining. **Stop when:** there are no changes to commit.

## Context

Run every JJ command with the shell tool's working directory set to the target workspace's **absolute root** (`workspace_root`), not with `jj -R` alone. Resolve that root with `jj workspace root` from the target directory first. Make each context command its own call. A non-zero exit is a normal state to interpret, not a failure to suppress. Never invoke the Git executable.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Working-copy state, including untracked/ignored-file notices | Not a JJ workspace — stop |
| `jj diff --summary` | Changed paths in the current change | Empty change, not proof that untracked files are absent |
| `jj log --no-graph -r '@ | @-'` | Current change and parent, bookmarks and conflicts | Resolve errors before continuing |
| `jj bookmark list` | Local and remote bookmark context | No bookmarks is valid in JJ |

Treat this as a snapshot. Re-read current change, bookmarks, and changed paths immediately before committing if anything may have changed. Inspect untracked and ignored content as well; do not add excluded or unrelated files merely to obtain a clean status. Honor repository tracking policy and explicit user scope.

Determine the actual task's history head from these facts and project instructions: the current change if it already contains relevant described history, or its verified parent/task bookmark when `@` is a fresh empty change. Do not assume a default remote bookmark. Resolve the repository's default bookmark from configured remote/project information only if needed; no guessed default is required to commit.

## Workflow

0. **Gather** — run every Context command above, then continue.

1. **Nothing to commit** — if status, diff, and untracked-file inspection show no in-scope changes, report that and stop. A diff alone does not establish cleanliness. Conflicts or uncertain ownership require a safe stop rather than a reset or discard.

2. **Bookmark first** — JJ does not require an attached branch. Still preserve the commit-only workflow's named feature reference: if no task bookmark exists, or only a default bookmark identifies this work, create a non-conflicting feature bookmark derived from the change content with `jj bookmark create <name> -r @`, then verify it. Do not move the default or unrelated bookmarks. If the name exists, choose a non-conflicting suffix. Record the task bookmark and its intended final in-scope commit; after committing, advance only that bookmark to the verified result if necessary, never to the residual working-copy change containing unrelated work.

3. **Convention and message** — the strongest instruction is:

   "Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards."

   Before composing, read the **full** https://go.dev/wiki/CommitMessage at runtime. From the target workspace's absolute root, inspect several recent full subjects **and bodies**, for example `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`, substituting the verified actual task history head. This style sample must not replace any task review range. Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement across several commits, not just one.

   Repository-local syntax established by project/user instructions and that history **always wins** over the Go guidance. Apply compatible Go guidance to clarity, quality, and structure within the observed pattern; do not impose Go package prefixes or any other fixed syntax. With no history, use explicit project/user instructions and compatible Go guidance without inventing a precedent.

   Verbatim excerpts from https://go.dev/wiki/CommitMessage (the example is **source guidance**, not a mandatory repository template):

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

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive patch selection). If ambiguous, one commit.

5. **Message content** — describe the outcome, not merely the file list, with motivation or trade-offs when needed. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or files belonging to one unit), include that U-ID using the runtime-established message conventions. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand. Preserve human authorship credit for someone else's work that will not otherwise land under their name (ported from their bookmark or PR, or applied from their patch). Inspect the original JJ descriptions and authors or patch, copy recorded identities exactly, and never guess an email. Use human-credit trailers only when required by project/user instructions, which take precedence over the quoted Go rule; otherwise credit them in the body using the established repository syntax. Do not add assistant attribution.

6. **Commit named files** — honor `exclude:<paths>` when the invocation carries it: those files stay uncommitted no matter what else changed; say in the report that they were left out. There is no staging step. Pass an explicit, verified nonempty file list to `jj commit`; never run a pathless commit or use a whole-tree fileset. Use exact literal path filesets when filenames contain fileset metacharacters. Run from the target workspace's absolute root, with repository-relative paths:

   ```bash
   jj commit -m "<message composed from the standards above>" -- file1 file2 file3
   ```

   Pass the full subject, blank line, and optional body as one literal argument through an argument-safe shell invocation; do not interpolate message text as shell code. If an intermediate message file is needed, write it under the target workspace's local `.tmp/`, never outside the repository or in OS temporary storage, and exclude it from the commit.

   JJ path-scoped commit keeps selected changes in the committed change and moves remaining changes into a new working-copy change above it. This explicit path list is required to preserve pre-existing unrelated work and exclusions. Verify the selected diff before committing, and inspect the committed diff and residual working copy afterward. Do not fold residual changes into the task bookmark or a later group accidentally. Do not rewrite unrelated history or mutate excluded files to obtain cleanliness.

7. **Confirm** — run `jj status`, inspect each resulting commit's description and scoped diff, and verify the task bookmark targets the final in-scope commit rather than the residual working copy. Report change/commit IDs and subjects, plus excluded or unrelated remaining work. A nonempty residual working copy is expected when other work was preserved.

Native command semantics: https://docs.jj-vcs.dev/latest/cli-reference/#jj-commit and https://docs.jj-vcs.dev/latest/git-command-table/.
