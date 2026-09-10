# Bookmark creation from the default bookmark

The local default bookmark may have diverged from its remote bookmark because another workspace advanced it, or because local changes were based on unpublished work. JJ cannot tell those apart from ancestry alone — ask when local-only changes are present.

## Decision flow

### 1. Fetch the remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for local-only changes on `<base>`

```bash
jj log -r '<base>@origin..<base>' --no-graph
```

- **Empty output:** set `BASE_REV=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N changes not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** → `BASE_REV=<base>`. The feature change is parented at the local default bookmark, preserving those changes.
  - **Leave on `<base>`** → `BASE_REV=<base>@origin`. The feature change starts from the remote bookmark; those changes remain on the local default.

  Never default silently — carrying unrelated local changes into a PR is worse than asking again.

### 3. Root the work and create the feature bookmark

JJ snapshots the working-copy change; there is no stash step. If the current change should move onto the selected base, rebase it:

```bash
jj rebase -s @ -o "$BASE_REV"
```

If rebase reports conflicts, surface the conflict output — do not auto-resolve.

Create or update the feature bookmark only after the work is described and `jj commit` has left a completed parent (see `references/commit-and-push.md`):

```bash
jj bookmark set <bookmark-name> -r @-
```

If the bookmark already exists at an unrelated revision, stop rather than moving it.

## Fetch failure fallback

Keep the current change's existing parent and create the feature bookmark at the completed change after committing:

```bash
jj bookmark set <bookmark-name> -r @-
```

Note in the user-facing summary that base freshness was not verified. Skip the local-only-changes check — without a fresh `<base>@origin`, the answer is unreliable.
