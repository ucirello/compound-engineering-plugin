---
name: ce-worktree
description: Set up an isolated Jujutsu workspace for fresh work or an existing bookmark, change, revision, or pull request. Use when starting isolated work or attaching an existing target without disturbing another workspace; reuse existing isolation when it already satisfies the request.
---

# Jujutsu Workspace Isolation

Produce a usable isolated Jujutsu workspace without disturbing the user's other workspaces. The workspace is ready when the requested target is available as a distinct editable working-copy change and the caller has its path, workspace name, change, bookmark state, and remote relationship, or a blocker explains why isolation cannot be created safely.

Invoking this skill authorizes creation of Jujutsu repository metadata, workspaces, changes, and task-scoped bookmarks needed for isolation. It does not authorize discarding work, deleting an existing workspace or bookmark, rewriting unrelated changes, pushing, or changing a pull request without separate authority.

## Operating Rules

- Use Jujutsu workspaces, working-copy changes, revisions, revsets, and bookmarks. Do not create or manage Git worktrees or branches with Git commands.
- Use `jj git` for remote discovery, fetch, tracking, import, export, and push. Use `gh` only for GitHub metadata and explicitly requested GitHub actions.
- Inspect installed command help before mutation when syntax varies by Jujutsu version. Runtime capabilities and the project's active instructions take precedence over spellings shown here.
- Preserve every existing change and workspace. Stop if an operation would abandon, overwrite, or unexpectedly rewrite existing work.
- Run shell examples in a POSIX shell; on native Windows, use Git Bash. Resolve and quote physical paths so drive-letter, separator, and whitespace differences do not create or match the wrong workspace.
- Do not add branding, generated-by text, or creator, model, provider, tool, agent, runtime, workflow, co-author, or other attribution.

## Establish Context

From the caller's current directory, identify the repository root, current workspace, current working-copy change, all registered workspaces, bookmarks, Git colocation state, and configured remotes with Jujutsu commands. Use `jj workspace root`, `jj workspace list`, `jj status`, `jj log`, `jj bookmark list`, `jj git colocation status`, and `jj git remote list` as supported by the installed runtime.

If the current directory is not in a Jujutsu repository, stop and report that state; do not substitute another version-control workflow or initialize Jujutsu without approval. If the current registered workspace already provides task-specific isolation, return it instead of creating another workspace. Before changing what any workspace edits, preserve occupied changes; never make two workspaces edit the same working-copy change.

Git-backed repositories may be colocated or non-colocated. A colocated root has `.jj` and `.git` and automatically imports and exports Git refs on Jujutsu commands; a non-colocated Git backend keeps its bare Git repository under `.jj`. A Jujutsu workspace has a linked `.jj` directory. Do not infer isolation, repository identity, or remote state from the presence, shape, or location of `.git`, and keep Git use read-only except where the mandated sentence literally mentions `git log`.

Determine the mode from the request:

- **Fresh work:** no existing target was supplied. Resolve the project's actual trunk or base and create a new editable child change.
- **Existing target:** resolve a bookmark, pull request, change ID, commit ID, tag, or caller-supplied revset to exactly one revision and create an editable child. Use `jj edit` only when the caller explicitly intends to rewrite that exact revision and no other workspace edits it.

## Create Isolation

Order of operations: detect suitable existing Jujutsu isolation, then use a native isolation primitive only if it can create a registered Jujutsu workspace at the required path, otherwise use `jj workspace add`. Never create a nested or unregistered workspace.

Every newly created workspace must be under `<repository-root>/.tmp/workspaces/<workspace-name>`. Do not create it elsewhere, including an OS-global temporary directory or a product-specific subdirectory. Choose a short, meaningful ASCII name and a collision-free path. Before creation, require the repository's active ignore mechanism to exclude `.tmp/`; because Jujutsu honors `.gitignore` and has no `.jjignore`, ask before making the smallest project-conventional ignore change when `.tmp/` is not already ignored.

Resolve the starting revision before creation:

- For fresh work, prefer a configured `trunk()` alias or the repository's established trunk bookmark. Otherwise inspect local and remote bookmarks and determine the actual default line without guessing a common name.
- For a local bookmark, start a child from its target; creating the child does not move the bookmark.
- For a remote bookmark, resolve `<bookmark>@<remote>` and fetch the ownership-matched remote with `jj git fetch --remote <remote>` when freshness matters.
- For another revision or revset, use `jj log` and the installed runtime's revset syntax to prove it resolves exactly once. Do not pin a log template or fixed query form.
- For a GitHub pull request, use `gh pr view <target> --json headRefName,headRefOid,headRepository,baseRepository,isCrossRepository` to identify its source. Match that source against `jj git remote list`; reuse the matching remote or add a narrowly scoped one with `jj git remote add`, then fetch it with `jj git fetch --remote <remote>`. Resolve the fetched remote bookmark and retained head object ID to the same revision before creating the child. Never substitute the base repository as a fork's push destination.

Inspect `jj workspace add --help`, then create the workspace with the installed runtime's supported destination, name, and revision options. The result must be a registered workspace at the required `.tmp/workspaces/` path with a distinct working-copy change parented by the resolved starting revision. Enter the exact path reported by `jj workspace root --name <workspace-name>` and verify the result with `jj workspace list`, `jj status`, and `jj log`.

If creation fails because of sandboxing, permissions, path state, stale workspace state, unsupported capabilities, or revision resolution, isolation was not created. Ask a blocking question before working in the current workspace, offering at least "work in the current workspace" and "stop and resolve isolation". If no blocking-question capability exists or it errors, present numbered choices in chat and wait. Work in place only after explicit confirmation; do not retry unrelated paths automatically.

## Preserve Publication

Isolation must not strand work that the caller intends to release or return to an existing pull request. Keep or create a local bookmark only when a pushable identity is needed, preserve its target and tracked remote relationship, and retain the exact source remote for fork pull requests. Do not move a bookmark merely by creating a child change.

When publication is explicitly requested later, first advance the intended bookmark to the publishable revision, verify its remote mapping, and use the installed `jj git push` form with an explicit remote and bookmark. Use `gh` to create, inspect, or update the GitHub pull request. If authentication, fork permissions, remote ownership, bookmark safety, or empty descriptions prevent publication, return the isolated workspace and report the blocker rather than pushing somewhere else. Workspace setup itself never pushes.

## Return

Return the absolute workspace path, Jujutsu workspace name, current change ID and parent target, bookmark name and target or `none`, tracked remote and push destination or `none`, whether the workspace was reused or created, and any fetch, fork, permission, or publication blocker.

The public functional name remains `ce-worktree`. Callers using that name are requesting Jujutsu workspace isolation, not a Git worktree.

## Other Workspace Operations

Use installed Jujutsu workspace commands for listing, locating, updating, and forgetting workspaces. `jj workspace forget` removes registration but does not delete workspace files. Forgetting metadata, deleting a workspace directory, abandoning its working-copy change, and deleting its bookmarks are distinct actions; perform only the requested action after leaving the workspace and confirming no work or artifacts would be lost.

For a stale workspace, enter it, run `jj workspace update-stale`, and inspect the recovered state. If a workspace directory was removed first, use a surviving workspace to resolve and forget only the exact missing registration.
