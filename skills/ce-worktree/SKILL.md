---
name: ce-worktree
description: Set up isolated Jujutsu workspaces — create a bookmark-oriented workspace for fresh work, or attach a workspace to an existing bookmark/PR/change to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's primary workspace. Most coding harnesses now create an isolated workspace by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to JJ workspace commands.** Never create a workspace the harness cannot see when a native tool exists.

## Two Modes

- **New work (default).** No specific ref named — create a fresh workspace from a base bookmark (trunk) and create a meaningful feature bookmark.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, an existing bookmark, or a change/commit ID. Attach a workspace to that revision. If the target bookmark is already active in another workspace, prefer entering that workspace or creating a workspace at the target revision without moving the bookmark until explicitly requested.

## Step 0: Detect Existing Isolation

Before creating anything, run:

```bash
jj workspace root
jj workspace list
```

If the current root is already a non-primary or harness-created workspace for the requested work, report that path and work in place. Do not create nested workspaces.

## Step 1: Prefer The Harness's Native Workspace Tool

If the harness provides a native workspace/worktree primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it.

## Step 2: JJ Workspace Fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the workspace root:** `cd "$(jj workspace root)"`.
2. Choose a meaningful bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) and a workspace path under `.workspaces/<bookmark-slug>`.
3. Resolve the base bookmark. Prefer the caller's base; otherwise use the project default (`main`, `master`, or `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`). Refresh it best-effort with `jj git fetch --remote origin --branch <base-bookmark>`; if fetch fails, continue with the local ref.
4. Create the workspace:

```bash
jj workspace add .workspaces/<bookmark-slug> --revision <base-bookmark>
```

5. Enter it and create or attach the bookmark:

```bash
cd .workspaces/<bookmark-slug>
jj bookmark create <bookmark-name> -r @
```

For an existing ref, use `jj workspace add .workspaces/<slug> --revision <target-rev>` and do **not** move an existing bookmark unless the caller explicitly requested that.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current workspace: use `AskUserQuestion` in Claude Code, `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), or `ask_user` in Pi. Ask whether to work in the current workspace or stop and resolve the permission issue. Only work in the current workspace on explicit confirmation.

## Other Workspace Operations

```bash
jj workspace list                         # list workspaces
jj workspace forget <workspace-name>      # stop tracking a workspace
jj bookmark delete <bookmark>             # remove a no-longer-needed bookmark
cd "$(jj workspace root)"                 # return to the current workspace root
```

## When To Create A Workspace

Create one only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current workspace free for other work
- Running multiple features in parallel without bookmark/workspace switching overhead

Do not create a workspace for single-task work that can happen on the current bookmark/change — and never when Step 0 shows you are already isolated.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects workspace isolation in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path or workspace name is in use. Switch to it (`cd .workspaces/<bookmark-slug>`) or forget/remove it before recreating.

**"Cannot forget workspace"**: leave the workspace first, then run `jj workspace forget <workspace-name>` from another workspace and remove the directory when safe.
