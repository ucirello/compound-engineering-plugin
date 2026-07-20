# Separating feature work from the default bookmark

This bookmark-separation flow protects the default bookmark while preserving the current JJ change stack. JJ snapshots working-copy files into `@`.

## Decision flow

### 1. Resolve and fetch the remote

Use project-local instructions first, then `jj git remote list`, to resolve `<remote>`. Resolve `<base>` from project-local instructions, PR metadata, or the GitHub default branch. Do not assume fixed names.

```bash
jj git remote list
jj git fetch --remote <remote>
jj bookmark list --all-remotes <base>
```

If fetch fails because of network or authentication, do not claim the base is fresh. Continue from an existing local or last-seen remote base only after warning the user; in pipeline mode, stop.

### 2. Inspect local-only base history and feature revisions

```bash
jj log -r '<base>@<remote>..<base>'
jj log -r '<base>..@'
jj bookmark list --all-remotes -r '@ | @- | <base> | <base>@<remote>'
jj status
jj diff
```

- **No local-only base changes:** use `<base>@<remote>` as the fresh base.
- **Local `<base>` is ahead:** show `jj log -r '<base>@<remote>..<base>'` and ask whether those changes belong in the PR stack or must remain only on the local default bookmark. Never guess.
- **Local `<base>` is conflicted:** stop and surface `jj status` plus `jj bookmark list --all-remotes <base>`. Do not create or push a feature bookmark until the user resolves it.

### 3. Keep the working-copy change distinct

The safe, expected shape is an unbookmarked working-copy change above the chosen base. Confirm it with `jj log`.

- If `@` is already a descendant of the chosen base and no default bookmark points at `@`, keep the stack in place.
- If the intended feature revisions are above local `<base>` and the user chose to leave local-only base changes behind, rebase only the explicit feature revset onto `<base>@<remote>`:

```bash
jj rebase -s 'roots(<base>..@)' -d '<base>@<remote>'
```

Inspect the proposed roots before running the rebase. If the revset includes a change the user chose to leave behind, stop rather than broadening or guessing.

- If the default bookmark points directly at modified `@`, the edits are part of that bookmarked change. Do not move or rewrite the default bookmark automatically or treat those edits as a separate change. Ask the user to choose whether the whole change belongs in the feature stack. If yes, first create the feature bookmark at `@`, then restore the default bookmark to its chosen existing target only with explicit confirmation. If only part belongs, use `jj split` with explicit filesets or an interactive diff editor before moving either bookmark.

### 4. Delay feature bookmark creation until the head is known

After Step 3 records the intended changes, resolve the final non-empty stack head and create the feature bookmark there:

```bash
jj bookmark create <bookmark> -r <stack-head>
```

If the bookmark already exists, inspect it and use `jj bookmark move <bookmark> --to <stack-head>` only when it is the intended PR bookmark. JJ bookmarks do not advance automatically when a new child change is committed.

### 5. Verify before push

```bash
jj status
jj diff
jj log -r '<base>@<remote>..<bookmark>'
jj bookmark list --all-remotes <base> <bookmark>
```

The range must contain exactly the intended PR stack, the default bookmark must remain at its intended target, and the feature bookmark must identify the final non-empty head. If base freshness was not verified, repeat that warning in the final summary.
