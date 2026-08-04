---
name: ce-commit
description: Record the current work as one or more coherent Jujutsu changes with repository-appropriate descriptions and bookmark placement. Use when the user asks to commit, save, or record the working-copy change.
---

# Record Jujutsu Changes

Record the current working-copy change as one or more coherent Jujutsu changes, place a feature bookmark on the final recorded change, and leave a new empty working-copy change on top.

Invoking this workflow authorizes describing and splitting the current mutable change, creating or moving a feature bookmark when needed, and creating the next empty change. It does not authorize pushing, rewriting unrelated changes, moving the default bookmark, or including unrelated files.

## Context

Run each command below as its **own** shell tool call: one program and its arguments, without `;`, `&&`, `||`, pipes, command substitutions, or redirects. Interpret each exit status directly; a non-zero exit can be an expected state.

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj root` | Confirm the workspace and obtain its repository root | Not a Jujutsu workspace: report and stop |
| `jj status` | Snapshot and inspect the working-copy change, conflicts, and bookmark warnings | Repository or working-copy problem: report and stop |
| `jj diff` | Inspect the complete current change | Empty output means there is no content to record |
| `jj log -r "@ | parents(@)"` | Inspect the working-copy change and its parent context | Repository or revision problem: report and stop |
| `jj bookmark list --all-remotes` | Inspect local, remote, tracked, and conflicted bookmarks | No bookmarks are configured |
| `jj log -r 'trunk()' --no-graph` | Identify the default-line revision and its bookmarks | No default line can be resolved |
| `jj git root` | Resolve the backing repository used only for history inspection | No backing repository is available |
| `git --git-dir <resolved-git-root> log -n 10 --format=full` | Perform the required read-only inspection of actual past message syntax | No history is available from this workspace |

These values are a snapshot. Immediately before the first mutation, run `jj status` and `jj diff` again because another process can update the working copy or repository operation concurrently.

If the current change is empty, report that there is nothing to record and stop. Do not treat an existing description by itself as content to record.

## Workflow

### 1. Determine Description Standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Repository-local instructions and the message syntax observed in the actual `git log` output override compatible Go guidance. Repository syntax wins. Use Go guidance only for quality, clarity, and structure where it does not conflict with either local source. Do not invent a prefix, type, scope, ticket marker, subject, body, layout, template, example, or other convention those sources do not establish.

Compose each description from the content and purpose of its own change. Preserve an existing description only when it remains accurate for that exact resulting change.

### 2. Identify Coherent Changes

Inspect all paths in `jj diff` for naturally distinct concerns before recording anything.

- Separate clearly unrelated concerns at the file level.
- Keep a source change with its directly corresponding tests and documentation.
- Do not split hunks within a file.
- If separation is ambiguous, keep one change.
- Prefer a small coherent stack over many narrowly sliced changes.

For each distinct group except the final remaining group, use `jj split` with explicit filesets and the composed description.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

```text
jj split <fileset>... --message <description>
```

Quote each fileset and description according to the active shell. The selected files become the parent change and the remaining files stay in the working-copy change. Verify the resulting stack with `jj log -r "@ | ancestors(@, 4)"` and inspect the remaining working-copy content with `jj diff` after every split. Stop and report any unexpected content movement or conflict rather than continuing.

### 3. Determine Bookmark Placement

Bookmarks are named pointers to revisions; Jujutsu has no active or checked-out bookmark. Determine whether the resulting work is already associated with a suitable local feature bookmark by inspecting bookmark targets and the nearby stack, not by assuming one bookmark is current.

Follow all repository-local bookmark naming and namespace rules; repository syntax wins. When no suitable feature bookmark exists, derive a name from the recorded work that satisfies those rules. If a required namespace or naming rule cannot be determined without guessing, ask the user for the bookmark name.

Never record feature work by moving the repository's default bookmark. If a suitable feature bookmark already points into the current stack, plan to move it forward to the final recorded change only when that is a forward placement consistent with the user's work. Otherwise, plan to create a new bookmark at that change.

If the default bookmark cannot be identified from repository-local context, `jj log -r 'trunk()' --no-graph`, or `jj bookmark list --all-remotes`, query the GitHub repository metadata with `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. If it still cannot be identified, do not guess; avoid moving any existing bookmark and ask before creating a potentially conflicting name. Use the harness's blocking question capability when available. Fall back to numbered chat options only when no blocking capability exists or the call errors; never silently skip the question.

### 4. Record the Final Change

Update the final working-copy change with its composed description.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

```text
jj describe --message <description>
```

Apply the bookmark action determined above to the now-described `@`, using the applicable operation with neutral runtime values:

```text
jj bookmark create <bookmark> --revision @
jj bookmark move <bookmark> --to @
```

Then create a new empty working-copy change:

```text
jj new
```

This leaves the bookmark on the recorded work while `@` becomes the new empty working-copy change. Jujutsu snapshots working-copy content automatically; do not stage files or invoke another version-control system's recording command.

Pass descriptions directly as command arguments. If the active interface requires a temporary file, resolve `WORKSPACE_ROOT` with `jj workspace root`, falling back to the physical current directory from `pwd -P`, create `$WORKSPACE_ROOT/.tmp/rocketclaw/ce-commit`, then create a unique per-run directory with `mktemp -d "$WORKSPACE_ROOT/.tmp/rocketclaw/ce-commit/run.XXXXXX"`. Keep the file beneath that directory and remove the directory after use.

### 5. Confirm

Run each confirmation as a separate shell tool call:

| Command | Confirmation |
| --- | --- |
| `jj status` | `@` is a new empty working-copy change and no conflict or bookmark warning was introduced |
| `jj log -r "@ | parents(@)"` | The recorded parent has the intended description and the bookmark targets it |
| `jj diff -r @-` | The final recorded change contains exactly its intended content |

When multiple changes were created, inspect each recorded revision with `jj show <change-id>`. Report the stable change ID, description, and bookmark for every recorded change. Also report any pre-existing or unrelated working-copy content left unrecorded.
