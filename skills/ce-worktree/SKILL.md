---
name: ce-worktree
description: Set up isolated Jujutsu workspaces — create a bookmark-oriented workspace for fresh work, or attach a workspace to an existing bookmark/PR/change to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Worktree Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's primary workspace. Most coding harnesses now create an isolated workspace by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace/worktree tool -> fall back to `jj workspace add`.** Never create a workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh Jujutsu change from a base bookmark (trunk) in a new workspace. This is what `ce-work` uses.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, an existing bookmark, or a change/revision. Create a workspace whose working-copy change is based on that ref. If the intent is to continue an existing mutable change, use `jj edit <change>` in the isolated workspace; otherwise use `jj new <bookmark-or-revision>` so the fix lands as a new change on top.

The steps below (detect -> native tool -> `jj` fallback) apply to both modes; the mode only changes which revision the new workspace is based on and what is reported back to the caller.

## Step 0: Detect existing isolation

Before creating anything, check the current Jujutsu workspace and the workspace list:

```bash
jj root
jj workspace list
jj log -r @ --no-graph -T 'change_id.short() ++ " " ++ commit_id.short() ++ " " ++ bookmarks.join(" ") ++ " " ++ description.first_line() ++ "\n"'
jj status
```

If `jj root` is already an isolated path chosen by the harness (for example a temporary workspace, a `.worktrees/<name>` path, or any non-primary workspace shown by `jj workspace list`), report the workspace root and current working-copy revision from `jj status`. Do not create another workspace — a workspace-from-workspace can land in a path the harness did not select or track. Then **work in place**: in new-work mode, continue here; in isolate-an-existing-ref mode, use `jj new <target>` or `jj edit <change>` here instead of nesting another workspace.

If `jj workspace list` shows only the primary/current workspace and the current root is the user's primary workspace, continue to Step 1.

Use `jj log`, `jj diff`, and `jj status` for inspection. Do not use plain `git status`, `git diff`, `git log`, `git checkout`, or `git switch`.

## Step 1: Prefer the harness's native workspace tool

If the harness provides a native workspace/worktree primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` can create state the harness cannot see, navigate to, or clean up.

## Step 2: Jujutsu fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the repo root.** The `.worktrees/` and `.gitignore` paths below are root-relative, but the skill runs from the user's current directory, which may be a subdirectory — so move to the root first: `cd "$(jj root)"`. Without this, `.worktrees/<name>` and the `.gitignore` edit would land in the subdirectory (e.g. `src/.worktrees/...`, `src/.gitignore`) instead of at the workspace root.
2. Choose a meaningful workspace/bookmark name from the work description (e.g. `feat-login`, `fix-email-validation`) — avoid opaque auto-generated names and avoid `/` because it creates nested paths under `.worktrees/`. Pick a base bookmark (default: `main`, `trunk`, or the repository's documented default bookmark; use `jj bookmark list` to inspect).
3. **Ensure `.worktrees/` is ignored before creating anything**, so workspace contents are never committed. Check `.gitignore` for a `.worktrees/` line; if it is absent, add one.
4. Best-effort refresh remote bookmarks without disturbing the current workspace: `jj git fetch --remote origin`. This is **non-fatal** — if it errors (no `origin` remote, a differently-named remote, or a local-only repository), do not abort; continue to the next step and use local bookmarks/revisions.
5. Create the workspace — the command depends on the mode:
   - **New work:** `jj workspace add --name <workspace-name> .worktrees/<workspace-name> --revision <base-bookmark>` creates a new workspace with a fresh working-copy change on top of the base. After committing work with `jj commit`, create or move a publication bookmark with `jj bookmark set <bookmark-name> -r @-` when the project workflow expects named bookmarks.
   - **Isolate an existing bookmark or revision:** `jj workspace add --name <workspace-name> .worktrees/<workspace-name> --revision <target-bookmark-or-revision>` creates a fresh working-copy change on top of that target. For continuing an existing mutable change instead of stacking a new one, enter the new workspace and run `jj edit <change-id>`.
   - **Isolate a PR:** prefer a native PR/workspace tool if available. If the PR head is available as a tracked remote bookmark, fetch with `jj git fetch --remote <remote> --branch <head-bookmark>` and base the workspace on `<head-bookmark>@<remote>`. If only a PR number is known and no bookmark/ref is available through `jj git fetch`, stop and ask for the PR head bookmark/ref or use the harness's native PR workspace tool; do not fall back to plain `git fetch` or detached Git state.
6. Enter it: `cd .worktrees/<workspace-name>`.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current workspace — do not silently continue there (the user chose isolation specifically to avoid it, especially when `ce-work` / `ce-code-review` routed here for the worktree option). Report the failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (via the `pi-ask-user` extension) — offering options such as "work in the current workspace" vs "stop and resolve the permission issue". If no blocking tool exists in the harness or the call errors, present the numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current workspace on explicit confirmation, and do not retry alternative paths automatically.

## Other worktree operations

Use `jj` directly:

```bash
jj workspace list                                      # list workspaces
jj workspace forget <workspace-name>                   # stop tracking a removed workspace
cd .worktrees/<workspace-name>                         # enter a workspace
cd "$(jj workspace root)"                              # return to the current workspace root
jj status                                              # inspect status
jj diff                                                # inspect diff
jj log                                                 # inspect history
```

## When to create a worktree

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current workspace free for other work
- Running multiple features in parallel without disrupting the current workspace

Do not create a workspace for single-task work that can happen as a new `jj` change in the current workspace — and never when Step 0 shows you are already isolated.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "worktree" in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful workspace/bookmark name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Enter it (`cd .worktrees/<workspace-name>`) or remove the directory and run `jj workspace forget <workspace-name>` before recreating.

**"Cannot forget current workspace"**: `cd` out of the workspace first, then remove its directory and run `jj workspace forget <workspace-name>` from another workspace.
