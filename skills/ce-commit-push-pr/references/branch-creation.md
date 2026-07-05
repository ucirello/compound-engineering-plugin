# Bookmark creation from default bookmark

Local `<base>` may have stale commits (another session/workspace advanced it) or commits the user authored intending to branch from later. Local JJ metadata can't distinguish these — ask when unpushed commits are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpushed local commits on `<base>`

```bash
jj log --no-graph -r 'remote_bookmarks(<base>, origin)..@' -T 'commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REF=remote_bookmarks(<base>, origin)` and proceed to step 3.
- **Non-empty output:** show the commit list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpushed commits not on `origin/<base>`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** -> `BASE_REF=@`. The new bookmark starts from the current change, preserving the commits.
  - **Leave on `<base>`** -> `BASE_REF=remote_bookmarks(<base>, origin)`. The new bookmark starts clean; commits remain on local `<base>`.

  Never default silently — carrying foreign commits into a PR is worse than asking again.

### 3. Create the feature bookmark

```bash
jj new "$BASE_REF"
jj bookmark create <branch-name> -r @
```

If moving to the fresh remote base would conflict with current working-copy changes, stop and ask whether to carry the current change forward instead. Do not hide the conflict with a stash-like workaround; JJ has already snapshotted the working copy.

If the user chooses to carry the current change forward:

```bash
jj bookmark create <branch-name> -r @
```

## Fetch failure fallback

If `jj git fetch` fails, create the bookmark at the current change:

```bash
jj bookmark create <branch-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the unpushed-commits check — without a fresh `origin/<base>`, the answer is unreliable.
