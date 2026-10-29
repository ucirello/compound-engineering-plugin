# Native execution and workspace lifecycle

Use latest JJ directly; never invoke the Git executable for history, transport, review, or cleanup. See https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace and https://docs.jj-vcs.dev/latest/git-command-table/. Set every shell call's cwd to the target workspace's absolute root (or use `(cd "$workspace_root" && jj ...)`); `jj -R` is not a cwd substitute. For repository-scoped GitHub operations use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Keep temporary files, prompts, errors and fallback scratch under the local `.tmp/`, ignored by JJ.

## Create or adopt

Detect existing isolation first. Reuse its verified name and preserve harness ownership/lifecycle; do not rename, recreate, reset, or modify existing isolation to enforce naming or colocation. A harness-native facility must support colocated JJ and, for new `ce-worktree` workspaces, the required name; otherwise report the compatibility blocker through the workflow's safe decision path.

Resolve and record the exact optimization bookmark's commit ID as the verified base; never silently substitute another revision. Capture the local creation date once. New `ce-worktree` names, including caller-selected experiment names, use `YYYYMMDD-<meaningful-kebab-case-slug>` (for example `20261029-optimize-parser-exp-001`). Normalize caller names without double-prefixing; derive slugs from the task, PR, or revision. Preserve the selected identity across retries, resumes and midnight. Use the same identity as JJ workspace name and destination basename under the source workspace's absolute `.tmp/workspaces/` directory. Check registrations and destinations; resolve collisions with `-2`, `-3`, etc., never overwrite. Existing PR/source bookmarks remain unchanged.

From the source's absolute root:

```sh
(cd "$workspace_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify the exact registration, destination, base and colocation before dispatch. Persist them in the ledger. On resume verify ownership and state rather than resetting an existing directory. Respect the configured concurrency budget by counting registered workspaces with `jj workspace list`. Copy configured shared files and applicable local environment files into each owned workspace while preserving relative paths; resolve symlinks and reject escapes from either source or destination. Never overwrite unexplained existing content. Preserve port parameterization and shared-resource probe mitigations.

## Retire

Only retire workspaces whose deletion is already authorized. Stop and await all workers; leave the target directory and move any active OpenCode session to a surviving workspace through the supported session-move interface first. Respect harness lifecycle authority. Verify the exact registered name, absolute destination and run ownership. Inspect `jj status`, conflicts, tracked diffs, and ignored/untracked files (including copied databases, environment files, measurements and markers); snapshots do not protect ignored or untracked content. Preserve any unrelated, ambiguously owned, still-referenced or non-disposable content and stop if uncertain.

Prove required integration using the recorded candidate and optimization head; preserve best/archive/recovery bookmarks. Copy required result markers, comparison evidence and recovery references outside the target and read them back before removal. Completion alone does not authorize deletion.

From a surviving workspace's absolute root run `jj workspace remove <verified-workspace-name>`. Verify both deregistration with `jj workspace list` and directory disappearance; warnings can leave files behind despite successful exit. If incomplete, retain remaining state and report the blocker: never force-delete or fall back to Git cleanup. Delete disposable experiment bookmarks separately only after evidence and integration are proven, never best/archive/recovery references. Use `jj workspace forget` only to unregister while intentionally preserving files, not as a deletion shortcut.

## Exact history and transport mechanics

All remaining workflow terms such as branch, merge, cherry-pick and revert describe intent implemented with JJ, not executable Git operations. Optimization/result branches are JJ bookmarks. Fetch exact result bookmarks with `jj git fetch --remote <verified-remote> --bookmark <result-bookmark>`; read marker bytes with `jj file show -r <verified-result-tip> result.yaml`. Resolve full commit IDs and parents with JJ before validating worker claims. Inspect the exact base/head tree difference with `jj diff --from <base_sha> --to <head_sha>` and its `--summary` path list, not a parent-relative substitute. Verify result-tip parent identity and that the tip adds only the marker. Preserve `base_sha`/`head_sha` schema keys as stable wire fields carrying full JJ commit IDs.

Preserve candidates in separate owned JJ changes and use `jj new <verified-base>` or separate workspaces for paired measurements; never stash, reset or discard unrelated content. Winners advance the optimization bookmark only after the verified integration/measurement gate. Runner-up application uses `jj duplicate <candidate> --onto <verified-new-baseline>`; rejecting it leaves the optimization bookmark unchanged and retains evidence before authorized retirement. Compose all new descriptions using `references/change-messages.md`. Publishing uses `jj git push --remote <verified-remote> --bookmark <authorized-bookmark>`; cleanup of remote references is separate and only after copied evidence is read back. No implicit push authority is granted.

## Native dispatch

Configuration remains the source of desired models, tiers, security posture, concurrency and failure semantics. Resolve permitted choices with `opencode.models` and execute with native subagents/shell, not another harness's dispatcher. Legacy `codex` backend configuration expresses route intent, not authorization to invoke another harness; disclose an unavailable required route rather than claiming it ran. Preserve the existing three-consecutive-failure fallback, receipt/checkpoint recovery and bounded capacity backpressure.

This skill explicitly requests worker and independent judge delegation where prescribed. Under a user-or-loaded-skill delegation rule that satisfies permission without another approval. A stronger prohibition or actual denial still applies. Model-selection permission is separate: omit model overrides when forbidden and use inherited-model reviewers only when suitable. Same-model contexts satisfy separation, not cross-model independence; required unavailable coverage stays incomplete. Classify actual errors as nesting/capacity, permission, model rejection or missing tool; never evade a denial/depth limit with shell or another harness. Judges cannot score inline when independence is required.
