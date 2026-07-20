---
name: ce-worktree
description: Set up isolated Jujutsu workspaces for fresh work or an existing bookmark, PR, change, or revision. Use when starting isolated work or attaching an existing target without disturbing another workspace; detects existing isolation first.
---

# Workspace Isolation

Create or reuse a Jujutsu workspace without changing the caller's working-copy commit, moving its bookmarks, or mixing its uncommitted files into the requested work. A JJ workspace has its own working-copy commit; it is not a branch checkout, and the same bookmark or revision may safely be the starting point for multiple workspaces.

Order of operations: **detect the current JJ workspace -> honor existing isolation -> resolve the target -> add or reuse a workspace.** Use JJ for all workspace and repository operations. Use `gh` only to resolve pull-request metadata.

## Modes

- **Fresh work (default):** no target was supplied. Start a new workspace at the best base revision selected under Target precedence.
- **Existing target:** start at a supplied bookmark, remote bookmark, change ID, commit ID, revset, or pull-request head. Do not move the target bookmark during setup; `jj workspace add` creates a new working-copy commit on top of the selected revision.
- **Workspace maintenance:** list or forget registered workspaces without creating one.

Workspace names are identifiers, not change descriptions. Prefer a caller-supplied name, then a provider-supplied name, then a short ASCII name derived from the task. Follow project naming conventions when present; do not impose a prefix, type list, or fixed naming syntax.

## Step 0: Detect the current workspace

Run these read-only commands before creating anything:

```bash
jj workspace root
jj workspace list
jj status
jj log -r @ --no-graph
```

- If `jj workspace root` succeeds, record its resolved path and identify the current workspace in `jj workspace list` by the working-copy revision shown for `@`.
- If the caller or harness already placed this task in a dedicated workspace, report its name and root and work there. Do not nest another workspace.
- Do not assume that every JJ workspace is already isolated: the repository's original workspace is also a workspace. When intent is unclear, use the caller's request, harness context, workspace name/path, and the other listed workspaces to decide whether the current one is task-specific.
- If the directory is not in a JJ workspace, stop and ask whether to initialize or colocate a JJ repository. Initialization changes repository state and is outside this skill's implicit authority.
- If `jj status` shows user work, leave it untouched. Never run commands in the current workspace that edit, abandon, rebase, squash, describe, or create a new `@` merely to prepare another workspace.

JJ command options evolve. Treat the commands in this skill as operational examples; when installed syntax differs, use runtime `jj help workspace`, `jj help git fetch`, and the project's working JJ syntax. Runtime behavior and help take precedence over fixed command spelling.

## Step 1: Reuse before creating

Inspect `jj workspace list` for a workspace already assigned to this task or target.

- Reuse it only when its identity and destination are unambiguous. Return its existing root rather than adding a duplicate.
- A stale workspace entry is not permission to forget it. Report it and ask before changing shared workspace metadata.
- If the requested workspace name is already registered for different work, or the intended destination already exists, preserve both and choose another name/path or ask. Never overwrite, empty, or delete a directory.

## Step 2: Resolve the target revision

Use this precedence:

1. The caller's explicit revision, change ID, bookmark, remote bookmark, or PR.
2. A target supplied by the routing provider or harness.
3. For fresh work, the project's configured trunk alias or established base revset.
4. For fresh work with no project convention, `trunk()` when it resolves unambiguously.
5. If no safe base resolves, ask rather than guessing from the caller's dirty `@`.

Resolve locally first with `jj log -r '<target>' --no-graph`. Bookmark names are revsets; remote bookmarks use their JJ form, such as `<bookmark>@<remote>`. Quote user-provided revsets as data and do not splice them into a larger expression.

For a bookmark expected from a remote, refresh remote state without changing any working copy:

```bash
jj git remote list
jj git fetch --remote <remote> --branch <bookmark>
jj bookmark list --all-remotes
jj log -r '<bookmark>@<remote>' --no-graph
```

Fetching is allowed only when needed to resolve the requested base or when the caller asks for current remote state. A fetch failure is non-destructive: report it and retain all current workspace state.

### Pull-request targets

