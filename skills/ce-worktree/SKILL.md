---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark/change for fresh work, or attach a workspace to an existing bookmark/PR/revision to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# JJ Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main workspace. Most coding harnesses now create an isolated workspace by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to JJ workspaces.** Never create an isolated workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh change from a base (trunk) and set a meaningful bookmark. This is what `ce-work` uses.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, an existing bookmark, or a revision. Attach the workspace to that ref instead of creating a new bookmark.

The steps below (detect -> native tool -> JJ fallback) apply to both modes; the mode only changes what revision is used and what is reported back to the caller.

## Step 0: Detect existing isolation

Before creating anything, inspect JJ's workspace view from the current directory:

```bash
jj workspace root
jj workspace list
jj st
```

If the workspace list shows the current path is already an isolated harness/JJ workspace for this task, report the workspace root and current bookmark/change, then work in place. Do not nest another workspace inside it.

## Step 1: Prefer the harness's native workspace tool

If the harness provides a native workspace/isolation primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or an isolation flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back workspace creates phantom state the harness cannot see, navigate to, or clean up.

## Step 2: JJ fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the workspace root.** The `.workspaces/` path below is root-relative, but the skill runs from the user's current directory, which may be a subdirectory — so move to the root first: `cd "$(jj workspace root)"`.
2. Choose a meaningful bookmark/workspace name from the work description (e.g. `feat/login`, `fix/email-validation`) — avoid opaque auto-generated names. Pick a base bookmark (default: the GitHub default branch name via `gh repo view`, else `main`).
3. Best-effort refresh remotes without disturbing the current workspace: `jj git fetch`. This is **non-fatal** — if it errors (no remote, auth unavailable, or local-only work), do not abort; continue and use the local ref.
4. Create the workspace — the command depends on the mode:
   - **New work:** `jj workspace add .workspaces/<workspace-name> <base-bookmark>`, then in that workspace run `jj bookmark set <bookmark-name> -r @`.
   - **Isolate an existing ref:** `jj workspace add .workspaces/<slug> <target-rev>`. For a **PR**, prefer `gh pr checkout <n>` only for GitHub metadata when needed, then reconcile with `jj git fetch` and a JJ bookmark/revision.
5. Switch into it: `cd .workspaces/<workspace-name>` (or `.workspaces/<slug>`).

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current workspace — do not silently continue there. Report the failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (via the `pi-ask-user` extension) — offering options such as "work in the current workspace" vs "stop and resolve the permission issue". If no blocking tool exists in the harness or the call errors, present the numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current workspace on explicit confirmation, and do not retry alternative paths automatically.

## Other workspace operations

Use `jj` directly — no wrapper is needed:

```bash
jj workspace list                          # list workspaces
cd .workspaces/<bookmark>                  # switch to a workspace
cd "$(jj workspace root)"                  # return to the current workspace root
```

## When to create a workspace

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current workspace free for other work
- Running multiple features in parallel without bookmark-switching overhead

Do not create a workspace for single-task work that can happen on a bookmark in the current workspace — and never when Step 0 shows you are already in one.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "workspace" in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Switch to it (`cd .workspaces/<bookmark>`) or remove the workspace directory only after ensuring no needed changes remain.

**"Cannot remove workspace: it is the current workspace"**: `cd` out of the workspace first, then clean it up according to `jj workspace list` and the harness's cleanup rules.
