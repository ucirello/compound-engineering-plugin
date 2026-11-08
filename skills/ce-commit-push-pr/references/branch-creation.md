# Feature bookmark creation from the default bookmark

Run every JJ command from the absolute target workspace root. Fetch with `jj git fetch --remote <base-remote> --branch <base>` and verify the exact fetched `<base>@<base-remote>`. Inspect `jj log -r '<remote-base>..<local-history-head>'` for local-only commits. If any exist, ask whether to carry them onto the feature bookmark or leave them on the default; pipeline mode reports the decision as a blocker rather than guessing.

Preserve recovery bookmarks before moving owned changes. Create a unique feature bookmark with `jj bookmark create <feature-name> -r <verified-selected-head>`. Full workflow intent already authorizes feature-bookmark creation; do not ask merely whether to branch. Preserve unrelated work and existing bookmarks. If owned changes need rebasing onto the fresh base, inspect tracked changes, conflicts and ignored/untracked collisions first; never discard, stash or remove colliding work. Stop for genuine unsafe-state decisions.

If fetch fails, retain state and report that freshness is unverified. Do not silently substitute a stale base; local-head continuation requires explicit authorization.
