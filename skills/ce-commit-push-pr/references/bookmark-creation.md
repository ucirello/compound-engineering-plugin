# Bookmark creation from default bookmark

Local `<base>` may be stale (another session/workspace advanced it) or may contain local changes the user authored intending to publish later. Ask when unpublished local changes are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpublished local changes on `<base>`

```bash
jj log -r '<base>@origin..@' --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REV=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpublished changes not on `<base>@origin`. Carry them onto the new feature bookmark, or start from `<base>@origin`?"

  - **Carry forward** -> `BASE_REV=@`. The new bookmark points at the current change chain, preserving the changes.
  - **Start from remote** -> `BASE_REV=<base>@origin`. The new bookmark starts clean; local changes remain where they are.

  Never default silently — carrying foreign changes into a PR is worse than asking again.

### 3. Create the feature bookmark

```bash
jj new "$BASE_REV"
jj bookmark create <bookmark-name> -r @ 2>/dev/null || jj bookmark set <bookmark-name> -r @
```

If `jj new` reports conflicts, surface the output to the user — do not auto-resolve.

## Fetch failure fallback

If `jj git fetch` fails, create the bookmark from the current change:

```bash
jj bookmark create <bookmark-name> -r @ 2>/dev/null || jj bookmark set <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the unpublished-change check — without a fresh remote bookmark, the answer is unreliable.
