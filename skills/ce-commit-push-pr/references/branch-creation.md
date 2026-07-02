# Bookmark creation from default bookmark

Local `<base>` may have unpublished changes another session authored intending to branch/bookmark from later. JJ makes every working-copy state a change, so do not stash; choose the parent revision for the feature bookmark explicitly.

## Decision Flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpublished local changes above `<base>`

```bash
jj log -r '<base>@origin..@' --no-graph -T 'commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REF=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpublished changes not on `<base>@origin`. Carry them onto the new feature bookmark, or start clean from `<base>@origin>`?"

  - **Carry forward** -> `BASE_REF=@`. The feature bookmark starts from the current change, preserving the local changes.
  - **Start clean** -> `BASE_REF=<base>@origin`. Create a new change from the fresh remote base; the local changes remain in their existing JJ change.

Never default silently — carrying foreign changes into a PR is worse than asking again.

### 3. Create the feature bookmark/change

If `BASE_REF` is not `@`, create a fresh working-copy change from it:

```bash
jj new "$BASE_REF"
```

Then create the bookmark on the current change:

```bash
jj bookmark create <bookmark-name> -r @
```

If the bookmark already exists, choose a non-conflicting suffix or ask only if the conflict cannot be resolved safely. Do not move an existing bookmark backwards or sideways unless the user explicitly approves.

## Fetch Failure Fallback

If `jj git fetch --remote origin` fails, create the feature bookmark on the current change:

```bash
jj bookmark create <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the unpublished-change comparison — without a fresh remote bookmark, the answer is unreliable.
