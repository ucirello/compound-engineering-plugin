# Bookmark creation from the default bookmark

Local `<base>` may point to stale changes or user-authored changes intended for a feature bookmark. Ask when unpushed local changes are present.

## Decision flow

### 1. Fetch the fresh remote bookmark

```bash
jj git fetch --remote origin --branch <base>
```

If the fetch fails (network, auth, or no remote), use the fallback at the bottom.

### 2. Check for unpushed local changes on `<base>`

```bash
jj log -r '<base>@origin..<base>'
```

- **Empty output:** set `BASE_REF=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpushed changes not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** -> `BASE_REF=<base>`. The new bookmark preserves the local changes in its ancestry.
  - **Leave on `<base>`** -> `BASE_REF=<base>@origin`. Rebase the current working-copy change onto the fresh remote bookmark; the other changes remain reachable from local `<base>`.

  Never default silently — carrying foreign changes into a PR is worse than asking again.

### 3. Create the feature bookmark

```bash
jj rebase -s @ -d "$BASE_REF"
jj bookmark create <bookmark-name> -r @
```

JJ preserves working-copy changes through the rebase. If the rebase records conflicts, surface `jj status` and `jj diff` to the user and do not auto-resolve.

## Fetch failure fallback

If `jj git fetch` fails, create the bookmark at the current change:

```bash
jj bookmark create <bookmark-name> -r @
```

Note in the user-facing summary that remote bookmark freshness was not verified. Skip the unpushed-changes check -- without a fresh `<base>@origin`, the answer is unreliable.
