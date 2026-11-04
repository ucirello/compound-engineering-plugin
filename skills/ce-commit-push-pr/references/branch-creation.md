# Feature bookmark creation from the default base

Use the absolute cwd rules in `context.md`.

1. Fetch `jj git fetch --remote <remote> --branch <base>` and verify `<base>@<remote>` resolves to the intended repository/commit.
2. Inspect `jj log --no-graph -r '<base>@<remote>..<local-history-head>'`. Exclude an empty working-copy tip when identifying unpushed substantive commits. If present, show them and ask whether to carry them or leave them on the local default bookmark; pipeline mode reports the decision as a blocker. Never silently carry foreign commits.
3. Carry-forward uses the verified local head; otherwise use the fetched base. Preserve owned working changes in a separate JJ change before rebasing only that change onto the verified base. Preserve unrelated tracked, ignored and untracked work. If conflicts/collisions or ownership make this unsafe, stop for user handling; do not stash, remove or discard paths.
4. Create `jj bookmark create <feature-name> -r <verified-feature-head>` with a non-conflicting name and verify it. Never move the default bookmark to publish feature work.

If fetch fails, create the feature bookmark at the unambiguous existing local head only, report unverified base freshness, and skip unreliable fresh-base comparisons. Do not substitute another ref.
