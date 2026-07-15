# Bookmark creation from the default bookmark

This flow applies when `<base>` points at `@`: the working-copy revision contains the feature work, while `@-` and earlier revisions form its base. Local `<base>` may lag `<base>@origin` or have local-only ancestors the user intended to keep on the default line. Ask when local-only ancestors are present.

## Decision flow

### 1. Fetch the remote bookmark

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for local-only revisions on `<base>`

```bash
jj log -r '<base>@origin..@-' --no-graph
```

- **Empty output:** move `<base>` back to `<base>@origin` with `jj bookmark set <base> -r '<base>@origin' --allow-backwards`, then rebase the working-copy revision with `jj rebase -r @ -o '<base>@origin'` and proceed to step 3.
- **Non-empty output:** show the commit list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N revisions not on `<base>@origin`. Include them in the new feature line, or base the feature directly on `<base>@origin`?"

  - **Include** → move `<base>` back to `@-` with `jj bookmark set <base> -r @- --allow-backwards`. The feature line remains on top of the local revisions.
  - **Use remote base** → first preserve the local default line with `jj bookmark set <base> -r @- --allow-backwards`, then rebase only the working-copy revision with `jj rebase -r @ -o '<base>@origin'`.

  Never default silently — carrying unrelated revisions into a PR is worse than asking again. If rebasing only `@` would also move content the user identified as belonging to the local default line, stop and ask them to separate the changes; do not guess a split.

### 3. Set the feature bookmark

```bash
jj bookmark set <feature-bookmark> -r @
```

JJ snapshots working-copy changes into `@`; there is no index or stash transition. If the rebase creates conflicts, surface `jj status` and the conflicted paths to the user and do not auto-resolve.

## Fetch failure fallback

If `jj git fetch` fails, set the feature bookmark at the current working-copy revision:

```bash
jj bookmark set <feature-bookmark> -r @
```

Note in the user-facing summary that base freshness was not verified. Skip the local-only revision check because `<base>@origin` may be stale.
