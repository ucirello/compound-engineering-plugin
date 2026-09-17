---
name: ce-worktree
description: Set up isolated Jujutsu workspaces — create a new bookmark for fresh work, or attach a workspace to an existing bookmark, PR, or change. Use when starting isolated work or isolating an existing ref.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Most coding harnesses now create a workspace by default at session start, so the common case is that **isolation already exists**.

**Done when:** the caller is working in an isolated tree — existing or newly created — and its path and bookmark have been reported, or a blocker has been reported instead.

**Order of operations: detect existing isolation -> prefer a native workspace tool -> fall back to plain jj.** Never create a workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No ref named — create a fresh bookmark from a base (trunk). This is what `ce-work` and `ce-code-review` use when the user picks the worktree option.
- **Isolate an existing ref.** The caller names a PR head, bookmark, or change — attach the workspace to that ref instead of creating a new bookmark. **A working-copy commit belongs to only one workspace at a time.** If the named ref is already the working-copy commit of any workspace (most commonly as the default workspace's `@`), do **not** create a second workspace — report that it is already checked out at `<path>` and let the caller act (work there in place; or, only if a clean separate tree is essential, create a workspace whose working-copy commit is a new change on top of the same commit).

## Step 0: Detect existing isolation

Repo presence: `jj workspace root` succeeding. Workspace membership: `jj workspace list` and `jj workspace root --name <name>`. Do not probe `.jj/` or `.git/`.

```bash
jj workspace root                          # current workspace root
jj workspace list                          # every workspace and its root
jj workspace root --name default           # default (primary) workspace root
```

**Equal** (current root equals default root) -> default workspace; continue to Step 1.

**Different** -> **already isolated**. Report the workspace path (`jj workspace root`) and bookmarks at the working copy (`jj bookmark list -r @`), then **work in place** — a workspace-from-workspace lands in the wrong tree and is invisible to the harness that made the current one. In isolate-an-existing-ref mode, start a change on that ref here with `jj new <ref>` (unless it is already current) rather than nesting a workspace. Use `jj edit <ref>` only when the workflow meant to edit that exact change and it is not another workspace's working-copy commit.

If `jj workspace root` fails, this is not a Jujutsu repository; report a blocker.

## Step 1: Prefer the harness's native workspace tool

If the harness provides a native workspace or worktree primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` creates phantom state the harness cannot see, navigate to, or clean up.

## Step 2: Jujutsu fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the workspace root:** `cd "$(jj workspace root)"`. The paths below are workspace-root-relative, but the skill runs from the user's current directory — without this, `.worktrees/<bookmark>` and the `.gitignore` edit land in a subdirectory (e.g. `src/.worktrees/...`). Do not use `jj -R` here: it selects a repository but does not change cwd.
2. Choose a meaningful bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) — never an opaque auto-generated one. Base: origin's default bookmark, else `main`. `--name` for `jj workspace add` must be a valid workspace name (no slash); when the bookmark name contains slashes, use the last path segment as `--name` and keep the destination `.worktrees/<bookmark-name>`.
3. **Ensure `.worktrees/` is ignored before creating anything:** check `.gitignore` for a `.worktrees/` rule — **with the trailing slash**, so an existing directory-only `.worktrees/` rule is honored even before the directory exists. Not ignored -> add a `.worktrees/` line to `.gitignore`. Do not probe `.git/` or `.jj/`.
4. Refresh the base with `jj git fetch --remote origin -b <from-bookmark>`. This is **non-fatal** — no `origin` remote (`jj git remote list`), a differently-named remote, or a local-only bookmark is not an abort; continue with the local ref.
5. Create the workspace, per mode (run `jj` from the workspace root, not via `jj -R`):
   - **New work:** `jj workspace add --name <workspace-name> .worktrees/<bookmark-name> -r <from-bookmark>@origin` (use the local `<from-bookmark>` ref if `<from-bookmark>@origin` does not exist). Then in the new workspace, `jj bookmark create <bookmark-name> -r @`.
   - **Existing bookmark or tag:** `jj workspace add --name <slug> .worktrees/<slug> -r <target-ref>`.
   - **PR:** identify the head with `GIT_DIR="$(jj git root)" GIT_WORK_TREE="$(jj workspace root)" gh pr view <n>`, fetch that bookmark when it is on origin (`jj git fetch --remote origin -b <headRefName>`), then `jj workspace add --name pr-<n> .worktrees/pr-<n> -r <head-rev>` and in the new workspace `jj bookmark create pr-<n> -r @`. Never leave the workspace working copy without that bookmark: that orphans the fix loop's changes instead of updating the PR. (For push-tracking back to the PR, create the workspace then `cd` in and run `GIT_DIR="$(jj git root)" GIT_WORK_TREE="$(jj workspace root)" gh pr checkout <n>`, which is fork-safe.)
   - If jj reports the ref is already a working-copy commit of another workspace, apply the one-working-copy-one-workspace rule above — do not force a second workspace.
6. `cd` into it, then report the path (`jj workspace root`) and bookmark (`jj bookmark list -r @`).

If `jj workspace add` fails with a sandbox or permission error, the requested isolation does not exist. Do **not** proceed in the current checkout — the user chose isolation specifically to avoid it. Report the failure and ask, offering options such as "work in the current checkout" vs "stop and resolve the permission issue", using the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Only when no such tool is in the list or a real question call errors, present the numbered options in chat and wait for the reply. Never skip the confirmation, and do not retry alternative paths automatically.
