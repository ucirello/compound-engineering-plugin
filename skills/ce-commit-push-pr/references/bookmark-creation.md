# Bookmark creation from the default bookmark

The local default bookmark may include changes absent from its remote counterpart. Preserve that work unless the user decides where it belongs.

## Decision flow

Fetch the authoritative remote state:

```bash
jj git fetch --remote origin
```

If fetch succeeds, inspect changes reachable from the local default bookmark but not its remote bookmark:

```bash
jj log -r '<base>@origin..<base>'
```

When the range is non-empty, show it and ask whether those changes belong in the new feature work. Carrying them uses `<base>` as `<start>`; leaving them uses `<base>@origin`. Never choose silently because including unrelated changes in a PR is the unsafe direction.

Move the working-copy change onto the selected start when necessary, preserving its file changes, and attach the feature bookmark:

```bash
jj rebase -r @ -o <start>
jj bookmark create <bookmark-name> -r @
```

Jujutsu rebases descendants automatically and records the operation, so no stash transition is needed. If the new parent causes conflicts, surface them and stop rather than resolving them automatically.

## Fetch failure fallback

If fetch fails, retain the current change and attach the feature bookmark directly:

```bash
jj bookmark create <bookmark-name> -r @
```

Report that remote freshness was not verified and skip remote-divergence classification because it would be unreliable.
