# Bookmark creation from default bookmark

Local `<base>` may point to stale changes (another session or workspace advanced it) or unpublished changes the user authored intending to carry forward. Ask when unpublished changes are present.

## Decision flow

### 1. Fetch the fresh remote base

```bash
jj git fetch --remote <base-remote> --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpublished local changes on `<base>`

```bash
jj log -r '<base>@<base-remote>..<base>'
```

- **Empty output:** set `BASE_REF=<base>@<base-remote>` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpublished changes not on `<base>@<base-remote>`. Carry them into the new feature work, or leave them on local `<base>`?"

  - **Carry forward** -> `BASE_REF=<base>`. The feature work keeps the local changes as ancestors.
  - **Leave on `<base>`** -> `BASE_REF=<base>@<base-remote>`. The feature work starts from the remote base; local changes remain reachable from local `<base>`.

  Never default silently — carrying unrelated changes into a PR is worse than asking again.

### 3. Rebase the working-copy change and create the bookmark later

```bash
STACK_REVSET="roots($BASE_REF..@)"
STACK_ROOTS=$(jj log -r "$STACK_REVSET" --no-graph -T 'change_id ++ "\n"') || exit 1
[ -n "$STACK_ROOTS" ] || { printf 'No feature-stack roots found after %s.\n' "$BASE_REF" >&2; exit 1; }
jj rebase -s "$STACK_REVSET" -d "$BASE_REF"
```

`roots($BASE_REF..@)` selects every root of the complete current feature stack outside the chosen base ancestry; passing the revset itself to `-s` carries each root and all of its descendants through `@`, including merge-shaped stacks. Do not rebase only `@`: that can detach or omit unpublished ancestors. Fail closed if the revset cannot resolve or is empty. JJ snapshots the working-copy change before rebasing. If the rebase creates conflicts, surface `jj status` and the conflicting paths to the user; do not auto-resolve.

After Step 3 in `SKILL.md` finishes the intended changes, create the feature bookmark at `@-` with `jj bookmark create <bookmark> -r @-`. If the feature bookmark already exists, move it with `jj bookmark set <bookmark> -r @-`.

## Fetch failure fallback

If `jj git fetch` fails, keep the current ancestry and create the feature bookmark after finishing the changes:

```bash
jj bookmark create <bookmark> -r @-
```

Note in the user-facing summary that base freshness was not verified. Skip the unpublished-change check; without a fresh `<base>@<base-remote>`, the answer is unreliable.
