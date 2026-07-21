---
name: ce-worktree
description: Set up isolated JJ workspaces -- create a new workspace for fresh work, or attach a workspace to an existing bookmark, PR, change, or revision. Use when starting isolated work or isolating an existing target; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated JJ workspace without disturbing the user's primary workspace. Detect existing isolation before creating anything; many coding harnesses provision an isolated workspace at session start.

Order of operations: **detect existing isolation -> prefer a native JJ-workspace tool -> use `jj workspace`.** Never create a workspace the harness cannot enter or track.

**Two modes, set by the caller's need:**

- **New work (default).** No target was named. Create a new workspace and working-copy change from the base bookmark. This is what `ce-work` uses.
- **Isolate an existing target.** The caller names a PR head, bookmark, change, or revision. Create a workspace whose working-copy change is based on that target. JJ workspaces have independent working-copy changes, so do not edit another workspace's working-copy change directly.

The steps below apply to both modes; the mode changes only the starting revision, bookmark handling, and report to the caller.

## Step 0: Detect Existing Isolation

Run from any directory inside the workspace:

```bash
jj workspace root
jj workspace list
jj status
```

Resolve workspace paths with `jj workspace root --name <workspace-name>` when needed. Treat the current workspace as already isolated when the harness says it provisioned the workspace, or when the current root is a registered non-primary workspace created for the task. Also check whether a workspace already exists for the requested target. If one does, report its resolved path and work there instead of creating another.

When already isolated, report the workspace root and current change from `jj log -r @`. In new-work mode, continue there. In isolate-an-existing-target mode, verify that `@` is based on the requested target; use `jj new <target>` only when the current working-copy change is empty and changing its parent will not discard work. Never nest another workspace merely to rename or retarget the current one.

## Step 1: Prefer a Native JJ-Workspace Tool

If the harness provides a primitive that explicitly creates and enters a JJ workspace, use it and stop after verifying the result with `jj workspace root` and `jj workspace list`. A native primitive must preserve the requested starting revision and expose the resulting path to the harness. Do not substitute a native tool that creates a non-JJ workspace.

## Step 2: JJ Workspace Fallback

Use this only when there is no suitable native tool and Step 0 found no existing isolation.

1. **Run from the workspace root.** Move there with `cd "$(jj workspace root)"` before using repo-relative paths.
2. Choose a meaningful ASCII workspace and bookmark name from the work description. Avoid opaque generated names. Resolve the base from a non-root `trunk() & ~root()` revision or the tracked default bookmark. When a tracked default bookmark is used, require exactly one associated remote from JJ's tracking information and retain it. With no associated remote, use the validated local base; with multiple associated remotes, stop and ask rather than choosing a lineage. Do not assume a bookmark name or remote.
3. **Ensure `.workspaces/` is ignored before creating anything.** Inspect the root `.gitignore`; if no existing rule covers the directory, add `.workspaces/`. JJ honors `.gitignore`, and ignored files are not automatically tracked.
4. When the resolved base has an associated remote, best-effort refresh it with `jj git fetch --remote <base-remote> --branch <base-bookmark>` and retain `<base-remote>` through workspace creation. This is non-fatal: if the fetch fails or the base is local-only, continue with the validated local base revision.
5. Create the workspace according to the mode:

```bash
# New work; use the retained tracked remote revision when refreshed, otherwise the validated base revision.
jj workspace add --name <workspace-name> -r <base-bookmark>@<base-remote> .workspaces/<workspace-name>
cd .workspaces/<workspace-name>
jj bookmark create <bookmark-name> -r @

# Existing bookmark, change, tag, or revision.
jj workspace add --name <workspace-name> -r <target> .workspaces/<workspace-name>
cd .workspaces/<workspace-name>
```

Use the validated `trunk()` or local `<base-bookmark>` revision when there is no associated remote bookmark. If the chosen bookmark already exists, do not recreate it; base the new workspace on that bookmark and move it to the completed change only when the owning workflow is ready to publish.

For a GitHub PR, use `gh pr view <number> --json headRefName,headRepository,headRepositoryOwner` to identify its head repository and bookmark. Fetch the head with `jj git fetch --remote <remote> --branch <head-bookmark>`, adding a clearly named remote with `jj git remote add` first only when the contributor repository is not already configured. Create the workspace with `-r <head-bookmark>@<remote>`. Before updating that PR, move or create the local `<head-bookmark>` at the intended completed revision and publish only that bookmark with `jj git push --remote <remote> --bookmark <head-bookmark>`. Do not push unrelated bookmarks.

If `jj workspace add` fails with a sandbox or permission error, isolation was not created. Ask for a **blocking** user decision before touching the current workspace. Use the harness's blocking question interface and offer "work in the current workspace" or "stop and resolve the permission issue". If no blocking interface exists or it errors, present numbered options in chat and wait. Continue in the current workspace only after explicit confirmation; do not retry alternate paths automatically.

## Change Descriptions

Before composing, editing, validating, or recommending a description for `jj workspace add --message`, `jj describe`, or `jj commit`, apply this rule:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Determine syntax from the project's active local standards and actual `git log`; those sources always win over compatible Go guidance. Do not impose a fixed prefix, type, scope, subject/body shape, syntax, wording, template, or example. JJ snapshots working-copy edits automatically, so never introduce a staging step.

## Common Operations

Use JJ directly:

```bash
jj workspace root                              # current workspace root
jj workspace list                              # registered workspaces
jj workspace root --name <workspace-name>      # another workspace's root
jj workspace forget <workspace-name>           # unregister; files remain on disk
jj status                                      # working-copy and bookmark status
jj diff                                        # current change diff
jj log                                         # relevant revision history
jj file annotate <path>                        # line history
jj bookmark list                               # local and remote bookmarks
jj bookmark set <bookmark> -r <revision>       # create or update a bookmark
jj git fetch --remote <remote>                 # refresh remote bookmarks
jj git push --remote <remote> --bookmark <bookmark>
```

After `jj workspace forget`, remove the forgotten workspace directory only if it is safe and the user or owning workflow requested cleanup. Never remove the current workspace.

## Temporary Files

Put temporary files under `$(jj workspace root)/.tmp/workspace-isolation`. If `jj workspace root` is unavailable, use `$PWD/.tmp/workspace-isolation`. Do not place temporary files outside the project.

## When to Create a Workspace

Create one only when the work is not already isolated and needs an independent working copy:

- Reviewing a PR while keeping the primary workspace free for other work
- Running multiple changes in parallel without switching the current working-copy revision

Do not create a workspace for single-task work that can happen safely in the current workspace, and never create a redundant workspace after Step 0 confirms isolation.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "worktree" in those flows, preserve that routing term but execute this JJ workspace workflow. Run Step 0 first; proceed in place when already isolated, otherwise create and enter a workspace with a meaningful name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: resolve its path with `jj workspace root --name <workspace-name>` and enter it, or use `jj workspace forget <workspace-name>` only when the old workspace is no longer needed. Do not silently reuse a workspace for a different target.

**Stale working copy**: from the affected workspace, run `jj workspace update-stale`, then inspect `jj status` and `jj diff` before continuing.

**Cannot forget the current workspace**: enter another registered workspace first, then forget the old workspace by name.
