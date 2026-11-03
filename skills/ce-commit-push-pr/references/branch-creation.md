# Feature bookmark creation

Run all JJ commands with the absolute target workspace root as cwd. Fetch the verified base with `jj git fetch --remote <remote> --branch <base>`. Inspect `jj log -r '<base>@<remote>..<verified-local-head>'`. Missing metadata or failed fetch blocks freshness-dependent decisions; never guess another ref.

If local default commits are absent remotely, ask whether to carry them or leave them on the default; pipeline returns that decision without guessing. Preserve a recovery bookmark before moving any tip. Carry uses the verified local head; leave uses the verified remote base. Preserve tracked, ignored, untracked, conflicted, and excluded work. If changing parents endangers any of it, stop without resetting or deleting it.

Create `jj bookmark create <feature-name> -r <verified-feature-head>` after collision checks. Explicit workflow intent authorizes this feature bookmark, not publishing directly to the default. Re-verify targets before publication. Reuse existing verified harness isolation without changing its name or lifecycle; no new workspace is needed.
