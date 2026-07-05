---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark for fresh work, or attach a workspace to an existing bookmark/PR/commit to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Most coding harnesses now create isolation by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to JJ workspaces.** Never create isolation the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh JJ change from a base/trunk bookmark and attach a meaningful feature bookmark. This is what `ce-work` uses.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, an existing bookmark, or a commit. Attach the workspace to that ref instead of creating an unrelated bookmark. Avoid multiple workspaces concurrently mutating the same bookmark/change unless the caller explicitly wants that; otherwise report the existing workspace/path and let the caller work there or choose a new bookmark.

The steps below (detect -> native tool -> JJ fallback) apply to both modes; the mode only changes what gets checked out and reported back to the caller.

## Step 0: Detect existing isolation

Before creating anything, inspect the current JJ workspace:

```bash
jj root
jj workspace list
jj log -r @ --no-graph -T 'bookmarks ++ " " ++ change_id.short() ++ " " ++ commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

If the workspace list already shows this checkout as a non-primary/harness-created isolated workspace, report the workspace path (`jj root`) and current bookmark/change. Do not create another nested workspace. Then **work in place**: in new-work mode, continue here; in isolate-an-existing-ref mode, move to the target only if doing so does not overwrite unrelated current work.

## Step 1: Prefer the harness's native workspace tool

If the harness provides a native isolation primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back raw VCS workspace creates phantom state the harness cannot see, navigate to, or clean up.

## Step 2: JJ workspace fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the repo root.** The `.worktrees/` ignore paths below are repo-root-relative, but the skill runs from the user's current directory, which may be a subdirectory — so move to the root first: `cd "$(jj root)"`. Without this, `.worktrees/<bookmark>` and ignore edits could land in the wrong directory.
2. Choose a meaningful bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) — avoid opaque auto-generated names. Pick a base bookmark (default: origin's default bookmark, else `main`).
3. Ensure `.worktrees/` is ignored before creating anything, so workspace contents are never included in JJ changes. Use the repository's ignore mechanism (normally `ignore file` in colocated JJ/Git repos) and add a `.worktrees/` rule if needed.
4. Best-effort refresh the base bookmark without disturbing the current workspace: `jj git fetch --remote origin`. This is **non-fatal** — if it errors (no `origin` remote, a differently-named remote, or a local-only bookmark), do not abort; continue to the next step and use the local ref.
5. Create the workspace — the command depends on the mode:
   - **New work:** `jj workspace add .worktrees/<bookmark-slug> -r <from-bookmark>` then, inside that workspace, `jj bookmark set <bookmark-name> -r @`. This creates a new isolated JJ change from the base and names it.
   - **Isolate an existing ref:** `jj workspace add .worktrees/<slug> -r <target-ref>`. For a **PR**, use `gh pr view` for metadata and import/fetch the PR head into a JJ-resolvable revision when available; keep `gh` for GitHub metadata, but use JJ for workspace and change state. If the target is already being worked in another workspace, follow the already-isolated rule under **Two modes** — do not force concurrent mutation of the same bookmark.
6. Switch into it: `cd .worktrees/<bookmark-slug>` (or `.worktrees/<slug>`).

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current checkout — do not silently continue there. Report the failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (via the `pi-ask-user` extension) — offering options such as "work in the current checkout" vs "stop and resolve the permission issue". If no blocking tool exists in the harness or the call errors, present the numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current checkout on explicit confirmation, and do not retry alternative paths automatically.

## Other Workspace Operations

Use JJ directly — no wrapper is needed:

```bash
jj workspace list                         # list workspaces
jj workspace forget <workspace-name>      # forget a workspace record when the checkout is gone
cd .worktrees/<bookmark-slug>             # switch to a workspace directory
cd "$(jj root)"                           # return to the current workspace root
```

## When To Create A Workspace

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current checkout free for other work
- Running multiple features in parallel without bookmark-switching overhead

Do not create a workspace for single-task work that can happen on a bookmark in the current checkout — and never when Step 0 shows you are already in one.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "worktree"/"workspace" in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Switch to it (`cd .worktrees/<bookmark-slug>`) or remove/forget it with JJ workspace cleanup before recreating.

**"Cannot forget workspace: it is the current workspace"**: `cd` out of the workspace first, then run the cleanup from another workspace.
