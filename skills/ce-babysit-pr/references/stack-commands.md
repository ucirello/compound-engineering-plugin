# Managed-stack CLI recipes

Load this file only for a fresh `manager_status == "confirmed"` stack. If `gh stack` is unavailable, return a residual rather than inferring membership from topology.

The stack extension is Git-facing. JJ bookmarks remain authoritative, so each transaction must start from unconflicted bookmarks and an empty dedicated `@`, save the current JJ change ID, export immediately before the `gh stack` calls, import immediately after them, fetch the tracking remote, inspect the imported bookmark/change graph, and restore the saved working-copy change. Never invoke raw Git yourself.

## Propagate An Owned Target Push

```bash
jj git export
gh stack rebase "<first-open-dependent-bookmark>" --upstack --no-trunk --remote <tracking-remote>
gh stack push --remote <tracking-remote>
jj git import
jj git fetch --remote <tracking-remote>
jj edit <saved-empty-working-copy-change>
```

Starting at the first dependent excludes the active target. Quote the exported bookmark name because it may contain shell metacharacters. If rebase reports a conflict, run `gh stack rebase --abort`, then `jj git import` and `jj edit <saved-empty-working-copy-change>` before surfacing the residual. After success, reject divergent changes, conflicted bookmarks, an altered target bookmark, or any remote result that does not match the manager's reported tips.

## Discover Order

```bash
jj git export
gh stack view --json
```

This is read-only after export. It must not change `@` or remote state.

## Land One Prefix

Only under `posture:stack-land`, merge the bottom-most open settled PR. The extension merges the prefix through that PR.

```bash
jj git export
gh stack merge <bottom-most-open-settled-pr> --yes --squash
gh stack sync --remote <tracking-remote>
jj git import
jj git fetch --remote <tracking-remote>
jj edit <saved-empty-working-copy-change>
```

Re-probe the landed PR before advancing. A queued but still-open PR is not landed. Under `target` and `stack-ready`, print the applicable `gh stack merge <pr> --yes --squash` command when ready-as-next but do not execute it. Never use `gh pr merge` on managed members.
