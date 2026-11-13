# Native experiment isolation and lifecycle

Use latest JJ; never launch Git, including history or transport. JJ reference:
https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace .
Run every JJ command with its working directory set to the absolute workspace
root, e.g. `(cd "$workspace_root" && jj status)`. Repository-scoped GitHub
commands use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`.
Temporary prompts, measurement scratch and fallback/error files belong under
the target workspace's ignored `.tmp/`; ensure `.tmp/` is ignored.

Existing schema/protocol terms `branch`, `commit`, `SHA`, and `worktree` mean
JJ bookmark, immutable commit ID, and JJ workspace respectively; preserve field
names for compatibility. Fetch exact remote result bookmarks with `jj git fetch`
and inspect files with `jj file show -r <verified-revision> <path>`. Validate the
exact base-to-head range with `jj diff --from <base> --to <head> --summary`,
not per-commit parent statistics. A result-marker revision must have exactly
the candidate parent and add only `result.yaml`. Create it as a separate JJ
change with `jj new <candidate>` and follow `messages.md` before describing.
Publish only its authorized result bookmark with `jj git push --bookmark
<result-bookmark>`; do not publish the optimization bookmark from a worker.
Resume an optimization bookmark with a new empty JJ change above its verified
revision, only after preserving existing work. Fresh starts first create and
verify the archive bookmark at the old revision; never overwrite it or best.

Detect harness-provided isolation first. Reuse verified existing isolation under
its existing name; do not rename, recreate or change its colocation. Use the
harness's supported colocated JJ facility and respect its ownership/session
contract. If incompatible, report the blocker rather than bypassing permissions.
Separate concurrent experiments still require separate writable workspaces.

For new experiment isolation, use `ce-worktree` with a task-derived name.
Capture local YYYYMMDD once in the run ledger; normalize caller names without
double-prefixing. Use `YYYYMMDD-optimize-<spec>-exp-<NNN>` as both registered
name and destination basename under the source root's `.tmp/ce-optimize/`.
Check `jj workspace list` and destination existence; collisions append `-2`,
`-3`, etc. Persist the selected identity across retries, resumes and midnight.
Do not change existing PR/source bookmarks. Verify the exact baseline revision
from the optimization bookmark before creation:

```sh
(cd "$workspace_root" && jj workspace add --colocate --name "$selected_name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Record name, canonical absolute path, base, run ownership and harness session.
Never reset or clean an existing path. Validate ownership and base on resume;
unexpected state is a safe-stop decision. Copy only declared shared resources,
preserving relative paths and rejecting traversal or symlink escapes; do not
overwrite unknown files. Parameterize ports as configured. Count registered
workspaces with `jj workspace list` for the twelve-workspace advisory budget.

## Retirement

Completion alone is not deletion authorization. Respect user authorization and
harness-owned lifecycle authority. Stop and await all workers first; leave the
target and move any active OpenCode session to a surviving workspace with the
supported session move tool. From the surviving absolute root verify exact
registered name/path and run ownership. Inspect target `jj status`, conflicts,
tracked changes, and ignored/untracked files (including local scratch and shared
resources). JJ snapshots do not protect ignored or untracked content. Never
remove unrelated, ambiguous, still-referenced or non-disposable data.

For winners, prove integration of the exact candidate into the optimization
bookmark; for rejected candidates preserve any required recovery revision.
Preserve best/archive/recovery bookmarks. Copy result markers, measurements,
receipts and required evidence outside the target and read them back before
removal. Retain recovery references before any destructive step.

Only after those checks and authorization:

```sh
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
```

Verify both deregistration with `jj workspace list` and directory disappearance;
successful exit alone is insufficient. On warnings, failure or remaining files,
retain state and report the blocker; no force deletion or Git cleanup fallback.
Bookmark deletion is a separate authorized action: never delete best, archive,
recovery or still-needed references. `jj workspace forget` is only for explicitly
unregistering while retaining files, not retirement.
