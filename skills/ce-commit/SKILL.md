---
name: ce-commit
description: Create a Jujutsu commit with a clear, value-communicating message. Use when the user asks to commit/save selected changes with a repo-appropriate message.
---

# Jujutsu Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and `jj status` is clean of those changes. **Stop when:** the working copy has no changes to commit; an empty `@` is normal in JJ.

## Context

Resolve the target workspace's absolute root with `jj workspace root`, then set that absolute root as the working directory for every JJ command and backend history read below. Use separate tool calls with explicit working directories and environment variables where shell syntax is unavailable. Shell examples use `(cd "$workspace_root" && jj ...)`; `jj -R` alone does not set the working directory. A non-zero exit is a normal state to interpret, not a failure to suppress.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Working-copy state and conflicts | Not a JJ repository — stop |
| `jj diff` | Current changes | Empty diff — also inspect untracked/ignored files |
| `jj bookmark list` and `jj log -r '@ | @-'` | Current change, parent, and bookmarks | No bookmark is normal; inspect before creating one |
| `jj git root` | Read-only Git backend for history and repository-scoped GitHub CLI | No Git backend — report history unavailable; do not invent precedent |
| `GIT_DIR=$(jj git root) git log -10 --format=%B` | Several recent complete subjects AND bodies, read-only | No history — use explicit project/user instructions and compatible Go guidance |
| `GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | Remote default bookmark | Unavailable — inspect project configuration; do not guess a mutation target |

Treat this as a snapshot. Re-read bookmarks, file selection, and working-copy state immediately before committing if anything may have changed. Backend Git is only for the read-only history operation JJ cannot supply as `git log`; do not stage, commit, or change branches with Git. Repository-scoped `gh` always receives `GIT_DIR` from `jj git root` in the target workspace.

See the [JJ Git command table](https://docs.jj-vcs.dev/latest/git-command-table/), [Git expert guide](https://docs.jj-vcs.dev/latest/git-experts/), and [CLI reference](https://docs.jj-vcs.dev/latest/cli-reference/) for native operation semantics.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to commit** — if `jj status` and the file inspection show no selected changes, report that and stop. Do not treat ignored or untracked content as disposable, automatically track it, or force it into a commit. Stop on conflicts and preserve unrelated work.

2. **Bookmark first** — if the selected change lacks a feature bookmark or is named only by the verified default bookmark, create a feature bookmark derived from the change content with `jj bookmark create <non-conflicting-name> -r @`, then re-read it. Do not move the default or an unrelated bookmark. If the derived name exists, choose a non-conflicting suffix. No branch checkout or workspace creation is needed.

3. **Convention** — **Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.** Before composing, read the full Go guide and compare several recent subjects AND bodies using the read-only backend command above from the absolute workspace root. Establish actual prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement. Repository-local syntax established by project instructions and history ALWAYS wins when it differs from Go guidance. Apply compatible Go guidance to clarity, quality, and structure without replacing that syntax. If there is no history, use explicit project/user instructions and Go guidance without inventing repository precedent. Do not impose a Conventional Commit or Go package-prefix template.

   The following verbatim Go excerpts are **source guidance, not a mandatory repository template**:

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

4. **Logical commits** — if changed files clearly split into distinct concerns, make separate commits (file level only, 2–3 max, no interactive hunk selection). If ambiguous, one commit.

5. **Message** — compose the subject and body dynamically from the standards above. Name the outcome (what is now possible or fixed), not merely the file list; explain motivation or trade-offs when needed. Apply imperative wording where compatible with repository syntax. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or the files belong to one unit), include that unit's U-ID in a repository-compatible location and form. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand. Do not add creator, model, harness, or branded attribution or coauthor/assistance trailers.

6. **Commit selected files** — JJ has no staging step. Use **named files only** with workspace-relative paths such as `src/example.py`, never paths prefixed by the workspace storage location. Honor `exclude:<paths>`: those files stay uncommitted and must be reported as left out. Write the full dynamically composed message with the file-write tool under `<absolute-workspace-root>/.tmp/`; ensure `.tmp/` is ignored in `.gitignore`, preserving existing rules. Never use OS-global temporary storage, including fallback/error paths. Inspect the selected diff before each commit:

```bash
(cd "$workspace_root" && jj diff -- file1 file2 file3)
```

```python
from pathlib import Path
import subprocess

# Set both paths to the verified absolute paths for this run.
workspace_root = Path("<absolute-workspace-root>")
message_file = workspace_root / ".tmp" / "<message-file>"
message = message_file.read_text(encoding="utf-8")
subprocess.run(
    ["jj", "commit", "--message", message, "--", "file1", "file2", "file3"],
    cwd=workspace_root,
    check=True,
)
```

The message file contains the message composed from the runtime standards above, not a fixed template. Read the complete UTF-8 file and pass it as one argv value to `--message`, without shell interpolation or truncation. Use the verified absolute workspace root as `cwd` and explicit workspace-relative file paths. Verify the stored description after committing.

The path list is required: a bare `jj commit` commits the entire working-copy change. Selected paths become the commit; unrelated and excluded changes remain in the new working-copy change. Re-read the resulting revisions and feature bookmark after every group; explicitly advance only the run's feature bookmark to the verified completed commit if needed. Never absorb unrelated work or move recovery/default bookmarks.

7. **Confirm** — run `jj status` and inspect the completed descriptions and bookmarks. Report commit/change IDs and subjects, excluded paths, and any remaining unrelated work. An empty working-copy child above the completed commit is expected. No push or PR mutation.
