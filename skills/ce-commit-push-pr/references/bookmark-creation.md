# Bookmark creation from the default bookmark

The local default bookmark may differ from its remote bookmark because another workspace advanced it or local changes were intentionally based on unpublished work. Resolve that ancestry before choosing the feature change's parent.

## Decision flow

### 1. Fetch the remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails because of network, authentication, or a missing remote, use the fallback below.

### 2. Check local-only changes on the default bookmark

```bash
jj log -r '<base>@origin..<base>'
```

- Empty output: use `<base>@origin` as `<base-revision>`.
- Non-empty output: show the changes and ask whether the feature should include them or start from `<base>@origin`. Including them uses `<base>` as `<base-revision>`; leaving them on the local default uses `<base>@origin`. Never guess because including unrelated local changes changes the PR.

### 3. Root the work and create its bookmark

JJ's working-copy change can be rebased without stashing. If the current change should move to the selected base, run:

```bash
jj rebase -s @ -o <base-revision>
```

After the work is described and `jj commit` has created a fresh empty change, create or update the feature bookmark at the completed parent:

```bash
jj bookmark set <bookmark-name> -r @-
```

If the bookmark already exists at an unrelated revision, stop rather than moving it. JJ automatically rebases descendants and records operations, but a bookmark collision still represents ambiguous user intent.

## Fetch failure fallback

Keep the current change's existing parent and create the feature bookmark at the completed change after committing. Report that remote-base freshness was not verified. Do not run the local-only comparison without a fresh remote bookmark.
