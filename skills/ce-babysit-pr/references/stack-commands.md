# Managed-stack CLI recipes

Load this file when the active run uses a confirmed managed stack (`manager_status == "confirmed"`) and needs `gh stack` command recipes. Soft-depend on the CLI: if `gh stack` is missing or exits unavailable (e.g. code 9), surface a clear residual — do not invent managed membership from topology.

Always non-interactive. Prefer JSON/view probes and explicit bookmark names; never rely on interactive prompts. Substitute `<remote>` with the stack bookmarks' actual remote.

## After an owned bookmark push on the active layer (dependents exist)

```bash
jj git fetch --remote <remote>
jj rebase -s <first-open-dependent-bookmark> -d <active-bookmark>
jj bookmark set <dependent-bookmark> -r <rebased-revision>
jj git push --bookmark <dependent-bookmark> --remote <remote>
```

Starting at the first dependent excludes the active target. Quote bookmark/revision expressions. On conflict, preserve the conflicted jj change for inspection or restore the single proven operation with `jj op restore <operation-id>`, then surface a needs-human / stack-sync residual.

## Discover order / next open layer

```bash
gh stack view --json
```

## Land one prefix (only under `posture:stack-land`)

Merge the **bottom-most open settled** PR — `gh stack merge <PR>` merges the full stack prefix through that PR atomically. Never merge an upstack active PR while downstack PRs remain open when single-prefix landing is intended.

```bash
gh stack merge <BOTTOM_MOST_OPEN_SETTLED_PR> --yes --squash
gh stack sync --remote <remote>
```

Re-probe the landed PR before advancing: on merge-queue bases the CLI may succeed after enqueue while the PR stays OPEN — keep watching or return a queued residual until `pr_state` is `MERGED`. Only then treat the just-merged PR as a **layer transition** (stop watcher, re-probe, continue next open non-draft needing work with posture restated) — not a run-level Terminal stop for this babysit invocation.

## Forbidden on managed stack members

```bash
gh pr merge …
```

Use `gh stack merge` only. Under `posture:target` and `posture:stack-ready`, print the exact merge command when reporting ready-as-next; do not execute it.
