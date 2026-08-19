# Feature Bookmark Creation from the Default Line

The result is a feature bookmark rooted on a verified base while preserving the working-copy change and any local-only default-line work. A conflict or ambiguous ownership decision is surfaced, never erased.

## Resolve the Base

Fetch the selected remote and base bookmark:

```bash
jj git fetch --remote <remote> --branch <base>
```

If fetch fails, create the feature bookmark at the current change, report that base freshness was not verified, and do not claim the change is rebased.

Compare local default-line work with the fetched remote bookmark:

```bash
jj log -r '<base>@<remote>..<base>'
```

- Empty means use `<base>@<remote>` as the destination.
- Non-empty means show the revisions and ask whether the feature should include that local work or start from the fetched base. Use `<base>` for carry-forward or `<base>@<remote>` for a clean remote base. Never silently carry local-only default work into a PR.

## Root the Change and Create the Bookmark

Before using branch rebase, inspect the exact closure it would rewrite: `(<base-ref>..@)::`. It is safe only when every revision in that closure belongs to the intended feature line. Any revision targeted by an unrelated local bookmark, edited by another workspace, or otherwise outside that line makes `jj rebase -b @` unsafe. Stop, or first isolate the selected work onto a dedicated change/bookmark and recompute the closure; do not let branch rebase carry unrelated descendants.

When the closure is proven safe, rebase the working-copy branch of changes onto the selected destination, preserving only its intended descendants:

```bash
jj rebase -b @ -o <base-ref>
jj bookmark create <feature-bookmark> -r @
```

If the bookmark already exists, choose a non-conflicting name unless identity is ambiguous. Jujutsu records conflicts in the rebased changes; if any appear, stop and report them without abandoning content or pushing. There is no stash/index transition: the working-copy change moves with the rebase.
