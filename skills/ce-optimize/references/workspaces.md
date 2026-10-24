# Native JJ experiment isolation

Use https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace and the `ce-worktree` workflow directly; there is no workspace bridge script. All JJ commands run with their working directory set to the target workspace's absolute root, not with `-R`. Repository-scoped GitHub calls use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Never invoke the Git executable.

Detect existing isolation first. Reuse its verified name and lifecycle without renaming or changing colocation. Respect harness ownership; use its supported colocated JJ capability and adopt the resulting workspace with the native session-move capability before executing there. Unsupported required naming or colocation is a compatibility blocker, not permission to bypass the harness.

For each new experiment, verify the exact optimization bookmark's commit ID with `jj log --no-graph -r 'optimize/<spec-name>' -T 'commit_id'`. Record that base in the ledger. Capture the local date once, normalize the task/spec/experiment slug (including caller-supplied names without double-prefixing), and persist `YYYYMMDD-<meaningful-kebab-case-slug>` before creation. Use the same identity for the workspace name and destination basename under the source root's `.tmp/ce-optimize/<spec-name>/`. Check both `jj workspace list` registrations and filesystem destinations; resolve collisions with `-2`, `-3`, etc. Persist the chosen identity across retries, resumes and midnight boundaries. Never overwrite an existing destination or substitute a random name. Existing PR/source bookmarks remain unchanged.

From the source workspace's absolute root:

```sh
(cd "$workspace_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Read back the registration, destination, base and colocation before dispatch. Give workers the absolute root. Copy only declared shared files after checking containment and symlinks; never reset or clean an existing workspace. Apply configured per-experiment port parameters and retain the measurement probe's shared-resource diagnostics. Count all registered workspaces with `jj workspace list` for the existing budget warning.

## Retirement

Completion alone does not authorize deletion. Stop workers and unregister their wakes; prove integration of a winner's exact candidate (not its result-only tip), or retain a recovery bookmark for a rejected candidate when required. Preserve best/archive/recovery bookmarks and any still-needed references. Copy required result markers, measurements and receipts outside the target and read them back before removal. Inspect tracked changes, conflicts and ignored/untracked files explicitly: the removal snapshot does not protect ignored files or files left untracked. Unknown ownership, unrelated content, live references, or non-disposable files block cleanup.

Verify the exact registered workspace name, absolute destination and recorded run ownership. Leave the target and move any active harness session to a surviving workspace first. Respect existing cleanup authorization and harness-owned lifecycle authority. Then from the surviving workspace's absolute root use `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")`. Verify both deregistration and directory disappearance, since deletion failures may only warn. On failure retain remaining state and report the blocker; never force-delete or fall back to Git cleanup. Bookmark deletion is separate. Use `jj workspace forget` only for intentional unregister-only operations that preserve files.
