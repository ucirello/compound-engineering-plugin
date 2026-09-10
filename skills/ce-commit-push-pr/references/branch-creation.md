# Bookmark creation from default bookmark

Local `<base>` may have stale commits (another session/workspace advanced it) or commits the user authored intending to bookmark from later. Local JJ can't distinguish these — ask when unpushed commits are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin -b <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpushed local commits on `<base>`

```bash
jj log -r '<base>@origin..@' --no-graph -T builtin_log_oneline
```

- **Empty output:** set `BASE_REF=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the commit list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpushed commits not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** → `BASE_REF=@`. The new bookmark starts from the current working-copy change, preserving the commits.
  - **Leave on `<base>`** → `BASE_REF=<base>@origin`. The new bookmark starts clean; commits remain on local `<base>`.

  Never default silently — carrying foreign commits into a PR is worse than asking again.

### 3. Create the feature bookmark

```bash
jj new "$BASE_REF"
jj bookmark create <branch-name>
```

`jj new` makes a new empty working-copy change on `$BASE_REF`. Previous working-copy changes remain on the previous change; if that previous change must stay reachable, it already has the local `<base>` bookmark (or keep it reachable before `jj new`). There is no stash: JJ snapshots the working copy.

If `jj new` reports conflicts, surface the conflict output to the user — do not auto-resolve.

## Fetch failure fallback

If `jj git fetch` fails, create the bookmark at the current working-copy change:

```bash
jj bookmark create <branch-name>
```

Note in the user-facing summary that base freshness was not verified. Skip the unpushed-commits check — without a fresh `<base>@origin`, the answer is unreliable.
