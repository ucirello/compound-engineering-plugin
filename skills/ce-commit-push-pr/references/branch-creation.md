# Bookmark creation from default bookmark

Local `<base>` may have stale commits (another session/workspace advanced it) or commits the user authored intending to branch from later. Ask when unpublished commits are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpublished local commits on `<base>`

```bash
jj log -r '<base>@origin..<base>' --no-graph -T 'commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REV=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the commit list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpublished commits not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** → `BASE_REV=<base>`. The new bookmark starts from local `<base>`, preserving the commits.
  - **Leave on `<base>`** → `BASE_REV=<base>@origin`. The new bookmark starts clean; commits remain on local `<base>`.

  Never default silently — carrying foreign commits into a PR is worse than asking again.

### 3. Create the feature bookmark

```bash
jj new "$BASE_REV"
jj bookmark create <bookmark-name> -r @
```

If existing working-copy changes need to move onto the new base, create the bookmark first, then use JJ's normal change movement tools (`jj squash`, `jj restore`, or `jj edit`) according to the caller's intent. Do not auto-resolve conflicts.

## Fetch failure fallback

If `jj git fetch` fails, create the bookmark at the current JJ change:

```bash
jj bookmark create <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the unpublished-commits check — without a fresh `<base>@origin`, the answer is unreliable.
