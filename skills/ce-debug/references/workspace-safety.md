# Isolated debugging and workspace lifecycle

Use native JJ commands, not workspace bridge scripts. References: https://docs.jj-vcs.dev/latest/git-experts/ , https://docs.jj-vcs.dev/latest/git-command-table/ , https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace . Run JJ from the relevant absolute workspace root, never rely on `-R` to set cwd.

Detect isolation first. Reuse verified existing isolation and its name, even if undated or noncolocated; do not rename, recreate, or change it merely to enforce new-workspace rules. Respect harness workspace ownership/session/lifecycle authority. Use its supported colocated JJ capability where available and verify it. Incompatible required naming or colocation is a blocker, not permission to bypass the harness or create a Git-only worktree.

For new isolation, verify the source/base revision and destination ownership first. Capture the local creation date once. When invoking `ce-worktree`, derive `YYYYMMDD-<meaningful-kebab-case-slug>` from task, PR (`YYYYMMDD-pr-214`), or revision (`YYYYMMDD-review-efcb657`); normalize supplied names without double-prefixing. Use the same identity as workspace name and absolute destination basename under the source root's local `.tmp/` parent. Check registrations and paths for collisions; use `-2`, `-3`, etc., never overwrite, and preserve the selected date/name across retries, resumes and midnight. Keep existing PR/source bookmarks unchanged.

```bash
(cd "$source_workspace_root" && jj workspace add --colocate --name "$selected_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Verify name, absolute root, base and colocation; adopt the workspace through the harness-supported session mechanism when it becomes primary. Never silently bypass lifecycle authority.

For an authorized clean-state experiment, preserve the original working copy and use a separate workspace at the verified pre-WIP revision; do not stash, reset or discard the user's work. Compare the reproduction with WIP and without it, accounting explicitly for untracked/ignored inputs and environment differences. If these cannot be reproduced safely, report the limitation rather than claim WIP is ruled out. A confirmed WIP cause belongs to the user's uncommitted work, not an automatically included fix commit.

Cleanup is not authorized merely by completion. Before retiring an explicitly disposable run-owned workspace: stop workers, leave the target and move any active harness session to a surviving workspace; verify exact registration name, absolute path and run ownership; prove integration where required; retain recovery references; copy required evidence outside the target and read it back. Inspect tracked changes, conflicts, ignored and untracked files. Removal snapshots working-copy state but does not protect ignored or left-untracked content. Preserve unrelated, ambiguous, still-referenced or non-disposable content and respect harness cleanup authority.

From the surviving absolute root, use `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")`. Verify both deregistration and directory disappearance: warnings can accompany a successful exit. On failure preserve remaining state and report the blocker; never force-delete or use Git removal. Keep bookmark deletion separate and preserve best/archive/recovery and still-needed references. `jj workspace forget` is only for explicitly unregistering while preserving files, never followed by directory deletion.
