# Feature bookmark creation from the default bookmark

Run from the absolute workspace root. Consult https://docs.jj-vcs.dev/latest/cli-reference/ .

1. Fetch fresh base with `jj git fetch --remote origin --branch <base>`.
2. Compare local committed work with `<base>@origin` using `jj log -r '<base>@origin..<committed-tip>'`. With no extra commits use the fetched base. Otherwise show the list and ask whether to carry them or leave them on the local default bookmark. Pipeline mode stops with a residual instead of guessing. Never silently carry foreign commits.
3. Preserve the current change ID and operation ID before moving work. Create a non-conflicting feature bookmark at the chosen committed tip using `jj bookmark create <branch-name> -r <chosen-tip>`. If working-copy changes must move onto a fresh base, rebase only that unpublished working-copy change with `jj rebase -r <working-change> -d <chosen-tip>`; preserve unrelated/excluded paths and stop on conflicts or collisions rather than stashing/removing files. Never move the default bookmark or rewrite published history implicitly.
4. On fetch failure, create the feature bookmark from the current committed tip and report that base freshness was not verified. Skip the unreliable unpushed-commit comparison.
