---
name: ce-worktree
description: Set up isolated JJ workspaces for fresh work or an existing bookmark, pull request, or revision. Use when starting isolated work or isolating an existing revision; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated JJ workspace without disturbing the user's primary workspace. Many coding harnesses create an isolated workspace at session start, so the common case is that isolation already exists.

**Done when:** the caller is working in an existing or newly created isolated workspace and its path, workspace name, working-copy change, and relevant bookmark or pull-request head have been reported, or a blocker has been reported instead.

**Order of operations: detect existing isolation -> prefer a JJ-aware native workspace tool -> fall back to `jj workspace`.** Never create a workspace the harness cannot enter or manage.

**Two modes, set by the caller's need:**

- **New work (default).** No revision named: create a fresh working-copy change and meaningful bookmark on the project's trunk revision. This is what `ce-work` and `ce-code-review` use when the user picks workspace isolation.
- **Isolate existing work.** The caller names a pull-request head, bookmark, tag, change ID, or commit ID: create the workspace with a fresh working-copy change whose parent is that revision. Separate JJ workspaces may use the same parent, so an existing workspace at that revision is not a conflict.

## Step 0: Detect Existing Isolation

Resolve the current root with `jj workspace root` and inspect `jj workspace list`, including each available root. Use the harness's workspace context to determine whether the current workspace is the isolation created for this task; the existence of another workspace alone does not make the current one isolated.

- If the current workspace is already the task's isolation, report its root, workspace name, `@` change ID, and bookmarks from `jj log`, then work in place. Creating another workspace can put the caller in a path the harness does not manage.
- In isolate-existing-work mode, first verify with `jj log` that the current working-copy change is based on the requested revision. If it is not and the current change contains work, stop and report the conflict rather than switching away from that work. If it is empty, create a new working-copy change on the requested revision with `jj new <target-revision>` and continue in place.
- If `jj workspace root` fails, no JJ workspace has been established. Use the current directory only as the local fallback root for `.tmp`; report the missing repository as a blocker unless a JJ-aware native tool can establish the requested workspace.

## Step 1: Prefer a Native Workspace Tool

If the harness provides a JJ-aware native workspace primitive - for example an `EnterWorktree` / `WorktreeCreate` tool, a `/worktree` command, or a `--worktree` flag whose implementation supports JJ - use it when it can create the workspace under `<workspace-root>/.tmp/rocketclaw/workspaces/<workspace-name>` and expose the resulting path to the current session. Native tools own their placement, navigation, and cleanup contracts; use the same base or target revision rules as the fallback below. If the primitive cannot satisfy the JJ or path contract, continue only when the `jj workspace` result will be visible to the harness; otherwise report the incompatibility as a blocker.

## Step 2: JJ Fallback

Only when there is no suitable native tool and Step 0 found no existing isolation:

1. Resolve `<workspace-root>` with `jj workspace root`; use the current directory only if that lookup fails. All temporary workspace state belongs under `<workspace-root>/.tmp/rocketclaw`, with this workflow's workspaces under `<workspace-root>/.tmp/rocketclaw/workspaces/`. Do not use OS-global temporary storage or a user-global cache.
2. Before creating the destination, ensure `.tmp/` is ignored according to the project's active ignore conventions. If it is not ignored, add the minimal `.tmp/` ignore entry before creating the directory so JJ does not snapshot workspace internals.
3. Use the project's active instructions and relevant `jj log` history to determine the trunk revision, remote, workspace name, bookmark conventions, and description style. Choose meaningful values from the work rather than opaque generated values, and use neutral dynamic placeholders in commands.
4. When composing or validating the initial change description, project-local conventions take precedence. Apply the following Go guidance only to quality, clarity, and structure; do not impose fixed syntax or content:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

5. Resolve the target revision:
   - **New work:** use the trunk revision established by the active project instructions and `jj log`; `trunk()` is acceptable when the repository config resolves it correctly. Refresh a configured remote bookmark with `jj git fetch --remote <remote-name> --branch <remote-branch>` when one exists. Fetch failure is non-fatal when the local revision is valid.
   - **Existing local work:** resolve the supplied bookmark, tag, change ID, or commit ID with `jj log -r <target-revision>`. Stop rather than guessing if it is absent or ambiguous.
   - **Pull request:** use `gh pr view <pull-request> --json headRefName,headRefOid,headRepository,headRepositoryOwner` to identify the exact head commit, head branch, and head repository. Reuse a matching configured JJ remote, or add a meaningfully named remote with `jj git remote add <remote-name> <head-repository-url>`, then import the head with `jj git fetch --remote <remote-name> --branch <head-branch>`. Verify the exact head commit with `jj log` and use it as the target. Preserve the remote and head-branch mapping in the handoff so later updates can move or create the corresponding bookmark and use `jj git push --remote <remote-name> --bookmark <bookmark-name>` without orphaning the work.
6. Create the parent directory under `<workspace-root>/.tmp/rocketclaw/workspaces/`, then create one workspace with `jj workspace add --name <workspace-name> --revision <target-revision> --message <description> <workspace-root>/.tmp/rocketclaw/workspaces/<workspace-name>`. This creates a fresh working-copy change on the selected revision; do not edit an immutable target directly. For new work, create the selected bookmark at `@` with `jj bookmark create <bookmark-name> --revision @`. For existing work, retain the resolved bookmark or pull-request mapping for the later bookmark update rather than inventing a disconnected name.
7. Enter the new workspace through the harness-supported navigation mechanism. Confirm its root and working-copy change with `jj workspace root`, `jj workspace list`, `jj status`, and `jj log`, then report the path, workspace name, `@` change ID, parent revision, and any relevant bookmark or pull-request remote mapping.

If workspace creation fails because of permissions, stale workspace state, revision resolution, or remote import, the requested isolation does not exist. Do **not** proceed in the current workspace: report the command and failure, then ask whether to work in the current workspace or stop and resolve the blocker using the platform's blocking question tool: `AskUserQuestion` in Claude Code (call `ToolSearch` with `select:AskUserQuestion` first if its schema isn't loaded), `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), or `ask_user` in Pi (via the `pi-ask-user` extension). Only when no blocking tool exists or the call errors, present numbered options in chat and wait for the reply. Never infer consent or retry in an external or global temporary path.
