---
name: ce-worktree
description: Set up isolated Jujutsu workspaces for fresh work or an existing bookmark, PR, change, or revision. Use when starting isolated work or attaching an existing target without disturbing another workspace; detects existing isolation first.
---

# Workspace Isolation

Ensure the current work happens in an isolated Jujutsu workspace without disturbing the user's primary workspace. A harness may already have isolated the session, so detect that before creating anything.

Order of operations: **detect an existing Jujutsu workspace -> prefer native harness isolation -> fall back to `jj workspace add`.** After native isolation, verify that Jujutsu recognizes the result. Never create a nested or unregistered workspace.

**Two modes, set by the caller's need:**

- **New work (default).** No target was named. Start a fresh working-copy change from the selected trunk or base revision.
- **Isolate an existing target.** The caller names a bookmark, PR, change ID, commit ID, tag, or other revset. Resolve that target and start from it. Create a child change by default; edit the target itself only when the caller explicitly intends to rewrite that revision.

Jujutsu has no active-bookmark constraint: bookmarks are pointers, not checked-out branches. Different workspaces must still have distinct working-copy changes. Never make two workspaces edit the same working-copy change.

## Step 0: Detect existing isolation

From the caller's current directory, run the read-only discovery commands:

```bash
jj workspace root
jj workspace list
```

- If `jj workspace root` fails, stop and report that the current checkout is not a Jujutsu workspace. Do not silently substitute another version-control workflow.
- Treat the resolved output of `jj workspace root` as the current workspace root. Use `jj workspace list` to match that path to its registered workspace and to distinguish the primary workspace from a secondary or harness-created workspace.
- If the session is already in a secondary or harness-created registered workspace, report its name and root and do not create another. Work there: in new-work mode, start a fresh change from the base if the workspace is not already prepared; in existing-target mode, start a child of the resolved target, or use `jj edit` only for an explicitly requested rewrite.
- If the current root is the primary workspace and no task-specific isolation exists, continue to Step 1.

Use `jj status` and `jj log` before changing what the current workspace edits. Preserve existing work; do not abandon, rebase, or overwrite an occupied working-copy change to prepare isolation.

## Step 1: Prefer native harness isolation

If the harness exposes a native workspace or isolation primitive, use it first. Supply the selected base or existing target through that primitive when supported. Native isolation lets the harness track navigation and cleanup.

After it completes, run `jj workspace root` and `jj workspace list` in the result. Continue there only if the new root is a registered Jujutsu workspace with its own working-copy change. If the native primitive cannot create Jujutsu-aware isolation, leaves the result unregistered, or reuses another workspace's working-copy change, clean up only what that primitive created and continue to Step 2. Do not layer `jj workspace add` inside the native result.

## Step 2: Jujutsu fallback

Use this only when there is no suitable native primitive and Step 0 found no existing task-specific isolation.

1. **Anchor paths at the current workspace root.** Resolve it with `jj workspace root`; do not assume the skill was invoked from the root.
2. Choose a short, meaningful ASCII workspace name from the task, such as `feat-login`, `fix-email-validation`, or `pr-123`. Workspace names and filesystem paths are identifiers, not change descriptions.
3. Put fallback workspaces under `<current-workspace-root>/.tmp/rocketclaw/workspaces/<workspace-name>`, never in a global temporary directory. Ensure `.tmp/` is ignored by the repository's `.gitignore` before creating the workspace. Do not overwrite or broadly reformat `.gitignore`.
4. Resolve the starting revision as described below. If current remote state matters, refresh it with `jj git fetch` first. A fetch failure is non-fatal only when the needed revision already resolves locally and the caller accepts potentially stale state.
5. Check the installed `jj workspace add --help` and use that runtime's supported `--name` and revision-selection syntax to add the named workspace at the chosen path. The runtime syntax wins; do not rely on a fixed command spelling copied from this skill.
6. Enter the exact root reported by `jj workspace root --name <workspace-name>`, then confirm `jj workspace list`, `jj status`, and `jj log` show the intended workspace and parent revision.

If workspace creation fails with a sandbox, permission, path, stale-state, or revision-resolution error, isolation was not created. Ask a blocking question before touching the primary workspace, offering at least "work in the current workspace" and "stop and resolve isolation". Use whatever blocking question capability the harness provides. If none exists or it errors, present numbered options in chat and wait. Work in the primary workspace only after explicit confirmation; do not retry unrelated paths automatically.

