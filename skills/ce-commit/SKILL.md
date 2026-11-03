---
name: ce-commit
description: Create a local Jujutsu commit with a clear, value-communicating message. Use when the user asks to commit/save selected working-copy changes with a repo-appropriate message.
---

# Local Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and `jj status` confirms those changes no longer remain in `@`. Unrelated or excluded changes may remain. **Stop when:** there are no requested changes to commit.

## Context

Resolve the target's absolute `workspace_root` using `jj workspace root` with the shell tool's working directory set to the known absolute target directory. Run every subsequent JJ command with that absolute workspace root as its working directory, not merely `-R`. Give each command its own shell call; interpret non-zero exits rather than suppressing them. Do not invoke Git directly.

| Command (working directory: absolute `workspace_root`) | Purpose |
| --- | --- |
| `jj status` | Working-copy changes, conflicts, and files left untracked |
| `jj diff --summary` and `jj diff` (separate calls) | Changed file list and content in `@` |
| `jj log --no-graph -r '@ | @-'` | Current change and parent(s), including bookmark context |
| `jj bookmark list` | Existing local and remote bookmark names and targets |
| `jj config get revset-aliases.'trunk()'` | Configured default-line intent, when present; verify its resolved target rather than guessing a branch name |

Treat this as a snapshot. Resolve the actual default-line bookmark from repository configuration and verified remote bookmarks; do not assume `main` or substitute an arbitrary ref. If unclear, preserve work and ask for the missing target. Re-read `jj status`, the selected paths, and bookmark targets immediately before committing when anything may have changed. An empty `@` can sit above a bookmarked parent; inspect `@-` before deciding which line this work belongs to.

## Workflow

0. **Gather** — collect the Context above. Stop on conflicts or an ambiguous target; do not discard or reset work.

1. **Nothing to commit** — if the requested paths have no changes, report that and stop. Check status as well as the diff: ignored or untracked files are not automatically included. If a requested file is untracked, explicitly track only that named file with `jj file track <path>` after checking that it is intended content; never override ignore rules indiscriminately.

2. **Bookmark first** — preserve the default-line bookmark. If the work lacks a suitable feature bookmark, create a non-conflicting task-derived bookmark on `@` using `jj bookmark create <name> -r @`; do not move the default-line bookmark. If an existing feature bookmark is on the verified parent, move only that intended bookmark to `@` with `jj bookmark set <name> -r @`. Do not rewrite shared history or move unrelated bookmarks. Re-read its target. A bookmark on the selected commit remains there when `jj commit` creates a new working-copy child; verify that behavior after each group and move the feature bookmark forward to the next owned group when needed.

3. **Convention and message** — before composing any message, read the **full** https://go.dev/wiki/CommitMessage, not just the excerpts below. Resolve `<verified-history-head>` from the actual task and repository's relevant history (including the verified parent when `@` is a new/empty change). From the absolute target workspace root, run:

   ```text
   jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'
   ```

   Compare several recent full subjects **and bodies**: infer prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Do not replace any task review base/head range with this style sample. Repository-local syntax established by project instructions and history wins over differing Go syntax. Apply compatible Go guidance to clarity, motivation, traceability, and structure. If history is absent, use explicit project/user instructions and the Go guide without inventing precedent.

   Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

   Describe the outcome, not merely the file list; include motivation or trade-offs when useful. When a plan Implementation Unit ID is already in hand and this commit belongs to that one unit, include its U-ID using the repository's observed syntax. Do not hunt for a plan; omit an unclear or multi-unit ID. When carrying someone else's work that will not otherwise land under their name, preserve human/source credit using repository-local conventions. Copy recorded identities exactly, never invent an email; use body credit when no email is recorded. Do not add assistant attribution.

### Illustrative Go source guidance — not a mandatory repository template

The following excerpts are verbatim source guidance from https://go.dev/wiki/CommitMessage. They do not override repository-local syntax or require emitting this example:

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

4. **Logical commits** — if named changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive hunk selection). If ambiguous, one commit. Honor `exclude:<paths>`: those files stay in the working copy and must be reported as excluded. Preserve unrelated changes and existing descriptions; if `@` already represents described work outside the requested scope, stop for a safe scope decision rather than overwriting it.

5. **Commit named files only** — JJ has no staging index. Use explicit workspace-relative paths for each group; never select the entire tree by default. `jj commit` with paths puts only those changes in the committed parent and leaves remaining changes in the new working-copy child:

   ```text
   jj commit -m "<message composed from the standards above>" -- file1 file2 file3
   ```

   This command is executed with the absolute `workspace_root` as its working directory. Pass the entire composed message as a single literal argument through the shell tool's safe argument/quoting mechanism; never evaluate message text as shell code. If a message file is needed, write it only beneath the absolute workspace's `.tmp/` and pass its content as one argument with safe local processing, not shell interpolation of untrusted text. Do not commit that file. Do not use an unscoped `jj describe` on a change containing excluded work. Verify each resulting commit's paths and full description before continuing.

6. **Confirm** — run `jj status` and inspect each new commit with `jj show -r <verified-commit>`, from the absolute workspace root. Report commit IDs and subjects, named files, feature bookmark, and any remaining/excluded/untracked changes. Do not claim the whole workspace is clean when unrelated work remains.

JJ reference: https://docs.jj-vcs.dev/latest/cli-reference/#jj-commit .
