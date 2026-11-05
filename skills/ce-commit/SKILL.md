---
name: ce-commit
description: Create a Jujutsu commit with a clear, value-communicating message. Use when the user asks to commit/save changes with a repo-appropriate message.
---

# Jujutsu Commit

Create well-crafted local commit(s) from the current working tree. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and `jj status` confirms those changes are no longer in the working copy. **Stop when:** the working copy has no changes to commit.

## Context

Gather context with each command as its **own** shell tool call (program + args only). Resolve the absolute target workspace root with `jj workspace root`, then set every subsequent command's working directory to that absolute root. Do not use `jj -R` as a substitute for the working directory. A non-zero exit is a normal state to interpret, not a failure to suppress. Use native JJ throughout; never invoke Git directly. See https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/cli-reference/.

| Command | Purpose | Non-zero / empty means |
| --- | --- | --- |
| `jj status` | Working-copy state and conflicts | Not a JJ workspace — stop |
| `jj diff` | Working-copy changes | Empty = inspect status and untracked files before stopping |
| `jj bookmark list` | Local bookmarks and their targets | No bookmark is normal in JJ |
| `jj log --no-graph -r '@ | @-' -T 'commit_id ++ " " ++ bookmarks ++ "\n" ++ description ++ "\n"'` | Actual working-copy and parent identities and descriptions | Resolve an unexpected history state before continuing |
| `jj git root` | Backend path for repository-scoped `gh` | If unavailable, do not guess a repository |

Treat this as a snapshot. Re-read bookmarks, status, and the exact selected file diff immediately before committing if anything may have changed. Inspect untracked and ignored content separately when relevant; do not assume a diff includes files JJ is not tracking. Conflicts require resolution or the existing safe decision path, not an automatic commit.

**Default bookmark:** resolve the actual repository and default branch, rather than guessing `main`. When needed, run `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` with `GIT_DIR` set to the absolute backend path returned by `jj git root` in this workspace (shell equivalent: `GIT_DIR=$(jj git root)`). Set this environment on every repository-scoped `gh` call. If the default cannot be verified, report the uncertainty instead of moving a possibly protected bookmark.

## Workflow

0. **Gather** — run every Context command above (own shell call each), then continue.

1. **Nothing to commit** — if status and inspection of untracked files show no changes eligible for this request, report that and stop. Ignored or excluded work is not permission to include it.

2. **Bookmark first** — identify the feature bookmark for this work. If none exists or the current change carries the verified default bookmark, create a feature bookmark derived from the change content using `jj bookmark create <non-conflicting-name> -r @`, then re-read its target. Do not move the default bookmark. A bookmark on the parent does not automatically follow a new JJ commit: after committing, advance only the verified task-owned feature bookmark to the resulting commit. Do not repoint unrelated bookmarks; if ownership is ambiguous, use the safe decision path.

3. **Convention and source guidance** — before composing any message, read the full https://go.dev/wiki/CommitMessage guide. Resolve the relevant history head from the actual task and repository: normally the verified working-copy parent for new work, or the actual task head when continuing existing work. Inspect several recent subjects AND bodies from that anchor, for example `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'` from the absolute target workspace root. Do not hardcode a default remote branch or replace a reviewed base/head range with this style sample. Compare prefixes/package names, casing, verb tense, subject/body separation, wrapping, and issue-reference placement.

   **Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.**

   Repository-local syntax established by project/user instructions and `jj log` always wins over differing Go syntax. Apply compatible Go guidance to clarity, motivation, concise subjects, body structure, and issue references within that observed pattern. If no history exists, use explicit project/user instructions and compatible Go guidance without inventing repository precedent. Do not impose a fixed prefix, Conventional Commit format, casing, or subject template.

   The following are verbatim source excerpts, not a mandatory repository template or a message to emit:

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

5. **Message** — compose the subject and body dynamically under step 3, communicating the outcome rather than merely listing files. Explain non-obvious motivation or trade-offs. When a plan Implementation Unit ID is already in hand for this commit (conversation, caller, or the files belong to one unit), include that U-ID using the repository's established syntax. Do not hunt for a plan. Omit when the commit spans units, the unit is unclear, or no plan is in hand. Preserve human authorship: when carrying someone else's work that will not otherwise land under their name, retain the exact recorded human credits from the source commits or patch in the locally required form. If local rules require human coauthor trailers, they take precedence over the Go source guidance; never guess an email, and name the person in the body when none is recorded. Do not add model, harness, or skill authorship/assistance attribution.

6. **Commit named files** — JJ has no Git staging index; commit **named files only**. Honor `exclude:<paths>` when the invocation carries it: those files stay uncommitted no matter what else changed; say in the report that they were left out. Write the full composed message to a unique file under the target workspace's ignored `.tmp/` using the file-write tool. Ensure `.tmp` is ignored, and never include the message file in the commit. Use one call per commit group:

```python
from pathlib import Path
import subprocess

workspace_root = "<absolute-target-workspace-root>"
message = (Path(workspace_root) / ".tmp" / "<unique-message-file>").read_text()
subprocess.run(
    ["jj", "commit", "-m", message, "--", "file1", "file2", "file3"],
    cwd=workspace_root,
    check=True,
)
```

Reading the message file into a subprocess argument avoids shell interpolation of quotes, backticks, dollar signs, and multiline content; do not use `shell=True`. The trailing path list is required: a bare `jj commit` commits all working-copy changes. Use repository-relative file paths and verify the exact group diff before committing. Unselected changes remain in the new working copy. Track each resulting commit ID explicitly, especially across multiple groups, and advance only the intended feature bookmark after verifying its target.

7. **Confirm** — run `jj status`, inspect each resulting commit's description and file list, and verify the feature bookmark target. Report commit ID(s), subject(s), and any excluded or unrelated changes remaining. Never claim the whole workspace is clean if unrelated work remains.
