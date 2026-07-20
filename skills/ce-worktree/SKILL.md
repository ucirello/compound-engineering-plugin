---
name: ce-worktree
description: Set up isolated Jujutsu workspaces for fresh work or an existing bookmark, PR, change, or revision. Use when starting isolated work or attaching an existing target without disturbing another workspace; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated Jujutsu workspace without disturbing the user's primary workspace. Detect an existing dedicated workspace first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a JJ-aware native workspace tool -> fall back to `jj workspace add`.** Never use Git worktrees or Git branches. Use `jj git` only for Git interoperability; `gh` is allowed for GitHub metadata and API operations.

**Two modes, set by the caller's need:**

- **New work (default).** No target was named. Create a working-copy revision on the selected trunk revision and a meaningful bookmark for the work.
- **Isolate an existing target.** The caller names a local or remote bookmark, GitHub PR, change ID, commit ID, tag, or other unambiguous JJ revset. Create a workspace whose working-copy revision is on top of that target. For a bookmark or PR, advance the corresponding local bookmark to the new working-copy revision so subsequent edits remain attached to it. For a bare revision, do not invent a bookmark unless the caller requests one.

JJ workspaces have independent working-copy revisions. Unlike Git worktrees, they do not make a bookmark exclusive to one workspace. Do not reuse or directly edit another workspace's working-copy revision; `jj workspace add -r <target>` creates a new working-copy revision on top of it.

The steps below apply to both modes. The mode changes only the starting revision, bookmark handling, and report to the caller.

## Step 0: Detect existing isolation

First resolve the current workspace and inspect the workspace set:

```bash
jj workspace root
jj workspace list
jj log -r @ --no-graph
```

Match the current `@` change/commit shown by `jj log` to the entry in `jj workspace list`. Also honor explicit harness context saying that the session already runs in a dedicated JJ workspace. A non-primary workspace created for this session is already isolated; report its root, workspace name, working-copy revision, and any bookmarks pointing at `@`, then work in place.

In existing-target mode, first resolve the target with `jj log -r '<target>' --no-graph`. If the current `@` is already the dedicated working-copy revision for that target, work in place. Otherwise, do not repoint or rebase the current workspace merely to avoid creating the requested isolated workspace.

Do not treat the mere existence of `.jj`, or the fact that every JJ checkout is called a workspace, as proof that the user's primary workspace is isolated. If only the primary workspace exists, or the current workspace is the primary one, continue.

If `jj workspace root` fails, this is not a Jujutsu repository and a JJ workspace cannot be created. Report the failure and get the same blocking user decision described under **Failure behavior** before touching the current checkout. Do not initialize or convert the repository automatically.

## Step 1: Prefer a JJ-aware native workspace tool

If the harness provides a native primitive that explicitly creates and enters a **Jujutsu workspace**, use it and stop after applying the mode's revision and bookmark behavior. Do not use a native primitive that creates a Git worktree or checks out a Git branch. A behind-the-back isolation mechanism can create state the harness cannot navigate or clean up.

## Step 2: `jj workspace add` fallback

Use this only when there is no JJ-aware native tool and Step 0 found no existing isolation.

1. Resolve the current root with `jj workspace root`. Put workspace directories beneath `$(jj workspace root)/.tmp/rocketclaw/workspaces/`. If root resolution is unavailable for any transient artifact that does not require a repository, use the current directory's `.tmp/rocketclaw/` instead. Never use an OS-global temporary directory.
2. Choose a unique ASCII workspace slug and a meaningful bookmark name from the work description. Workspace names must be unique in `jj workspace list`. Keep an existing target bookmark's exact name.
3. Before creating `.tmp/`, ensure the workspace root's `.gitignore` ignores it. Preserve all existing `.gitignore` content and ordering. If no existing rule covers the root `.tmp/` directory, append exactly `.tmp/`; create `.gitignore` if needed. Do not replace GitHub-specific or other existing ignore rules.
4. Resolve the starting revision as described below. A best-effort `jj git fetch --remote <remote>` is non-fatal: if it fails because the remote or network is unavailable, continue only when the required revision already resolves locally. Otherwise report that the target cannot be resolved.
5. Create the workspace with `jj workspace add --name <workspace-slug> -r '<revision>' "$(jj workspace root)/.tmp/rocketclaw/workspaces/<workspace-slug>"`. Do not pass `-m` or compose a change description. The command creates a new working-copy revision with `<revision>` as its parent.
6. Enter the returned destination. Run all later JJ commands from that workspace unless using `-R` explicitly.
7. Apply bookmark behavior only after the workspace succeeds:

- **New work:** create the selected bookmark at the new `@` with `jj bookmark create <bookmark> -r @`. If the name already exists, stop and ask for a different name; do not move it silently.
- **Existing local bookmark:** move it forward to the new `@` with `jj bookmark move <bookmark> --to @`. Do not use `jj bookmark set` to conceal a missing or misspelled bookmark.
- **Existing remote bookmark:** track it first with `jj bookmark track <bookmark>@<remote>` when appropriate, create the workspace from `<bookmark>@<remote>`, then move the resulting local bookmark to the new `@`.
- **Bare revision, change ID, commit ID, or tag:** leave bookmarks unchanged unless the caller requested one.

