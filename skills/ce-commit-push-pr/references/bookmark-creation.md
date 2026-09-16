# Bookmark creation from default bookmark

Local `<base>` may have stale changes (another session/workspace advanced it) or changes the user authored intending to bookmark from later. Local jj can't distinguish these — ask when unpublished local changes are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpublished local changes on `<base>`

```bash
jj log -r '<base>@origin..<base>' --no-graph
```

- **Empty output:** set `<base-revision>` to `<base>@origin` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpublished changes not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** → `<base-revision>` is `@`. The feature bookmark starts from the current working-copy change, preserving those changes.
  - **Leave on `<base>`** → `<base-revision>` is `<base>@origin`. The feature starts from the remote base; those changes remain on local `<base>`.

  Never default silently — carrying foreign changes into a PR is worse than asking again.

### 3. Root the work and create the feature bookmark

The working copy is the change; there is no stash. If the default bookmark is on `@`, move it to `@-` so the default stays at the parent. If the current change should sit on `BASE_REV` and does not already, rebase it:

```bash
jj rebase -s @ -o <base-revision>
```

If rebase fails because of conflicts, stop and ask the user to handle the colliding paths. In `mode:pipeline`, report the blocker without asking. Do not abandon or overwrite the colliding paths.

Then create the feature bookmark on the working-copy change (Step 3's `jj commit` will leave it on the completed change):

```bash
jj bookmark create <bookmark-name>
```

If the bookmark name already exists at an unrelated revision, stop rather than moving it, or choose a non-conflicting suffix as Step 1 allows.

## Fetch failure fallback

If `jj git fetch` fails, keep the current change's existing parent and create the feature bookmark on `@`:

```bash
jj bookmark create <bookmark-name>
```

Note in the user-facing summary that base freshness was not verified. Skip the unpublished-changes check — without a fresh `<base>@origin`, the answer is unreliable.
