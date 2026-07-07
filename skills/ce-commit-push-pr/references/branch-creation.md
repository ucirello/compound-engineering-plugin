# Bookmark creation from default bookmark

Local `<base>` may have stale changes (another session/workspace advanced it) or changes the user authored intending to bookmark from later. JJ cannot distinguish these — ask when unpublished changes are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpublished local changes on `<base>`

```bash
jj log -r 'remote_bookmarks(exact:<base>@origin)..@' --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REF=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpublished changes not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** -> `BASE_REF=@`. The new bookmark starts from the current change, preserving the changes.
  - **Leave on `<base>`** -> `BASE_REF=<base>@origin`. The new bookmark starts clean; changes remain on local `<base>`.

  Never default silently — carrying foreign changes into a PR is worse than asking again.

### 3. Create the feature bookmark

```bash
jj new "$BASE_REF"
jj bookmark create <bookmark-name>
```

If creating the new change fails because working-copy changes would conflict with the fresh base, split or squash the local work explicitly before retrying:

```bash
jj split <paths-for-local-work>
jj new "$BASE_REF"
jj bookmark create <bookmark-name>
jj squash --from <local-work-change> --into @
```

If `jj squash` reports conflicts, surface the conflict output and involved change IDs to the user — do not auto-resolve.

## Fetch failure fallback

If `jj git fetch` fails, bookmark the current change:

```bash
jj bookmark create <bookmark-name>
```

Note in the user-facing summary that base freshness was not verified. Skip the unpublished-changes check — without a fresh `<base>@origin`, the answer is unreliable.
