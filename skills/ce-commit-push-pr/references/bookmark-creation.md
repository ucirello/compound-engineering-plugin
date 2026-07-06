# Bookmark creation from default bookmark

Local `<base>` may have stale changes (another session/workspace advanced it) or unpublished changes the user authored intending to bookmark from later. Ask when unpublished local changes are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpublished local changes on `<base>`

```bash
jj log -r '<base> ~ <base>@origin' --no-graph -T 'change_id.short() ++ " " ++ commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REF=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpublished changes not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** -> `BASE_REF=<base>`. The new bookmark starts from local `<base>`, preserving the changes.
  - **Leave on `<base>`** -> `BASE_REF=<base>@origin`. The new bookmark starts clean; changes remain on local `<base>`.

  Never default silently -- carrying foreign changes into a PR is worse than asking again.

### 3. Create the feature bookmark

```bash
jj new "$BASE_REF"
jj bookmark create <bookmark-name> -r @
```

If `jj new` reports conflicts, surface the conflict output to the user -- do not auto-resolve.

If the original working-copy change on the default bookmark already contains the user's edits, create the feature bookmark at the current change first, then move the default bookmark back to `BASE_REF` before continuing:

```bash
jj bookmark create <bookmark-name> -r @
jj bookmark move <base> --to "$BASE_REF"
```

## Fetch failure fallback

If `jj git fetch --remote origin` fails, create the bookmark from the current local working-copy change:

```bash
jj bookmark create <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the unpublished-change check -- without a fresh `<base>@origin`, the answer is unreliable.
