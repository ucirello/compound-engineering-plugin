# Bookmark Creation From Default Bookmark

Local `<base>` may have stale changes or user-authored local work intended to become feature work. JJ makes the current work an explicit change, so avoid stash-style flows; ask only when local-vs-remote base intent is ambiguous.

## Decision Flow

### 1. Fetch Fresh Remote Base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check Local Work Relative To `<base>@origin`

```bash
jj log -r '<base>@origin..@'
```

- **Empty output:** set `BASE_REV=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N changes not on `<base>@origin`. Carry them onto the new feature bookmark, or start from the remote base?"

  - **Carry forward** -> `BASE_REV=@`. The new bookmark points at the current change, preserving local work.
  - **Start from remote base** -> `BASE_REV=<base>@origin`. Create a new change from the remote base; existing local changes remain in history and are not abandoned.

Never default silently — carrying foreign changes into a PR is worse than asking again.

### 3. Create The Feature Bookmark

If `BASE_REV` is `@`, create the bookmark on the current change:

```bash
jj bookmark create <bookmark-name> -r @
```

If `BASE_REV` is a remote base, create a new change there and bookmark it:

```bash
jj new "$BASE_REV"
jj bookmark create <bookmark-name> -r @
```

If JJ reports conflicts while moving to the new base, surface the conflict output to the user — do not auto-resolve.

## Fetch Failure Fallback

If `jj git fetch` fails, bookmark the current change:

```bash
jj bookmark create <bookmark-name> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the local-vs-remote check — without a fresh `<base>@origin`, the answer is unreliable.
