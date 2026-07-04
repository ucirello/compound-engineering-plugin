# Bookmark creation from default bookmark

Local `<base>` may have stale commits (another session/workspace advanced it) or commits the user authored intending to bookmark from later. Ask when unpushed commits are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpushed local commits on `<base>`

```bash
jj log -r '<base>@origin..@' --no-graph --template 'commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REF=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the commit list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpushed commits not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** -> `BASE_REF=@`. The new bookmark starts from the current change, preserving the commits.
  - **Leave on `<base>`** -> `BASE_REF=<base>@origin`. The new change starts clean; commits remain on local `<base>`.

  Never default silently — carrying foreign commits into a PR is worse than asking again.

### 3. Create the feature bookmark

If the current change already contains the work to commit, keep that work on the feature line:

```bash
jj rebase -r @ -o "$BASE_REF"
jj bookmark create <bookmark-name>
```

If the current change is empty and the work has not started yet, create a fresh change from the base:

```bash
jj new "$BASE_REF"
jj bookmark create <bookmark-name>
```

If the bookmark already exists, choose a non-conflicting suffix or use `jj bookmark set <bookmark-name>` only when intentionally moving that bookmark.

## Fetch failure fallback

If `jj git fetch` fails, create the bookmark from the current change:

```bash
jj bookmark create <bookmark-name>
```

Note in the user-facing summary that base freshness was not verified. Skip the unpushed-commits check — without a fresh `<base>@origin`, the answer is unreliable.
