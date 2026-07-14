# Bookmark creation from the default bookmark

Read this reference whenever the full workflow starts from the default bookmark or must choose whether local default-bookmark changes belong in the PR. Its result is an explicit base revision, head bookmark name, and correctly based working-copy change.

Local `<base>` may contain changes absent from `<base>@<remote>` because another workspace advanced it or because the user intentionally created local work there. JJ exposes the topology, but it cannot infer ownership or intent. Ask when local-only changes are present.

## Decision flow

### 1. Fetch the remote base

Resolve the intended fetch remote from `jj git remote list`, then run:

```bash
jj git fetch --remote <base-remote>
```

Confirm `<base>@<base-remote>` exists with `jj bookmark list --all-remotes`. If fetch fails because of authentication, connectivity, or a missing remote, use the fallback below.

### 2. Check local-only default-bookmark changes

Inspect the local default bookmark relative to its remote counterpart:

```bash
jj log -r '<base>@<base-remote>..<base>' --no-graph
```

- **Empty output:** set `<base-revision>` to `<base>@<base-remote>`.
- **Non-empty output:** show the changes and ask whether they belong in the new PR.
- **Carry forward:** set `<base-revision>` to `<base>` so those local changes remain ancestors of the feature work.
- **Leave on the default bookmark:** set `<base-revision>` to `<base>@<base-remote>` and move only the current working-copy change onto it in Step 3.

Never choose silently. Carrying unrelated local changes into a PR is more harmful than asking again.

If the local bookmark is conflicted, stop and surface both targets from `jj bookmark list --all-remotes`. Do not move or push a conflicted bookmark.

### 3. Base the working-copy change safely

Bookmarks do not become active and do not move with new JJ changes. Record a non-conflicting `<head-bookmark>` derived from the work's purpose, but create or move it only after Step 3 of `SKILL.md` identifies the completed stack head.

Inspect `jj status`, `jj diff`, and the parents of `@`. If `@` is already based on `<base-revision>`, preserve it. Otherwise move only the working-copy change, leaving unwanted local default-bookmark ancestors behind:

```bash
jj rebase -s @ -o <base-revision>
```

Jujutsu records rebase conflicts as first-class state and completes the operation. If `jj status` reports conflicts, resolve mechanical conflicts with `jj resolve` or direct edits. A semantic conflict that requires intent is a blocker to surface, not a reason to discard the working-copy change.

Do not create a temporary stash, switch a checkout, or create a raw Git branch. The working-copy change already preserves uncommitted content while JJ changes its parent.

After the final content change is finished, `SKILL.md` creates or advances the explicit head bookmark at the actual stack head and publishes only that bookmark through `jj git`.

## Fetch failure fallback

When fresh remote state cannot be obtained, preserve the current JJ topology and use the current parent of `@` as `<base-revision>`. Do not move the default bookmark or claim it is current. Continue only if the intended head bookmark and PR range remain unambiguous, and report that base freshness was not verified. If the missing remote state makes the PR range ambiguous, stop and ask rather than guessing.
