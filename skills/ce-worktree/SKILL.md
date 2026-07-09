---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark for fresh work, or attach a workspace to an existing bookmark/PR/change to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# JJ Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main workspace. Most coding harnesses now create an isolated workspace by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to `jj workspace add`.** Never create a workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh change from a base bookmark (trunk). This is what `ce-work` uses.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, an existing bookmark, or a change. Attach the workspace to that ref instead of creating a new bookmark. If the named ref is already the active change in the current workspace, do **not** create a second workspace for it — report that it is already active at `<path>` and let the caller act.

The steps below (detect -> native tool -> JJ fallback) apply to both modes; the mode only changes which change gets activated and what is reported back to the caller.

## Step 0: Detect Existing Isolation

Before creating anything, list JJ workspaces and identify the current workspace root:

```bash
jj workspace root
jj workspace list
```

If the current root is already a harness-created or linked workspace for this task, report the workspace path and current bookmark/change (`jj bookmark list --revisions @`, `jj log -r @ --no-graph`). Do not create another workspace — a workspace-from-workspace can land somewhere the harness does not track. Then **work in place**: in new-work mode, continue here; in isolate-an-existing-ref mode, run `jj new <target-ref>` or `jj edit <target-ref>` here when needed rather than nesting a workspace.

## Step 1: Prefer The Harness's Native Workspace Tool

If the harness provides a native workspace primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` can create phantom state the harness cannot see, navigate to, or clean up.

## Step 2: JJ Fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the repo root.** The `.workspaces/` and ignore-file paths below are repo-root-relative, but the skill runs from the user's current directory, which may be a subdirectory — so move to the root first: `cd "$(jj workspace root)"`.
2. Choose a meaningful bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) — avoid opaque auto-generated names. Pick a base bookmark (default: `main@origin`, else `main`).
3. **Ensure `.workspaces/` is ignored before creating anything**, so workspace contents are never tracked. If it is not ignored, add a `.workspaces/` line to the repo ignore file.
4. Best-effort refresh the base bookmark without disturbing the current workspace: `jj git fetch --remote origin --branch <from-bookmark>`. This is **non-fatal** — if it errors (no `origin` remote, a differently-named remote, or a local-only bookmark), do not abort; continue to the next step and use the local ref.
5. Create the workspace — the command depends on the mode:
   - **New work:** `jj workspace add .workspaces/<bookmark-name> <from-bookmark>@origin` (use the local `<from-bookmark>` ref if `<from-bookmark>@origin` does not exist), then `cd .workspaces/<bookmark-name>` and `jj bookmark create <bookmark-name> -r @`. This creates a new workspace and named line of work from the base.
   - **Isolate an existing ref:** `jj workspace add .workspaces/<slug> <target-ref>`, then `cd .workspaces/<slug>`. For a **PR**, use `gh pr checkout <n>` when the platform supports it, or fetch the PR head through `jj git fetch` if the remote exposes it; then attach the workspace to the fetched change/bookmark.
6. Switch into it: `cd .workspaces/<bookmark-name>` (or `.workspaces/<slug>`).

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current workspace — do not silently continue there (the user chose isolation specifically to avoid it, especially when `ce-work` / `ce-code-review` routed here for the workspace option). Report the failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (via the `pi-ask-user` extension) — offering options such as "work in the current workspace" vs "stop and resolve the permission issue". If no blocking tool exists in the harness or the call errors, present the numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current workspace on explicit confirmation, and do not retry alternative paths automatically.

## Other Workspace Operations

Use JJ directly — no wrapper is needed:

```bash
jj workspace list                         # list workspaces
jj workspace forget <workspace-name>       # stop tracking a workspace
cd .workspaces/<bookmark>                  # switch to a workspace path
cd "$(jj workspace root)"                  # return to the current workspace root
```

## When To Create A Workspace

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current workspace free for other work
- Running multiple features in parallel without bookmark-switching overhead

Do not create a workspace for single-task work that can happen on a new change in the current workspace — and never when Step 0 shows you are already in one.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "worktree" in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create a JJ workspace (native tool preferred) with a meaningful bookmark name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Switch to it (`cd .workspaces/<bookmark>`) or forget/remove it before recreating.

**"Cannot forget workspace: it is the current workspace"**: `cd` out of the workspace first, then run `jj workspace forget <workspace-name>`.
