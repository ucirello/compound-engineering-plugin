---
name: ce-worktree
description: Set up isolated Jujutsu workspaces — create a new bookmark for fresh work, or attach a workspace to an existing bookmark, PR, or commit. Use when starting isolated work or isolating an existing ref.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Most coding harnesses now create a workspace by default at session start, so the common case is that **isolation already exists**.

**Done when:** the caller is working in an isolated tree — existing or newly created — and its path and bookmark have been reported, or a blocker has been reported instead.

**Order of operations: detect existing isolation -> prefer a native worktree tool -> fall back to `jj workspace`.** Never create a workspace the harness cannot see.

Run every `jj` command with the process cwd set to the target workspace's absolute root: `(cd "$workspace_root" && jj ...)`. Do not use `jj -R` as a cwd substitute.

**Two modes, set by the caller's need:**

- **New work (default).** No ref named — create a fresh bookmark from a base (trunk). This is what `ce-work` and `ce-code-review` use when the user picks the worktree option.
- **Isolate an existing ref.** The caller names a PR head, bookmark, or commit — attach the workspace to that ref instead of creating a new bookmark. **A bookmark should not get a second workspace when it is already the working copy of one.** If `jj workspace list` shows that bookmark on an existing workspace's working-copy commit (most commonly the default workspace), do **not** create a second workspace — report that it is already at `<path>` and let the caller act (work there in place; or, only if a clean separate tree is essential, create a workspace at the same commit with `--revision` and do not move the bookmark).

## Step 0: Detect existing isolation

Compare the current workspace root to the default workspace root. Both commands return absolute paths:

```bash
jj workspace root
jj workspace root --name default
```

**Equal** -> primary checkout; continue to Step 1.

**Different** -> **already isolated**. Report the workspace path (`jj workspace root`) and current bookmark, then **work in place** — a workspace-from-workspace lands in the wrong tree and is invisible to the harness that made the current one. Current bookmark (cwd = that root):

```bash
jj log -r @ --no-graph -T 'local_bookmarks.map(|b| stringify(b.name())).join(" ") ++ "\n"'
```

In isolate-an-existing-ref mode, start a working-copy commit on that ref here with `jj new <target>` (unless `@` is already that revision or already carries that bookmark) rather than nesting a workspace.

If `jj workspace root --name default` fails (no workspace named `default`), use `jj workspace list` and `jj workspace root --name <name>`: a single workspace is the primary checkout; if several exist and the current root is not the default-named one, treat it as already isolated.

To see which bookmark each workspace's working copy carries:

```bash
jj workspace list -T 'name ++ "\t" ++ stringify(root.absolute()) ++ "\t" ++ target.local_bookmarks().map(|b| stringify(b.name())).join(",") ++ "\n"'
```

## Step 1: Prefer the harness's native worktree tool

If the harness provides a native worktree primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` creates phantom state the harness cannot see, navigate to, or clean up.

## Step 2: Jujutsu fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the repo root:** `cd "$(jj workspace root)"`. The paths below are repo-root-relative, but the skill runs from the user's current directory — without this, `.worktrees/<bookmark>` and the `.gitignore` edit land in a subdirectory (e.g. `src/.worktrees/...`).
2. Choose a meaningful bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) — never an opaque auto-generated one. Base: `main@origin` (or the remote default bookmark), else `main`.
3. **Ensure `.worktrees/` is listed in `.gitignore` before creating anything:** read `.gitignore` for a `.worktrees/` line — **with the trailing slash**, so a directory-only `.worktrees/` rule is honored even before the directory exists (without the slash the probe misses it and dirties a correctly-configured repo). Not present -> add a `.worktrees/` line to `.gitignore`.
4. Refresh the base with `jj git fetch --remote origin --branch <from-branch>` (cwd = repo root). This is **non-fatal** — no `origin` remote, a differently-named remote, or a local-only bookmark is not an abort; continue with the local ref (`<from-branch>@origin` if it exists, else `<from-branch>`).
5. Create the workspace, per mode (cwd = repo root):
   - **New work:** `jj workspace add --name <bookmark-name> --revision <from-branch>@origin .worktrees/<bookmark-name>` (use local `<from-branch>` if `<from-branch>@origin` does not exist). Then `(cd .worktrees/<bookmark-name> && jj bookmark set <bookmark-name>)`.
   - **Existing bookmark or tag:** `jj workspace add --name <slug> --revision <target-ref> .worktrees/<slug>`.
   - **PR:** `jj workspace add --name pr-<n> .worktrees/pr-<n>`, then `(cd .worktrees/pr-<n> && GIT_DIR="$(jj git root)" gh pr checkout <n>)`, which is fork-safe and leaves a local bookmark the fix loop can update. Never leave the workspace on an anonymous fetched commit with no bookmark.
   - If `jj workspace list` already shows the named bookmark on another workspace's working-copy commit, apply the one-bookmark-one-workspace rule above — do not force a second workspace.
6. `cd` into it, then report the path and bookmark.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation does not exist. Do **not** proceed in the current checkout — the user chose isolation specifically to avoid it. Report the failure and ask, offering options such as "work in the current checkout" vs "stop and resolve the permission issue", using the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Only when no such tool is in the list or a real question call errors, present the numbered options in chat and wait for the reply. Never skip the confirmation, and do not retry alternative paths automatically.
