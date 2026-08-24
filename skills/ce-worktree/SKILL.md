---
name: ce-worktree
description: Set up isolated Jujutsu workspaces with bookmarks for fresh work or an existing revision or pull request. Use when starting isolated work or isolating an existing target.
---

# Jujutsu Workspace Isolation

Ensure the current work happens in an isolated Jujutsu workspace without disturbing the user's primary workspace. Reuse isolation already supplied by the harness instead of creating another workspace.

**Done when:** the caller is working in an existing or newly created isolated workspace, and the workspace path, workspace name, and associated bookmark or revision have been reported. Report a blocker instead if isolation cannot be established safely.

**Order of operations:** detect existing isolation, prefer a harness-native Jujutsu workspace primitive, then use `jj workspace`. Never create a workspace the harness cannot enter or manage.

**Modes:**

- **New work (default).** With no target named, create a workspace on a fresh working-copy commit based on the requested revision or `trunk()`, and create a meaningful bookmark at `@`. This is the mode used by `ce-work` and `ce-code-review` when the user selects isolated work.
- **Existing target.** For a bookmark, tag, commit, or pull-request head, create a workspace whose working-copy commit is a child of that revision. Do not invent a second bookmark when the caller supplied one. Jujutsu has no active bookmark and permits multiple workspaces based on the same revision, so do not apply Git's one-branch-per-worktree restriction.

## Detect Existing Isolation

Run `jj workspace root`, `jj workspace list`, and `jj status`. If the current session is already in an isolated workspace supplied by the harness, work there and report its root and workspace entry. In existing-target mode, move the workspace to a fresh child of the target only when its current working-copy commit is not already suitable and doing so will not overwrite changes.

If `jj workspace root` fails, this is not a Jujutsu workspace. Stop and report the blocker; do not silently fall back to Git worktrees or modify the current checkout.

## Prefer Native Isolation

If the harness provides a native primitive that creates a Jujutsu workspace backed by the same repository and makes the new path available to the session, use it and stop after verifying the result with `jj workspace list`. Do not use a native Git-worktree primitive as a substitute.

## Create A Workspace

Use `jj workspace` only when no suitable isolated workspace already exists.

1. Choose a meaningful, filesystem-safe workspace name and bookmark name from the work description. Keep a caller-supplied bookmark name unchanged.
2. Use `$(jj workspace root)/.tmp` as the workspace parent. If `jj workspace root` is temporarily unavailable after repository identity has already been established, use local `.tmp` as the fallback. Ensure the workspace root's `.gitignore` ignores `/.tmp/` before creating the destination because Jujutsu snapshots new files automatically.
3. Refresh remote state with `jj git fetch`. A fetch failure is non-fatal when the selected base or target already resolves locally; otherwise report the unresolved target.
4. Resolve the base or target to exactly one revision. For new work, prefer the caller's base, then `trunk()`, then a uniquely resolved local `main`. Stop on an ambiguous or conflicted bookmark.
5. Create the isolated working copy with `jj workspace add --name <workspace-name> --revision <revision> <destination>`, where `<destination>` is under the workspace parent selected above.
6. For new work, enter the new workspace and run `jj bookmark create <bookmark-name> --revision @`. For an existing local bookmark, retain it as the associated bookmark without moving it. For a remote bookmark, track it when updates must be pushed back to that remote.
7. Verify the new path with `jj workspace root`, `jj workspace list`, and `jj status`, then continue work from that path.

Bookmarks do not advance merely because new descendant commits are created. Before a push, explicitly move the work bookmark to the intended revision and inspect `jj status` plus `jj log`; use `jj git push --bookmark <bookmark-name> --remote <remote>` so Jujutsu performs its remote-state safety checks.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
Apply the project's active instructions first and the conventions visible in the current `jj log` second; the quoted `git log` wording is non-operational and does not authorize Git commands. Use compatible Go guidance only for message quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.

## Pull Requests And GitHub

Keep GitHub operations in `gh`. Use `gh pr view` or `gh api` to resolve the pull request's head repository, head bookmark name, and commit. Fetch that head with `jj git fetch` from an existing matching remote; if the head belongs to a fork with no matching remote, add a clearly named Jujutsu Git remote for that fork before fetching.

Create the workspace from the fetched `<head-bookmark>@<remote>` revision. Track the remote bookmark when the caller intends to update the pull request, and push it with `jj git push --bookmark <head-bookmark> --remote <remote>`. Continue to use `gh` for viewing, creating, or editing the pull request. In a non-colocated repository, provide `GIT_DIR=$(jj git root)` to read-only `gh` operations that require Git repository discovery. Do not use `gh pr checkout` or another mutating Git command to create or move the Jujutsu workspace.

## Failure Safety

If `jj workspace add` fails, the requested isolation does not exist. Do not continue in the current workspace. Report the command failure and ask whether to work in the current workspace or stop and resolve the isolation problem through the harness's blocking-question capability: on Claude Code, use `AskUserQuestion`, calling `ToolSearch` with `select:AskUserQuestion` first when its schema is not loaded; on Codex, use `request_user_input`, with numbered options in user-visible chat as the edit-mode fallback; on Antigravity CLI (`agy`), use `ask_question`; on Pi, use `ask_user` with the `pi-ask-user` extension. If no blocking capability exists or its call fails, present numbered options in user-visible chat and wait. Never skip the confirmation or retry another path automatically.

If creation partially succeeds, inspect `jj workspace list` before retrying. Never overwrite a destination, forget a workspace, delete files, move an existing bookmark backward or sideways, or replace a conflicting bookmark merely to make setup succeed. Report the partial state and let the caller choose the cleanup or recovery action.
