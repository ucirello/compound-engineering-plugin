# Bookmark creation from default bookmark

Local `<base>` may have stale changes (another session/workspace advanced it) or changes the user authored intending to bookmark from later. Ask when unpublished changes are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpublished local changes on `<base>`

```bash
jj log -r '<base>@origin..<base>' --no-graph --template 'change_id.short() ++ " " ++ commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REV=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpublished changes not on `<base>@origin`. Carry them onto the new topic bookmark, or leave them on local `<base>`?"

  - **Carry forward** -> `BASE_REV=@`. The new bookmark starts from the current JJ change, preserving the local change stack.
  - **Leave on `<base>`** -> `BASE_REV=<base>@origin`. The new change starts clean; changes remain on local `<base>`.

  Never default silently — carrying foreign changes into a PR is worse than asking again.

### 3. Create the topic bookmark

If the current change already contains the work to commit, keep that work on the feature line:

```bash
jj rebase -r @ -o "$BASE_REV"
jj bookmark create <bookmark-name>
```

If the current change is empty and the work has not started yet, create a fresh change from the base:

```bash
jj new "$BASE_REV"
jj bookmark create <bookmark-name>
```

If the bookmark already exists, choose a non-conflicting suffix or use `jj bookmark set <bookmark-name>` only when intentionally moving that bookmark.

## Fetch failure fallback

If `jj git fetch` fails, create the bookmark from the current change:

```bash
jj bookmark create <bookmark-name>
```

Note in the user-facing summary that base freshness was not verified. Skip the unpublished-change check — without a fresh `<base>@origin`, the answer is unreliable.
