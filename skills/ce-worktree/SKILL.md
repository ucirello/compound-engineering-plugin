---
name: ce-worktree
description: Set up isolated workspaces — create a new bookmark/workspace for fresh work, or attach a workspace to an existing branch/PR/commit to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Worktree Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Most coding harnesses now create a worktree by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native worktree/workspace tool -> use `jj workspace add` only when needed.** Never create a workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh bookmark from a base (trunk). This is what `ce-work` uses.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, an existing bookmark/branch, or a commit. Attach the workspace to that ref instead of creating unrelated work. If the named ref is already checked out in the current workspace, do **not** create a second workspace for it — report that it is already checked out at `<path>` and let the caller act there.

The steps below (detect -> native tool -> JJ fallback) apply to both modes; the mode only changes what gets checked out and is reported back to the caller.

## Step 0: Detect existing isolation

Before creating anything, check whether the current directory is already a separate JJ workspace. Use JJ's workspace list and root output, not raw Git metadata:

```bash
jj workspace list
jj workspace root
```

If the current workspace is not the user's main checkout, report the workspace root and current bookmark, then **work in place**. Do not create another workspace — nested or behind-the-back isolation lands in a tree the harness may not manage. In isolate-an-existing-ref mode, check that ref out here unless it is already current.

## Step 1: Prefer the harness's native worktree tool

If the harness provides a native worktree primitive or workspace primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back workspace creates phantom state the harness cannot see, navigate to, or clean up.

## Step 2: JJ workspace fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the workspace root.** Move to `$(jj workspace root)` before using repo-relative paths.
2. Choose meaningful workspace and bookmark names from the work description (e.g. `feat-login`, `fix-email-validation`) — avoid opaque auto-generated names. Pick a base branch/bookmark (default: origin's default branch, else `main`).
3. Best-effort refresh the base bookmark without disturbing the current workspace: `jj git fetch --remote origin --branch <from-branch>`. This is **non-fatal** — if it errors (no `origin` remote, a differently-named remote, or a local-only branch), do not abort; continue and use the local bookmark/ref.
4. Create the workspace under `.worktrees/<workspace-name>` — the command depends on the mode:
   - **New work:** `jj workspace add --name <workspace-name> -r <from-branch>@origin .worktrees/<workspace-name>` (use the local `<from-branch>` ref if `<from-branch>@origin` does not exist). Then create a bookmark for the work if needed: `jj bookmark create <bookmark-name> -r @`.
   - **Isolate an existing ref:** `jj workspace add --name <workspace-name> -r <target-ref> .worktrees/<workspace-name>`. For a PR, fetch it to a local bookmark first when needed, then create the workspace from that bookmark. If the ref is already checked out in the current workspace, follow the already-checked-out rule under **Two modes**.
5. Enter it: use the harness navigation primitive when available, otherwise set the shell workdir to `.worktrees/<workspace-name>` for subsequent commands.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current checkout — do not silently continue there (the user chose isolation specifically to avoid it, especially when `ce-work` / `ce-code-review` routed here for the worktree option). Report the failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (via the `pi-ask-user` extension) — offering options such as "work in the current checkout" vs "stop and resolve the permission issue". If no blocking tool exists in the harness or the call errors, present the numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current checkout on explicit confirmation, and do not retry alternative paths automatically.

## Other worktree operations

Use the repository's native workspace commands directly:

```bash
jj workspace list                          # list JJ workspaces
jj workspace forget <workspace-name>       # stop tracking a workspace after its directory is gone
cd .worktrees/<workspace-name>             # switch to a workspace when shell navigation is available
cd "$(jj workspace root)"                  # return to the current workspace root
```

## When to create a worktree

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current checkout free for other work
- Running multiple features in parallel without branch-switching overhead

Do not create a workspace for single-task work that can happen on a bookmark in the current checkout — and never when Step 0 shows you are already isolated.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "worktree" or "workspace" in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with meaningful workspace/bookmark names derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Switch to it (`cd .worktrees/<workspace-name>`) or remove the directory and run `jj workspace forget <workspace-name>` before recreating.

**"Cannot remove workspace: it is the current workspace"**: `cd` out of the workspace first, remove the directory, then run `jj workspace forget`.
