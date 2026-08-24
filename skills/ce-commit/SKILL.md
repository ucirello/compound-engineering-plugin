---
name: ce-commit
description: Record Jujutsu working-copy changes with repository-appropriate descriptions and bookmark placement. Use when the user asks to commit, save, or record local changes.
---

# Record Jujutsu Changes

Record the intended working-copy content as one or more coherent local Jujutsu changes and place a suitable feature bookmark on the final recorded change. Leave excluded or unrelated content in `@`; otherwise leave a new empty working-copy change. Do not push or open a pull request; use `ce-commit-push-pr` for that flow.

**Done when:** every intended file belongs to the correct described change, a suitable non-default bookmark points to the final recorded change, and `@` contains none of the recorded content. When no excluded or unrelated content remains, `@` is a new empty working-copy change. **Stop when:** the current change has no content to record, the directory is not a Jujutsu workspace, or ambiguity or conflicts prevent a truthful boundary, description, or bookmark action.

Invoking this skill authorizes describing and splitting the current mutable change, creating or moving a feature bookmark when needed, and creating the next empty change. It does not authorize pushing, rewriting unrelated changes, moving the default bookmark, including excluded content, or adding visible creator, model, provider, tool, or runtime branding.

## Context

Run each command as its own shell tool call: one program and its arguments, without shell operators, substitutions, pipes, or redirects. Interpret each exit status directly. Use the installed `jj help <command>` when repository configuration or the installed version affects command syntax.

| Command | Purpose | Non-zero or empty result |
| --- | --- | --- |
| `jj workspace root` | Confirm the workspace and obtain its root | Not a Jujutsu workspace; stop |
| `jj status` | Inspect the working-copy change, conflicts, and bookmark warnings | Repository or working-copy problem; stop |
| `jj diff` | Inspect the complete current change | No content to record |
| `jj log -r '@ | parents(@)'` | Inspect the current change and its parent context | Revision state unavailable; stop |
| `jj log -r :: -n 10 --no-graph` | Observe established description syntax | No useful local history |
| `jj bookmark list --all-remotes` | Inspect local, remote, tracked, and conflicted bookmarks | No bookmark context is available |
| `jj log -r 'trunk()' --no-graph` | Identify the default-line revision and its bookmarks | The default line cannot be resolved |

Use `jj git` only when Git-backed remote interoperability requires it. If JJ state and the project's active context cannot identify the remote default, query provider metadata with `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` when available; otherwise ask rather than inventing a default.

Treat this evidence as a snapshot. Immediately before the first mutation, re-run `jj status`, `jj diff`, and the relevant bookmark inspection because another process may have changed the workspace or repository operation.

If temporary storage is unavoidable, resolve the workspace root with a separate `jj workspace root` call and use a unique per-run directory beneath the path represented by `$(jj workspace root)/.tmp/rocketclaw/commit/`. Outside a Jujutsu workspace, use `./.tmp/rocketclaw/commit/`. Confirm the scratch path is ignored before writing, remove the run directory after use, and never use an operating-system or global temporary directory. Do not create persistent workflow state; if an active repository protocol requires it, use `.rocketclaw/`.

## Description Authority

The user's request, the project's active instructions and conventions already in context, and message syntax observed in the current `jj log` determine the description standard. Repository-local instructions and observed syntax always win over general guidance.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Apply only compatible Go guidance to message quality, clarity, and structure. Preserve each logical change's semantic requirements while adapting its syntax dynamically. Do not impose a fixed prefix, type, scope, subject, body, layout, template, example, tense, punctuation, or line width that runtime evidence does not establish. Use `<description-composed-from-runtime-conventions>` only as a neutral command placeholder, never as literal description text. Communicate the change's purpose and effect rather than reciting its path list, and include supporting explanation only when it materially helps a future reader understand motivation or consequences.

Preserve repository-required traceability in the observed form when its value is already available and applies unambiguously to that exact change. Do not search for or invent traceability metadata. Do not add generated-by text, authorship, co-authorship, sign-off, badges, bylines, or other attribution. If a machine-readable protocol requires a neutral actor identity, use `ai:assistant`; never place that identity in the human-visible description.

## Workflow

1. **Inspect and bound the request** - Gather all Context evidence before mutating the change. Compare the complete working-copy diff with the user's request. Honor `exclude:<paths>` whenever the invocation carries it: excluded paths remain outside every recorded change and are named in the report. Stop and ask when content ownership is ambiguous or unresolved conflicts prevent an accurate boundary or description.

2. **Choose logical boundaries** - Map every changed path to an independently understandable outcome. Keep directly corresponding implementation, tests, and documentation together. Use one change when separation is ambiguous and normally no more than three unless the user requests otherwise. Select whole files with explicit JJ filesets; do not split hunks interactively.

3. **Split only when boundaries require it** - When `@` contains multiple groups, exclusions, or unrelated content, use `jj split -r <source-change> -m <description-composed-from-runtime-conventions> <included-filesets...>` for each group that must be separated. The selected filesets form the described parent change and unselected content remains in the child working-copy change. When an existing change already contains exactly one intended group, preserve its content and topology and use `jj describe -r <target-change> -m <description-composed-from-runtime-conventions>` instead.

After each mutation, identify revisions by stable change ID rather than assuming a parent or child position. Inspect the target's full `jj diff`, the remaining working-copy diff, and nearby `jj log` before continuing. Stop if content moved unexpectedly, appeared concurrently, or no longer supports the description.

4. **Place the bookmark** - Jujutsu has no active bookmark. Determine association from bookmark targets and the nearby stack. Preserve a suitable existing local feature bookmark and move it forward to the final recorded change when needed. If the work is unbookmarked or associated only with the default line, derive a non-conflicting bookmark name from repository-local conventions and the work when unambiguous; otherwise ask. Never move the default bookmark to feature work.

Use `jj bookmark create <bookmark-derived-from-runtime-conventions> -r <final-recorded-change>` for a new bookmark or `jj bookmark move <bookmark-derived-from-runtime-conventions> --to <final-recorded-change>` for an existing bookmark. Re-read bookmark placement after the mutation. Do not move an ambiguous bookmark.

5. **Open the next working-copy change** - If no excluded or unrelated content remains in `@`, ensure the final intended revision has its runtime-composed description and run `jj new` on top of it. If residual content must remain, keep that content in `@` and do not create another change. In either state, Jujutsu snapshots working-copy content automatically; there is no staging step.

6. **Verify and report** - Run `jj status`; inspect every recorded revision with `jj diff -r <recorded-change>` and `jj log -r <recorded-change> --no-graph`; and confirm the bookmark target with `jj bookmark list -r <final-recorded-change>`. Verify that descriptions and exact filesets match each intended group and that `@` contains no recorded content. Report each stable change ID, commit ID, description, and fileset; the resulting bookmark placement; and every excluded, unrelated, or newly arrived path left in `@`. Report a blocker instead of claiming completion when any verification fails.
