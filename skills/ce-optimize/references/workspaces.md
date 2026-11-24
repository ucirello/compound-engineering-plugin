# Local JJ workspace lifecycle

Use the [JJ workspace CLI reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace) and [command table](https://docs.jj-vcs.dev/latest/git-command-table/). `execution.backend: worktree` is the persisted spec value for local JJ workspace execution.

## Verify isolation before creating it

Discover the absolute source root with `jj workspace root` and use it as the command working directory. Check the harness's isolation record and JJ registrations (`jj workspace list`). Verify any already-isolated workspace's exact name (`jj workspace list -T 'if(current_workspace, name ++ "\n", "")'` from that root), absolute root, colocation (`jj git colocation status` from that root), and suitability for its assigned base and task. Reuse it under its existing name when suitable; don't rename, reset, or change its colocation. The coordinator's workspace is not an experiment workspace: concurrent experiments must not share a mutable working copy.

When the harness owns workspace creation or adoption, use only its supported colocated JJ capability, requesting the identity and verified base below. Verify the actual name, colocation, path and base; an unsupported capability or mismatch is a blocker, not permission to bypass the harness. Move or attach worker sessions to the verified roots using supported OpenCode session tools; merely changing shell cwd does not adopt a workspace. If the worker cannot be confined to its assigned workspace, do not dispatch it.

## Create and record

1. Before launch, verify a single full base commit ID for the assigned task, not a moving bookmark. For experiments, resolve `optimize/<spec-name>` and compare its target to the ledger's expected tip; for confirmation or coordinator setup, verify the exact baseline or candidate specified by that step. For a new workspace capture the local date once (`date +%Y%m%d`). Use `YYYYMMDD-<meaningful-kebab-case-slug>`, e.g. `20261008-optimize-feed-exp-003`; normalize caller-supplied names without double-prefixing. The registered name and directory basename are identical, under the absolute source root's `.tmp/rocketclaw/ce-optimize/workspaces/` parent. Check both registrations and destination paths (including symlinks); add `-2`, `-3`, etc. on collisions. Persist and read back the selected identity, path, base, run ID, role/experiment index and ownership before dispatch; on retry or resume use the recorded name, including across midnight. Don't repurpose an occupied path or change PR/source bookmarks.
2. For inline creation, create the local parent, verify it resolves inside the source workspace and is ignored by JJ, then use:

   ```bash
   (cd "$source_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$absolute_destination")
   (cd "$absolute_destination" && jj git colocation status)
   ```

   From the destination root verify its identity via the workspace registration and confirm that `@` is empty with exactly the verified base as its parent. For a resumed experiment verify the recorded candidate instead; never reset it to the base. Verify that `.tmp/` is ignored here before writing scratch or recovery markers; if the project has not configured it, surface the blocker rather than snapshotting temporary data or changing project ignore policy without authorization.
3. Copy the declared `execution.shared_files`, Phase 1's verified immutable harness inputs, and required local `.env*` resources into the experiment workspace before dispatch. Check source and destination paths (including symlinks and shared directory contents) for containment, avoid copying repository metadata or unrelated credentials, and don't replace tracked input or existing worker state. Require authorized copying and worker access to any secrets; never include those files in a commit, prompt, or remote payload. Record which local inputs were copied so cleanup can distinguish them from unrelated ignored files. Apply the configured port/environment isolation.

## Retire a run-owned workspace

Use this for completed local experiments and wrap-up. Stop workers and waits that use the target, leave its directory, and move any active harness session to a surviving workspace first. For harness-owned workspaces use its supported release/adoption lifecycle; don't delete underneath a harness that still owns the workspace. Proceed only for an authorized, disposable, run-owned workspace, matching its exact recorded registered name and absolute path with the live JJ registration and workspace root.

Before removal, verify the log entry and copy/read back `result.yaml` and other required evidence outside the target. For kept experiments verify the exact integrated result is reachable from the optimization bookmark, and keep the refs needed for best, archive or recovery. Inspect tracked changes and conflicts with JJ, then inspect ignored and still-untracked content separately against the run's inventory. JJ snapshots state during removal, but ignored and remaining untracked files aren't protected by that snapshot. Retain anything still referenced, ambiguous, or not proven disposable and report why.

From a surviving absolute root run `(cd "$surviving_root" && jj workspace remove "$verified_name")`. Recheck both deregistration **and** disappearance of the exact directory; success can include a directory-removal warning. On failure retain the remaining state and report it; no manual directory deletion or Git fallback. `jj workspace forget` is only for unregistering while preserving files. Bookmark cleanup is a separate authorized step after checking ownership and reachability; don't remove the optimization/best, archive, source, or recovery refs.
