---
name: ce-commit
description: Create a local Jujutsu commit with a clear, value-communicating message. Use when the user asks to commit/save changes with a repo-appropriate message.
---

# Jujutsu Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and those changes no longer remain in the working copy. **Stop when:** there are no changes to commit. Preserve unrelated work.

## Context

Resolve the target workspace's absolute root with `jj workspace root`. Run every subsequent command with the shell tool's working directory set to that absolute root; never use `jj -R` as a substitute. Use repository-relative paths. Gather each command as its own shell call; interpret non-zero exits rather than suppressing them. Never invoke the Git executable.

| Command | Purpose |
| --- | --- |
| `jj status` | Working-copy changes, conflicts, and untracked-file warnings; stop outside a JJ workspace |
| `jj diff --summary` | Named changed files; also inspect status for untracked files |
| `jj log --no-graph -r '@ | @-'` | Actual working-copy and parent identities, descriptions and bookmarks |
| `jj bookmark list` | Local and remote bookmark context; no bookmark is valid JJ state |

Treat this as a snapshot. Re-read status, the selected file list, and relevant bookmarks immediately before committing if anything may have changed. Stop on conflicts or ambiguous ownership rather than discarding work.

## Message standards

**Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.**

Before composing each message, read the full Go guide and project/user instructions. Resolve the relevant history head from the actual task and repository: normally the current change's established ancestry, or the verified task/bookmark head. An empty `@` above that head is normal. Do not hardcode a remote default branch, invent a head, or substitute this style sample for any task's reviewed base/head range. From the target workspace's absolute root, inspect several recent subjects **and full bodies**, for example:

```bash
jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'
```

Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement across several messages. Repository-local syntax established by project instructions and history ALWAYS wins over differing Go guidance. Apply compatible Go guidance to clarity, outcome, motivation, and structure within that observed pattern. If there is no history, follow explicit project/user instructions and compatible Go guidance without inventing repository precedent. Do not impose Conventional Commit types, scopes, or a fixed subject/body template.

### Go source guidance (illustrative, not a mandatory repository template)

Verbatim excerpts from https://go.dev/wiki/CommitMessage:

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

The full guide additionally covers sign-offs, issue references that do not close an issue, cross-repository provenance, and reverts. Apply these where compatible with local requirements. Do not add model/harness authorship or generated-by attribution.

## Workflow

0. **Gather** — run the Context commands and read the message standards above.

1. **Nothing to commit** — if status and the file inventory show no changes, report that and stop. Inspect untracked and ignored content where relevant: JJ does not automatically track every file (for example ignored or oversized files). Do not silently omit requested files or force-track unrelated content.

2. **Bookmark first** — identify the repository's actual default bookmark from project/remote configuration; do not guess a default name. If work is unbookmarked or the relevant bookmark is the default, choose a feature bookmark from the change content, checking for collisions and using a non-conflicting suffix. JJ has no detached-HEAD requirement, and an empty working-copy tip above a feature bookmark does not itself require a new bookmark. Preserve existing default/remote bookmarks; create the chosen feature bookmark on the first completed commit below, not on the residual working-copy change. Do not push.

3. **Convention** — perform the full-guide and JJ-history read-and-compare procedure above before composing. User/project requirements and actual repository syntax govern the result.

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive hunk selection). If ambiguous, one commit.

5. **Message** — describe the outcome, not merely the file list, using the runtime-established syntax. Explain motivation or trade-offs when not obvious. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or files belonging to one unit), include that U-ID compatibly with local syntax. Do not hunt for a plan. Omit it when the commit spans units, the unit is unclear, or no plan is in hand. Do not emit fixed example messages or attribution trailers.

6. **Commit named files only** — honor `exclude:<paths>`: those files stay outside the completed commits regardless of other changes; report their exclusion. JJ has no staging index. Use explicit literal filesets such as `file:path/to/file` for each selected file (and both paths of a rename), not broad directory or all-file selection. Check that the list contains exactly the intended changes. Execute `jj commit` with the full composed message as one literal argument through the tool's argument interface, not shell interpolation:

```bash
jj commit -m "<message composed from the standards above>" 'file:file1' 'file:file2' 'file:file3'
```

For multiline or shell-sensitive messages when the tool only accepts a shell string, write the message with the file-write tool under the workspace's local `.tmp/`, ensuring `.tmp/` is ignored. Use local processing to read it and pass its complete contents as one argument to `subprocess.run(["jj", "commit", "-m", message, *selected_filesets], cwd=workspace_root, check=True)`; never evaluate message text as shell syntax. Never use global temporary storage or accidentally include the message file. `jj commit` has no `-F` option.

Path-limited `jj commit` keeps the selected changes in the completed commit and moves all remaining changes into a new working-copy child. Verify the completed commit's exact file scope. Create the selected feature bookmark at that verified commit, or advance only the task-owned feature bookmark to the verified latest completed commit with `jj bookmark set`; do not move unrelated, default, or remote bookmarks. Repeat for each logical group.

7. **Confirm** — run `jj status` and inspect the completed commits' descriptions and diffs from the absolute workspace root. Report their change/commit IDs and subjects, the task bookmark, and any deliberately remaining/excluded files. Do not claim a fully clean workspace if unrelated changes remain.

Native command references: https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-command-table/.
