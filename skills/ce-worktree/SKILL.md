---
name: ce-worktree
description: Set up isolated colocated JJ workspaces for fresh work or an existing bookmark, PR, or revision. Use when starting isolated work or isolating an existing ref.
---

# Worktree Isolation

Ensure the current work happens in an isolated workspace without disturbing the user's primary checkout. The common case is that the harness already provided isolation.

**Done when:** the caller is working in a verified isolated workspace, existing or newly created, and its absolute path, registered workspace name, revision, and applicable bookmarks have been reported; otherwise report a blocker.

**Order:** detect existing isolation → prefer a supported harness-native colocated JJ workspace capability → native JJ creation with harness-session adoption. Never create a workspace the harness cannot see. Use the latest JJ; never invoke the Git executable or fall back to a Git-only worktree. References: [JJ workspaces](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace), [Git experts](https://docs.jj-vcs.dev/latest/git-experts/), and [command table](https://docs.jj-vcs.dev/latest/git-command-table/).

**Two modes:**

- **New work (default):** create a fresh working-copy change from a verified base revision. Keep any task bookmark selection separate from the workspace identity.
- **Isolate an existing ref:** resolve the caller's bookmark, tag, PR head, or revision to an exact commit and create a working-copy change on that commit. JJ does not impose Git's one-branch-one-worktree restriction. Preserve existing PR/source bookmark names and push-tracking intent; do not rename or move them merely to name a workspace.

## Step 0: Detect existing isolation

Resolve the current absolute root with `jj workspace root`. Run all subsequent JJ commands with their working directory set to that absolute root, for example `(cd "$workspace_root" && jj workspace list)`, not merely `jj -R`. Inspect workspace registrations, the current revision/bookmarks, and the harness's workspace/session information. Do not infer isolation solely from the presence of `.git`, a directory name, or a submodule's shared backend.

If the current workspace is already the caller's isolated workspace, **reuse it under its existing registered name and absolute path**, even if its name does not follow the new-creation format below. Do not rename, recreate, or silently alter it to enforce colocation. Check `(cd "$workspace_root" && jj git colocation status)` and report an unmet compatibility requirement through the safe decision path below. Never nest another workspace just because isolation was requested again.

For an existing-ref request, verify whether the current working copy is already based on the exact requested revision. If a change of base is needed, preserve unrelated tracked, ignored, untracked, or conflicted work: only align a verified clean, disposable working-copy change when authorized by the caller's workflow; otherwise stop for a decision rather than resetting, discarding, or guessing the target.

## Step 1: Resolve the base and one stable identity

1. Resolve the requested source from repository configuration and the actual task. For new work, determine the configured trunk/default remote bookmark, not an assumed `main`. A requested refresh uses `jj git fetch --remote "<verified-remote>"`; resolve and record the exact resulting base commit. If fetching fails, an explicitly identified local base may be used only when the caller's workflow permits it; disclose the failure and local choice. Never silently substitute a ref. For an explicit revision, verify it resolves uniquely before creation.
2. For a PR, verify its head repository, remote, bookmark, and commit. Run repository-scoped GitHub CLI commands from the source absolute root with `GIT_DIR=$(jj git root)`, for example `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view <number> --json headRefName,headRefOid,headRepository,headRepositoryOwner)`. Retrieve the exact head through native `jj git fetch` with the verified remote/ref mapping; if it cannot be retrieved, report the exact target and blocker. Preserve the PR's source bookmark and fork push destination so later fixes update the intended PR, not an unrelated branch. Do not use `gh pr checkout` as a workspace bridge.
3. Capture the **local creation date once** as `YYYYMMDD`, and persist it together with the selected identity in the caller's run context outside the proposed destination. Derive a meaningful kebab-case slug from the task (`fix-email-validation`), PR (`pr-214`), or revision (`review-efcb657`). Normalize caller-supplied names: lowercase, replace separators/punctuation with hyphens, collapse/trim hyphens, and remove an existing leading `YYYYMMDD-` before applying the captured date, so it is never double-prefixed. If no meaningful slug remains, request one.
4. Use **one identity** for both the JJ registered workspace name and destination directory basename: `20261008-fix-email-validation`, `20261008-pr-214`, or `20261008-review-efcb657`. Preserve the caller's established absolute local `.tmp/` parent layout; otherwise use `$workspace_root/.tmp/workspaces/`. Ensure `.tmp/` is ignored through the repository's `.gitignore` before creation; inspect the effective ignore rules locally without invoking Git. Do not use global temporary directories.
5. Check both registered workspace names (`jj workspace list`) and destination filesystem entries, including symlinks. If either collides, select `-2`, `-3`, etc.; never overwrite or adopt unknown state. Save the final name, absolute destination, verified base, and ownership before attempting creation. Reuse that exact selection across retries, resumes, and midnight boundaries; do not recapture the date or silently generate another name. If a retry finds state at the selected name/path, first determine whether it is the verified workspace created by this run; otherwise stop and resolve the collision explicitly. No timestamp, PID, or random naming substitutes.

## Step 2: Create and adopt the workspace

Prefer the harness's supported colocated JJ workspace capability. Request the exact selected dated name and destination and verify its resulting registration, base, and colocation. Preserve the harness's ownership and lifecycle contract. A native tool that cannot support the required name or colocation is a compatibility blocker, not permission to create a noncompliant workspace or bypass its lifecycle.

Only when no applicable harness-native creation capability exists, Step 0 found no existing isolation, and the harness supports adopting the result, create directly from the source absolute root:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
(cd "$absolute_destination" && jj workspace root)
(cd "$absolute_destination" && jj workspace list)
```

Verify the registered name equals the destination basename, the resolved root equals the intended absolute destination, the working-copy parent is the verified base, and colocation status confirms colocation; do not rely on configuration defaults. Adopt the workspace with the harness's native session-move capability (for OpenCode, `opencode.session_move` with the absolute destination). Merely changing a shell directory does not move the active harness session. Report the verified path, name, revision, bookmarks, ownership, and session adoption before continuing work there.

If creation, verification, session adoption, sandbox access, or permission fails, the requested isolation has not been established. Preserve any partial state and report it. Do **not** proceed in the original checkout, retry alternative paths automatically, reset anything, or bypass permissions. Ask whether to work in the current checkout or stop to resolve the blocker, using the host's listed blocking question capability. Load a listed-but-unloaded capability through native tool discovery if needed; never use a question call to discover tools. Only if no such capability is listed or an actual call errors, present numbered options in chat and wait for the reply.

## Retirement: only when authorized

Completion alone does not authorize deleting a user's workspace. Respect the caller's cleanup authorization and the harness's lifecycle authority; do not directly remove a harness-owned workspace behind its back.

Before retiring a run-owned disposable workspace:

1. Stop all workers and processes using it. Leave the target directory and move any active harness session to a verified surviving workspace; ensure no remaining session or task still references the target.
2. From that surviving workspace's absolute root, verify the target's exact registered name, canonical absolute path, and run ownership against the saved creation record. Reject unrelated, ambiguous, symlink-substituted, still-referenced, or non-disposable targets.
3. Prove integration into the intended surviving revision/bookmark when the workflow requires it. Preserve best/archive/recovery bookmarks and any needed references separately; workspace retirement is not bookmark deletion.
4. Inspect target `jj status`, `jj diff`, and conflicts from its absolute root, plus filesystem content and ignore rules for ignored/untracked files. Removal snapshots working-copy state, but ignored files and files left untracked are **not protected** by that snapshot. Preserve required content and establish a recovery reference before removal. Copy required logs, receipts, reports, and other evidence outside the target directory, then read them back and verify they are complete. Unknown or valuable content blocks removal until preserved and authorized.
5. With all checks satisfied and applicable harness authorization/lifecycle coordination complete, use JJ-owned removal from the surviving root:

   ```bash
   (cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
   ```

6. Verify **both** deregistration in `jj workspace list` and disappearance of the exact destination directory. A successful exit is insufficient: directory-deletion failures can be warnings. If either check fails, retain all remaining state and recovery references and report the blocker. Never force-delete the directory, fall back to Git removal, or discard evidence to make cleanup appear successful.

Use `jj workspace forget` only for an explicitly requested **unregister-only** operation that preserves the workspace files; it is not the first half of destructive cleanup.
