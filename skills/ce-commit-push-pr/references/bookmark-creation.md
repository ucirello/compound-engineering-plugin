# Bookmark Creation From Default Bookmark

Local `<base>` may have stale changes or changes the user authored intending to bookmark from later. JJ makes the current work explicit as `@`, so preserve it unless the user chooses a fresh base.

## Decision Flow

### 1. Fetch Fresh Remote Base

```bash
jj git fetch --remote origin
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check For Local Work On `<base>`

Inspect the current change and recent descendants:

```bash
jj status
jj log --no-graph -r '<base>..@'
```

- **No local work to preserve:** create a new change from `<base>@origin` when available, otherwise `<base>`.
- **Local work exists:** show the change list and ask whether to carry it forward or start clean from the remote base.

Use the "Asking the user" convention in `SKILL.md`:

> "Local `<base>` has work not confirmed on the remote base. Carry it onto the new feature bookmark, or start the feature bookmark from the fresh remote base?"

- **Carry forward** -> keep `@` and set the bookmark there.
- **Start clean** -> `jj new <base>@origin` when available, otherwise `jj new <base>`, then set the bookmark.

Never default silently — carrying unrelated work into a PR is worse than asking again.

### 3. Create The Feature Bookmark

```bash
jj bookmark set <bookmark-name> -r @
```

If unrelated working-copy changes block a clean start, create a sibling change first (`jj new @-`) or ask the user whether to carry the current change forward. Do not emulate stash-style hidden state.

## Fetch Failure Fallback

If `jj git fetch --remote origin` fails, set the bookmark on the current change:

```bash
jj bookmark set <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip remote freshness checks because without a fresh remote bookmark, the answer is unreliable.
