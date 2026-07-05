---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark for fresh work, or attach a workspace to an existing bookmark/PR/commit to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Worktree Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Most coding harnesses now create a worktree by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace/worktree tool -> fall back to JJ.** Never create a workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh change from a base (trunk) and attach a meaningful bookmark. This is what `ce-work` uses.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, an existing bookmark, or a commit. Create a workspace at that ref and work on a new change from it. If the same workspace/ref is already available, report that path and let the caller work there instead of creating redundant isolation.

The steps below (detect -> native tool -> JJ fallback) apply to both modes; the mode only changes what revision the workspace starts from and what is reported back to the caller.

## Step 0: Detect existing isolation

Before creating anything, check whether the current directory is already an isolated workspace and whether sibling JJ workspaces already exist:

```bash
jj workspace root
jj workspace list
```

If the current path is already a non-primary isolated workspace for this task, report the workspace path and current bookmark/change, then **work in place**. Do not create another workspace — a workspace-from-workspace lands in the wrong tree and is invisible to the harness that made the current one.

If the target ref already has a suitable workspace listed, report that path and use it. Otherwise continue to Step 1.

## Step 1: Prefer the harness's native worktree tool

If the harness provides a native worktree/workspace primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` creates phantom state the harness cannot see, navigate to, or clean up.

## Step 2: JJ fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the repo root.** The `.worktrees/` and `.gitignore` paths below are repo-root-relative, but the skill runs from the user's current directory, which may be a subdirectory — so move to the root first: `cd "$(jj workspace root)"`. Without this, `.worktrees/<bookmark>` and the `.gitignore` edit would land in the subdirectory (e.g. `src/.worktrees/...`, `src/.gitignore`) instead of at the repo root.
2. Choose a meaningful bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) — avoid opaque auto-generated names. Pick a base bookmark (default: origin's default bookmark when known, else `main`).
3. **Ensure `.worktrees/` is ignored before creating anything**, so workspace contents are never committed: check the project's ignore rules for `.worktrees/` and add a `.worktrees/` line to `.gitignore` if it is not ignored.
4. Best-effort refresh the base bookmark without disturbing the current workspace: `jj git fetch --remote origin --branch <from-bookmark>`. This is **non-fatal** — if it errors (no `origin` remote, a differently-named remote, or a local-only bookmark), do not abort; continue to the next step and use the local ref.
5. Create the workspace — the command depends on the mode:
   - **New work:** `jj workspace add .worktrees/<bookmark-name> --revision <from-bookmark>` then, inside that workspace, `jj new` if needed and `jj bookmark create <bookmark-name> -r @`. This creates a new change from the base and gives it a bookmark for pushes/PRs.
   - **Isolate an existing ref:** create a workspace at the ref, then work on a new change from it: `jj workspace add .worktrees/<slug> --revision <target-ref>` followed by `jj new` inside the workspace when the fix should be a child change. For a **PR**, resolve the PR head with `gh pr view <n>` / `gh pr checkout <n>` only as the GitHub interface requires, then use JJ commands for subsequent status, commits, fetches, pushes, and bookmark movement. Avoid orphaned detached work: make sure the workspace has a bookmark you can push or that `gh` has checked out the PR's update target.
6. Switch into it: `cd .worktrees/<bookmark-name>` (or `.worktrees/<slug>`).

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current checkout — do not silently continue there (the user chose isolation specifically to avoid it, especially when `ce-work` / `ce-code-review` routed here for the worktree option). Report the failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (via the `pi-ask-user` extension) — offering options such as "work in the current checkout" vs "stop and resolve the permission issue". If no blocking tool exists in the harness or the call errors, present the numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current checkout on explicit confirmation, and do not retry alternative paths automatically.

## Other worktree operations

Use JJ directly — no wrapper is needed:

```bash
jj workspace list                          # list workspaces
jj workspace forget <workspace-name>        # remove JJ's record for a deleted workspace
cd .worktrees/<bookmark>                    # switch to a workspace
cd "$(jj workspace root)"                   # return to the current workspace root
```

## When to create a worktree

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current checkout free for other work
- Running multiple features in parallel without bookmark-switching overhead

Do not create a worktree for single-task work that can happen on a bookmark/change in the current checkout — and never when Step 0 shows you are already in one.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "worktree" in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Switch to it (`cd .worktrees/<bookmark>`) or remove the directory and run `jj workspace forget <workspace-name>` before recreating.

**"Cannot remove workspace: it is the current workspace"**: `cd` out of the workspace first, then remove the directory and run `jj workspace forget <workspace-name>`.
