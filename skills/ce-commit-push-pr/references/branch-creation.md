# Bookmark creation from trunk

Local `<base>` may have stale commits (another session/workspace advanced it) or commits the user authored intending to bookmark from later. Local Jujutsu cannot distinguish these — ask when unpushed commits are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpushed local commits on `<base>`

```bash
jj log --no-graph -T builtin_log_oneline -r '<base>@origin..@'
```

- **Empty output:** set `BASE_REF=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the commit list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpushed commits not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** → `BASE_REF=@`. The new bookmark starts from the working copy, preserving the commits.
  - **Leave on `<base>`** → `BASE_REF=<base>@origin`. The new bookmark starts clean; commits remain on local `<base>`.

  Never default silently — carrying foreign commits into a PR is worse than asking again.

### 3. Create the feature bookmark

```bash
jj new "$BASE_REF"
jj bookmark create <bookmark-name> -r @
```

If updating the working copy would overwrite uncommitted or ignored files, stop and ask the user to handle the colliding paths. In `mode:pipeline`, report the blocker without asking. Do not move the working copy aside with `jj new @-` or discard colliding paths with `jj restore`.

## Fetch failure fallback

If `jj git fetch` fails, bookmark the current working-copy change:

```bash
jj bookmark create <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the unpushed-commits check — without a fresh `<base>@origin`, the answer is unreliable.
