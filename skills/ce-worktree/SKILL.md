---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark for fresh work, or attach a workspace to an existing bookmark/PR/commit to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's primary workspace. Most coding harnesses now create an isolated workspace by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to JJ.** Never create a workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh bookmark from a base (trunk). This is what `ce-work` uses.
- **Isolate an existing revision.** The caller names a target to work on in isolation — a PR head, an existing bookmark/revision, or a change. Attach the workspace to that target instead of creating a new bookmark. If the named target is already active in another workspace, do **not** create a duplicate workspace for it — report that it is already active at `<path>` and let the caller act. Never create two active isolated workspaces for the same bookmark unless the user explicitly asks for detached experimentation.

The steps below (detect -> native tool -> JJ fallback) apply to both modes; the mode only changes which ref/workspace is selected and reported back to the caller.

## Step 0: Detect existing isolation

Before creating anything, check whether the current directory is already an isolated workspace. Prefer JJ's workspace view:

```bash
jj workspace list
jj root
```

If the current workspace is already a non-default or harness-created isolated workspace, report the workspace path and current bookmark/change, then **work in place**. Do not create another workspace — workspace-from-workspace lands in the wrong place and may be invisible to the harness that made the current one.

If this is the primary workspace and no isolation exists, continue to Step 1.

## Step 1: Prefer the harness's native workspace tool

If the harness provides a native isolation primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a workspace flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back workspace creates phantom state the harness cannot see, navigate to, or clean up.

## Step 2: JJ fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the repo root.** Use `cd "$(jj root)"` before creating paths so `.workspaces/<bookmark>` lands at the repo root rather than a subdirectory.
2. Choose a meaningful bookmark/workspace name from the work description (e.g. `feat/login`, `fix/email-validation`) — avoid opaque auto-generated names. Pick a base bookmark (default: `main@origin`, else `master@origin`, else the local default bookmark).
3. **Ensure `.workspaces/` is ignored before creating anything**, so workspace contents are never committed: check the project's ignore rules and add a `.workspaces/` line to `.gitignore` if needed.
4. Best-effort refresh remote bookmarks without disturbing the current workspace: `jj git fetch`. This is **non-fatal** — if it errors (no `origin` remote, a differently-named remote, or a local-only repository), do not abort; continue to the next step and use the local ref.
5. Create the workspace — the command depends on the mode:
   - **New work:** `jj workspace add .workspaces/<bookmark-name> --revision <base-bookmark>` then `cd .workspaces/<bookmark-name>` and `jj bookmark create <bookmark-name>`. This creates an isolated workspace on a new change from the base.
   - **Isolate an existing target:** attach to the target instead of creating a new bookmark: `jj workspace add .workspaces/<slug> --revision <target-revision>`. For a **PR**, prefer fetching remotes with `jj git fetch` and attaching to the relevant remote bookmark/revision; avoid `gh pr checkout` unless the repo's GitHub workflow strictly requires GitHub's PR handling. If JJ reports the target is already active elsewhere, follow the already-active rule under **Two modes** — do not force a duplicate workspace.
6. Switch into it: `cd .workspaces/<bookmark-name>` (or `.workspaces/<slug>`).

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current workspace — do not silently continue there (the user chose isolation specifically to avoid it, especially when `ce-work` / `ce-code-review` routed here for the workspace option). Report the failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (via the `pi-ask-user` extension) — offering options such as "work in the current workspace" vs "stop and resolve the permission issue". If no blocking tool exists in the harness or the call errors, present the numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current workspace on explicit confirmation, and do not retry alternative paths automatically.

## Other workspace operations

Use JJ directly:

```bash
jj workspace list                          # list workspaces
jj workspace forget <workspace-name>        # forget a workspace after its directory is removed
cd .workspaces/<bookmark>                   # switch to a workspace
cd "$(jj root)"                             # return to the current workspace root
```

## When to create a workspace

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current workspace free for other work
- Running multiple features in parallel without bookmark-switching overhead

Do not create a workspace for single-task work that can happen on a bookmark in the current workspace — and never when Step 0 shows you are already in one.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "workspace"/"isolation" in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark/workspace name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Switch to it (`cd .workspaces/<bookmark>`) or remove that directory and run `jj workspace forget <workspace-name>` before recreating.

**"Cannot forget workspace: it is the current workspace"**: `cd` out of the workspace first, then remove the directory and run `jj workspace forget <workspace-name>` from another workspace.
