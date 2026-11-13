---
name: ce-commit
description: Create a local Jujutsu commit with a clear, value-communicating message. Use when the user asks to commit/save selected working-copy changes with a repo-appropriate message.
---

# Jujutsu Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and `jj status` shows those changes no longer pending. **Stop when:** there are no changes to commit.

## Context

Discover the absolute workspace root with `jj workspace root`. Run every subsequent JJ command with the shell tool's working directory set to that absolute root, not merely with `jj -R`. Each command is its own shell call (program + args); interpret non-zero exits rather than suppressing them. Never invoke the Git executable, including for history or index inspection. JJ has no staging index: existing Git staging is not a selection mechanism.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Working-copy changes, conflicts and untracked-file warnings | Not a JJ workspace — stop |
| `jj diff --summary` | Changed paths in `@` | Empty may mean nothing to commit; also inspect status warnings |
| `jj log --no-graph -r '@ | @-'` | Current change and parent identities | Resolve errors before continuing |
| `jj bookmark list` | Local and remote bookmark targets | No bookmarks is valid |
| `jj git remote list` | Configured remotes | No remote is valid for local commits |

Resolve the actual task history head from the verified current change, its parent(s), and any task-specified bookmark or revision. An empty `@` may sit above the relevant history. Do not assume a default-branch name or silently replace the task's anchor. If the default branch matters, inspect repository configuration or query `gh repo view --json defaultBranchRef` with `GIT_DIR` set to the value obtained by `jj git root` in this absolute workspace root. If it cannot be established, report that ambiguity rather than guessing.

Treat this as a snapshot. Re-read status, identities and selected paths immediately before committing if anything may have changed. Stop on conflicts or ambiguous scope; preserve unrelated work.

## Message standards

**Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.**

Before composing, read the **full** https://go.dev/wiki/CommitMessage at runtime. From the target workspace's absolute root, inspect several recent complete subjects **and bodies** at the verified task history head:

```bash
jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'
```

Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement across several commits. Repository-local syntax established by project/user instructions and that history **always wins** over differing Go guidance. Apply compatible Go guidance to clarity, quality and structure within the observed pattern; do not impose a fixed prefix, type, scope or template. With no history, use explicit project/user instructions and Go guidance without inventing a repository precedent.

### Verbatim Go source guidance — illustrative, not a repository template

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

## Workflow

0. **Gather** — run the Context commands, resolve the history anchor, and read and compare the message standards above.

1. **Nothing to commit** — if status and diff show no pending changes or untracked files to include, report that and stop. Do not mistake ignored or untracked-file warnings for committed content.

2. **Bookmark first** — JJ changes do not have detached HEAD. If the work has no task bookmark, or its bookmark is the verified default branch, create a non-conflicting feature bookmark derived from the change content at `@` using `jj bookmark create <name> -r @`, then verify its target. Do not move the default bookmark. If a name exists, choose a non-conflicting suffix. Preserve existing task/source bookmarks.

3. **Convention** — determine syntax at runtime using Message standards; do not select a fallback Conventional Commit template.

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive patch selection). If ambiguous, one commit.

5. **Message** — communicate the outcome rather than merely listing files. Include motivation or trade-offs when needed. When an Implementation Unit ID is already in hand and this commit belongs to that single unit, include that ID in the repository-compatible form; do not hunt for a plan. Omit it when spanning units or when unclear. Preserve human authorship credit for ported branch/PR/patch work: copy recorded names and identities exactly, never guess an email. Follow repository-local credit requirements when present; otherwise acknowledge those humans in the body consistently with the Go guidance. Do not add assistant/model/harness attribution.

6. **Commit named files only** — honor `exclude:<paths>`: those paths remain uncommitted and must be mentioned in the report. Use root-relative explicit file paths (not workspace-prefixed paths), including deleted paths; do not use a broad directory or whole-tree selection. If an intended untracked file is not tracked, use `jj file track <exact-path>` only for that authorized file and verify selection again. Never force-track ignored content without authorization.

   Supply the full dynamically composed message as a single literal argument through the shell tool's program/argument interface, without interpolating message text into shell source:

```bash
jj commit -m "<message composed from the standards above>" -- file1 file2 file3
```

   JJ commits the selected paths in `@` and moves the remaining changes to a new working-copy child. The explicit path list is required: omitting it would include unrelated or excluded changes. No index staging or Git commit command is needed. If a tool requires a message artifact, keep it under the absolute workspace root's `.tmp/`, ensure `.tmp/` is ignored, and read it literally rather than evaluating its contents.

   Record the committed revision after each group and verify the feature bookmark still targets the intended committed work. `jj commit` does not move bookmarks to its new child: for subsequent groups move only this task's feature bookmark to the verified selected working-copy change before committing, leaving other bookmarks untouched.

7. **Confirm** — run `jj status`, inspect the committed revisions and their complete descriptions, and report commit IDs and subjects. Verify only selected files were included and excluded/unrelated changes remain pending. An empty working-copy child is normal, not an additional commit to publish.

JJ operation references: https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-command-table/.
