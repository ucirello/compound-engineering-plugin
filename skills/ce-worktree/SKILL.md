---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark for fresh work, or attach a workspace to an existing bookmark, PR, or change. Use when starting isolated work or isolating an existing ref.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Most coding harnesses now create a workspace by default at session start, so the common case is that **isolation already exists**.

**Done when:** the caller is working in an isolated workspace — existing or newly created — and its path and bookmark have been reported, or a blocker has been reported instead.

**Order of operations: detect existing isolation -> prefer a native worktree tool or workspace tool -> fall back to `jj workspace add`.** Never create a workspace the harness cannot see.

Do not inspect `.jj/` or `.git/`. Membership is `jj workspace list` plus `jj workspace root --name <name>` only.

**Two modes, set by the caller's need:**

- **New work (default).** No ref named — create a fresh bookmark from a base (trunk). This is what `ce-work` and `ce-code-review` use when the user picks the worktree option.
- **Isolate an existing ref.** The caller names a PR head, bookmark, or change — attach the workspace to that ref instead of creating a new bookmark. If the named ref already has a workspace (a listed name whose `jj workspace root --name` succeeds, or a workspace whose `@` already carries that bookmark), do **not** add a second workspace — report that it is already isolated at `<path>` and let the caller act (work there in place; or, only if a clean separate tree is essential, add a workspace whose working-copy parent is that same revision).

## Step 0: Detect existing isolation

```bash
workspace_root=$(jj workspace root) || { echo "not a jj workspace" >&2; exit 1; }
```

If `jj workspace root` fails, this is not a JJ workspace — report that blocker and stop. Do not walk the filesystem for `.jj/` or `.git/`.

List membership with `jj workspace list`. Resolve each listed name with `jj workspace root --name <name>` (absolute path). The current workspace is the listed name whose resolved root equals `$workspace_root`. The primary checkout is `jj workspace root --name default`.

**Current root equals default** (or `default` is absent and the list has a single workspace) -> primary checkout; continue to Step 1.

**Current root differs from default** (or `default` is absent and more than one workspace is listed, and the current name is not the only one) -> **already isolated**. Report the workspace path (`jj workspace root`) and bookmarks on `@` (`jj log -r @ --no-graph -T 'bookmarks'`, cwd = that workspace root), then **work in place** — a workspace-from-workspace lands in the wrong tree and is invisible to the harness that made the current one. In isolate-an-existing-ref mode, `jj new <target-ref>` here (unless that ref is already current) rather than nesting a workspace.

When running any `jj` command against a workspace, set that command's working directory to that workspace's absolute root. `jj -R` selects a repository but does not change cwd.

## Step 1: Prefer the harness's native worktree/workspace tool

If the harness provides a native worktree primitive or workspace primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, a `--worktree` flag, or a session-move-into-workspace tool that both places and tracks the tree — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` creates phantom state the harness cannot see, navigate to, or clean up (`jj workspace forget` is then the harness's problem, not a fallback cleanup step).

If the harness can only move the session into a directory after one exists, continue to Step 2, then invoke that move on the new workspace root so the harness tracks it.

## Step 2: JJ workspace fallback

Only when there is no native create tool **and** Step 0 found no existing isolation.

1. **Run from the primary checkout root:** `default_root=$(jj workspace root --name default)` (if `default` is absent, use the sole listed workspace root). `cd` there. Destinations below are that-root-relative, but the skill runs from the user's current directory — without this, `.tmp/<name>` lands in a subdirectory.
2. Choose a meaningful workspace and bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) — never an opaque auto-generated one. Base: trunk bookmark (`jj bookmark list` / remote bookmarks such as `main@origin`), else `main`. `gh` is OK for GitHub's default branch; run `(cd "$default_root" && jj git root)` first, then pass that path as `GIT_DIR` on the `gh` call.
3. **Ensure `.tmp/` is ignored before creating anything.** Isolation workspaces live under `$(jj workspace root --name default)/.tmp/<name>`, never OS-global temp. If `.gitignore` has no `.tmp/` line, add one. Create the `.tmp` directory if it does not exist.
4. Refresh the base with `(cd "$default_root" && jj git fetch)`. This is **non-fatal** — no `origin` remote, a differently-named remote, or a local-only bookmark is not an abort; continue with the local ref.
5. Create the workspace, per mode (`(cd "$default_root" && jj workspace add ...)`):
   - **New work:** `jj workspace add --name <name> -r <from-bookmark> .tmp/<name>` (use the local bookmark if `<from-bookmark>@origin` does not exist). Then in the new workspace, `jj bookmark create <bookmark>` on `@`.
   - **Existing bookmark or tag:** `jj workspace add --name <slug> -r <target-ref> .tmp/<slug>`.
   - **PR:** resolve the head with `gh` (`GIT_DIR` from the prior `jj git root`), `jj git fetch` as needed, then `jj workspace add --name pr-<n> -r <head> .tmp/pr-<n>`. Never leave the new working-copy on an anonymous fetched commit with no bookmark: create or keep a local `pr-<n>` bookmark so later changes update the PR. (For fork-safe push tracking, add the workspace first, then `cd` in and run `GIT_DIR=<jj git root> gh pr checkout <n>`.)
   - If a listed workspace already belongs to that name or already carries that bookmark on `@`, apply the one-ref-one-workspace rule above — do not force a second workspace.
6. `cd` into it (and invoke the harness move-into-workspace primitive if Step 1 deferred to it), then report the path and bookmarks on `@`.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation does not exist. Do **not** proceed in the current checkout — the user chose isolation specifically to avoid it. Report the failure and ask, offering options such as "work in the current checkout" vs "stop and resolve the permission issue", using the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Only when no such tool is in the list or a real question call errors, present the numbered options in chat and wait for the reply. Never skip the confirmation, and do not retry alternative paths automatically.
