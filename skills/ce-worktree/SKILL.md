---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark-oriented workspace for fresh work, or attach a workspace to an existing bookmark/PR/change to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Most coding harnesses now create a workspace by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to `jj workspace`.** Never create a workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh workspace from a base bookmark (trunk). This is what `ce-work` uses.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, an existing bookmark, or a change. Attach the workspace to that ref instead of creating a new bookmark. If the named ref is already active in another workspace, do **not** create a conflicting duplicate; report where it is already checked out and let the caller act (work there in place; or, only if a clean separate tree is essential, create a new workspace at the same change with a distinct workspace name).

The steps below (detect -> native tool -> JJ fallback) apply to both modes; the mode only changes what gets checked out and is reported back to the caller.

## Step 0: Detect existing isolation

Before creating anything, check whether the current directory is already an isolated JJ workspace. Compare the current workspace root to the repo root and list workspaces:

```bash
jj workspace root                                    # current workspace root
jj root                                              # repo root
jj workspace list                                    # all known JJ workspaces
```

If `jj workspace list` shows only the current workspace at the repo root, this is the normal checkout — continue to Step 1.

If the current workspace root differs from the repo root, or `jj workspace list` shows this as a named non-root workspace, you are **already in an isolated workspace**. Report the workspace path (`jj workspace root`) and current bookmark/change. Do not create another workspace — nesting a workspace lands in the wrong tree and is invisible to the harness that made the current one. Then **work in place**: in new-work mode, continue here; in isolate-an-existing-ref mode, move this workspace to that ref only when that is what the caller asked for.

## Step 1: Prefer the harness's native workspace tool

If the harness provides a native workspace primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back `jj workspace add` creates phantom state the harness cannot see, navigate to, or clean up.

## Step 2: JJ fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the repo root.** The `.workspaces/` and `.gitignore` paths below are repo-root-relative, but the skill runs from the user's current directory, which may be a subdirectory — so move to the root first: `cd "$(jj root)"`. Without this, `.workspaces/<bookmark>` and the `.gitignore` edit would land in the subdirectory (e.g. `src/.workspaces/...`, `src/.gitignore`) instead of at the repo root.
2. Choose a meaningful bookmark/workspace name from the work description (e.g. `feat/login`, `fix/email-validation`) — avoid opaque auto-generated names. Pick a base bookmark (default: origin's default bookmark, else `main`).
3. **Ensure `.workspaces/` is ignored before creating anything**, so workspace contents are never described in a JJ change: check the project's ignore rules for `.workspaces/` with the trailing slash. If it is not ignored, add a `.workspaces/` line to `.gitignore`.
4. Best-effort refresh the base bookmark without disturbing the current checkout: `jj git fetch`. This is **non-fatal** — if it errors (no remote, a differently-named remote, or a local-only bookmark), do not abort; continue to the next step and use the local ref.
5. Create the workspace — the command depends on the mode:
   - **New work:** `jj workspace add .workspaces/<bookmark-name> -r <base-bookmark>` then create or move a meaningful bookmark for the work with `jj bookmark create <bookmark-name> -r @` if needed. This creates an isolated workspace from the base.
   - **Isolate an existing ref:** attach to the ref instead of creating a new bookmark — for an existing bookmark or change, `jj workspace add .workspaces/<slug> -r <target-ref>`. For a **PR**, use `gh pr checkout <n>` only for GitHub PR discovery/checkout if required by the project, then anchor the JJ workspace/bookmark to the checked-out PR ref. If JJ reports the workspace/ref is already active elsewhere, follow the already-active rule under **Two modes** — do not force a duplicate workspace.
6. Switch into it: `cd .workspaces/<bookmark-name>` (or `.workspaces/<slug>`).

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current checkout — do not silently continue there (the user chose isolation specifically to avoid it, especially when `ce-work` / `ce-code-review` routed here for the workspace option). Report the failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (via the `pi-ask-user` extension) — offering options such as "work in the current checkout" vs "stop and resolve the permission issue". If no blocking tool exists in the harness or the call errors, present the numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current checkout on explicit confirmation, and do not retry alternative paths automatically.

## Other workspace operations

Use `jj` directly — no wrapper is needed:

```bash
jj workspace list                          # list workspaces
rm -rf .workspaces/<bookmark> && jj workspace forget <workspace>  # remove a workspace
cd .workspaces/<bookmark>                  # switch to a workspace
cd "$(jj root)"                            # return to the current checkout root
```

## When to create a workspace

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current checkout free for other work
- Running multiple features in parallel without bookmark-switching overhead

Do not create a workspace for single-task work that can happen on a bookmark in the current checkout — and never when Step 0 shows you are already in one.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "workspace" in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark/workspace name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Switch to it (`cd .workspaces/<bookmark>`) or remove it (`rm -rf .workspaces/<bookmark> && jj workspace forget <workspace>`) before recreating.

**"Cannot remove workspace: it is the current workspace"**: `cd` out of the workspace first, then remove the directory and run `jj workspace forget <workspace>`.
