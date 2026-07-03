# Bookmark Creation From Default Bookmark

Local `<base>` may be stale (another session/workspace advanced it) or may carry changes the user authored intending to build from later. JJ can show the graph, but intent is still a product decision — ask when local commits are present.

## Decision Flow

### 1. Fetch Fresh Remote Base

```bash
jj git fetch --remote origin
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check For Local Commits On `<base>`

```bash
jj log -r '<base>@origin..@' --no-graph -T 'commit_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REF=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the commit list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N commits not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** -> `BASE_REF=@`. The new bookmark starts from the current change, preserving the commits.
  - **Leave on `<base>`** -> `BASE_REF=<base>@origin`. The new bookmark starts clean; commits remain on local `<base>`.

  Never default silently — carrying foreign commits into a PR is worse than asking again.

### 3. Create The Feature Bookmark

```bash
jj new "$BASE_REF"
jj bookmark create <bookmark-name> -r @
```

If creating the new change reports conflicts with current working-copy changes, surface the JJ conflict output to the user — do not auto-resolve.

## Fetch Failure Fallback

If `jj git fetch` fails, create the bookmark from the current local `@`:

```bash
jj bookmark create <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the local-vs-remote check — without a fresh `<base>@origin`, the answer is unreliable.
