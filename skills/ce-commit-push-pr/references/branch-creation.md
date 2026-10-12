# Feature bookmark creation from the default bookmark

Run JJ from the target workspace's absolute root. Fetch the verified base remote with `jj git fetch --remote <remote> --branch <base>`. Inspect `jj log -r '<base>@<remote>..<local-tip>'` for local commits not on that fresh base.

If there are local commits, show them and ask whether to carry them into the feature or leave them on the existing base. Pipeline mode reports the decision as a residual; never silently carry foreign commits. Carry uses the verified local tip; leave uses the verified remote base. Preserve local commits with their existing bookmark/recovery reference.

Create a nonconflicting feature bookmark at the selected revision with `jj bookmark create <feature> -r <verified-tip>`. Before changing parents, inspect tracked, ignored/untracked work and conflicts; do not discard, stash, or overwrite colliding work. A clean workspace can use `jj new <verified-base>`; pending work needing a different parent requires a verified safe rebase of only the owned working change, preserving excluded/user paths, or a blocker. A bookmark creation alone does not transfer changes to another base.

If fetch fails, use the verified current local tip only when that fallback is permitted by the caller; disclose unverified base freshness and skip the unreliable remote comparison. Uncertain target or colliding work takes the safe stop/decision path, without reset or Git checkout fallback.

JJ guidance: https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/cli-reference/ .
