---
name: ce-worktree
description: Set up isolated JJ workspaces for fresh work or an existing bookmark, PR, change, or revision. Use when starting isolated work or attaching an existing target without disturbing another workspace; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated JJ workspace without disturbing the user's primary workspace. Coding harnesses may create one at session start, so detect that first and do not create a redundant workspace.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to `jj workspace`.** Never create a workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No specific target named: create a fresh workspace and change from the trunk base. This is what `ce-work` uses.
- **Isolate an existing target.** The caller names a PR head, bookmark, change ID, or revision. Attach the workspace to that target instead of starting from trunk. JJ workspaces may point at the same revision, but each workspace must have a distinct workspace name and working-copy change. When the target is already the working copy of another workspace, create the isolated workspace at that target revision; do not move or abandon the other workspace's working-copy change.

The steps below apply to both modes; the mode only changes the revision used to create the workspace and what is reported to the caller.

## Step 0: Detect existing isolation

Run from anywhere inside the current workspace:

```bash
jj workspace root
jj workspace list
jj status
```

Use `jj workspace root` as the resolved absolute current workspace path and `jj workspace list` to identify the current workspace and the other workspaces in the repository.

- If the current workspace was created by the harness or is already a non-primary workspace for this task, report its path and current change/bookmarks from `jj status` and `jj log -r @ -n 1`. Do not nest another workspace. In new-work mode, continue in place. In existing-target mode, update this workspace to the requested revision only when doing so will not discard or mix unrelated work.
- If the current workspace is the user's primary workspace and separate isolation is needed, continue to Step 1.
- If the directory is not in a JJ repository, stop and report that JJ workspace isolation is unavailable. Do not fall back to operational Git commands.

## Step 1: Prefer the harness's native workspace tool

If the harness provides a native workspace primitive, use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. Do not create behind-the-back workspace state when a native primitive exists.

## Step 2: JJ fallback

Only when there is no native tool and Step 0 found no existing isolation.

1. **Run from the workspace root:** `cd "$(jj workspace root)"`. The `.workspaces/` path below is root-relative, and the skill may start in a subdirectory.
2. Choose a meaningful ASCII workspace name and path slug from the work description, avoiding opaque generated names. Choose the base revision from repository-local conventions, defaulting to `trunk()`.
3. The orchestrator owns ignore configuration. Do not inspect or edit `.gitignore`.
4. Best-effort refresh remote state with `jj git fetch --remote <remote>`. This is non-fatal when no remote is configured or the work is local-only; use the local revision.
5. Create the workspace according to the mode:
   - **New work:** `jj workspace add --name <workspace-name> --revision <base-revision> .workspaces/<slug>`, then run `jj new <base-revision>` in the new workspace if `jj workspace add` did not already create a fresh working-copy change.
   - **Existing bookmark, change, or revision:** `jj workspace add --name <workspace-name> --revision <target-revision> .workspaces/<slug>`. For a PR, first use `gh pr checkout <n>` in a temporary JJ workspace when needed to obtain the fork-safe PR head, then identify that head with `jj log` and create or retain a local JJ bookmark for the fetched PR head and for pushing updates.
6. Switch into it: `cd .workspaces/<slug>`, then confirm with `jj workspace root`, `jj status`, and `jj log -r @ -n 1`.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current workspace. Report the failure and use the platform's blocking question capability to offer "work in the current workspace" or "stop and resolve the permission issue." If no blocking capability exists or it errors, present numbered options in chat and wait. Work in the current workspace only on explicit confirmation; do not retry alternative paths automatically.

## Other workspace operations

Use JJ directly:

```bash
jj workspace list                              # list workspaces
jj workspace forget <workspace-name>           # forget after its directory is removed
cd .workspaces/<slug>                          # switch to a workspace
cd "$(jj workspace root)"                      # return to the current workspace root
jj workspace update-stale                      # repair a stale working copy
```

Before removing a workspace directory, inspect it with `jj status` and preserve any wanted change. Never delete a workspace containing unreviewed work.

## When to create a workspace

Create one only when you are not already isolated and need a separate workspace:

- Reviewing a PR while keeping the primary workspace free for other work
- Running multiple features in parallel without moving the primary working-copy change

Do not create a workspace for a single task that can safely happen in the current isolated workspace, and never when Step 0 shows suitable isolation already exists.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects workspace isolation in those flows, run Step 0 first: proceed in place when already isolated; otherwise create a workspace, preferring the native tool, with a meaningful name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: inspect `jj workspace list`. Switch to the existing path or choose a distinct workspace name and path; do not overwrite it.

**Stale workspace**: enter it and run `jj workspace update-stale`, then inspect `jj status` before continuing.
