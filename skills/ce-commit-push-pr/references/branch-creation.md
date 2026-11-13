# Feature bookmark creation from the default

Run commands from the absolute target workspace root. Fetch the confirmed base with `jj git fetch --remote <remote> --branch <base>` and verify `<base>@<remote>` resolves to the intended commit.

Compare local default history with that exact fetched tip using `jj log --no-graph -r '<remote-base>..<local-head>'`. If local-only commits exist, show them and ask whether to carry them or leave them on the default bookmark. Pipeline mode reports this decision as a residual rather than guessing. Preserve their existing bookmark and recovery references either way.

Create a nonconflicting feature bookmark at the selected verified revision with `jj bookmark create <feature> -r <verified-revision>`. Preserve working changes, including excluded paths. If work must be transferred onto a fresh base, inspect conflicts and ignored/untracked collisions first; do not reset, discard, stash, or remove colliding content. Stop for a safe decision if transfer is uncertain.

If fetch fails, preserve the actual error and report freshness unverified. The existing fallback may create the feature bookmark at the verified current local head, without claiming a fresh base or reliable unpushed-commit comparison. Publishing still requires the project gate and a known target. Never use a Git fallback.
