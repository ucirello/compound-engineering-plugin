# Bookmark Creation from the Default Bookmark

The local default bookmark may differ from its remote bookmark because another workspace advanced it or because the user has local changes based on it. Resolve that state before naming and publishing the work.

## Decision Flow

### 1. Fetch the Remote Base

```bash
jj git fetch --remote <remote>
```

If fetch fails because the network, authentication, or remote is unavailable, use the fallback below.

### 2. Check the Local Default Bookmark

Run these separately:

```bash
jj bookmark list <base> --all-remotes
jj log -r '<base>@<remote>..<base>'
```

- **No local-only changes:** Use `<base>@<remote>` as the destination for any required rebase.
- **Local-only changes:** Show them and ask whether they belong in the feature work or must remain reachable only from the local default bookmark.

If they belong in the feature work, preserve the current ancestry. If they must remain on the local default bookmark, rebase only the intended feature changes onto `<base>@<remote>`; do not rebase the local-only default-bookmark changes with them. Use the narrowest correct `jj rebase` selector after inspecting `jj help rebase`. Stop and surface conflicts instead of resolving them without direction.

Never move or delete the local default bookmark merely to make the remote and local names agree. A feature bookmark is the publication boundary.

### 3. Create the Feature Bookmark

Before composing, editing, checking, or recommending the change description: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Finish and describe the intended change according to project instructions and runtime history, applying only compatible Go guidance and no fixed syntax. Use:

```bash
jj describe -r <change> -m "<message composed from the standards above>"
jj bookmark create <bookmark> -r <change>
```

If the bookmark name already exists, inspect its target. Reuse it only when it identifies this work; otherwise choose a non-conflicting name or ask when the intended identity is ambiguous.

## Fetch Failure Fallback

Create the feature bookmark at the intended local change without rebasing it:

```bash
jj bookmark create <bookmark> -r <change>
```

Report that remote-base freshness was not verified. Do not claim the change is current with the default bookmark, and do not push until the remote can be checked.
