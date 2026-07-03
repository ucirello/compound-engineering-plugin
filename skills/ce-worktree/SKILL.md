---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark for fresh work, or attach a workspace to an existing bookmark/PR/revision. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace without disturbing the user's main checkout. Most coding harnesses now create isolation by default at session start, so the common case is that **isolation already exists** — detect that first and do not create a redundant one.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to JJ workspace commands.** Never create an isolated workspace the harness cannot see when a native primitive exists.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh JJ workspace and bookmark from a base bookmark/revision. This is what `ce-work` uses.
- **Isolate an existing ref.** The caller names a ref to work on in isolation — a PR head, existing bookmark, tag, change ID, commit ID, or revset. Attach the workspace to that ref instead of creating an unrelated bookmark.

## Step 0: Detect Existing Isolation

Run:

```bash
jj workspace list
jj root
```

If `jj workspace list` shows the current workspace is already a secondary or task-specific workspace (for example under `.worktrees/`, `.workspaces/`, `.claude/worktrees/`, or another harness-managed isolation path), report the workspace path and current `@` summary. Do not create another workspace. Work in place unless the caller explicitly needs a different target ref.

If the current workspace is the main checkout, continue to Step 1.

## Step 1: Prefer The Harness Native Workspace Tool

If the harness provides a native isolation primitive — for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a workspace flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it.

## Step 2: JJ Fallback

Only when there is no native tool **and** Step 0 found no existing isolation.

1. **Run from the repo root.** The `.worktrees/` path below is repo-root-relative, but the skill runs from the user's current directory, which may be a subdirectory:

   ```bash
   cd "$(jj root)"
   ```

2. Choose a meaningful bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) — avoid opaque auto-generated names. Pick a base revision (default: the remote default bookmark if known, else `main@origin`, else `main`).
3. Ensure `.worktrees/` is ignored by the repo before creating anything. If it is not already covered by ignore rules, add a `.worktrees/` line to the repo-root ignore file used by the project.
4. Best-effort refresh the base without disturbing the current workspace:

   ```bash
   jj git fetch --remote origin --branch <from-bookmark>
   ```

   This is **non-fatal** — if it errors (no `origin` remote, a differently-named remote, or local-only work), continue and use the local bookmark/revision.

5. Create the workspace — the command depends on the mode:

   ```bash
   # New work
   jj workspace add --name <bookmark-name> --revision <base-rev> .worktrees/<bookmark-name>
   cd .worktrees/<bookmark-name>
   jj bookmark create <bookmark-name> -r @

   # Existing ref
   jj workspace add --name <slug> --revision <target-rev> .worktrees/<slug>
   cd .worktrees/<slug>
   ```

For a PR, prefer `gh pr view <number> --json headRefName,headRefOid,baseRefName` to identify the target, then create the JJ workspace at the fetched/visible head revision. Keep the PR number in the summary so later PR operations use `gh` against the right PR.

If `jj workspace add` fails with a sandbox or permission error, the requested isolation could not be created. This needs a **blocking** user decision before touching the current workspace — do not silently continue there. Report the failure and ask via the platform's blocking question tool (`AskUserQuestion` / `request_user_input` / `ask_user`), offering options such as "work in the current workspace" vs "stop and resolve the permission issue". Only work in the current workspace on explicit confirmation, and do not retry alternative paths automatically.

## Other Workspace Operations

Use JJ directly — no wrapper is needed:

```bash
jj workspace list                         # list workspaces
jj workspace forget <workspace-name>      # forget workspace metadata
cd .worktrees/<bookmark-or-slug>          # switch to a workspace directory
cd "$(jj root)"                           # return to the current workspace root
```

If you need to delete the directory too, remove it after `jj workspace forget` from a different workspace/directory.

## When To Create A Workspace

Create one (Step 1/2) only when you are **not** already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current workspace free for other work
- Running multiple features in parallel without bookmark-switching overhead

Do not create a workspace for single-task work that can happen on the current bookmark/change — and never when Step 0 shows you are already in one.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects isolation in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark name derived from the work description.
