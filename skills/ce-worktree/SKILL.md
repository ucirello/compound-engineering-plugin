---
name: ce-worktree
description: Set up isolated Jujutsu workspaces — create a new bookmark for fresh work, or attach a workspace to an existing bookmark, PR, or commit. Use when starting isolated work or isolating an existing ref.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main workspace. Most coding harnesses now create a workspace by default at session start, so the common case is that **isolation already exists**.

**Done when:** the caller is working in an isolated tree — existing or newly created — and its path and bookmark have been reported, or a blocker has been reported instead.

**Order of operations: detect existing isolation -> prefer a native worktree tool -> fall back to `jj workspace add`.** Never create a workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No ref named — create a fresh bookmark from a base (trunk). This is what `ce-work` and `ce-code-review` use when the user picks the worktree option.
- **Isolate an existing ref.** The caller names a PR head, bookmark, or commit — attach the workspace to that ref instead of creating a new bookmark. **A named isolation should occupy only one workspace.** If `jj workspace list` / `jj workspace root --name <name>` already shows that workspace, or the named bookmark is already this or another workspace's working copy (most commonly the default workspace), do **not** create a second workspace — report that it is already at `<path>` and let the caller act (work there in place; or, only if a clean separate tree is essential, create a workspace at the same commit without a bookmark).

## Step 0: Detect existing isolation

Compare the current workspace root to the default workspace root. `jj workspace root` returns the absolute workspace root even from a subdirectory, so a subdirectory CWD in the default workspace is not misread as isolation. Never read or parse `.jj/` or `.git/`.

```bash
jj workspace root                                          # current workspace root
jj workspace root --name default                           # default workspace root
jj workspace list -T 'name ++ "\t" ++ stringify(root) ++ "\n"'
```

If `jj workspace root` is nonzero, this is not a JJ repo; report that blocker.

**Equal** (current root is the default workspace) -> continue to Step 1.

**Different** -> **already isolated**. Report the workspace path (`jj workspace root`) and current bookmark (`jj log -r @ -T 'bookmarks.join("\n")' --no-graph`), then **work in place** — a workspace-from-workspace lands in the wrong tree and is invisible to the harness that made the current one. In isolate-an-existing-ref mode, switch this workspace to that ref with `jj new <target-ref>` (unless it is already current) rather than nesting a workspace.

## Step 1: Prefer the harness's native worktree tool

If the harness provides a native worktree primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` creates phantom state the harness cannot see, navigate to, or clean up. `opencode2` is a distinct harness from `opencode`; do not treat an `opencode` primitive as an `opencode2` one. Use whichever native primitive the current harness actually provides.

## Step 2: JJ fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

Run every `jj` command with cwd set to the workspace root being operated on (`(cd "$workspace_root" && jj ...)`). `jj -R` selects a repository but does not change cwd.

1. **Run from the repo root:** `cd "$(jj workspace root)"`. The paths below are repo-root-relative, but the skill runs from the user's current directory — without this, `.worktrees/<bookmark>` and the `.gitignore` edit land in a subdirectory (e.g. `src/.worktrees/...`).
2. Choose a meaningful bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) — never an opaque auto-generated one. Base: origin's default bookmark, else `main`.
3. **Ensure `.worktrees/` is in `.gitignore` before creating anything:** read `.gitignore` for a `.worktrees/` rule — **with the trailing slash**, so an existing directory-only `.worktrees/` rule is honored even before the directory exists (without the slash the probe misses it and dirties a correctly-configured repo). Not present -> add a `.worktrees/` line to `.gitignore`. There is no public `jj` equivalent of `git check-ignore`; do not call `git`.
4. Refresh the base with `jj git fetch --remote origin -b <from-branch>`. This is **non-fatal** — no `origin` remote, a differently-named remote, or a local-only bookmark is not an abort; continue with the local ref.
5. Create the workspace, per mode. Before adding, if `jj workspace list` / `jj workspace root --name <name>` already shows that isolation, apply the one-workspace rule above — do not force a second workspace.
   - **New work:** `(cd "$(jj workspace root)" && jj workspace add --name <bookmark-name> -r '<from-branch>@origin' .worktrees/<bookmark-name>)` then `(cd .worktrees/<bookmark-name> && jj bookmark create <bookmark-name>)` (use the local `<from-branch>` ref if `<from-branch>@origin` does not exist — verify with `jj log -r '<from-branch>@origin' -n 1 --no-graph`).
   - **Existing bookmark or tag:** `(cd "$(jj workspace root)" && jj workspace add --name <slug> -r <target-ref> .worktrees/<slug>)`.
   - **PR:** obtain the PR head with `GIT_DIR=$(jj git root) gh pr view <n> --json headRefOid` (cwd: repo root), then `(cd "$(jj workspace root)" && jj workspace add --name pr-<n> -r <headRefOid> .worktrees/pr-<n>)` and `(cd .worktrees/pr-<n> && jj bookmark create pr-<n>)`. Never leave the new workspace without a bookmark: that orphans the fix loop's changes instead of updating the PR. (For push-tracking back to the PR, create the workspace without a bookmark — `jj workspace add --name pr-<n> .worktrees/pr-<n>` — then `cd` in and run `GIT_DIR=$(jj git root) gh pr checkout <n>`, which is fork-safe.)
6. `cd` into it, then report the path and bookmark.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation does not exist. Do **not** proceed in the current workspace — the user chose isolation specifically to avoid it. Report the failure and ask, offering options such as "work in the current workspace" vs "stop and resolve the permission issue", using the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Only when no such tool is in the list or a real question call errors, present the numbered options in chat and wait for the reply. Never skip the confirmation, and do not retry alternative paths automatically.