## Resolve the starting revision

Use `jj log` with the syntax supported by the installed runtime to prove that the requested revset resolves to exactly one revision before creating or retargeting a workspace. Do not pin a template or fixed `jj log` invocation: aliases, revset configuration, and supported flags vary by runtime.

- **New work:** prefer the repository's configured trunk alias or established trunk bookmark. Otherwise inspect local and remote bookmarks and select the repository's actual default line. After any needed `jj git fetch`, start a fresh child change from that revision.
- **Local bookmark:** resolve the bookmark directly. A workspace starts a child change from it by default; bookmarks do not move automatically as new child changes are created.
- **Remote bookmark:** use the Jujutsu namespace `<bookmark>@<remote>`. Fetch that remote when freshness matters. Track or create a local bookmark only when later updates must be pushed under that bookmark name.
- **Change or commit:** pass the unambiguous change ID, commit ID, or caller-supplied revset after verifying it resolves once. Prefer a child change; use `jj edit` only when rewriting that exact revision is intentional.
- **PR:** query the available review-host capability for the PR's source repository, source bookmark, and head revision. Map the source to Jujutsu's `<bookmark>@<remote>` namespace. If the source remote is already configured, fetch that bookmark with `jj git fetch`; otherwise add a narrowly named remote such as `pr-<number>`, fetch it, and resolve `<source-bookmark>@pr-<number>`. Start a child change for additive fixes, or edit the intended PR revision only when the update workflow requires rewriting it. Keep the source bookmark mapping so later work can move and push the correct bookmark instead of publishing an unrelated one.

Never guess that `main`, `master`, `origin`, a PR number, or a filesystem slug is a valid revset. Quote shell revsets when they contain operators or punctuation.

## Other workspace operations

Use Jujutsu's workspace commands directly:

```bash
jj workspace list
jj workspace root
jj workspace root --name <workspace-name>
jj workspace update-stale
```

Use the installed command help for mutating forms so runtime syntax wins. `jj workspace forget` removes workspace registration but does not delete its files.

## Safe cleanup

Clean up only when requested or when this skill is undoing a workspace it just created unsuccessfully.

1. Leave the workspace being removed and operate from another registered workspace.
2. Resolve the exact workspace name and root with `jj workspace list` and `jj workspace root --name <workspace-name>`. Refuse cleanup if either is ambiguous, if the target is the current workspace, or if the path is not the expected native-isolation path or `<known-workspace-root>/.tmp/rocketclaw/workspaces/<workspace-name>`.
3. Inspect the target from its verified root with `jj -R <target-workspace-root> status` and `jj -R <target-workspace-root> log`. If it contains undescribed work, changes not reachable elsewhere, or bookmarks the caller still needs, stop and report them. Also check for ignored or untracked artifacts that Jujutsu status may not report.
4. Forget the exact workspace with `jj workspace forget` using the installed runtime's syntax. Do not abandon its change or delete its bookmarks as part of workspace cleanup.
5. Confirm the name disappeared from `jj workspace list`. Delete the exact filesystem directory separately only when the caller requested deletion and all retained artifacts have been handled. Never use globs, delete a workspace root that still appears in the list, or recursively delete an unverified path.

## When to create a workspace

Create one only when the current session is not already isolated and separate files are useful:

- Reviewing a PR while keeping the primary workspace free for other work
- Running multiple features or long-running tasks in parallel
- Working on a named revision without changing another workspace's working-copy change

Do not create a workspace for work that can safely happen in the current task-specific workspace, and never nest one inside existing harness isolation.

## Integration

`ce-work` and `ce-code-review` offer this skill as an option. When the user selects "worktree" in those flows, interpret that existing label as a request for Jujutsu workspace isolation. Run Step 0 first; proceed in place when already isolated, otherwise create a workspace with a meaningful task-derived name.

## Troubleshooting

**Workspace name or path already exists:** inspect `jj workspace list`. Reuse the existing workspace only if it is the intended target. Otherwise choose a different name; do not overwrite the path.

**Workspace is stale:** enter that workspace and use `jj workspace update-stale`, then inspect the recovered state before continuing.

**Workspace directory was removed first:** from a surviving workspace, inspect the registered entry and use `jj workspace forget` for that exact missing workspace.

**Cannot forget the current workspace:** leave it, resolve another registered workspace root, and run cleanup from there.
