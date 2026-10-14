# Feature bookmark creation from the default

From the target absolute workspace root, fetch the verified base remote and bookmark with `jj git fetch --remote <remote> --bookmark <base>`. Resolve its exact remote revision and compare local default history with `jj log -r '<base>@<remote>..<local-base>'`, distinguishing an empty working copy from authored commits.

Show unpushed local default commits and ask whether to carry them or leave them on the default; pipeline mode stops with that decision as a residual. Carry uses verified local tip; leave uses verified remote tip. Never silently import foreign commits. Preserve original revisions through recovery bookmarks before an authorized rebase.

Derive a meaningful collision-free feature bookmark and create it with `(cd "$workspace_root" && jj bookmark create <feature> -r <verified-revision>)`. Creation does not switch the working copy. If ancestry must change, use a bounded JJ rebase of only intended unpublished work after resolving the base decision. Preserve unrelated tracked, untracked and ignored files; conflicts, ambiguous state or collisions stop rather than authorizing overwrite, discard or stash.

If fetch fails, retain local state. When the workflow authorizes it, use the verified local revision but report unverified freshness and skip the unreliable unpushed comparison. See https://docs.jj-vcs.dev/latest/git-experts/ .
