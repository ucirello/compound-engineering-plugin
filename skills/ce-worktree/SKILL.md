---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark/workspace for fresh work, or attach a workspace to an existing bookmark/PR/revision to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# JJ Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main workspace. Most coding harnesses now create isolation by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to `jj workspace add`**. Never create isolation the harness cannot see when a native tool exists.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh JJ change from a base (`trunk()` by default) and attach a meaningful bookmark.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, existing bookmark, tag, or commit ID. Attach the workspace to that ref instead of creating unrelated work.

## Step 0: Detect Existing Isolation

Run:

```bash
jj workspace list
jj root
jj log -r @ --no-graph -T 'change_id.short() ++ " " ++ bookmarks.join(" ") ++ "\n"'
```

If the current path is already a harness-managed isolated workspace, report the workspace path and current bookmark/change, then work in place. Do not nest another workspace.

## Step 1: Prefer The Harness Tool

If the harness provides a native workspace/isolation primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it.

## Step 2: JJ Fallback

Only when there is no native tool **and** Step 0 found no existing isolation:

1. **Run from the repo root.** Resolve it with `jj root`, then `cd "$(jj root)"` before using relative workspace or ignore paths.
2. Choose a meaningful bookmark/workspace name from the work description (e.g. `feat/login`, `fix/email-validation`) — avoid opaque auto-generated names.
3. Ensure `.worktrees/` is covered by the project's ignore rules before creating a fallback workspace, so workspace contents are never committed.
4. Best-effort refresh remotes without disturbing the current workspace: `jj git fetch --remote origin`. If it errors because there is no remote, continue with local refs.
5. Create the workspace:

```bash
# New work from trunk/default
jj workspace add .worktrees/<slug> -r 'trunk()'
jj bookmark create <bookmark-name> -r @

# Existing ref/bookmark/revision
jj workspace add .worktrees/<slug> -r <target-ref>
```

For a PR, prefer `gh pr view <number-or-url> --json headRefName,headRefOid` to identify the head, then attach to the fetched/ref-resolved head revision. Do not switch the user's primary workspace.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current workspace. Use the platform's blocking question tool (`AskUserQuestion` in Claude Code, `request_user_input` in Codex, `ask_user` in Pi, or equivalent) to ask whether to work in the current workspace or stop and resolve the permission issue. Only work in the current workspace on explicit confirmation.

## Other Workspace Operations

```bash
jj workspace list                       # list workspaces
jj workspace forget <workspace-name>    # forget a workspace when safe
cd .worktrees/<slug>                    # switch to a workspace path
cd "$(jj root)"                         # return to the current workspace root
```

## When To Create A Workspace

Create one only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current workspace free for other work
- Running multiple features in parallel without bookmark-switching overhead

Do not create a workspace for single-task work that can happen on the current JJ change — and never when Step 0 shows you are already isolated.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects isolation in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create a workspace (native tool preferred) with a meaningful bookmark/workspace name derived from the work description.
