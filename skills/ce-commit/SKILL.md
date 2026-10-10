---
name: ce-commit
description: Create a local JJ change with a clear, value-communicating description. Use when the user asks to commit/save changes with a repo-appropriate message.
---

# Local Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and `jj status` is clean of those changes. **Stop when:** the working copy has no changes to commit.

## Context

Resolve the target workspace's absolute root as `workspace_root`. Run every JJ command with that root as its working directory, never with `jj -R`; file lists remain repo-relative. Gather each command in its own tool call. Use native program/argument arrays with an explicit working directory when available; the shell examples below use POSIX syntax, so adapt the wrapper to the actual shell rather than passing it to PowerShell. A non-zero exit is a normal state to interpret, not a failure to suppress.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `(cd "$workspace_root" && jj status)` | Working-copy state and conflicts | Not a JJ workspace — stop |
| `(cd "$workspace_root" && jj diff)` | Changes in `@` | Empty = inspect status for untracked files too |
| `(cd "$workspace_root" && jj bookmark list)` | Local and remote bookmark targets | No local bookmark = choose a feature bookmark |
| `(cd "$workspace_root" && jj log -r '@ \| @-')` | Current change and parent | An empty `@` is normal |
| `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)` | Recent subjects **and bodies**, read-only backend history | No history — use explicit project/user guidance and Go guidance |
| `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')` | Remote default bookmark name | Unavailable — use project configuration, else `main` |

Treat this as a snapshot. Re-read bookmarks, status, and the named files immediately before committing if anything may have changed. Stop for unresolved conflicts or ambiguous ownership; do not discard unrelated work.

**Default bookmark name:** use the bare name returned above for default-bookmark checks, distinguishing it from remote-qualified targets. JJ has no checked-out Git branch or staging index.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to commit** — if `jj status` shows no changes and inspection finds no intended untracked files, report that and stop. Do not use the diff alone as cleanliness. Ignored/untracked files may not be snapshotted; preserve them and track only explicitly intended files.

2. **Bookmark first** — identify the intended feature bookmark from the caller and verified targets. If none exists, or only the default bookmark names the work, derive a feature bookmark from the change content and create it with `(cd "$workspace_root" && jj bookmark create "<feature-name>" -r @)`. Do not ask again for this routine local action authorized by the commit request. If the name exists, choose a non-conflicting suffix; never overwrite an unrelated bookmark. Leave the default and remote bookmarks unchanged. Re-read targets. After each commit, move only the verified feature bookmark to the resulting committed revision with `jj bookmark set "<feature-name>" -r "<verified-committed-revision>"` from the absolute root.

3. **Convention** — follow the Message standards below before composing each description. Do not choose a prefix, scope, case, tense, or body template in advance.

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive hunk selection). If ambiguous, one commit.

5. **Message** — name the outcome (what is now possible or fixed), not merely the file list, in the syntax derived at runtime. Include motivation or trade-offs when not obvious from the subject. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or the files belong to one unit), include that unit's U-ID in the repository-appropriate location and syntax. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand.

### Message standards

**Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.**

Before composing, read the **full** Go guide and compare several recent subjects **and bodies** from the Context history command. Establish actual prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Repository-local instructions and observed history **always win** when their syntax differs from Go guidance; apply compatible Go quality, clarity, and structure within that pattern. With no history, use explicit project/user instructions and Go guidance without inventing precedent.

The following verbatim **Go source guidance** is illustrative, subordinate to the runtime repository pattern, and **not a mandatory repository template**:

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

6. **Commit named files** — JJ snapshots automatically; there is no staging step. Commit **named files only**, never all paths implicitly. Honor `exclude:<paths>`: those files remain in the working copy, uncommitted, and report that they were left out. For intentionally untracked files, use `jj file track` with only their named repo-relative paths from the absolute root; do not force-track ignored content without authorization. Then commit each explicit group:

```bash
(cd "$workspace_root" && jj commit -m "<message composed from the standards above>" -- file1 file2 file3)
```

Pass the actual full message as one literal argument using a program/argument tool with `cwd=workspace_root`, avoiding shell interpolation of quotes, dollars, backticks, and multiline bodies. If storing a message temporarily, use only a uniquely owned file under `$workspace_root/.tmp/`, not OS-global temporary storage. The trailing explicit path list is required: partial `jj commit` puts only those paths in the committed change and leaves the remainder in the new working-copy change. Verify the actual committed revision before moving the feature bookmark; never assume its old target advanced automatically.

7. **Confirm** — from the absolute root, run `jj status` and inspect the committed revisions with `jj log`; report change/commit IDs and subjects, the feature bookmark, and excluded or unrelated work left in `@`. An empty `@` over the committed change is expected, not a failed commit.

Command semantics: [JJ CLI reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-commit), [Git command equivalents](https://docs.jj-vcs.dev/latest/git-command-table/), and [Git experts guide](https://docs.jj-vcs.dev/latest/git-experts/).
