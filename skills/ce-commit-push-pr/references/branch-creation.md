# Bookmark creation from the default bookmark

Local `<base>` may have stale changes (another session/workspace advanced it) or local-only changes the user authored intending to build from later. JJ cannot infer intent from topology alone — ask when local-only changes are present.

## Decision Flow

### 1. Fetch Fresh Remote Base

```bash
jj git fetch --remote origin
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check For Local-Only Changes On `<base>`

```bash
jj log -r "<base>@origin..@" --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

- **Empty output:** set `BASE_REV=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N changes not on `<base>@origin`. Carry them onto the new feature bookmark, or start from the remote base?"

  - **Carry forward** -> `BASE_REV=@`. The new change starts from the current workspace, preserving the local changes.
  - **Start from remote** -> `BASE_REV=<base>@origin`. The new change starts clean; local changes remain on their existing change line.

  Never default silently — carrying unrelated local changes into a PR is worse than asking again.

### 3. Create The Feature Bookmark

```bash
jj new "$BASE_REV"
jj bookmark set <bookmark-name> -r @
```

If JJ reports conflicts after creating the new change, surface the conflict output and stop for user direction — do not auto-resolve.

## Fetch Failure Fallback

If `jj git fetch` fails, create the bookmark from the current change:

```bash
jj bookmark set <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the local-only check — without fresh `<base>@origin`, the answer is unreliable.
