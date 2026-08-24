# Feature bookmark creation from the default bookmark

The local `<base>` bookmark may differ from `<base>@<remote>`. Ask when the local bookmark has unpublished changes because Jujutsu cannot infer whether those changes belong in the new work.

## Decision flow

### 1. Fetch the remote base

```bash
jj git fetch --remote <remote> --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpublished local changes on `<base>`

```bash
jj log -r '<base>@<remote>..<base>' --no-graph
```

- **Empty output:** use `<base>@<remote>` as the base.
- **Non-empty output:** show the commit list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpublished changes not on `<base>@<remote>`. Include them in the new feature work, or start from the remote bookmark?"

  - **Include** -> use `<base>` as the base.
  - **Start remote-clean** -> use `<base>@<remote>` as the base; local changes remain reachable from `<base>`.

  Never default silently because including unrelated unpublished changes in a PR is worse than asking again.

### 3. Root the working-copy change

```bash
jj rebase -r @ -o <base-ref>
```

Jujutsu rebases the working-copy change and automatically rebases descendants. If the rebase produces conflicts, surface them and stop; do not auto-resolve. Create or move `<feature-bookmark>` only after the intended commit exists, as `references/commit-and-push.md` specifies.

## Fetch failure fallback

If fetch fails, leave `@` on its current parent and continue only when that parent is the intended base:

```bash
jj log -r '@-' --no-graph
```

Otherwise stop and ask for a resolvable base. Note in the user-facing summary when base freshness was not verified. Skip the unpublished-change comparison because a stale remote bookmark cannot answer it reliably.
