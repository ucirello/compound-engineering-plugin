# Feature bookmark creation from the default base

Resolve the absolute workspace root and run every JJ call there. Local default ancestry may contain stale or deliberately unpushed work; do not decide its ownership from the bookmark name.

## 1. Fetch the remote base

```bash
jj git fetch --remote <base-remote> --branch <base>
```

If fetch fails, retain the current local ancestry, create a non-conflicting feature bookmark at the verified work tip, and report that base freshness was not verified. Do not infer unpushed ownership from a stale remote bookmark.

## 2. Resolve local-only ancestry

Inspect `jj log -r '<base>@<base-remote>..<local-tip>'`. Distinguish the current working change from completed local ancestors, including the `@-` head when `@` is empty. If completed local commits are absent from the fetched base, show them and ask whether to carry them into the feature or leave them on the local default. Pipeline stops with this decision unresolved. Never silently carry potentially foreign commits.

- **Carry:** preserve the current ancestry and create the feature bookmark at the intended publishable tip.
- **Leave:** retain a recovery bookmark at the original tip, and move only the explicitly selected unpublished feature changes onto the fetched base using public JJ rebase/split operations. The default bookmark and its commits remain intact.
- **No local-only ancestors:** the fresh remote base is safe for the selected feature changes.

## 3. Preserve work while creating the feature

Use `jj bookmark create <branch-name> -r <intended-tip>`. A bookmark does not check out or move files. If the selected working change needs a new parent, rebase only that verified change, never unrelated descendants or excluded files. Inspect the resulting diff and conflicts before continuing. If the operation cannot preserve excluded or colliding ignored paths exactly, stop and ask the user; pipeline reports the blocker. Never stash, delete, or overwrite those paths.

Do not use this default-base flow for an upstack layer; its base is the authoritative immediate parent resolved in `references/stack-submit.md`.
