# Feature bookmark creation from the default bookmark

The local default bookmark may be stale or may point to local-only changes the user intends to preserve separately. JJ changes and workspaces make those states visible, but intent still requires a question when local-only changes are present.

## Decision flow

### 1. Fetch the remote default bookmark

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Inspect local-only changes

```bash
jj log -r '<base>@origin..<base>'
```

- **Empty output:** use `<base>@origin` as the fresh base and proceed to step 3.
- **Non-empty output:** show the changes and ask (per the "Asking the user" convention in `SKILL.md`):

  > "The local default bookmark has <count> local-only changes. Should the feature include them, or should they remain separate from the feature?"

  - **Include them** — retain them in the feature ancestry. The feature bookmark will point to the final intended feature change.
  - **Keep them separate** — identify the feature stack in `jj log` by change ID, then rebase that stack onto `<base>@origin` with `jj rebase -s <feature-root-change> -d <base>@origin`. Do not move or abandon the local-only changes.

  Never default silently. Including unrelated changes in a PR is worse than asking again.

### 3. Verify the feature stack

Run `jj status`, `jj diff`, and `jj log -r '<base>@origin..<head-change>'`. If a rebase produced conflicts, surface `jj status` and the affected change IDs; do not auto-resolve. Create the feature bookmark only after the intended stack and head are unambiguous, using `jj bookmark create <bookmark> -r <head-change>`.

## Fetch failure fallback

If `jj git fetch` fails, retain the current change ancestry and create the feature bookmark at the intended head. Note in the user-facing summary that base freshness was not verified. Skip the local-only comparison because `<base>@origin` is not known to be fresh.
