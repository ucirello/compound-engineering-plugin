---
name: ce-commit
description: Record a Jujutsu change with a clear, value-communicating description. Use when the user asks to commit/save changes with a repo-appropriate message.
---

# Jujutsu Commit

Create well-crafted local change(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is recorded with an explicit file list and a description that states the outcome, and `jj status` shows those changes no longer in the working-copy change. **Stop when:** there are no file changes to record.

## Context

Gather context with each command as its **own** shell tool call. Set the tool's working directory to the target workspace's absolute root for every JJ command; `jj -R` does not change cwd. Obtain that root with `jj workspace root`. A non-zero exit is a normal state to interpret, not a failure to suppress. Use native tool cwd/environment fields where available; shell examples below assume a POSIX shell. See the [JJ Git command table](https://docs.jj-vcs.dev/latest/git-command-table/) and [CLI reference](https://docs.jj-vcs.dev/latest/cli-reference/).

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Working-copy state and conflicts | Not a JJ workspace — stop |
| `jj diff` | Current file changes | Empty = no file changes |
| `jj log -r '@ | @-'` and `jj bookmark list` | Current change, parent, and bookmarks | No bookmark is normal, not detached HEAD |
| `jj git root`, then read-only `git --git-dir="<returned-backend-path>" log -10 --format=%B` | Recent subjects AND bodies | No history — use explicit project/user instructions and Go guidance |
| `(cd "$workspace_root" && export GIT_DIR=$(jj git root) && gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')` | Remote default bookmark name | Unavailable — inspect verified remote bookmarks; otherwise use `main` |

Treat this as a snapshot. Re-read bookmarks, file changes, and conflicts immediately before recording if anything may have changed. Git is used only to read backend history, never to stage or commit.

**Default bookmark name:** use the verified bare name for default-bookmark checks, not a remote-qualified bookmark.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to record** — inspect `jj status`, `jj diff`, and untracked/ignored content. If no intended file changes exist, report that and stop. JJ normally snapshots eligible new files automatically; ignored or intentionally untracked files require an explicit decision, not silent inclusion. Stop on unresolved conflicts without discarding work.

2. **Bookmark first** — JJ has no detached-HEAD requirement. Preserve any existing feature bookmark; if none identifies the intended work, choose a feature bookmark name from the change content, checking for collisions and adding a non-conflicting suffix. Create it on the recorded change after committing, not on the new empty working-copy change. Never move the default bookmark or unrelated bookmarks. This local naming action is part of the authorized commit-only workflow.

3. **Convention** — follow the message standards below at runtime. Do not select a fixed prefix, type, scope, or template in advance.

4. **Logical changes** — if changed files clearly split into distinct concerns, record separate changes (file level only, 2–3 max, no interactive hunk selection). If ambiguous, one change. Keep excluded and unrelated files in the working copy.

5. **Message** — compose using the standards below. Communicate the outcome, not just the file list; explain motivation or trade-offs when useful. When a plan Implementation Unit ID is already in hand (conversation, caller, or the files belong to one unit), include its U-ID in the location and syntax compatible with the observed repository pattern. Do not hunt for a plan. Omit when the change spans units, the unit is unclear, or no plan is in hand.

### Message standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide and examine recent subjects AND bodies with the read-only backend Git log from the target workspace's absolute root: obtain the backend with `jj git root`, then run `git --git-dir="<returned-backend-path>" log -10 --format=%B` with that same cwd. Compare several commits for prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Repository-local syntax established by project instructions and history ALWAYS wins over differing Go guidance. Apply compatible Go guidance to clarity, quality, and structure without replacing that syntax. With no history, use explicit project/user instructions and Go guidance without inventing a precedent. Do not add model/harness attribution or coauthor/assistance trailers.

The following verbatim Go excerpts are source guidance, not a mandatory repository template or a message to emit:

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

6. **Record named files only** — honor `exclude:<paths>`: those files remain outside every recorded group; report that they were left out. Write the dynamically composed full message with your file-write tool to a unique file under the target workspace's local `.tmp/`; ensure `.tmp/` is ignored. Use repository-relative explicit file paths, never temporary-workspace-prefixed paths. From the target absolute root, record each group:

```python
from pathlib import Path
import subprocess

workspace_root = "<absolute-target-workspace-root>"
message = Path(workspace_root, ".tmp", "<unique-message-file>").read_text()
subprocess.run(
    ["jj", "commit", "--message", message, "--", "file1", "file2", "file3"],
    cwd=workspace_root,
    check=True,
)
```

Read the message file and pass its contents as one literal `--message` argument through the shell tool's argument API or the inline subprocess example; do not interpolate it into shell source. JJ commit has no message-file option. The explicit path list is required: `jj commit` with paths records only that group and leaves other file changes in the new working-copy change. There is no staging area. Identify the resulting recorded revision from JJ output and inspect it; create the selected new feature bookmark with `jj bookmark create <name> -r <verified-recorded-revision>`. Move an existing feature bookmark only when it belongs to this authorized work and its target is verified.

7. **Confirm** — inspect `jj status` and the recorded revisions' descriptions and file lists. Verify that intended files were recorded and excluded/unrelated files remain untouched. Report change IDs, commit IDs, subjects, and any remaining changes.
