# Feature bookmark creation from the default bookmark

Local `<base>` may have stale changes (another session/workspace advanced it) or unpublished changes the user authored intending to build on. JJ local and remote bookmarks can diverge, so ask before carrying local-only base changes into a feature line.

## Decision Flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpublished local changes on `<base>`

```bash
jj log -r "<base>@origin..<base>" --no-graph -T 'change_id.short() ++ " " ++ commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REV=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpublished changes not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** -> `BASE_REV=@`. The new feature bookmark starts from the current change, preserving the local changes.
  - **Leave on `<base>`** -> `BASE_REV=<base>@origin`. The new feature bookmark starts clean; local changes remain on local `<base>`.

Never default silently; carrying unrelated local changes into a PR is worse than asking again.

### 3. Create the feature bookmark

If the current workspace change already contains the work, attach the bookmark to it:

```bash
jj bookmark set <bookmark-name> -r @
```

If the work should start from the selected base first, create a new workspace change from that base, then set the bookmark:

```bash
jj new "$BASE_REV"
jj bookmark set <bookmark-name> -r @
```

If current changes conflict with moving to the selected base, keep the current work as its own JJ change, create the new change from `BASE_REV`, then rebase or squash the saved work onto the feature line. Surface JJ conflicts to the user; do not auto-resolve them.

## Fetch Failure Fallback

If `jj git fetch` fails, create the bookmark at the current JJ change:

```bash
jj bookmark set <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the unpublished-base check; without a fresh `<base>@origin`, the answer is unreliable.
