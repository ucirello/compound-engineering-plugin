# Feature bookmark creation from the default bookmark

Run commands from the absolute workspace root. Fetch the exact base using `jj git fetch --remote <base-remote> --branch <base>` and verify `<base>@<base-remote>` with `jj log`. Inspect `jj log -r '<verified-remote-base>..<local-base-tip>'` for local-only commits.

If local-only default-bookmark commits exist, show them and ask whether to carry them into the feature or leave them on the default bookmark; pipeline mode reports this decision as a blocker. Never silently include foreign commits. Carry uses the verified local tip; leave uses the verified remote base. Preserve a recovery bookmark before any rewrite and keep the default bookmark unchanged.

Create a collision-free feature bookmark with `jj bookmark create <feature-name> -r <verified-selected-tip>`. Preserve owned uncommitted changes by a path-scoped JJ operation only after verifying their prerequisites against that base; excluded/unrelated files stay untouched. If moving work would collide with tracked, untracked, or ignored paths, stop and ask (pipeline: report); never stash, discard, or remove colliding paths.

On fetch failure, a local-tip feature bookmark may preserve the work without claiming freshness. Report freshness unverified; do not infer unpushed commits from stale remote state. Publishing still requires an exact verified base and head and the project publishing gate.