Use `gh pr view <number-or-url>` to obtain the PR's head repository owner, head repository, head branch, head revision, and state. Do not use `gh pr checkout`: it models branch checkout and may mutate the current working copy.

1. Match the PR head repository to an existing entry from `jj git remote list`.
2. If no matching remote exists, obtain the repository URL with `gh repo view <owner>/<repository>` and ask before adding a JJ remote. Adding a remote is shared repository configuration, so do not do it silently.
3. Fetch only the head branch with `jj git fetch --remote <remote> --branch <head-bookmark>`.
4. Verify the fetched remote bookmark and, when available, compare its commit ID with the PR head revision reported by `gh`.
5. Use `<head-bookmark>@<remote>` as the workspace target. Do not create or move a local bookmark during workspace setup.

If the PR is closed, its branch was deleted, the head revision cannot be fetched, or metadata and fetched state disagree, stop and report the discrepancy. Never substitute the base branch or a similarly named local bookmark.

## Step 3: Add the workspace

Choose a durable destination that the user can find and manage. Prefer a destination explicitly supplied by the caller or harness; otherwise use a non-existing sibling directory outside the current workspace. A workspace is durable user work, not scratch: do not place it in OS temporary storage or inside the current repository's tracked tree.

From the current JJ workspace, add the new workspace at the resolved target:

```bash
jj workspace add --name <workspace-name> --revision '<target>' <destination>
```

Before running it, confirm from `jj workspace list` that the name is unused and confirm that the destination does not exist. Do not pre-create the destination unless runtime `jj help workspace add` requires it.

After creation, operate in the returned destination and verify:

```bash
jj workspace root
jj status
jj log -r @ --no-graph
```

The new `@` should be a distinct working-copy commit based on the target. The original workspace's `@`, files, and bookmarks must remain unchanged. Do not create a bookmark merely to represent the workspace. If later work needs to publish through an existing bookmark, the shipping flow moves that bookmark deliberately after changes are ready.

If workspace creation fails, do not retry with destructive flags, another base, or a path inside the current workspace. Report the command failure and ask via the platform's blocking question interface: `AskUserQuestion` in Claude Code, `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), or `ask_user` in Pi through the `pi-ask-user` extension. Offer to choose another destination, continue in the current workspace, or stop. If no blocking interface exists, present numbered options and wait. Continue in the current workspace only after explicit confirmation.

## Describing fresh work

Workspace creation does not require a description. If the caller explicitly asks to describe the new working-copy change during setup, inspect the project's runtime instructions and recent descriptions using the project's working `jj log` syntax before composing it. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime project instructions and description syntax inferred from `jj log` take precedence; apply compatible Go guidance only to quality, clarity, and structure. Do not impose fixed prefixes, types, scopes, wording, examples, or templates.

Apply the resulting project-native text with `jj describe -m '<description-composed-from-runtime-conventions>'` from the new workspace only. Do not describe the original workspace's `@`.

## List, enter, and forget

```bash
jj workspace list
jj -R <workspace-path> status
jj workspace forget <workspace-name>
```

- **List:** use `jj workspace list`; verify a candidate path with `jj -R <workspace-path> workspace root` before operating there.
- **Enter:** change the tool working directory to the workspace root. Do not infer a destination solely from the workspace name.
- **Forget:** run `jj workspace forget <workspace-name>` from another live workspace only after confirming the target name and preserving any work it contains. Forgetting unregisters workspace metadata; it does not delete the directory or its files.
- Never recursively delete a forgotten workspace. Return the preserved directory path so the user can inspect or remove it separately.
- If a workspace copy is stale after repository activity elsewhere, use the JJ-provided stale-workspace recovery shown by runtime help rather than recreating, overwriting, or manually editing metadata.

## Integration

`ce-work` and `ce-code-review` may route here when the user selects workspace isolation. Provider-native isolation may supply a workspace name, destination, or already-created JJ workspace; honor that runtime state before applying local defaults. Functional provider tools still take precedence for navigation and lifecycle when they explicitly support JJ workspaces, but never translate the request into another VCS's worktree operations.

Return the workspace name, absolute root, starting revision/change ID, target bookmark or PR when applicable, and whether the workspace was reused or created. Return failures without modifying the original workspace.
