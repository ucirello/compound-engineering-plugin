# Bookmark creation from the default bookmark

The local default bookmark may differ from its remote bookmark because another workspace advanced it or because the user has local changes based on it. Resolve that state before naming and publishing the work.

## Decision flow

### 1. Fetch the remote base

```bash
jj git fetch --remote <remote>
```

If fetch fails because the network, authentication, or remote is unavailable, use the fallback below.

### 2. Check the local default bookmark

Inspect both bookmarks and the changes between them:

```bash
jj bookmark list <base> --all-remotes
jj log -r '<base>@<remote>..<base>'
```

- **No local-only changes:** use `<base>@<remote>` as the destination for any required rebase.
- **Local-only changes:** show them and ask whether they belong in the feature work or must remain reachable only from the local default bookmark.

If they belong in the feature work, preserve the current ancestry. If they must remain on the local default bookmark, rebase only the intended feature changes onto `<base>@<remote>`; do not rebase the local-only default-bookmark changes with them. Stop and surface conflicts instead of resolving them without direction.

Never move or delete the local default bookmark merely to make the remote and local names agree. A feature bookmark is the publication boundary.

### 3. Create the feature bookmark

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Finish and describe the intended change according to project instructions and the syntax observed in `jj log`, without supplying a fixed message, prefix, type, scope, suffix, template, or example. Then create the bookmark at that change:

```bash
jj bookmark create <bookmark> -r <change>
```

If the name already exists, inspect its target. Reuse it only when it identifies this work; otherwise choose a non-conflicting name or ask when the intended identity is ambiguous.

## Fetch failure fallback

Create the feature bookmark at the intended local change without rebasing it:

```bash
jj bookmark create <bookmark> -r <change>
```

Report that remote-base freshness was not verified. Do not claim the change is current with the default bookmark, and do not push until the remote can be checked.
