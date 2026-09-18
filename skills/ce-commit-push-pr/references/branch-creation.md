# Bookmark creation from the default bookmark

Local `<base>` may have stale commits (another session or workspace advanced it) or commits the user authored intending to bookmark from later. Local jj cannot distinguish these — ask when unpublished commits are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch --remote origin --branch <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpublished local commits on `<base>`

```bash
jj log -r '<base>@origin..@' --no-graph
```

- **Empty output:** set `BASE_REF=<base>@origin` and proceed to step 3.
- **Non-empty output:** show the commit list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpublished commits not on `<base>@origin`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** → `BASE_REF=@`. The new bookmark names the current line, preserving those commits.
  - **Leave on `<base>`** → `BASE_REF=<base>@origin`. The new bookmark starts clean; those commits remain on local `<base>`.

  Never default silently — carrying foreign commits into a PR is worse than asking again.

### 3. Create the feature bookmark

The new feature bookmark's first parent is `BASE_REF`, and the user's intended work is on that bookmark. Unpublished local-default commits are included only when the user said to carry them.

When the working copy already is the feature tip (carry, or already on the fresh base with the work in `@`):

```bash
jj bookmark create <bookmark-name>
```

When the working copy must move onto a clean remote base (leave, or local `<base>` is behind `<base>@origin` and the work is not yet on that tip):

```bash
jj new <base>@origin
jj bookmark create <bookmark-name>
```

`jj new` leaves the previous working-copy change as a sibling. If that sibling still holds file changes that belong on the new bookmark, restore those files onto the new working copy without bringing the unpublished local `<base>` commits. If `jj new` or that restore would overwrite colliding uncommitted or ignored paths, stop and ask the user to handle the colliding paths. In `mode:pipeline`, report the blocker without asking. Do not abandon, restore-over, or otherwise remove the colliding paths.

## Fetch failure fallback

If `jj git fetch` fails, create the bookmark on the current working copy:

```bash
jj bookmark create <bookmark-name>
```

Note in the user-facing summary that base freshness was not verified. Skip the unpublished-commits check — without a fresh `<base>@origin`, the answer is unreliable.
