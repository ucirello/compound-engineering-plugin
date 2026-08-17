---
name: rocketclaw-commit
description: Record the current work as one or more coherent Jujutsu changes with repository-appropriate descriptions and bookmark placement. Use when the user asks to commit, save, or record the working-copy change.
---

# Record Jujutsu Changes

Record the intended working-copy content as one or more coherent Jujutsu changes and place a feature bookmark on the final recorded change. Leave only excluded or unrelated content in `@`, or a new empty working-copy change when none remains. For the full push and pull-request flow, use `rocketclaw-commit-push-pr`.

**Done when:** every intended file belongs to the correct described change, a suitable feature bookmark points to the final recorded change, and `@` contains none of the recorded content. When no excluded or unrelated content remains, `@` is a new empty working-copy change. **Stop when:** the current change has no content to record.

Invoking this workflow authorizes describing and splitting the current mutable change, creating or moving a feature bookmark when needed, and creating the next empty change. It does not authorize pushing, rewriting unrelated changes, moving the default bookmark, including excluded or unrelated files, or adding promotional, creator, model, provider, tool, or runtime text.

## Context

Run each command below as its **own** shell tool call: one program and its arguments, without `;`, `&&`, `||`, pipes, command substitutions, or redirects. Interpret each exit status directly; a non-zero exit can be an expected state.

| Command | Purpose | Non-zero exit / empty output means |
| --- | --- | --- |
| `jj workspace root` | Confirm the workspace and obtain its root | Not a Jujutsu workspace: report and stop |
| `jj status` | Snapshot and inspect the working-copy change, conflicts, and bookmark warnings | Repository or working-copy problem: report and stop |
| `jj diff` | Inspect the complete current change | Empty output means there is no content to record |
| `jj log -r "@ | parents(@)"` | Inspect the working-copy change and parent context | Repository or revision problem: report and stop |
| `jj bookmark list --all-remotes` | Inspect local, remote, tracked, and conflicted bookmarks | No bookmarks are configured |
| `jj log -r "trunk()" --no-graph` | Identify the default-line revision and its bookmarks | No default line can be resolved |
| `jj log -r :: -n 10 --no-graph -T 'description ++ "\n\n"'` | Inspect actual past description syntax read-only | No history is available from this workspace |

Treat these values as a snapshot. Immediately before the first mutation, run `jj status` and `jj diff` again because another process can update the working copy or repository operation concurrently.

If the current change is empty, report that there is nothing to record and stop. An existing description by itself is not content to record.

## Description Standard

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and conventions already in context and the message syntax observed in the actual history always win. Incorporate compatible Go guidance for clarity and structure: communicate the change's purpose and effect, keep the first line readable as a summary, and add explanatory detail only when it helps a future reader understand motivation or consequences. Do not invent a type, scope, prefix, ticket marker, subject form, body layout, template, or example that runtime evidence does not establish.

Compose each description from the content and purpose of that exact change. Preserve an existing description only when it remains accurate after any split. When a plan Implementation Unit ID is already available from the conversation, caller, or clearly corresponding files, retain it in the repository's observed form for a change that covers exactly that unit; do not search for a plan, invent an ID, or attach an ambiguous ID.

Every command below that accepts a description uses `<description-composed-from-runtime-conventions>` as a neutral placeholder for the result of this section, never as literal text.

## Workflow

### 1. Identify Coherent Changes

Inspect every path in `jj diff` for naturally distinct concerns before recording anything. Honor any `exclude:<paths>` supplied with the invocation: excluded paths remain in the working-copy change and must not appear in any recorded change; report them as left out.

- Separate clearly unrelated concerns at the file level.
- Keep a source change with its directly corresponding tests and documentation.
- Do not split hunks within a file.
- If separation is ambiguous, keep one change.
- Prefer a small coherent stack, with at most two or three recorded changes, over narrowly sliced changes.

For each distinct group except the final remaining group, use `jj split` with explicit filesets and the description composed from runtime conventions:

```text
jj split "<fileset>"... --message "<description-composed-from-runtime-conventions>"
```

The selected files become the parent change and the remaining files stay in the working-copy change. After every split, verify the stack with `jj log -r "@ | ancestors(@, 4)"` and inspect the remaining content with `jj diff`. Stop and report unexpected content movement or conflicts rather than continuing.

### 2. Determine Bookmark Placement

Bookmarks are named pointers to revisions; Jujutsu has no active or checked-out bookmark. Determine whether the resulting work is already associated with a suitable local feature bookmark by inspecting bookmark targets and the nearby stack, not by assuming one bookmark is current.

Follow repository-local bookmark naming and namespace rules. When no suitable feature bookmark exists, derive a non-conflicting name from the recorded work only when those rules make the result unambiguous; otherwise ask the user for the bookmark name.

Never record feature work by moving the repository's default bookmark. If a suitable feature bookmark already points into the current stack, move it to the final recorded change only when that is a forward placement consistent with the user's work. Otherwise, create a new bookmark there.

If the default bookmark cannot be identified from repository-local context, `jj log -r "trunk()" --no-graph`, or `jj bookmark list --all-remotes`, query GitHub metadata with `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. If it still cannot be identified, do not guess or move an existing bookmark; ask before creating a potentially conflicting name. Preserve normal `gh` authentication and repository-discovery behavior.

### 3. Record the Final Change

Re-run `jj status` and `jj diff`, then confirm the intended final files and exclusions.

When `@` contains only the intended final group, update it with its runtime-composed description:

```text
jj describe --message "<description-composed-from-runtime-conventions>"
```

In that state, the final recorded revision is `@`. After placing the bookmark, create a new empty working-copy change with `jj new`.

When excluded or unrelated content must remain, split the intended files explicitly instead of describing all of `@`:

```text
jj split "<intended-fileset>"... --message "<description-composed-from-runtime-conventions>"
```

The selected parent, normally `@-`, is the final recorded revision; `@` retains only the excluded or unrelated content. Verify both revisions and do not run `jj new` in this state.

Apply only the bookmark action selected above to `<final-recorded-revision>`:

```text
jj bookmark create "<bookmark-derived-from-runtime-conventions>" --revision <final-recorded-revision>
jj bookmark move "<bookmark-derived-from-runtime-conventions>" --to <final-recorded-revision>
```

For the no-residual-content state, finish with:

```text
jj new
```

This leaves the bookmark on the recorded work while `@` becomes the new empty working-copy change. In either state, Jujutsu snapshots working-copy content automatically; do not stage files or invoke another version-control system's recording command.

Pass descriptions directly as command arguments. If the active interface requires temporary storage, resolve the root with `jj workspace root`; if that command is unavailable, use the physical current directory reported by `pwd -P`. Store the data only in a unique per-run directory beneath `<resolved-root>/.tmp/rocketclaw/commit/`, and remove that run directory after use.

### 4. Confirm

Run each confirmation as a separate shell tool call:

| Command | Confirmation |
| --- | --- |
| `jj status` | `@` contains no recorded content and no conflict or bookmark warning was introduced |
| `jj log -r "@ | parents(@)"` | The recorded revision has the intended description and the bookmark targets it |
| `jj diff -r <final-recorded-revision>` | The final recorded change contains exactly its intended files and content |

When multiple changes were created, inspect every recorded revision with `jj show <change-id>`. Report each stable change ID, description, and bookmark, plus any excluded or unrelated working-copy content left unrecorded.
