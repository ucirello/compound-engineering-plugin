---
name: ce-worktree
description: Set up isolated Jujutsu workspaces for fresh work or an existing bookmark, pull request, change, or revision. Use when starting isolated work or isolating an existing ref.
---

# Workspace Isolation

Ensure the current work happens in an isolated Jujutsu workspace without disturbing the user's primary workspace.

**Done when:** the caller is working in an existing or newly created isolated workspace and its path, workspace name, working-copy change, and relevant bookmark have been reported, or a blocker has been reported.

**Order:** detect existing isolation, prefer a native workspace capability the host can enter, then use `jj workspace`. Never create an isolated workspace the host cannot use.

## Interpret The Request

- **New work:** create an isolated workspace at the requested base revision, normally the remote default bookmark.
- **Existing work:** create or reuse an isolated workspace at the named bookmark, pull-request revision, change ID, commit ID, or revset. A Jujutsu bookmark is not checked out or active and may be used by several workspaces; each workspace has its own working-copy change.

Resolve GitHub pull-request metadata with `gh`. Fetch remote state with `jj git fetch`, then address imported Git branches as remote bookmarks such as `<name>@<remote>`. Keep `gh`; for a non-colocated Jujutsu repository, set `GIT_DIR` to the value of `jj git root` for the individual `gh` call.

## Detect Existing Isolation

Run `jj root` and `jj workspace list`. Resolve the current root with `jj workspace root`. If the repository has more than one workspace and the current root is not the repository's primary workspace root, report the current path, workspace name, working-copy change (`jj log -r @`), and bookmarks pointing to it, then work in place. Do not nest another workspace merely because the caller requested isolation.

If the current directory is outside a Jujutsu repository, report the blocker. Do not silently substitute another VCS isolation mechanism.

## Prefer Native Isolation

If the host exposes a native isolated-workspace primitive that returns a path the host can enter and confirms it is backed by the same Jujutsu repository, use it and stop. A user-facing command that the agent cannot invoke is not such a primitive.

## Jujutsu Fallback

Run from the path returned by `jj root` and keep workspaces under the workspace-root `.tmp/rocketclaw/workspaces/` directory. Ensure `.tmp/` is ignored before creating the directory; Jujutsu honors `.gitignore` files. Choose a meaningful ASCII workspace name and path from the work description, without fixed type prefixes.

1. Discover remotes with `jj git remote list`. Fetch the selected remote with `jj git fetch --remote <remote>` when available; fetch failure is non-fatal when the requested base already resolves locally.
2. Resolve the base to exactly one revision with `jj log -r '<base-revset>' --no-graph`. Prefer the repository's tracked remote default bookmark; use repository metadata from `gh repo view --json defaultBranchRef` when necessary. Stop on an empty, conflicted, or multi-revision result.
3. Create the workspace with `jj workspace add --name <workspace-name> -r '<base-revset>' .tmp/rocketclaw/workspaces/<workspace-name>`. For fresh work, the new working-copy change is the feature change. For existing work, the named change or revision is the parent unless the caller explicitly asked to edit it, in which case use `jj edit -r '<target-revset>'` inside the new workspace.
4. Enter the returned path, run `jj workspace update-stale` if Jujutsu reports stale working-copy state, and verify with `jj workspace root`, `jj status`, and `jj log -r @`.
5. Do not create a bookmark merely to begin work. Create or move one only when a stable Git-visible name is required for push or pull-request interoperability, and point it at the intended completed revision rather than an empty working-copy child.

If workspace creation fails because of permissions, a stale registration, or an unsafe path, do not continue in the current workspace. Report the command failure and ask whether to work in place or stop and resolve isolation. Cleanup is two-part: `jj workspace forget <workspace-name>` unregisters the workspace; filesystem removal is separate and must occur only when its work is integrated or explicitly abandoned.
