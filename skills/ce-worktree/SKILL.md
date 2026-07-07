---
name: ce-worktree
description: Set up isolated JJ workspaces — create a bookmark-oriented workspace for fresh work, or attach a workspace to an existing bookmark/PR/change to work on it in isolation. Use when starting isolated work or isolating an existing ref; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated JJ workspace without disturbing the user's primary workspace. Most coding harnesses now create isolation at session start, so first detect whether isolation already exists and avoid creating a redundant workspace.

Order of operations: **detect existing isolation -> prefer a native workspace tool -> fall back to `jj workspace add`**. Never create a workspace the harness cannot see when a native tool is available.

**Two modes, set by the caller's need:**

- **New work (default).** No specific ref named — create a fresh change from a trunk bookmark and attach a meaningful bookmark.
- **Isolate an existing ref.** The caller names a PR head, existing bookmark, change ID, or revision ID. Create or enter a workspace at that target instead of switching the current workspace.

## Step 0: Detect Existing Isolation

Before creating anything, inspect JJ workspaces:

```bash
jj workspace list
jj workspace root
```

If the current directory is already a non-primary or harness-managed workspace, report the workspace path and current revision/bookmarks, then work in place. Do not create a workspace from inside another workspace unless the user explicitly asks for a second isolated copy.

## Step 1: Prefer The Harness Native Workspace Tool

If the harness provides a native workspace primitive — for example an `EnterWorkspace` / `WorkspaceCreate` tool, a `/workspace` command, or a workspace flag — use it and stop. Native tools place, track, and clean up the workspace so the harness can manage it.

## Step 2: JJ Fallback

Only when there is no native tool and Step 0 found no existing isolation:

1. Resolve the repo root with `jj workspace root`; run from the repo root before using relative `.workspaces/` paths.
2. Choose a meaningful bookmark name from the work description (e.g. `feat/login`, `fix/email-validation`) and a base bookmark (default: the project's trunk bookmark, usually `main` or `main@origin`).
3. Ensure `.workspaces/` is ignored before creating anything so nested workspaces are not tracked. If needed, add `.workspaces/` to repo ignore rules.
4. Refresh remotes when useful with `jj git fetch`. This is non-fatal for local-only repos.
5. Create the workspace:

```bash
jj workspace add --name <workspace-name> .workspaces/<workspace-name> <base-bookmark-or-rev>
# Work in .workspaces/<workspace-name> after the workspace is created.
jj bookmark set <bookmark-name> -r @
```

For an existing PR, use `gh` to identify the PR head ref and create the JJ workspace at that fetched bookmark or revision. Do not switch the current workspace; the target is a JJ workspace plus bookmark/change.

If `jj workspace add` fails with a sandbox or permission error, ask a blocking user question before touching the current workspace. Use `AskUserQuestion` in Claude Code, `request_user_input` in Codex, `ask_question` in Antigravity CLI, or `ask_user` in Pi when available; fall back to chat only when no blocking tool exists or the call errors. Offer options such as "work in the current workspace" vs "stop and resolve the permission issue". Only work in the current workspace on explicit confirmation.

## Other Workspace Operations

Use JJ directly:

```bash
jj workspace list
jj workspace forget <workspace-name>
cd .workspaces/<workspace-name>
cd "$(jj workspace root)"
```

Delete the workspace directory only after `jj workspace forget <workspace-name>` succeeds or reports that the workspace is already forgotten.

## When To Create A Workspace

Create one only when you are not already isolated and you need a separate workspace:

- Reviewing a PR while keeping the current workspace free for other work
- Running multiple features in parallel without bookmark/revision switching overhead

Do not create a workspace for single-task work that can happen on the current change, and never when Step 0 shows you are already in an isolated workspace.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects workspace isolation in those flows, run Step 0 first: if the work is already isolated, proceed in place; otherwise create one (native tool preferred) with a meaningful bookmark name derived from the work description.

## Troubleshooting

**"Workspace already exists"**: the path is in use. Switch to it (`cd .workspaces/<workspace-name>`) or forget and remove it before recreating.

**"Cannot forget current workspace"**: move to another workspace first, then run `jj workspace forget <workspace-name>`.
