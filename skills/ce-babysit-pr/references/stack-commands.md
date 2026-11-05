# Managed-stack CLI recipes

Load this file when the active run uses a confirmed managed stack (`manager_status == "confirmed"`) and needs `gh stack` command recipes. Soft-depend on the CLI: if `gh stack` is missing or exits unavailable (e.g. code 9), surface a clear residual — do not invent managed membership from topology.

Always non-interactive. Prefer JSON/view probes and explicit branch names; never rely on interactive prompts. Substitute `<tracking-remote>` with the stack branches' actual tracking remote (often `origin`, but may be `upstream` or a fork remote) — never hard-code `origin` when SKILL.md already resolved a different tracking remote.

## After an owned push on the active layer (dependents exist)

```bash
jj rebase -s <verified-first-dependent-series-root> -d <verified-pushed-target-head>
jj git push --remote <tracking-remote> --bookmark <verified-dependent-bookmark>
```

Select the exact dependent series from the confirmed manager order and saved pre-push OIDs, excluding the active target and trunk. Preserve each dependent bookmark and push only those verified owned bookmarks, bottom-up. Quote bookmark names. Save recovery bookmarks first. On conflict stop before push; preserve the recoverable operation and surface a needs-human / stack-sync residual, never discard unrelated work. Re-fetch and reconcile partial pushes individually, not as an assumed atomic transaction.

## Check out a layer on a fresh checkout

```bash
jj git fetch --remote <verified-head-remote> --branch exact:<head-bookmark>
jj new <verified-pushed-head-oid>
```

Use the explicit PR number to resolve the exact repository/bookmark/OID first and follow the clean alignment gate in `setup.md`; an empty tip above that head needs no new change. Discover manager membership read-only; never infer or import it by checkout.

## Discover order / next open layer

```bash
gh stack view --json
```

## Land one prefix (only under `posture:stack-land`)

Merge the **bottom-most open settled** PR — `gh stack merge <PR>` merges the full stack prefix through that PR atomically. Never merge an upstack active PR while downstack PRs remain open when single-prefix landing is intended.

```bash
gh stack merge <BOTTOM_MOST_OPEN_SETTLED_PR> --yes --squash
```

Only after confirmed merge, fetch the exact new base and propagate the remaining confirmed layers using the native JJ series recipe above, preserving manager order and recovery evidence. Never sync after a failed merge: it would restart CI/review unnecessarily. If the merge reports a concurrent manager edit, retry shortly within budget; never bypass its ownership lock.

Re-probe the landed PR before advancing: on merge-queue bases the CLI may succeed after enqueue while the PR stays OPEN — keep watching or return a queued residual until `pr_state` is `MERGED`. Only then treat the just-merged PR as a **layer transition** (stop watcher, re-probe, continue next open non-draft needing work with posture restated) — not a run-level Terminal stop for this babysit invocation.

## Forbidden on managed stack members

```bash
gh pr merge …
```

Use `gh stack merge` only. Under `posture:target` and `posture:stack-ready`, print the exact merge command when reporting ready-as-next; do not execute it.
