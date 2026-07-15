---
name: ce-worktree
description: Set up isolated JJ workspaces -- create a new workspace for fresh work, or attach a workspace to an existing bookmark, PR, change, or revision. Use when starting isolated work or isolating an existing target; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main workspace. Most coding harnesses now create an isolated workspace by default at session start, so the common case is that **isolation already exists** -- detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a compatible native workspace tool -> fall back to plain JJ and report the resulting path.** Every newly created workspace must live under the current JJ workspace's `.tmp/rocketclaw/` directory, or the local `.tmp/rocketclaw/` fallback when the workspace root cannot be resolved.

**Two modes, set by the caller's need:**

- **New work (default).** No specific revision named -- create a fresh working-copy change from the repository's trunk. This is what `ce-work` uses.
- **Isolate an existing target.** The caller names a target to work on in isolation -- a PR head, an existing bookmark, a change, or a revision. Create the workspace with a new working-copy change on top of that target. If the target is already the working-copy change of another workspace, do not edit that same change from two workspaces; report the existing workspace path and let the caller work there or create a new child change in a separate workspace.

The steps below (detect -> native tool -> JJ fallback) apply to both modes; the mode only changes the parent revision of the new working-copy change and what is reported back to the caller.

## Step 0: Detect existing isolation

Before creating anything, resolve the current workspace root and enumerate all workspaces with their absolute roots:

```bash
jj workspace root
jj workspace list -T 'name ++ "\t" ++ root ++ "\n"'
```

Use the harness's session context and the listed roots to determine whether the current root is already a task-specific isolated workspace. In particular, a current root selected or created by the harness, or one under `.tmp/rocketclaw/`, is already isolated. Report its path and current working-copy change with `jj log -r @`; do not create another workspace. Then **work in place**: in new-work mode, continue here; in isolate-an-existing-target mode, resolve the target to exactly one revision with `jj log -r '<target>'` and use `jj new '<target>'` unless `@` is already a child working-copy change on that target. Before switching, inspect `jj log -r 'working_copies()'` and do not use `jj edit` or otherwise take over a change that is another workspace's working copy. If the current working-copy change contains unrelated work, stop and ask before replacing it with a new child of the target.

## Step 1: Prefer the harness's native workspace tool

If the harness provides a native workspace primitive, use it only when it supports an explicit destination under `$(jj workspace root)/.tmp/rocketclaw/<workspace-name>` (or local `.tmp/rocketclaw/<workspace-name>` when the root is unavailable) and creates or registers a JJ workspace there. Report the resulting root and verify it with `jj workspace list`; do not use a native primitive that creates a Git worktree, places temporary files elsewhere, or leaves the directory unregistered with JJ.

## Step 2: JJ fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Resolve the workspace-local temporary root.** Run `workspace_root="$(jj workspace root 2>/dev/null || pwd -P)"`; use `$workspace_root/.tmp/rocketclaw/<workspace-name>` as the destination. If `jj workspace root` is unavailable, use local `.tmp/rocketclaw/<workspace-name>`. Do not use any other temporary location.
2. Choose a meaningful workspace name from the work description without imposing a fixed prefix, type, scope, template, or example. Resolve the caller's target to exactly one JJ revision with `jj log -r '<target>'`; for fresh work, resolve `trunk()` after any fetch. Reject an ambiguous or missing target rather than guessing.
3. **Ensure `.tmp/` is ignored before creating anything**, so workspace contents are never snapshotted. Honor an existing repository or local Git-exclude rule. Otherwise add `.tmp/` to the repository's `.gitignore` as an intentional tracked change before creating the directory; do not place an ignore helper in another temporary directory.
4. Best-effort refresh without disturbing the current workspace. Discover configured remotes with `jj git remote list`; do not assume a remote name. For fresh work, run `jj git fetch --remote <remote>` and then resolve `trunk()`. For a named remote bookmark, run `jj git fetch --remote <remote> --branch <bookmark>` and resolve `<bookmark>@<remote>`. This is **non-fatal** when there is no remote or the repository is local-only, but a caller-requested remote target that still cannot be resolved is a blocking error rather than permission to use a different revision.
5. Create the workspace -- the command depends on the mode:
   - **New work:** `jj workspace add --name <workspace-name> -r 'trunk()' "$workspace_root/.tmp/rocketclaw/<workspace-name>"`. This creates a new working-copy change on top of trunk; do not create a bookmark until one is needed for Git interoperability or publishing.
   - **Isolate an existing target:** `jj workspace add --name <workspace-name> -r '<target-revision>' "$workspace_root/.tmp/rocketclaw/<workspace-name>"`. This creates a new working-copy change on top of the resolved target instead of editing the target itself. First inspect `jj log -r 'working_copies()'`; if the target itself is another workspace's working-copy change, use the target only as the parent of this new change and never edit it directly. For a **PR**, preserve GitHub interoperability: use `gh pr view <n>` to identify the head bookmark and repository, ensure its Git remote exists with `jj git remote list` / `jj git remote add`, fetch it with `jj git fetch --remote <remote> --branch <head-bookmark>`, verify `<head-bookmark>@<remote>` resolves to exactly one revision, then use that remote bookmark as the parent revision. Create or track the local bookmark only when needed to update the PR, move it to the completed revision with `jj bookmark move <head-bookmark> --to <completed-revision>`, and publish it with `jj git push --bookmark <head-bookmark> --remote <remote>`. If a required `gh` operation mutates the colocated Git repository, run a JJ command afterward so automatic import occurs; in a non-colocated repository, run `jj git import` explicitly.
6. Switch into it: `cd "$workspace_root/.tmp/rocketclaw/<workspace-name>"` (or local `.tmp/rocketclaw/<workspace-name>` when using the fallback).

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current workspace -- do not silently continue there (the user chose isolation specifically to avoid it, especially when `ce-work` / `ce-code-review` routed here for the workspace option). Report the failure and use the host platform's blocking question interface to offer "work in the current workspace" and "stop and resolve the permission issue." If no blocking interface exists or the call errors, present numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current workspace on explicit confirmation, and do not retry alternative paths automatically.

## Other workspace operations

Use `jj` directly -- no wrapper is needed:

```bash
jj workspace list
jj workspace root --name <workspace-name>
jj workspace forget <workspace-name>  # stop tracking; remove files separately
cd "$(jj workspace root)"              # return to the current workspace root
```

## When to create a workspace

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current workspace free for other work
- Running multiple features in parallel without changing the current working-copy change

Do not create a workspace for single-task work that can happen in the current workspace -- and never when Step 0 shows you are already in an isolated one.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "worktree" in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create a workspace (native tool preferred) with a meaningful name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the name or path is in use. Switch to the root shown by `jj workspace root --name <workspace-name>`, or run `jj workspace forget <workspace-name>` and remove its files before recreating.

**Stale workspace**: from that workspace, run `jj workspace update-stale`.
