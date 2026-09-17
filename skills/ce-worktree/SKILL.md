---
name: ce-worktree
description: Set up isolated Jujutsu workspaces — create a new bookmark for fresh work, or attach a workspace to an existing bookmark, PR, or change. Use when starting isolated work or isolating an existing ref.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Most coding harnesses now create a workspace by default at session start, so the common case is that **isolation already exists**.

**Done when:** the caller is working in an isolated workspace — existing or newly created — and its path and bookmark have been reported, or a blocker has been reported instead.

**Order of operations: detect existing isolation -> prefer a native worktree tool -> fall back to `jj workspace add`.** Never create a workspace the harness cannot see.

Run every `jj` command with cwd at that workspace's absolute root (`cd` there first). Do not use `jj -R` (it selects a repository and does not change the working directory). Do not read or parse `.jj/` or `.git/`. Discover workspace membership with `jj workspace list` and `jj workspace root --name <name>`.

**Two modes, set by the caller's need:**

- **New work (default).** No ref named — create a fresh bookmark from a base (trunk). This is what `ce-work` and `ce-code-review` use when the user picks the worktree option.
- **Isolate an existing ref.** The caller names a PR head, bookmark, or change — attach the workspace to that ref instead of creating a new bookmark. If `jj workspace root --name <name>` already resolves, or an existing workspace's working copy is already that ref, do **not** add a second workspace — report that it is already at `<path>` and let the caller act (work there in place; or, only if a clean separate tree is essential, add a workspace at the same revision with a different `--name`).

## Step 0: Detect existing isolation

Compare the current workspace root to the `default` workspace root. `jj workspace root` prints an absolute path from any subdirectory, so this compare does not need filesystem identity:

```bash
jj workspace root
jj workspace root --name default
jj workspace list
```

**Equal** (current root is the `default` workspace) -> primary checkout; continue to Step 1.

**Different** -> **already isolated**. Report the workspace path (`jj workspace root`) and current bookmarks (`jj log -r @ -T 'bookmarks ++ "\n"' --no-graph`), then **work in place** — a workspace-from-workspace lands in the wrong tree and is invisible to the harness that made the current one. In isolate-an-existing-ref mode, move this workspace onto that ref with `jj new <ref>` or `jj edit <ref>` (unless it is already current) rather than nesting a workspace.

If `jj workspace root --name default` fails, use `jj workspace list`: one workspace means this is the primary checkout (continue to Step 1); more than one means the current workspace is already isolated (work in place).

## Step 1: Prefer the harness's native worktree tool

If the harness provides a native worktree primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` creates phantom state the harness cannot see, navigate to, or clean up.

## Step 2: `jj workspace add` fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the workspace root:** `cd "$(jj workspace root)"`. The paths below are workspace-root-relative, but the skill runs from the user's current directory — without this, `.worktrees/<name>` and the `.gitignore` edit land in a subdirectory (e.g. `src/.worktrees/...`).
2. Choose a meaningful workspace name (and, for new work, bookmark name) from the work description (e.g. `feat/login`, `fix/email-validation`) — never an opaque auto-generated one. Base: origin's default bookmark, else `main`.
3. **Ensure `.worktrees/` is ignored before creating anything:** at the workspace root, if `.gitignore` has no `.worktrees/` line — **with the trailing slash**, so a directory-only `.worktrees/` rule is honored even before the directory exists (without the slash the probe misses it and dirties a correctly-configured repo) — add that line. Do not probe ignore rules by reading `.git/` or `.jj/`.
4. Refresh the base with `jj git fetch --remote origin --branch <from-bookmark>`. This is **non-fatal** — no `origin` remote, a differently-named remote, or a local-only bookmark is not an abort; continue with the local ref.
5. Create the workspace, per mode (cwd stays the primary workspace root until the next step):
   - **New work:** `jj workspace add .worktrees/<name> --name <name> -r '<from-bookmark>@origin'` (use the local `<from-bookmark>` ref if `<from-bookmark>@origin` does not exist).
   - **Existing bookmark or tag:** `jj workspace add .worktrees/<slug> --name <slug> -r <target-ref>`.
   - **PR:** attach on a **local bookmark** `pr-<n>` so later changes can update the PR — `jj workspace add .worktrees/pr-<n> --name pr-<n>`, then from that workspace root run `GIT_DIR=$(jj git root) gh pr checkout <n>` (fork-safe). Never leave the workspace without a bookmark: that orphans the fix loop's changes instead of updating the PR.
   - If `jj workspace root --name <name>` already resolves, apply the one-name-one-workspace rule above — do not force a second workspace.
6. `cd` into the new workspace destination. For new work, then `jj bookmark create <name>`. Report the path (`jj workspace root`) and bookmark (`jj log -r @ -T 'bookmarks ++ "\n"' --no-graph`). Further `jj` commands use that cwd.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation does not exist. Do **not** proceed in the current checkout — the user chose isolation specifically to avoid it. Report the failure and ask, offering options such as "work in the current checkout" vs "stop and resolve the permission issue", using the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Only when no such tool is in the list or a real question call errors, present the numbered options in chat and wait for the reply. Never skip the confirmation, and do not retry alternative paths automatically.
