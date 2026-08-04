# Bookmark creation from the default bookmark

Local `<base>` may differ from `<base>@<remote>` because another workspace advanced it or because the user has local changes they intend to carry forward. Ask when local-only changes are present.

## Decision flow

### 1. Fetch the remote base

```bash
jj git fetch --remote <remote> --branch <base>
```

If fetch fails, use the fallback below.

### 2. Check for local-only changes

```bash
jj log -r '<base>@<remote>..<base>'
```

- **Empty output:** use `<base>@<remote>` as the base.
- **Non-empty output:** show the changes and ask whether to carry local `<base>` forward or start from `<base>@<remote>`. Never choose silently.

### 3. Create the feature change and bookmark

```bash
jj new <base-revision>
jj bookmark create <bookmark-name> -r @
```

Jujutsu preserves the previous working-copy change when creating the new change; do not introduce stash behavior.

## Fetch failure fallback

```bash
jj new <base>
jj bookmark create <bookmark-name> -r @
```

Report that base freshness was not verified and skip the local-only comparison.
