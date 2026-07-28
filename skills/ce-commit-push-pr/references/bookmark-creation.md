# Feature bookmark creation from the default bookmark

The local default bookmark may differ from its tracked remote bookmark because another workspace advanced it or because the user has unpublished changes. Jujutsu exposes that state directly; do not infer intent from bookmark position.

Use the writable publication `<remote>` passed by `SKILL.md` throughout this flow. Do not resolve or substitute a different remote here.

## Decision flow

### 1. Fetch the remote state

```bash
jj git fetch --remote <remote>
```

If fetch fails because of network, authentication, or missing remote configuration, use the fallback below.

### 2. Inspect unpublished local revisions

```bash
jj log -r '<base>@<remote>..<base>'
```

- **Empty output** - use `<base>@<remote>` as the destination for feature work.
- **Non-empty output** - show the revisions and ask whether they belong in the new feature stack or must remain only on the local default bookmark. Never choose silently.

If they belong in the feature stack, use `<base>` as the destination. If they must remain on the local default bookmark, use `<base>@<remote>`.

### 3. Rebase the work onto the selected destination

Identify the earliest revision that belongs to the feature work, then move that revision and its descendants:

```bash
jj rebase -s <work-root> -d <selected-base>
```

Jujutsu preserves working-copy changes during this graph rewrite. If `jj status` or `jj resolve --list` reports conflicts, stop for user resolution; do not silently resolve them or create or move a bookmark. Explain that Jujutsu has no continue step: after the user resolves the files and squashes the resolution into the intended change if needed, rerun both checks. Use `jj log -r '<selected-base>..@'` and `jj diff` to verify that the intended stack and content remain.

Do not create the feature bookmark yet. After Step 3 in `SKILL.md` has split, squashed, and described the final changes, create it at the publishable head with `jj bookmark create <bookmark> -r @-`.

## Fetch failure fallback

Keep the current ancestry, create or move the feature bookmark only after the publishable head is final, and state in the user-facing summary that remote base freshness was not verified. Do not compare against stale remote state or claim that the stack is current.