### Resolve new work

Use the project's configured trunk bookmark. Prefer the tracked default remote bookmark; use `GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef` when GitHub metadata is needed. Confirm the chosen local or remote bookmark with `jj bookmark list --all-remotes` and `jj log -r '<bookmark-or-bookmark@remote>'`. Do not assume `main`, `master`, or `origin` when project data provides another value.

Best-effort refresh the selected remote with `jj git fetch --remote <remote> --branch <trunk>`. If fetch fails but the selected trunk revision already resolves locally, continue from the local revision and report that it may be stale.

### Resolve an existing bookmark or revision

Resolve the caller's input with `jj log -r '<target>' --no-graph` before creating anything. Require exactly one revision unless the caller intentionally supplied multiple parents. Prefer explicit remote bookmark syntax such as `<bookmark>@<remote>` when local and remote names are ambiguous.

If the target is another workspace's working-copy revision, create the new workspace on top of it. Never run `jj edit` against that revision in the current workspace and never abandon, forget, or rewrite the other workspace.

### Resolve a GitHub PR

Use `gh` only to identify the PR head repository, head bookmark, and URL. In a non-colocated JJ repository, point `gh` at the backing Git repository without invoking Git:

```bash
GIT_DIR=$(jj git root) gh pr view <number-or-url> --json headRefName,headRepository,headRepositoryOwner,isCrossRepository,url
```

Find an existing JJ Git remote for that head repository with `jj git remote list`. If a fork remote is missing, obtain its clone URL with `gh repo view <owner/repo> --json sshUrl,url`, choose a non-conflicting remote name, and add it with `jj git remote add <remote> <url>`. Fetch only through `jj git fetch --remote <remote> --branch <head-bookmark>`.

Create or track the local bookmark from `<head-bookmark>@<remote>`, create the workspace on top of that remote bookmark, and move the local bookmark to the new `@`. Preserve the PR's actual head bookmark; do not create a detached `FETCH_HEAD`, synthetic `pr-<number>` bookmark, or replacement branch. Report the remote and bookmark that a later `jj git push --remote <remote> --bookmark <head-bookmark>` must use. Do not push as part of workspace setup.

## Failure behavior

If `jj workspace add` fails for any reason, especially a sandbox or permission error, the requested isolation was not created. This needs a **blocking** user decision before touching the current workspace. Do not silently continue there, do not retry another destination automatically, and do not leave a bookmark moved to a workspace that was not created.

Report the exact failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema is not loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), or `ask_user` in Pi (through the `pi-ask-user` extension). Offer options such as "work in the current workspace" and "stop and resolve the isolation issue". If no blocking tool exists or the call errors, present numbered options in chat and wait for the reply. Work in the current workspace only after explicit confirmation.

If workspace creation succeeds but bookmark setup fails, keep the workspace, report the partial result, and block before editing. Offer to resolve the bookmark collision or work in the isolated workspace without moving or creating a bookmark. Never delete the workspace or overwrite a bookmark automatically.

## Other workspace operations

Use JJ directly:

```bash
jj workspace list
jj workspace root
jj workspace root --name <workspace>
jj workspace update-stale
jj workspace forget <workspace>
```

`jj workspace forget` only stops tracking the workspace's working-copy revision; it does not delete files on disk. Before forgetting, inspect that workspace's `jj status` and preserve any changes. Delete its directory only when the user explicitly requests deletion and the workspace has been safely forgotten. To switch workspaces, change directory to the root reported for that workspace; JJ has no workspace checkout command.

## When to create a workspace

Create one only when the current directory is not already a dedicated isolated workspace and separate filesystem state is useful:

- Reviewing or updating a GitHub PR while keeping the primary workspace free for other work
- Running multiple features in parallel without changing another workspace's working-copy revision

Do not create another workspace for a single task already running in a dedicated workspace.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects workspace isolation in those flows, run Step 0 first. If the work is already isolated, proceed in place. Otherwise create a JJ workspace with a meaningful workspace name and the correct bookmark or revision target.

## Troubleshooting

**"Workspace already exists"**: inspect `jj workspace list`. If the named workspace is valid, enter its root instead of recreating it. If its directory is gone, preserve any reachable revision, then use `jj workspace forget <workspace>` only with the user's approval before recreating it.

**"Workspace is stale"**: run `jj workspace update-stale` from that workspace. Do not abandon its working-copy revision.

**Bookmark is conflicted or refuses to move**: fetch with `jj git fetch --remote <remote>`, inspect all sides with `jj bookmark list --all-remotes` and `jj log`, and ask the user which lineage to preserve. Do not use `--allow-backwards`, delete a bookmark, or overwrite remote history automatically.
