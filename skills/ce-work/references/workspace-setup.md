# Workspace Setup

## Detect isolation before changing anything

Resolve an existing absolute writable workspace root by walking to `.jj` and reading the active harness's workspace/session lifecycle contract. Run all JJ subprocesses with that absolute workspace root as cwd: shell form `(cd "$workspace_root" && jj ...)`. Inspect `jj root`, `jj workspace list`, `jj status`, bookmarks and the current parent/history head. Never substitute `-R` for cwd. Detect harness-owned isolation first; preserve its exact existing name, registered path, ownership, base, and session adoption. Do not rename or recreate a supplied workspace, even if its name is nonconforming. Unsupported harness naming, base, or colocation is a safe compatibility blocker, not an excuse to bypass lifecycle ownership.

If no writable canonical checkout exists, use only an explicitly exposed writable repository surface; otherwise report blocked. Never synthesize repository work in non-repository scratch.

## Prepare the work

Read `work-intake.md` for plan clarification and task derivation. Do not edit plan bodies for progress. Read `.rocketclaw` configuration at this root. Discover the remote default from JJ remote bookmarks or verified repository metadata; repository GitHub calls use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Preserve existing task/PR/source bookmark names. Fetch only with authorized `jj git fetch`; never a direct Git executable, including read-only history or transport.

Record `jj status`, `jj diff --summary`, current parent commit ID, remote-default relation, and complete untracked/ignored inventory before editing. Pre-existing local changes and unpublished revisions are not offered for commit/push. Use a task bookmark when needed, preserving the verified current history if it contains local work. Never describe or move the real default bookmark without explicit user direction. Unknown default/history relations stay unknown and constrain shipping.

Use the supplied isolated checkout when valid. Otherwise create isolation only when the user requests `ce-worktree`, a multi-PR group requires it, or the active native-worker lifecycle assigns creation to the caller. A shared-workspace wave must satisfy `execution-strategy.md`; a subagent API alone is not proof of isolation.

For authorized new caller-owned workspaces, use `ce-worktree` with one persisted `YYYYMMDD-task-slug` identity for registration and absolute local `.tmp/` destination basename. Capture date once across retry/resume/midnight, normalize already-dated callers without double prefix, derive a meaningful task/`pr-N`/`review-ID` slug, inspect both registrations and destination collisions, and append `-2`, `-3`, etc. Never change PR/source bookmarks to match it. Verify and record the exact base commit ID at the source root before creation:

```sh
(cd "$source_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify registration, exact path, actual parent/base and colocation, then adopt/move the active session only through its exposed lifecycle tool. A mismatch blocks writes. Do not silently fall back to non-colocated workspaces or a different base.

## Ownership and commits

Only owned files enter host canonical changes. JJ snapshots are not an index: inspect the full working-copy diff, separate owned paths with an explicit path-limited `jj split`/equivalent native operation, and prove unrelated user deltas remain unchanged. Never describe a mixed working-copy change as if it were entirely yours. If a required file was already dirty, standalone asks once whether to include or exclude it; return-to-caller blocks without editing it. Pass every untouched/declined path as `exclude:` at shipping. Retain pre-existing unpublished history locally unless publication was authorized. Use native task tracking if available, not plan-body checkboxes as execution state.

## Retire only explicitly disposable owned isolation

Completion alone is not deletion permission. Follow harness-owned cleanup only through its lifecycle contract. For caller-owned disposable JJ workspaces, first stop all workers, leave the target, move any active session to a surviving absolute root, verify exact registered name/path/run ownership and explicit disposal authorization, and prove required integration. Copy receipts, logs, packet and recovery evidence outside the target and read them back; preserve recovery/best/archive bookmarks separately from workspace removal.

Inspect changes, conflicts, untracked and ignored content (including local `.tmp` evidence). Ambiguous, unrelated, non-disposable, or unpreserved content blocks removal. From the surviving absolute root use `jj workspace remove <exact-name>`, never `forget` plus directory deletion, Git cleanup, or force deletion. Verify both deregistration and directory disappearance. Warnings or incomplete cleanup retain recovery state and are reported; never force-delete the remainder. Reserve `jj workspace forget` solely for explicit unregister-and-preserve-files intent. Bookmark deletion is a separate authorization and never discards recovery references implicitly.

Removal snapshots working-copy state, but ignored files and files left untracked are not protected by that snapshot. Preserve still-referenced content and evidence explicitly; never treat the snapshot as recovery for disposable-directory contents it does not track.
