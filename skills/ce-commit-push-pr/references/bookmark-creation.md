# Bookmark creation from default bookmark

Local `<base>` may have stale changes (another session/workspace advanced it) or changes the user authored intending to bookmark from later. Ask when unpublished local changes are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpublished local changes on `<base>`

```bash
jj log -r '<base>@origin..@' --no-graph -T 'commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REF=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpublished changes not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** -> `BASE_REF=@`. The new bookmark starts from the current working-copy commit, preserving the changes.
  - **Leave on `<base>`** -> `BASE_REF=<base>@origin`. The new bookmark starts clean; changes remain on local `<base>`.

  Never default silently — carrying foreign changes into a PR is worse than asking again.

### 3. Create the feature bookmark

```bash
jj new "$BASE_REF"
jj bookmark create <bookmark-name> -r @
```

If `jj new "$BASE_REF"` fails because the current working-copy changes conflict with the fresh base, surface the conflict and stop for user resolution; do not auto-resolve.

## Fetch Failure Fallback

If `jj git fetch` fails, bookmark the current working-copy commit:

```bash
jj bookmark create <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the unpublished-changes check — without a fresh `<base>@origin`, the answer is unreliable.
