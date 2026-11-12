# Feature bookmark creation from the default bookmark

Run JJ from the absolute target workspace root. Fetch `jj git fetch --remote <base-remote> --bookmark <base>` and verify the exact `<base>@<base-remote>` commit. Inspect `jj log -r '<base>@<base-remote>..<verified-task-head>'` with full descriptions to identify local-only commits. JJ cannot distinguish another session's stale default-bookmark commits from work intended for this task.

- No local-only commits: the fetched exact base is the bottom parent.
- Local-only commits: show them and ask whether to carry them forward or leave them on the local default bookmark. Carry uses the verified task head; leave uses the fetched base. Pipeline stops with this decision rather than guessing.

Capture the original task tip and preserve a recovery bookmark before changing ancestry. Inspect tracked changes, conflicts, ignored and untracked data; a snapshot does not protect ignored/untracked files. Create the feature bookmark with `jj bookmark create <feature> -r <verified-tip>`. When owned changes must be transplanted to the selected base, use explicitly scoped `jj rebase -r <owned-revision> -d <verified-base>` only after proving ownership and preserving unrelated work. Stop on conflicts or path collisions; never stash, overwrite, or remove colliding data. Published-history rewriting requires explicit approval.

If fetch fails, preserve the local task head and report that base freshness is unverified. Do not infer an unpushed-commit decision from stale remote state. Do not publish with an unresolved base: ask interactively or return a pipeline blocker.
