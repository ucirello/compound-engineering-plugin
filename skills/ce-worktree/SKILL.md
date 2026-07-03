---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark/workspace for fresh work, or attach a workspace to an existing bookmark/PR/revision to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's primary workspace. Most coding harnesses now create an isolated workspace by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace tool or isolation primitive -> fall back to plain JJ.** Never create a workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh JJ workspace from a base revision (usually `trunk()`) and put a meaningful bookmark on it when needed for sharing/push. This is what `ce-work` uses.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, an existing bookmark, or a revision. Attach the new workspace to that revision instead of starting from trunk. JJ workspaces have independent working-copy commits, so multiple workspaces can be based on the same bookmark/revision. If the named workspace path already exists, report it and let the caller choose whether to work there or remove/forget it; never overwrite an existing workspace path.

The steps below (detect -> native tool -> JJ fallback) apply to both modes; the mode only changes which revision the new workspace is based on and what is reported back to the caller.

## Step 0: Detect existing isolation

Before creating anything, check whether the current directory is already an isolated workspace by inspecting the JJ workspace root and the registered workspaces:

```bash
jj workspace root
jj workspace list
```

If `jj workspace list` shows only the current workspace, treat this as the primary workspace and continue to Step 1.

If multiple workspaces exist and the current `jj workspace root` is not the primary workspace path (or is already under the harness/workspace directory), you are **already in an isolated workspace**. Report the workspace root and current bookmark/revision:

```bash
jj workspace root
jj log -r @ --no-graph -T 'change_id.short() ++ " " ++ bookmarks.join(" ") ++ " " ++ description.first_line()'
```

Do not create another workspace from inside an isolated workspace — a workspace-from-workspace can land where the harness cannot see it. Then **work in place**: in new-work mode, continue here; in isolate-an-existing-ref mode, use `jj new <target-rev>` here only if the caller explicitly wants to move this workspace to that line of work.

## Step 1: Prefer the harness's native workspace tool or isolation primitive

If the harness provides a native workspace/isolation primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` can create phantom state the harness cannot see, navigate to, or clean up.

## Step 2: JJ fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the repo root.** The `.worktrees/` and `.gitignore` paths below are repo-root-relative, but the skill runs from the user's current directory, which may be a subdirectory — so move to the root first: `cd "$(jj root)"`. Without this, `.worktrees/<bookmark>` and the `.gitignore` edit would land in the subdirectory (e.g. `src/.worktrees/...`, `src/.gitignore`) instead of at the repo root.
2. Choose a meaningful bookmark/workspace name from the work description (e.g. `feat/login`, `fix/email-validation`) — avoid opaque auto-generated names. Pick a base revision (default: `trunk()`, else the nearest sensible local trunk bookmark such as `main`).
3. **Ensure `.worktrees/` is ignored before creating anything**, so workspace contents are never committed by accident. If `.gitignore` does not already contain a `.worktrees/` entry, add one before creating the workspace.
4. Best-effort refresh remote bookmarks without disturbing the current workspace: `jj git fetch --remote origin`. This is **non-fatal** — if it errors (no `origin` remote, a differently-named remote, or a local-only repo), do not abort; continue to the next step and use the local revision.
5. Create the workspace — the command depends on the mode:
   - **New work:** `jj workspace add .worktrees/<bookmark-name> --name <bookmark-name> -r 'trunk()'`, then `cd .worktrees/<bookmark-name>` and create a matching bookmark with `jj bookmark create <bookmark-name> -r @` when the work needs a durable name for pushing or PR creation.
   - **Isolate an existing ref:** create the workspace at that revision: `jj workspace add .worktrees/<slug> --name <slug> -r <target-rev>`. For a **PR**, prefer `gh pr checkout <n>` only when needed to resolve the fork-safe PR head, then import/update JJ state as required by the local setup; otherwise fetch with `jj git fetch --remote origin` and use the PR head's local/remote bookmark as `<target-rev>`. Do not use a detached PR-ref workflow; keep the work attached to a named JJ revision/bookmark so later commits can be pushed deliberately.
6. Switch into it: `cd .worktrees/<bookmark-name>` (or `.worktrees/<slug>`).

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current workspace — do not silently continue there (the user chose isolation specifically to avoid it, especially when `ce-work` / `ce-code-review` routed here for the workspace option). Report the failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (via the `pi-ask-user` extension) — offering options such as "work in the current workspace" vs "stop and resolve the permission issue". If no blocking tool exists in the harness or the call errors, present the numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current workspace on explicit confirmation, and do not retry alternative paths automatically.

## Other workspace operations

Use `jj` directly — no wrapper is needed:

```bash
jj workspace list                          # list workspaces
jj workspace forget <workspace-name>        # stop tracking a removed workspace
cd .worktrees/<bookmark-or-slug>            # switch to a workspace
cd "$(jj workspace root)"                  # return to the current workspace root
```

## When to create a workspace

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current workspace free for other work
- Running multiple features in parallel without bookmark/workspace-switching overhead

Do not create a workspace for single-task work that can happen on a bookmark in the current workspace — and never when Step 0 shows you are already in one.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "worktree"/"workspace" in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark/workspace name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Switch to it (`cd .worktrees/<bookmark-or-slug>`) or remove that directory and run `jj workspace forget <workspace-name>` before recreating.

**"Cannot forget current workspace"**: `cd` out of the workspace first, then remove the workspace directory and run `jj workspace forget <workspace-name>` from another workspace.
