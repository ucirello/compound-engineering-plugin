---
name: ce-worktree
description: Set up isolated Jujutsu workspaces for fresh work or an existing bookmark, PR, change, or revision. Use when starting isolated work or attaching an existing target without disturbing another workspace; detects existing isolation first.
---

# RocketClaw Workspace Isolation

Ensure the requested work happens in an isolated Jujutsu workspace without disturbing the user's other workspaces. Keep the functional `ce-worktree` name because callers already route to it; interpret "worktree" as Jujutsu workspace isolation.

Order of operations: **detect existing isolation -> prefer native harness isolation -> fall back to `jj workspace add`.** Every successful route ends in a registered Jujutsu workspace with a distinct working-copy change. Never create arbitrary or snapshot-tracked nested workspaces or let two workspaces edit the same working-copy change; the registered, ignored `.tmp` fallback below is the only workspace-local nesting allowed.

## Choose the mode

- **New work (default):** no target was named. Create a fresh child change from the repository's established trunk or selected base revision.
- **Existing target:** the caller named a bookmark, PR, change ID, commit ID, tag, or other revset. Create a fresh child change from that target by default. Use `jj edit <revision>` only when the caller explicitly intends to rewrite that exact mutable revision and no other workspace edits it.

Bookmarks are pointers; Jujutsu has no active bookmark. Isolation does not require creating a bookmark, and creating a child change does not advance one.

## Change descriptions

Before composing, editing, validating, or recommending any Jujutsu change description, follow the project's active instructions and observed message syntax. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply compatible guidance for a concise subject and explanatory body without imposing a fixed prefix, type, scope, canned wording, branding, or attribution. Use dynamic content, such as `jj describe -r <revision> -m <change-description>`, `jj new <parent-revision> -m <change-description>`, or `jj workspace add --name <workspace-name> --revision <starting-revision> -m <change-description> <destination>`. If an actor identifier is required, use the neutral actor `ai:assistant`.

## Step 0: Detect existing isolation

From the caller's current directory, run:

```bash
jj workspace root
jj workspace list
```

- If `jj workspace root` fails, stop: this workflow requires an existing Jujutsu repository. Do not silently substitute another version-control workflow.
- Resolve listed workspace roots with `jj workspace root --name <workspace-name>` when needed. `jj workspace list` identifies registered workspaces and their working-copy revisions; it does not establish which workspace is "primary."
- Treat the session as already isolated only when runtime context positively identifies the current registered workspace as task-specific or harness-created. Do not infer isolation from list order, workspace count, path shape, or workspace name alone.
- If already isolated, report the workspace name and root and work there. For new work, retain a prepared task change or use `jj new <base-revision>` to start a fresh child. For an existing target, use `jj new <target-revision>` by default; use `jj edit <target-revision>` only for an explicit rewrite after proving no workspace already edits it.

Before changing the current workspace's revision, inspect `jj status`, `jj log -r '@ | parents(@)'`, and `jj workspace list`. Preserve occupied work; do not abandon, overwrite, or repurpose it to manufacture isolation.

## Step 1: Prefer native harness isolation

If the harness exposes a native workspace or isolation capability, use it first and supply the selected base or target when supported. Native isolation preserves the harness's navigation and cleanup lifecycle.

After creation, verify the result with `jj workspace root`, `jj workspace list`, and `jj log -r '@ | parents(@)'`. Accept it only when Jujutsu reports a registered workspace with its own working-copy change and the intended parent. If the native result is not Jujutsu-aware, clean up only what that capability just created and continue to Step 2 from the original workspace. Do not add a nested workspace inside the rejected result.

## Step 2: Jujutsu fallback

Use this route only when no suitable native isolation capability exists and Step 0 found no existing task-specific isolation.

1. Resolve the source root with `jj workspace root`; never assume the skill was invoked from that root.
2. Choose a short, meaningful ASCII workspace name from the task. Treat the workspace name and path as identifiers, not as a change description.
3. Set the destination to `<source-workspace-root>/.tmp/rocketclaw/workspaces/<workspace-name>`. Use only workspace-local `.tmp`; never use a global temporary directory. A registered Jujutsu workspace may be placed there only after confirming `.tmp/` is excluded from snapshot tracking, the resolved destination remains under `<source-workspace-root>/.tmp/rocketclaw/workspaces/`, and no existing destination component is a symlink. If `.tmp/` is not excluded, ask before changing the ignore policy and make no workspace there until the exclusion exists. Never create an arbitrary or unignored nested workspace.
4. Resolve the starting revision to exactly one revision using `jj log -r <revset>`. Never guess a trunk name, remote, PR ref, or revset.
5. Create a distinct child working-copy change with `jj workspace add --name <workspace-name> --revision <starting-revision> -m <change-description> <destination>`.
6. Enter the exact path returned by `jj workspace root --name <workspace-name>`, then verify `jj workspace list`, `jj status`, and `jj log -r '@ | parents(@)'` show the intended workspace and parent.

