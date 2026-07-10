---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark/change for fresh work, or attach a workspace to an existing bookmark/PR/revision to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated JJ workspace, without disturbing the user's main checkout. Most coding harnesses now create isolation by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to JJ workspace commands.** Never create a workspace the harness cannot see when a native tool is available.

**Two modes, set by the caller's need:**

- **New work (default).** No specific revision named — create a fresh change from a base/default bookmark. This is what `ce-work` uses.
- **Isolate an existing revision.** The caller names a revision to work on in isolation — a PR head, an existing bookmark, or a commit ID. Create a workspace whose working-copy change is based on that revision. Avoid duplicate mutable work on the same change; if the current workspace already targets the requested revision, report that and work in place.

The steps below apply to both modes; the mode only changes what revision becomes the new workspace parent and what bookmark is created/reported.

## Step 0: Detect Existing Isolation

Before creating anything, inspect JJ workspaces:

```bash
jj root
jj workspace list
jj log -r @ --no-graph -T 'change_id ++ " " ++ commit_id ++ "\n"'
jj bookmark list --revisions @
```

If the harness already placed the session in an isolated workspace, report the workspace path/name and continue in place. Do not nest a new workspace inside an isolated one unless the user explicitly asks for a second workspace.

## Step 1: Prefer The Harness's Native Workspace Tool

If the harness provides a native isolation primitive — for example an `EnterWorkspace` / `WorkspaceCreate` tool, a `/workspace` command, or a workspace flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it.

## Step 2: JJ Fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the repo root.** Resolve it with `jj root`. The `.workspaces/` and ignore-rule paths below are repo-root-relative.
2. Choose a meaningful bookmark/workspace name from the work description (e.g. `feat/login`, `fix/email-validation`) — avoid opaque auto-generated names. Pick a base revision (default: the GitHub default bookmark at `<default>@origin`, else `main@origin`, `master@origin`, then local `main`/`master`).
3. Ensure `.workspaces/` is ignored before creating anything, so workspace contents are never tracked by the parent workspace. If the ignore rules do not already cover it, add a `.workspaces/` line to `.gitignore`.
4. Best-effort refresh remote bookmarks without disturbing the current workspace: `jj git fetch --remote origin`. This is **non-fatal** — if it errors, do not abort; continue with local revisions.
5. Create the workspace:
   - **New work:** `jj workspace add --name <workspace-name> --revision <base-rev> .workspaces/<workspace-name>`, then in that workspace run `jj bookmark set <bookmark-name> -r @` if the work needs a publishable bookmark.
   - **Isolate an existing revision:** resolve the PR/bookmark/commit to `<target-rev>`, then run `jj workspace add --name <workspace-name> --revision <target-rev> .workspaces/<workspace-name>`. For PRs, use `gh pr view <n> --json headRefOid,headRefName` for metadata and `jj git fetch --remote origin` so the head revision is visible when possible.
6. Switch into it: `cd .workspaces/<workspace-name>`.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current workspace — do not silently continue there. Report the failure and ask via the platform's blocking question tool, offering options such as "work in the current workspace" vs "stop and resolve the permission issue". Only work in the current workspace on explicit confirmation.

## Other Workspace Operations

Use JJ directly:

```bash
jj workspace list                         # list workspaces
jj workspace forget <workspace-name>       # forget a workspace after removing its directory
cd .workspaces/<workspace-name>             # switch to a workspace
cd "$(jj root)"                            # return to the current workspace root
```

## When To Create A Workspace

Create one only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current workspace free for other work
- Running multiple features in parallel without bookmark-switching overhead

Do not create a workspace for single-task work that can happen in the current workspace — and never when Step 0 shows you are already isolated.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects isolation in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark/workspace name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Switch to it (`cd .workspaces/<workspace-name>`) or remove the directory and run `jj workspace forget <workspace-name>` before recreating.

**"Cannot forget workspace"**: leave the workspace first, then run `jj workspace forget <workspace-name>` from another workspace.
