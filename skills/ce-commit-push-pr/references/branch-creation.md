# Branch creation from default branch

Local `<base>` may have stale changes (another session/worktree advanced it) or changes the user authored intending to branch from later. Local Jujutsu can't distinguish these — ask when unpushed changes are present.

## Decision flow

### 1. Fetch fresh remote base

```bash
jj git fetch origin <base>
```

If fetch fails (network, auth, no remote), use the fallback at the bottom.

### 2. Check for unpushed local changes on `<base>`

```bash
jj log origin/<base>..@ --oneline
```

- **Empty output:** set `BASE_REF=origin/<base>` and proceed to step 3.
- **Non-empty output:** show the change list and ask (per the "Asking the user" convention in `SKILL.md`):

  > "Local `<base>` has N unpushed changes not on `origin/<base>`. Carry them onto the new feature bookmark, or leave them on local `<base>`?"

  - **Carry forward** → `BASE_REF=@`. The new branch starts from local @, preserving the changes.
  - **Leave on `<base>`** → `BASE_REF=origin/<base>`. The new branch starts clean; changes remain on local `<base>`.

  Never default silently — carrying foreign changes into a PR is worse than asking again.

### 3. Create the feature bookmark

```bash
jj bookmark set <branch-name> "$BASE_REF"
```

If checkout fails because uncommitted changes would be overwritten, stash and retry:

```bash
jj new push -u -m "ce-commit-push-pr: pre-branch <branch-name>"
jj bookmark set <branch-name> "$BASE_REF"
jj new pop
```

If `jj new pop` reports conflicts, surface the conflict output and the stash ref to the user — do not auto-resolve.

## Fetch failure fallback

If `jj git fetch` fails, branch from current local @:

```bash
jj bookmark set <branch-name>
```

Note in the user-facing summary that base freshness was not verified. Skip the unpushed-changes check — without a fresh `origin/<base>`, the answer is unreliable.
