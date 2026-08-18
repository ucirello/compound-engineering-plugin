# Feature bookmark creation from the default bookmark

Local `<base>` may contain unpublished changes or lag `<base>@<remote>`. Jujutsu exposes both states, but it cannot infer whether unpublished changes belong in the new PR. Ask when they exist.

## Decision flow

### 1. Fetch the authoritative base

```bash
jj git fetch --remote <remote> --branch <base>
```

If fetch fails, use the fallback below.

### 2. Check unpublished local base changes

```bash
jj log -r '<base>@<remote>..<base>'
```

- Empty output: use `<base>@<remote>` as `<base-revision>`.
- Non-empty output: show the changes and ask whether the feature should include them or leave them on the local default bookmark. Carrying them uses `<base>`; leaving them uses `<base>@<remote>`. Never choose silently.

### 3. Root the work and create the feature bookmark

Preserve the working-copy change while rebasing it onto `<base-revision>`, then create the feature bookmark at `@`. If the default bookmark followed the rewritten change, move it back to `<base-revision>` with `--allow-backwards` only after confirming that this restores the default rather than discarding unrelated work.

```bash
jj rebase -s @ -o <base-revision>
jj bookmark create <bookmark-name> -r @
jj bookmark move <base> --to <base-revision> --allow-backwards
```

Jujutsu needs no stash: the working-copy change is a revision and follows the rebase. Surface conflicts and stop; do not resolve them automatically.

## Fetch failure fallback

Create the feature bookmark at `@` without rebasing, and report that base freshness was not verified. Skip the unpublished-base comparison because its answer is unreliable without a fresh remote bookmark.

```bash
jj bookmark create <bookmark-name> -r @
```
