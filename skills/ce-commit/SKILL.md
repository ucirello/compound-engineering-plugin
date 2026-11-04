---
name: ce-commit
description: Create a local JJ commit with a clear, value-communicating message. Use when the user asks to commit/save selected changes with a repo-appropriate message.
---

# Local Commit

Create well-crafted local commit(s) from the current working copy. No push, no PR — use `ce-commit-push-pr` for the full ship flow.

**Done when:** each logical change is committed with an explicit file list and a message that states the outcome, and those changes no longer appear in the working-copy diff. **Stop when:** there are no eligible changes, conflicts, ambiguous ownership, or an unsafe existing revision to rewrite. Preserve unrelated work.

## Context

Resolve the target workspace's absolute root as `workspace_root`. Run every JJ command with that root as its actual working directory, using a shell tool's absolute `workdir`, or `(cd "$workspace_root" && jj ...)`; `-R` alone is insufficient. File arguments remain repository-relative. Never invoke the Git executable.

Gather each command separately and interpret failures rather than hiding them:

| Command (at the absolute workspace root) | Purpose |
| --- | --- |
| `jj status` | Working-copy state, including conflicts and untracked files |
| `jj diff --summary` and `jj diff` | Exact current changes and content |
| `jj log --no-graph -r '@ | @-' -T 'commit_id ++ " " ++ bookmarks ++ "\n" ++ description ++ "\n"'` | Capture exact working-copy and parent identities, bookmarks, and descriptions |
| `jj bookmark list --all-remotes` | Identify local and tracked default/source bookmarks without guessing a default name |

Capture the actual relevant history head as an exact commit ID: normally the verified parent of the working-copy change; for a merge inspect all relevant parent histories. Do not substitute a default branch, remote head, or a different range. Run `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'` with the captured ID substituted. Read several recent **full subjects and bodies**, not one-line summaries. A history failure is not proof that history is empty; report and resolve it before claiming conventions were checked. The root revision's empty description is not precedent.

Treat this as a snapshot. Re-read status, exact revision identities, bookmarks, and the selected file changes immediately before each commit if anything may have changed.

## Workflow

1. **Gather and scope** — run the Context commands. If there are no eligible tracked or untracked changes, report that and stop. Inspect ignored content when relevant; do not automatically track ignored files. Honor `exclude:<paths>`: excluded files remain uncommitted, even if otherwise selected, and are listed as excluded in the report. Never absorb another person's unrelated changes.

2. **Protect revision identity** — JJ does not require a checked-out branch. Do not rename or move an existing default/source bookmark merely to create a feature identity. If the working-copy revision is published, immutable, conflicted, already described as existing work, or has unexpected descendants, stop rather than silently rewriting it. For an ordinary mutable working-copy change, create a non-conflicting task bookmark at `@` with `jj bookmark create <task-name> -r @` if it has no suitable feature bookmark. Inspect registered bookmark names first and append a numeric suffix on collision. Preserve all existing bookmarks. If an existing default/source bookmark points at the working-copy change, ask for a safe revision arrangement instead of rewriting that reference implicitly.

3. **Read and compare standards before composing** — read the **full** https://go.dev/wiki/CommitMessage guide, then compare the runtime history captured above. Analyze prefix/package usage, capitalization and tense, subject/body separation, body wrapping, and issue-reference placement. Project instructions and observed repository syntax always win over incompatible Go formatting; apply compatible Go quality guidance. If there is genuinely no history, use project/user instructions plus the Go guidance without inventing precedent.

   Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

   **SOURCE GUIDANCE — verbatim Go excerpts, not a mandatory repository template:**

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

4. **Logical commits and message** — if files clearly split into distinct concerns, make separate file-level commits (2–3 maximum, no interactive hunk selection). If ambiguous, use one commit. Communicate the outcome rather than merely listing files; explain motivation or trade-offs when needed. Use the standards established in step 3 for all syntax, including any plan Implementation Unit ID already supplied by the caller. Preserve its semantic association when appropriate, but do not prescribe a suffix or invent an ID. Do not hunt for a plan. Preserve recorded human authorship when carrying another person's work; never guess identities or emails. Do not add assistant/model/harness credits. Follow explicit project/user requirements for human attribution, with compatible source guidance otherwise.

5. **Commit named files only** — use native JJ file selection, not a staging/index workflow. Write any scratch message file only beneath the target root's ignored `.tmp/` directory, never an OS temporary location. Prefer a subprocess argument array so the complete message is passed literally without shell interpolation. For example, use Python with `workspace_root` set to the verified absolute root, `message` composed from step 3, and `paths` containing only the explicitly selected repository-relative files:

```python
subprocess.run(["jj", "commit", "--message", message, "--", *paths],
               cwd=workspace_root, check=True)
```

   Import `subprocess` in the invoking script. Require a nonempty `paths` list and reject fileset metacharacters or encode paths as literal JJ filesets before invoking; verify the selection matches exactly the named files. Never omit the path list: bare `jj commit` includes the whole working-copy change. JJ commits the selected changes and leaves remaining changes in a new working-copy child; it does not move the selected commit's bookmarks forward to that child. This preserves excluded/unrelated working-copy changes. Do not describe or commit the unrelated remainder. If a selected file also contains unowned edits that cannot be separated at file level, stop for clarification.

6. **Confirm** — run `jj status`, `jj diff --summary`, and inspect each resulting commit's full description and changed-file list from the absolute workspace root. Verify only the intended named changes landed and exclusions remain untouched. Report exact commit IDs, subjects, selected paths, and any remaining or excluded work. Do not claim the entire workspace is clean when unrelated changes remain.