If creation fails because of permissions, sandboxing, an occupied path, stale state, or revision resolution, isolation was not created. Ask a blocking question with at least these choices: work in the current workspace, or stop and resolve isolation. Use the harness's blocking-question capability when available; otherwise ask in chat and wait. Work in the current workspace only after explicit confirmation, and do not retry unrelated paths automatically.

## Resolve the starting revision

Use `jj log -r <revset>` to prove each candidate resolves to exactly one revision before workspace creation.

- **New work:** prefer the configured `trunk()` alias or the repository's established trunk bookmark. Inspect `jj bookmark list --all-remotes` if the base is unclear. When current remote state matters, identify the owning remote and run `jj git fetch --remote <remote> --branch <bookmark>` before resolving `<bookmark>@<remote>`. Ask when remote ownership is ambiguous.
- **Local bookmark:** resolve `<bookmark>`. Start a child change from it; do not move the bookmark merely to isolate work.
- **Remote bookmark:** resolve `<bookmark>@<remote>`. Fetch the selected remote when freshness matters. Track or create a local bookmark only when later publication requires that local name.
- **Change, commit, tag, or revset:** use the caller's value only after it resolves once. Start a child change by default.
- **GitHub PR:** use `gh` only to read the source repository, source bookmark, and head revision. Match an existing remote from `jj git remote list`; if none matches, ask before adding the source repository with `jj git remote add <remote> <url>`. Fetch with `jj git fetch --remote <remote> --branch <source-bookmark>`, resolve `<source-bookmark>@<remote>`, and create the workspace through Step 2. Do not let `gh` checkout or mutate repository state in place of Jujutsu.

For an explicit rewrite, first prove with `jj workspace list` that no workspace edits the target. Create the isolated workspace as a child, enter it, then run `jj edit <target-revision>`. If Jujutsu rejects the edit or reports the revision in use, stop rather than forcing shared working-copy state.

## Bookmarks

Create or move a bookmark only when the surrounding workflow needs a named publication target:

```bash
jj bookmark create <bookmark> -r <revision>
jj bookmark set <bookmark> -r <revision>
```

Use `create` when the local bookmark must be absent and `set` when create-or-update behavior is intended. Confirm the target with `jj bookmark list <bookmark>`; do not infer an active bookmark.

## Workspace operations

```bash
jj workspace list
jj workspace root
jj workspace root --name <workspace-name>
jj workspace update-stale
jj workspace forget <workspace-name>
```

`jj workspace forget` removes registration but does not delete files. Enter a surviving workspace before forgetting another workspace.

## Safe cleanup

Clean up only when requested or when undoing a failed workspace this invocation just created.

1. From another registered workspace, resolve the exact target name and root with `jj workspace list` and `jj workspace root --name <workspace-name>`.
2. Refuse cleanup if the target is current, ambiguous, still needed by the harness, or outside the verified native-isolation path or `<source-workspace-root>/.tmp/rocketclaw/workspaces/<workspace-name>`.
3. Inspect the target with `jj -R <target-root> status` and `jj -R <target-root> log`. Stop if it contains undescribed work, unique changes, needed bookmarks, or ignored artifacts the user has not approved deleting.
4. Run `jj workspace forget <workspace-name>` and confirm the name disappeared from `jj workspace list`.
5. Only after positively confirming the registration is gone, delete the exact directory separately when the user requested deletion and retained artifacts have been handled. Never use globs or recursively delete an unverified path.

## Completion and integration

Creation is complete only after reporting the registered workspace name, resolved root, working-copy revision, parent revision, and any bookmark or remote selected for later publication. If already isolated, report that result instead of creating another workspace. If blocked, report the failed invariant and wait for the required decision.

`ce-work` and `ce-code-review` may route here under the established "worktree" label. Preserve that routing label while providing Jujutsu workspace isolation. Create a workspace only when separate files are useful, such as parallel feature work, long-running checks, or PR review that must not disturb another workspace.

## Troubleshooting

**Workspace name or path exists:** inspect `jj workspace list`. Reuse it only when it is the intended target; otherwise choose another meaningful name without overwriting the path.

**Workspace is stale:** enter it, run `jj workspace update-stale`, and inspect the recovered state before continuing.

**Workspace directory was removed first:** from a surviving workspace, verify the stale registration and run `jj workspace forget <workspace-name>` for that exact entry.

**Cannot forget the current workspace:** leave it, resolve another registered workspace root, and retry from there.
