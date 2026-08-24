# Bookmark creation from trunk

Jujutsu has no current branch and needs no stash before changing topology. A bookmark names the change that GitHub will expose as a branch; it does not own the working copy.

Fetch the selected base remote with `jj git fetch --remote <remote>`. If fetch succeeds, use the resolved `trunk()` target or the explicitly resolved base remote bookmark as the parent. Before moving work, inspect `jj log -r '<base>@<remote>..<local-base>'` when a local base bookmark exists. If it contains unpublished changes, show them and ask whether the feature should include them or start at the remote base. Never silently include unrelated local changes.

Create or rebase the feature change on the chosen parent with Jujutsu operations. Preserve the current change ID when the work already exists; use `jj rebase -r @ -o <parent>` rather than copying its diff. If the work has not started, use `jj new <parent>`. Create the publication bookmark only after the target change is known:

```bash
jj bookmark create <bookmark> -r <target>
```

If the bookmark already exists, verify its target and ownership. Move it with `jj bookmark move <bookmark> --to <target>` only when advancing the intended publication line; a backward or sideways move requires explicit confirmation and `--allow-backwards`.

If fetch fails, retain the existing parent and report that remote-base freshness was not verified. Do not invent a remote target or rewrite the change onto an unverified base.
