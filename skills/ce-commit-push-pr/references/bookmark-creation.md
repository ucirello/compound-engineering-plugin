# Feature bookmark creation from the default bookmark

JJ has no current bookmark. Local `<base>` may have unpublished revisions, may have diverged from `<base>@<base-remote>`, or may have been advanced by another workspace. Fetch before deciding what belongs in the feature line.

## Decision flow

### 1. Fetch the fresh remote base

```bash
jj git fetch --remote <base-remote> --branch <base>
jj status
```

If fetch fails because of network or authentication, use the fallback below. If the local bookmark becomes conflicted, stop and surface `jj bookmark list <base>`; do not pick a side or push through the conflict.

### 2. Check for unpublished local revisions

Use a revset, not a range inferred from working-copy files:

```bash
jj log -r '(::<base> ~ ::<base>@<base-remote>) & ~root()'
```

- **Empty output** - use `<base>@<base-remote>` as the fresh parent.
- **Non-empty output** - show the revisions and ask whether they belong in the feature line or should remain only under local `<base>`.
- **Carry forward** - preserve the current ancestry and use the current feature stack head as the intended line.
- **Leave on local `<base>`** - rebase only the working-copy change onto the fresh remote base with `jj rebase -r @ -d <base>@<base-remote>`. This leaves the unpublished revisions reachable from local `<base>`.

Never default silently. Before rebasing `@`, save its full change ID with `jj log -r 'exactly(@, 1)' --no-graph -T 'change_id ++ "\n"'` and verify that the source revset resolves to exactly one revision.

### 3. Handle working-copy conflicts

JJ snapshots working-copy changes into `@`; rebasing `@` carries those changes to the new parent. Run `jj status` afterward. If conflicts materialize, surface them and stop for resolution; do not auto-resolve or undo the operation globally. The saved change ID lets the user inspect the intended working-copy change through its evolution.

### 4. Create the feature bookmark only at the finished head

Do not create a bookmark on an empty working-copy child. After Step 3 of `SKILL.md` finishes the intended changes, resolve the final non-empty revision, then create or advance the exact feature bookmark:

```bash
jj bookmark set <head-bookmark> -r <final-intended-revision>
```

If the name already exists on an unrelated revision, choose a non-conflicting name or ask. Never move an existing bookmark backwards or sideways without explicit user confirmation.

## Fetch failure fallback

Keep the current ancestry and working-copy change in place. Create no default-bookmark update. Continue by finishing the intended changes and setting a feature bookmark at their final revision. Report that base freshness was not verified and skip the unpublished-revision classification because `<base>@<base-remote>` is stale or unavailable.
