# Feature bookmark creation from default

Run JJ from the absolute target workspace root. Fetch the verified base with `jj git fetch --remote <base-remote> --bookmark <base>` and verify its exact remote bookmark revision. Never silently substitute a ref.

Inspect `jj log -r '<base>@<base-remote>..<local-base-tip>'` for local-only commits. If present, show them and ask whether to carry them onto the feature or leave them on the local base. Pipeline mode stops with that decision as a residual. Preserve the base bookmark and recovery references; never silently carry foreign commits.

With no local-only commits use the verified fetched base; with authorized carry-forward use the verified local tip. Derive a meaningful collision-free feature name and `jj bookmark create <feature> -r <verified-selected-tip>`. Creating a bookmark does not move working files. Before changing ancestry, inspect tracked changes, conflicts, ignored and untracked files. Rebase only owned working changes onto the selected base when safe; never overwrite, stash, discard, or absorb unrelated work. Stop on collisions or uncertain ownership; pipeline mode reports without asking.

If fetch fails, report freshness as unverified. Preserve work and use the verified current local revision only under the workflow's authorized fallback; skip the unreliable local-only comparison. Publishing still requires a known target and authority. Never invent a base.
