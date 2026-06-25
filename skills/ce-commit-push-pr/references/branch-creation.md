# Bookmark creation from default bookmark

Local `<base>` may have stale commits (another session/workspace advanced it) or commits the user authored intending to branch from later. Ask when unpushed commits are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpushed local commits on `<base>`

```bash
jj log -r '<base>@origin..@' --no-graph -T 'commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REF=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the commit list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpushed commits not on `origin/<base>`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** -> `BASE_REF=@`. The new bookmark starts from the current change, preserving the commits.
  - **Leave on `<base>`** -> `BASE_REF=<base>@origin`. The new bookmark starts clean; commits remain on local `<base>`.

Never default silently — carrying foreign commits into a PR is worse than asking again.

### 3. Create the feature bookmark

If the current change already contains the work to ship, keep that change as the feature change. Rebase it only when the user chose a fresh remote base:

```bash
if [ "$BASE_REF" != "@" ]; then
  jj rebase -r @ -d "$BASE_REF"
fi
jj bookmark create <bookmark-name> -r @
```

If there is no current work yet and the user is just creating a place to start, create a new working-copy change on the chosen base:

```bash
jj new "$BASE_REF"
jj bookmark create <bookmark-name> -r @
```

If rebase reports conflicts, surface the conflict output to the user — do not auto-resolve.

## Fetch failure fallback

If `jj git fetch` fails, create the bookmark at the current change:

```bash
jj bookmark create <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the unpushed-commits check — without a fresh `origin/<base>`, the answer is unreliable.
