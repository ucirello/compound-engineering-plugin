---
name: ce-worktree
description: Set up isolated Jujutsu workspaces for fresh work or an existing bookmark, pull request, change, or revision. Use when starting isolated work or isolating an existing ref.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Most coding harnesses now create a workspace by default at session start, so the common case is that **isolation already exists**.

**Done when:** the caller is working in an isolated workspace — existing or newly created — and its path and bookmark have been reported, or a blocker has been reported instead.

**Order of operations: detect existing isolation -> prefer a native workspace tool -> fall back to public `jj`.** Never create a workspace the harness cannot see.

Use public `jj` only. Never read or parse `.jj/` or `.git/` files, and never treat their presence as repo identity. Identify workspaces with `jj workspace list` and `jj workspace root` / `jj workspace root --name <name>`. When a `jj` command must run against a workspace, set that command's cwd to that workspace's absolute root — do not use `jj -R`. If `jj` cannot provide a required fact, stop and report the gap.

**Two modes, set by the caller's need:**

- **New work (default).** No ref named — create a fresh bookmark from a base (trunk). This is what `ce-work` and `ce-code-review` use when the user picks the isolation option.
- **Isolate an existing ref.** The caller names a PR head, bookmark, or revision — attach the workspace to that ref instead of creating a new bookmark. If a workspace already exists for that named ref, do **not** add a second — report that it is already at `<path>` (`jj workspace root --name <name>`) and let the caller act (work there in place; or, only if a clean separate tree is essential, add another workspace at the same revision without moving the existing bookmark).

## Step 0: Detect existing isolation

Compare the current workspace root to the default workspace root. Both commands print absolute paths:

```bash
jj workspace root
jj workspace root --name default
```

**Equal** -> primary checkout; continue to Step 1.

**Different** -> **already isolated**. Report the workspace path (`jj workspace root`) and the bookmark(s) on `@` (`jj log -r @ -T 'bookmarks' --no-graph`), then **work in place** — a workspace-from-workspace lands in the wrong tree and is invisible to the harness that made the current one. In isolate-an-existing-ref mode, point this workspace at that ref with `jj new <ref>` (or `jj edit <ref>` when the caller needs to edit that change) unless it is already `@`, rather than nesting a workspace.

If `jj workspace root --name default` fails, use `jj workspace list` and `jj workspace root --name <name>` for each listed name. One workspace whose root equals the current root -> primary checkout; continue to Step 1. Current root matches a non-default name -> already isolated. If `jj` still cannot identify the primary workspace, stop and report that gap.

## Step 1: Prefer the harness's native workspace tool

If the harness provides a native worktree or workspace primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` creates phantom state the harness cannot see, navigate to, or clean up.

## Step 2: Jujutsu fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the current workspace root.** Set `workspace_root` from `jj workspace root` and run every later `jj` command with cwd at the workspace it targets. The destination below is repo-root-relative; without this, `.tmp/rocketclaw/workspaces/<slug>` lands in a subdirectory (e.g. `src/.tmp/...`).
2. Choose a meaningful bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) — never an opaque auto-generated one. Workspace `--name` and the destination slug are ASCII without `/` (replace `/` with `-`). Base: `main@origin`, else `trunk@origin`, else local `main`.
3. Create workspaces under `.tmp/rocketclaw/workspaces/<slug>` of `workspace_root` (create that directory first if needed). Do not edit `.gitignore`.
4. Refresh the base with `(cd "$workspace_root" && jj git fetch)`. This is **non-fatal** — no `origin` remote, a differently-named remote, or a local-only bookmark is not an abort; continue with the local ref.
5. Add the workspace with one skeleton, cwd `workspace_root`:

   `(cd "$workspace_root" && jj workspace add --name <slug> --revision <rev> .tmp/rocketclaw/workspaces/<slug>)`

   Then `new_root=$(cd "$workspace_root" && jj workspace root --name <slug>)`.

   - **New work:** `<rev>` is the base from step 2. Then `(cd "$new_root" && jj bookmark create <bookmark-name>)`.
   - **Existing bookmark or tag:** `<rev>` is the target ref. Do not create a second bookmark unless the target has none.
   - **PR:** fetch the head, then add at that revision, then `(cd "$new_root" && jj bookmark create pr-<n>)` so later fixes can update the PR. Never leave the new workspace without that local bookmark — an anonymous fetched revision orphans the fix loop. Fetch with `(cd "$workspace_root" && jj git fetch --branch pull/<n>/head)` when the remote advertises it (`<rev>` is then `pull/<n>/head@origin` or the imported bookmark). For fork-safe push-tracking, add the workspace first, then `(cd "$new_root" && GIT_DIR=$(jj git root) gh pr checkout <n>)` and ensure bookmark `pr-<n>` points at `@`.
   - If `jj workspace list` already shows a workspace for this slug or named ref, apply the one-workspace-per-named-ref rule above — do not add a second.
6. `cd` into `$new_root`, then report the path (`jj workspace root`) and bookmark.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation does not exist. Do **not** proceed in the current checkout — the user chose isolation specifically to avoid it. Report the failure and ask, offering options such as "work in the current checkout" vs "stop and resolve the permission issue", using the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Only when no such tool is in the list or a real question call errors, present the numbered options in chat and wait for the reply. Never skip the confirmation, and do not retry alternative paths automatically.
