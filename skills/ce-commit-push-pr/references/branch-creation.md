# Feature bookmark from the default bookmark

This flow decides which remote-backed base should parent the current work. JJ working-copy changes do not need stashing or checkout protection: rebasing a change preserves its diff, and the operation log provides recovery.

## Resolve the fresh base

Fetch the selected named remote and bookmark:

```bash
jj git fetch --remote <remote> --branch <base>
```

Inspect local-only changes based on the remote bookmark:

```bash
jj log -r '<base>@<remote>..<base>'
```

- Empty output means `<base>@<remote>` is the publish base.
- Non-empty output means the local default bookmark contains unpublished changes. Show them and ask whether the feature should include them or start from `<base>@<remote>`. Never carry them silently.
- If included, use `<base>` as the parent. Otherwise use `<base>@<remote>` and rebase only the intended working-copy change or unpublished feature changes onto it; do not move the default bookmark.

If fetch fails, ask before using the local `<base>` because freshness is unknown. In pipeline mode, stop with that residual.

## Place the feature bookmark

After the intended filesets have been committed, identify the top published change explicitly and create the feature bookmark there:

```bash
jj bookmark create <bookmark> -r <publish-change>
```

If the bookmark already exists and is the intended feature bookmark, advance it without moving it backward or sideways:

```bash
jj bookmark move <bookmark> --to <publish-change>
```

A non-fast-forward move is a history rewrite decision. Stop unless the user explicitly authorized it; only then use `--allow-backwards`. A name collision with an unrelated local or remote bookmark requires a new unambiguous name or user input.
