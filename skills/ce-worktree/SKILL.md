---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark for fresh work, or attach a workspace to an existing bookmark/PR/revision. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Most coding harnesses now create an isolated workspace by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace/worktree tool -> fall back to JJ.** Never create a workspace the harness cannot see when a native tool exists.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh change from a base (trunk) and attach a meaningful bookmark. This is what `ce-work` uses.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, existing bookmark, or revision. Attach the workspace to that revision. In JJ, bookmarks are movable pointers and workspaces edit changes, so do not apply Git's "one branch per worktree" rule. If the named ref is already being edited in the current workspace, report that and work in place unless the caller explicitly needs a separate workspace.

The steps below (detect -> native tool -> JJ fallback) apply to both modes; the mode only changes the revision/bookmark used and reported back to the caller.

## Step 0: Detect existing isolation

Before creating anything, list JJ workspaces and identify the current workspace:

```bash
jj workspace list
jj root
```

If the current workspace path is already outside the user's main checkout or already matches the requested isolated workspace, report the workspace path and current bookmark/change, then work in place. Do not create nested isolation: a workspace-from-workspace can be invisible to the harness that created the current one.

## Step 1: Prefer the harness's native workspace tool

If the harness provides a native workspace/worktree primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` creates state the harness may not see, navigate to, or clean up.

## Step 2: JJ fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the repo root.** The `.worktrees/` and ignore-rule paths below are repo-root-relative, but the skill runs from the user's current directory, which may be a subdirectory — so move to the root first: `cd "$(jj root)"`.
2. Choose a meaningful bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) — avoid opaque auto-generated names. Pick a base bookmark (default: origin's default bookmark, else `main@origin`, else `main`).
3. **Ensure `.worktrees/` is ignored by the project's VCS ignore rules before creating anything**, so workspace contents are never committed. If it is not ignored, add a `.worktrees/` line to the repo's shared ignore file or local exclude mechanism according to the project's conventions.
4. Best-effort refresh remote bookmarks without disturbing the current workspace: `jj git fetch --remote origin`. This is **non-fatal** — if it errors (no `origin` remote, a differently-named remote, or a local-only repo), do not abort; continue to the next step and use the local ref.
5. Create the workspace — the command depends on the mode:
   - **New work:** `jj workspace add .worktrees/<bookmark-slug> -r <base-rev>` then, inside that workspace, `jj bookmark create <bookmark-name> -r @`. This creates a fresh change from the base and names it.
   - **Isolate an existing ref:** `jj workspace add .worktrees/<slug> -r <target-ref>`. For a **PR**, prefer `gh pr checkout <n>` only if it integrates cleanly with the current JJ setup; otherwise fetch remote bookmarks with `jj git fetch --remote origin` and add a workspace at the PR head revision exposed by the remote. If no local PR head revision is available, report the limitation rather than guessing.
6. Switch into it: `cd .worktrees/<bookmark-slug>` (or `.worktrees/<slug>`).

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current checkout — do not silently continue there. Report the failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (via the `pi-ask-user` extension) — offering options such as "work in the current checkout" vs "stop and resolve the permission issue". If no blocking tool exists in the harness or the call errors, present the numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current checkout on explicit confirmation, and do not retry alternative paths automatically.

## Other Workspace Operations

Use JJ directly — no wrapper is needed:

```bash
jj workspace list                         # list workspaces
jj workspace forget <workspace-name>       # forget a workspace after its directory is removed or no longer needed
cd .worktrees/<bookmark-slug>              # switch to a workspace directory
cd "$(jj root)"                            # return to the current workspace root
```

## When To Create A Workspace

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current checkout free for other work
- Running multiple features in parallel without bookmark-switching overhead

Do not create a workspace for single-task work that can happen on a feature bookmark in the current checkout — and never when Step 0 shows you are already isolated.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "worktree" or workspace isolation in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Switch to it (`cd .worktrees/<bookmark-slug>`) or remove/forget it before recreating.

**"Cannot remove workspace: it is the current workspace"**: `cd` out of the workspace first, then remove the directory and run `jj workspace forget <workspace-name>` if needed.
