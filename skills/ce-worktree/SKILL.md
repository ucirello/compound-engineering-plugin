---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmarked change for fresh work, or attach a workspace to an existing bookmark/PR/change to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main working copy. Most coding harnesses now create an isolated workspace by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to `jj workspace add`.** Never create an isolated workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh JJ workspace from a base bookmark (trunk), then create a meaningful bookmark for the new change. This is what `ce-work` uses.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, an existing bookmark, or a change/commit ID. Attach the workspace to that ref instead of creating a new bookmark. If the named work is already active in another workspace, do **not** create a confusing duplicate workspace for it — report that it is already active at `<path>` and let the caller act there, unless a clean separate workspace is essential.

The steps below (detect -> native tool -> JJ fallback) apply to both modes; the mode only changes what gets created and is reported back to the caller.

## Step 0: Detect existing isolation

Before creating anything, check whether the current directory is already an isolated JJ workspace. Use JJ's workspace commands rather than raw VCS directory probes:

```bash
jj workspace root
jj workspace list
```

If `jj workspace list` shows the current root as a non-primary or harness-created workspace, you are **already isolated**. Report the workspace path (`jj workspace root`) and current bookmarks (`jj bookmark list --revisions @`). Do not create another workspace — a workspace-from-workspace lands in the wrong tree and is invisible to the harness that made the current one. Then **work in place**: in new-work mode, continue here; in isolate-an-existing-ref mode, move to the named ref here rather than nesting another workspace.

## Step 1: Prefer the harness's native workspace tool

If the harness provides a native isolation primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a workspace flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it. A behind-the-back workspace creates phantom state the harness cannot see, navigate to, or clean up.

## Step 2: JJ fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the repo root.** The `.workspaces/` and ignore paths below are repo-root-relative, but the skill runs from the user's current directory, which may be a subdirectory — so move to the root first: `cd "$(jj workspace root)"`. Without this, `.workspaces/<name>` and the ignore edit would land in the subdirectory (e.g. `src/.workspaces/...`, `src/.gitignore`) instead of at the repo root.
2. Choose a meaningful workspace/bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) — avoid opaque auto-generated names. Pick a base bookmark (default: `main@origin`, else `main`).
3. **Ensure `.workspaces/` is ignored before creating anything**, so workspace contents are never tracked: if the repo uses `.gitignore`, add a `.workspaces/` line when absent.
4. Best-effort refresh the base bookmark without disturbing the current workspace: `jj git fetch`. This is **non-fatal** — if it errors (no remote, a differently-named remote, or a local-only repo), do not abort; continue to the next step and use the local ref.
5. Create the workspace — the command depends on the mode:
   - **New work:** `jj workspace add --name <workspace-name> .workspaces/<workspace-name> <base-bookmark>` then `jj bookmark create <bookmark-name> -r @` inside the new workspace. This creates a new change from the base and gives it a bookmark.
   - **Isolate an existing ref:** attach to the ref instead of creating a new bookmark — for an existing bookmark or change ID, `jj workspace add --name <workspace-name> .workspaces/<workspace-name> <target-ref>`. For a **PR**, keep using `gh` for GitHub discovery/checkout when needed, then run `jj git import` if the VCS view changed and attach a JJ workspace to the imported PR ref/bookmark.
6. Switch into it: `cd .workspaces/<workspace-name>`.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current working copy — do not silently continue there (the user chose isolation specifically to avoid it, especially when `ce-work` / `ce-code-review` routed here for the workspace option). Report the failure and ask via the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (via the `pi-ask-user` extension) — offering options such as "work in the current working copy" vs "stop and resolve the permission issue". If no blocking tool exists in the harness or the call errors, present the numbered options in chat and wait for the reply; never skip the confirmation. Only work in the current working copy on explicit confirmation, and do not retry alternative paths automatically.

## Other workspace operations

Use `jj` directly — no wrapper is needed:

```bash
jj workspace list                          # list workspaces
jj workspace forget <workspace-name>        # forget a removed workspace
cd .workspaces/<workspace-name>             # switch to a workspace
cd "$(jj workspace root)"                   # return to the current workspace root
```

## When to create a workspace

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current working copy free for other work
- Running multiple features in parallel without bookmark-switching overhead

Do not create a workspace for single-task work that can happen on a bookmark in the current working copy — and never when Step 0 shows you are already in one.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects isolated workspace in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark/workspace name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Switch to it (`cd .workspaces/<workspace-name>`) or remove the directory and run `jj workspace forget <workspace-name>` before recreating.

**"Cannot forget workspace: it is the current workspace"**: `cd` out of the workspace first, remove the directory if needed, then run `jj workspace forget <workspace-name>`.
