---
name: ce-worktree
description: Set up an isolated Jujutsu workspace and working-copy change for new work or for work based on an existing change, bookmark, commit, or GitHub PR. Use when starting isolated work or isolating an existing revision; preserves an already suitable workspace.
---

# Jujutsu Workspace Isolation

Ensure the requested work happens in its own Jujutsu workspace and working-copy change without disturbing another workspace. A workspace owns a working-copy change; bookmarks are named revision pointers, not checked-out branches, and no bookmark is active.

**Done when:** the caller is operating in an already suitable or newly created workspace, its root and workspace name are reported, and `@` is the intended working-copy change with the requested parent. Report a blocker instead when that state cannot be established safely.

**Two modes, selected by caller intent:**

- **New work (default):** create an empty, unbookmarked working-copy change whose sole parent is `main@origin`.
- **Existing work:** create an empty working-copy change on the requested change, bookmark, commit ID, or GitHub PR head. This gives the workspace an independent child to edit; do not make two workspaces edit the same change.

`ce-work` and `ce-code-review` may route here when isolation is requested. Preserve that routing and preserve all `gh`/GitHub behavior used to identify a PR.

## Command Discipline

Run each command as its own shell tool call: one program and its arguments, with no shell operators, pipes, substitutions, redirects, or dependence on shell state from another call. Interpret non-zero status as state to resolve, not permission to switch version-control systems.

| Command | Purpose | Failure or empty result |
| --- | --- | --- |
| `jj workspace root` | Confirm Jujutsu context and resolve the current workspace root | Not a Jujutsu workspace; report and stop |
| `jj workspace list` | Inspect workspace names, roots, and working-copy changes | Workspace state is unavailable; report and stop |
| `jj status` | Snapshot and inspect `@`, conflicts, and bookmark warnings | Repository or working-copy state is unavailable; report and stop |
| `jj diff` | Determine whether the current working-copy change has content | Empty means `@` has no content |
| `jj log -r "@ | parents(@)"` | Inspect the current change and its parentage | The current revision state is unresolved |
| `jj bookmark list --all-remotes` | Resolve local and remote bookmark targets | No bookmarks are known |
| `jj log -n 10` | Inspect actual repository message conventions before any description work | No message history is available; use active repository instructions and compatible Go guidance only |

Treat the results as a snapshot. Re-run `jj status` and the relevant revision query immediately before creating a workspace because another workspace may update repository state concurrently.

## Preserve Existing Isolation

If the harness or caller already placed this session in a dedicated workspace, prefer it when its current change can safely represent the requested work. Do not infer suitability merely from the existence of `.jj/`: every Jujutsu workspace has one.

- For new work, preserve the current workspace only when `@` is empty, has exactly the requested parent, and contains no unrelated description, conflict, or bookmark placement.
- For existing work, preserve it only when `@` is an empty child of the resolved target and has no unrelated description, conflict, or bookmark placement.
- If `@` contains user work, has the wrong parent, or is shared with another task, leave it untouched and create a separate workspace.

A bookmark may identify a parent used by several workspaces. Never reject isolation because a bookmark is visible from another workspace, and never move, create, track, or delete a bookmark merely to create isolation.

## Resolve The Parent

### New Work

Refresh the relevant remote state with `jj git fetch --remote origin`. Fetch failure is non-fatal only when the recorded remote bookmark still resolves unambiguously and the user accepts that it may be stale. Resolve the parent with `jj log -r "main@origin" --no-graph`; it must identify exactly one non-root revision. Do not substitute another inferred or fixed reference, a local bookmark, or the current parent. If it does not resolve, report the blocker and ask for the intended parent rather than guessing.

### Existing Change, Bookmark, Or Commit

Resolve the caller's value directly with `jj log -r <requested-revision> --no-graph`. Accept a change ID, commit ID, local bookmark, or explicit remote bookmark when it resolves to exactly one revision. Preserve the caller's revision identity; do not create a local bookmark as an alias and do not attach workspace state to an existing bookmark.

### GitHub PR

Use `gh pr view <pr-ref> --json number,url,headRefName,headRefOid,headRepositoryOwner,headRepository,isCrossRepository,state` to identify the exact open PR head. Preserve normal `gh` authentication and repository discovery, adding `-R <owner>/<repository>` only when repository context is unavailable or ambiguous.

Resolve `headRefOid` in Jujutsu first. If it is absent, fetch the PR's head bookmark from the remote that corresponds to `headRepositoryOwner` and `headRepository`, then resolve the fetched remote bookmark and confirm its commit ID equals `headRefOid`. Reuse a matching configured remote. Adding a remote changes repository configuration, so ask before doing so. Do not use a detached checkout, a branch, `FETCH_HEAD`, or an unverified same-named bookmark. A closed or unresolvable PR is a blocker unless the caller explicitly asks to use its last head revision.

## Message Standard

At every site that composes, edits, checks, validates, recommends, templates, or exemplifies a Jujutsu change description, repository instructions and actual history win. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Do not impose a fixed type, scope, prefix, capitalization, mood, subject form, body layout, line limit, trailer, template, or example. Workspace creation normally leaves the new empty working-copy change undescribed. If caller intent or repository convention requires an early description, immediately before composing, editing, or validating it: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

## Create The Workspace

Follow repository-local workspace naming conventions observed in `jj workspace list`. Derive a meaningful, collision-free name from the requested work only when those conventions make it unambiguous; otherwise ask. Do not impose a fixed namespace or naming syntax.

Resolve the destination base from `jj workspace root` and use `<workspace-root>/.tmp/rocketclaw/ce-worktree/<workspace-name>`. If that root cannot host the destination, use the current project's local `.tmp/rocketclaw/ce-worktree/<workspace-name>` as the only fallback. Confirm the destination does not already contain user data; never overwrite or reuse an unverified path.

Create the destination directory's parent with the native filesystem capability, then create the workspace and its independent empty change:

```text
jj workspace add --name <workspace-name> --revision <resolved-parent> <destination>
```

Do not pass `--message` by default, create or move a bookmark, run `jj edit`, or mutate the source workspace's change. Jujutsu snapshots working-copy content automatically; there is no staging or branch checkout step.

If creation fails because the destination is nested beneath content that Jujutsu would track, because the sandbox denies the path, or because the workspace name/path conflicts, no isolation was created. Leave existing workspace state untouched and ask whether to choose another workspace-local path or stop and resolve the blocker. Do not silently continue in the source workspace.

## Verify And Report

Run each verification from the new workspace:

| Command | Required result |
| --- | --- |
| `jj workspace root` | Exactly the resolved destination |
| `jj status` | A clean, conflict-free working-copy change |
| `jj diff` | Empty |
| `jj log -r "@ | parents(@)"` | `@` is a distinct empty change with exactly the resolved parent |
| `jj workspace list` | The chosen workspace name maps to the destination and current change |

If any invariant fails, stop and report it; do not repair parentage, descriptions, bookmarks, or user content by guessing. On success, switch subsequent tool calls to the new workspace directory and report its root, workspace name, working-copy change ID, parent revision, and any bookmark or PR identity used only to resolve that parent.

Workspace cleanup is separate user intent. When explicitly requested, verify the workspace name and root, preserve any non-empty change, run `jj workspace forget <workspace-name>`, and remove only the confirmed run-owned directory after Jujutsu no longer lists it.
