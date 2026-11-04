# Feature bookmark creation from the default

Run all JJ commands with cwd the absolute target workspace root and gh with the `GIT_DIR` environment obtained there, as in `context.md`.

1. Fetch the confirmed remote/base with `jj git fetch --remote <remote> --branch <base>`. Verify and capture its exact commit ID. On failure stop: do not silently substitute a stale local base.
2. Inspect `jj log --no-graph -r '<verified-remote-base>..<verified-local-tip>'`. If local default commits are absent remotely, show them and ask whether to carry them or leave them; pipeline mode reports this unresolved decision. Never discard or silently include them.
3. Preserve the original tip with a recovery bookmark. Create a unique feature bookmark at the chosen exact base/tip using `jj bookmark create <feature> -r <verified-tip>`. Preserve source/default bookmarks. If work must be moved to a new parent, inspect the exact changes and conflicts first and use JJ's native change operations only for authorized owned work. Do not reset, stash, overwrite ignored content, or rebase unrelated changes. Conflicts or ambiguous ownership stop safely.

Creating the feature bookmark itself needs no repeat approval under the full shipping workflow. Existing verified isolation is reused without recreating it.
