---
name: ce-commit
description: Create local commits with JJ and clear, repository-appropriate messages. Use when the user asks to commit/save changes.
---

# Local Commit

Create well-crafted local commit(s) from the current working tree. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and `jj status` is clean of those changes. **Stop when:** there are no eligible changes to commit. Leave unrelated and excluded work untouched.

## Context

Resolve the target absolute workspace root first. Run every JJ command with the shell tool's working directory set to that root, not with `-R` as a substitute. Use JJ only; never invoke the Git executable, including for read-only context or fallback. Gather each command as its own shell call. A non-zero exit is a state to interpret, not suppress.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj workspace root` | Verify target absolute root | Not a JJ workspace — stop |
| `jj status` | Working-copy state and conflicts | Failure — stop and diagnose |
| `jj diff --summary` and `jj diff` | Named changes and complete content | Empty = inspect untracked/ignored state before stopping |
| `jj log -r '@ | @-' --no-graph` | Working change, parent, bookmarks | Resolve merges or uncertain task ancestry before proceeding |
| `jj bookmark list --all-remotes` | Local and remote bookmarks | Empty = no bookmark yet, not an error |
| `jj log -r 'ancestors(<verified-task-history-head>, 10)' --no-graph -T 'commit_id ++ "\n" ++ description ++ "\n\n"'` | Several recent full subjects AND bodies | No history = disclose that; never invent precedent |

Treat this as a snapshot. Verify the actual task history head from caller/task evidence and the graph: an empty `@` commonly sits above the task head at `@-`; a nonempty task change may itself be the head. Do not anchor style to an unrelated default branch. Substitute the captured exact commit ID in the history command, retain full descriptions without subject-only truncation, and inspect several messages. Re-read status, bookmarks, and the exact owned file set immediately before committing if anything may have changed.

**Default branch:** use verified repository instructions or GitHub repository metadata, not an assumed `main`. If repository-scoped `gh` is needed, run it from the target absolute root with `GIT_DIR` set to the path returned by `jj git root` in that same root. Pass the environment through the shell tool or a subprocess environment. If the default is unknown, do not move any possibly-default bookmark.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to commit** — inspect `jj status`, the diff, and untracked/ignored paths relevant to the request. JJ snapshots tracked changes automatically; ignored and untracked files may not be represented in the diff. If there is no eligible work, report that and stop. Never force-track ignored files without authorization. Stop on conflicts or uncertain ownership.

2. **Bookmark first** — JJ changes need no branch checkout, but commit-only must leave task work reachable by a non-default task bookmark. Reuse the verified task bookmark; otherwise derive a meaningful name from the change content, check local and remote names, and use `jj bookmark create <task-name> -r @`. Pick a non-conflicting suffix when needed. Never move the default bookmark or an unrelated bookmark. Verify the bookmark after creation and move only this owned bookmark to the resulting task commit after splitting.

3. **Convention** — before composing any message, read the FULL https://go.dev/wiki/CommitMessage (not just these excerpts) and read the recent full subjects and bodies from the verified task history above. Compare repository prefixes, casing, tense, body structure, wrapping, and issue references. Explicit user/project instructions and actual repository history syntax always win over source-guide syntax. Apply compatible Go guidance about clarity, motivation, and useful context only; do not impose a prefix, type, scope, casing, or issue keyword without local authority. If the guide or history cannot be retrieved, disclose the gap and resolve it before composing rather than inventing precedent.

   Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

### Illustrative source excerpts — NOT a repository message template

The following are exact excerpts from the Go guide. They describe Go's conventions, not mandatory syntax for this repository; the full runtime read and local history comparison above remain required.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

> Notably, for the subject (the first line of description):
>
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).

> For the body (the rest of the description):
>
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - we **do not** use `Signed-off-by` lines. Don’t add them. Our Gerrit server & GitHub bots enforce CLA compliance instead.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.
> - when referencing CLs, prefer saying “CL nnn” or using a go.dev/cl/nnn shortlink over a direct Gerrit URL or git hash, since that’s more future-proof.
> - when moving code between repos, include the CL, repository name, and git hash that it was moved from/to, so it is easier to trace history/blame.

> Please *don’t* use alternate GitHub-supported aliases like `Close` or `Resolves` instead of `Fixes`.

> To link a commit to an issue without marking it fixed—for example, if the commit is working toward a fix but not yet a complete fix—GitHub requires only that the issue is mentioned by number in the commit message. By convention, Go commits mention this at the bottom of the message using `For`, where `Fixes` might be expected, even if the number is also mentioned in the body of the commit message.

> It is common in other Git projects to use `Updates` instead of `For`, and that is acceptable too, even though it makes little sense (the commit does not update the issue). More precise phrasings are fine too. Don’t be too pedantic in code reviews: it’s not worth asking people to change from `Updates` or something else to `For`, or vice versa.

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive patch selection). If ambiguous, one commit. JJ has no staging index; preserve unrelated changes in the remaining working-copy change.

5. **Message** — use the standards established above to state the outcome, not just the file list, and explain motivation or trade-offs when useful. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or the files belong to one unit), retain that U-ID as context in a position and syntax compatible with repository standards. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand. Preserve factual human authorship: if carrying someone else's work that will not otherwise land under their name, credit the recorded people in ordinary body prose and identify the source change when useful. Never guess identities or email addresses. Do not add coauthor/assistant trailers or creator, model, or harness attribution.

6. **Commit named files only** — honor `exclude:<paths>` when the invocation carries it: those files stay outside the completed commits no matter what else changed; say in the report that they were left out. Review the exact named files before selection. Do not select the entire workspace or unrelated pre-existing work. Use explicit literal JJ filesets (for example `file:"path/to/file"`) so special characters do not broaden selection. For each group, split only those files into a completed parent with the composed full message; the remainder stays at `@`:

```bash
jj split -m "<message composed from the standards above>" <explicit-owned-file-filesets>
```

```bash
jj describe -m "<message composed from the standards above>" -r <verified-selected-change-id>
```

The split command sets the full message directly; the describe command is for a needed correction to that verified selected change, not the remaining `@`. Pass message arguments through an argument-safe subprocess API so `$`, quotes, backticks, and multiline bodies remain literal. If a message file is needed, write it only under the target workspace's local `.tmp/` and use the command's supported file input after checking help. Do not use OS temporary paths. Never run commands with the placeholder text as an actual message.

After each split, verify the selected commit's exact file list and complete message, and verify excluded/unrelated work remains in `@`. If a file mixes owned and unrelated edits, stop for clarification rather than committing the whole file. After all groups, move only the verified owned task bookmark using `jj bookmark set <task-name> -r <verified-last-task-commit>`. An empty `@` above it is normal. Do not rewrite earlier published history, push, or open a PR.

7. **Confirm** — run `jj status` and inspect the committed changes and task bookmark. Report commit/change IDs, subjects, explicit file groups, and excluded or remaining changes. Never call the entire tree clean if unrelated, ignored, or untracked work remains.
