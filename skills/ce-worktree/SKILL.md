---
name: ce-worktree
description: Set up an isolated Jujutsu workspace for fresh work or an existing bookmark, change, revision, or pull request. Use when starting isolated work or attaching an existing target without disturbing another workspace; reuse existing isolation when it already satisfies the request.
---

# Jujutsu Workspace Isolation

Produce a usable isolated JJ workspace and return its path, workspace name, current change, bookmark state, and remote relationship to the caller. The workspace is ready when the requested target is checked out as an editable change, or when a blocker explains why that cannot be done safely.

Invoking this skill authorizes creation of JJ repository metadata, workspaces, changes, and task-scoped bookmarks needed for isolation. It does not authorize discarding work, deleting an existing workspace or bookmark, rewriting unrelated changes, pushing, or changing a pull request without separate authority.

## Operating Rules

- Use JJ workspaces, changes, revisions, and bookmarks. Do not create or manage Git worktrees or branches through Git commands.
- Use JJ's Git interoperability for remote discovery, fetch, tracking, import, export, and push. Use `gh` only to resolve pull-request metadata or perform an explicitly requested pull-request action.
- Treat command spelling as runtime-dependent. Inspect the installed `jj` and `gh` help for the supported form before acting; do not assume fixed syntax from this skill.
- Preserve every existing change and workspace. If a requested operation would abandon, overwrite, or unexpectedly rewrite work, stop and report the conflict.
- At every point that creates or rewrites a change description, follow the project's active instructions and inspect actual history with `jj log`. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local syntax always wins; apply compatible Go guidance only to quality, clarity, and structure. Do not impose a fixed prefix, type, scope, subject, body, layout, template, or example.

## 1. Establish Context

Confirm that the current directory belongs to a JJ repository and identify its repository root, current workspace, current change, colocated Git state, configured remotes, tracked bookmarks, and all existing workspaces.

If the checkout is Git-backed but not yet a JJ repository, ask before initializing a colocated JJ repository. If it is not Git-backed, continue without remote or pull-request behavior. If the current workspace is already isolated and satisfies the requested mode, return it instead of creating another workspace.

Determine the mode from the request:

- **Fresh work:** no existing target was supplied. Start from the project default base and create a new editable change.
- **Existing target:** attach an existing bookmark, change ID, revision, commit, or pull request. Preserve the target's existing history and bookmark relationship.

Resolve ambiguous targets before mutation. A change ID, commit ID, local bookmark, tracked remote bookmark, and pull-request number can overlap textually but require different handling.

## 2. Choose Names And Location

Derive a short ASCII slug from the work. Use a workspace name and any new bookmark under the `ce-worktree/` namespace so skill-created state does not collide with user names. Reuse a caller-supplied bookmark name rather than renaming it.

Place new workspaces under `<workspace-root>/.tmp/rocketclaw/ce-worktree/<repository-key>/`; when no JJ repository exists, use `<current-directory>/.tmp/rocketclaw/ce-worktree/<repository-key>/`. Reject symlinked path components and choose a collision-free workspace directory. Do not migrate unrelated existing workspaces.

The repository key must be stable for the same repository and must not expose credentials or remote URLs. The final workspace directory must be unique; never replace an existing path.

## 3. Resolve The Target

For fresh work, best-effort refresh the configured Git remote through JJ, resolve the remote's default bookmark when available, and otherwise use the project's local default base. Create the workspace at that base, then create one editable child change and describe it according to the message rule above. Create a namespaced bookmark only when the work needs a pushable identity; point it at the intended publishable change.

For an existing local change or revision, add a workspace at that target. If the target is immutable, create an editable child rather than rewriting it and describe the child according to the message rule above. If it is already checked out in another JJ workspace, report that workspace and reuse it when it satisfies the isolation request; otherwise create and describe a separate child change so concurrent work does not share one working-copy change.

For an existing bookmark, refresh and import remote state through JJ when a remote relationship exists. Attach the workspace without silently moving the bookmark. If new edits require a child change, describe it according to the message rule above and keep the bookmark at its existing target until the caller is ready to advance it.

For a pull request, use `gh` to obtain the head repository, head ref, head commit, base ref, and whether the head comes from a fork. Map or add the necessary Git remote without embedding credentials, fetch it through JJ, and attach the workspace to the fetched head with a described editable child. Track or create the corresponding local bookmark only when it can preserve the pull request's actual push destination. If fork permissions or remote mapping cannot be established, create the isolated workspace but report that push-back is blocked; never substitute the base repository as the push destination.

## 4. Verify And Return

From the new workspace, verify that JJ recognizes the workspace, the working copy is on the intended editable change, the parent matches the selected target or base, and any bookmark and remote tracking relationship point where reported. Do not push as part of setup.

Return:

- absolute workspace path;
- JJ workspace name;
- current change ID and parent target;
- bookmark name and target, or `none`;
- tracked remote and push destination, or `none`;
- whether the workspace was reused or created;
- any fetch, fork, permission, or publish blocker the caller must resolve.

If workspace creation fails because of permissions, sandboxing, unsupported installed capabilities, or conflicting JJ state, do not continue in the current workspace without explicit approval. Present the available safe choices and wait for the user's decision.

## Other Operations

For listing, switching, forgetting, or removing workspaces, use the installed JJ workspace capabilities after inspecting their current help. Forgetting JJ workspace metadata and deleting its directory are distinct actions: explain which one is requested, verify that no uncommitted working-copy state would be lost, and obtain explicit approval before deletion.

Use JJ bookmark operations for bookmark movement or deletion and JJ Git interoperability for remote synchronization. A request to remove an isolated workspace does not implicitly authorize deleting its changes or bookmarks.
