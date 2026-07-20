# Bookmark setup from the default line

JJ bookmarks are named pointers, not checked-out branches. Preserve the snapshotted working-copy change while deciding which base belongs under it; no stash or branch checkout is needed.

## Decision flow

### 1. Snapshot and fetch the remote base

Run `jj status` first so `@` records the current working-copy content, then fetch only through JJ's Git interoperability layer:

```bash
jj status
jj git fetch --remote <base-remote>
```

If fetch fails because of network, authentication, or remote configuration, use the fallback below.

### 2. Inspect local-only default-line revisions

```bash
jj log -r '<base>@<base-remote>..<base>'
```

- **No revisions:** use `<base>@<base-remote>` as the destination.
- **Revisions present:** show them and ask whether they belong in the feature stack or should remain only on the local default line. Never carry them silently.
- **Carry them:** use `<base>` as the destination.
- **Leave them:** use `<base>@<base-remote>` as the destination.

If pipeline mode suppresses the question, leave the local-only revisions out of the feature stack.

### 3. Place the working-copy change on the selected base

Inspect `jj log -r 'ancestors(@, 20)'` before moving anything. If `@` is the sole feature revision, rebase it directly:

```bash
jj rebase -s @ -d <selected-base>
```

If the feature already contains multiple revisions, identify its earliest revision after the selected base and rebase the whole feature branch with `jj rebase -b <feature-root> -d <selected-base>`. Do not rebase local-only default-line revisions that the user chose to leave behind.

Run `jj status`, `jj diff -r @`, and `jj log` afterward. JJ may materialize conflicts in the rebased revisions; surface them and stop for deliberate resolution rather than changing content automatically.

Do not create the feature bookmark yet. Step 3 in `SKILL.md` sets it on the final described tip after splitting and description work is complete.

## Fetch failure fallback

Keep the existing parentage of `@`, inspect it with `jj log`, and continue without rebasing. Report that remote-base freshness was not verified. Do not perform the local-only comparison because the remembered remote bookmark may be stale.
