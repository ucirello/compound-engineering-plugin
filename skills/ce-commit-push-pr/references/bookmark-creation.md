# Bookmark creation from default bookmark

Local `<base>` may have stale JJ changes (another session/workspace advanced it) or JJ changes the user authored intending to bookmark from later. Ask when unpushed JJ changes are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpushed local JJ changes on `<base>`

```bash
jj log --no-graph -r '<base>..@'
```

- **Empty output:** set `BASE_REF=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the JJ change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpushed JJ changes not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** -> `BASE_REF=@`. The new bookmark starts from the current JJ change, preserving the changes.
  - **Leave on `<base>`** -> `BASE_REF=<base>@origin`. The new bookmark starts clean; JJ changes remain on local `<base>`.

  Never default silently — carrying foreign JJ changes into a PR is worse than asking again.

### 3. Create the feature bookmark

```bash
jj new "$BASE_REF"
jj bookmark create <bookmark-name> -r @
```

If `jj new "$BASE_REF"` reports conflicting working-copy state, surface the output to the user and stop — do not auto-resolve.

## Fetch failure fallback

If `jj git fetch` fails, create the bookmark from the current JJ change:

```bash
jj bookmark create <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the unpushed-JJ-changes check — without a fresh `<base>@origin`, the answer is unreliable.
