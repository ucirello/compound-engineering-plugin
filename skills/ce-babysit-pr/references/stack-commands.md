# Managed-stack CLI recipes

Load this file when the active run uses a confirmed managed stack (`manager_status == "confirmed"`) and needs Jujutsu propagation or `gh stack` provider recipes. Soft-depend on `gh stack`: if it is missing or unavailable, surface a clear residual; do not invent managed membership from topology.

Always non-interactive. Prefer JSON/view probes and explicit Jujutsu bookmark names. Substitute `<tracking-remote>` with the stack bookmarks' actual remote; never hard-code `origin` when setup resolved a different remote.

## After an owned push on the active layer

```bash
jj git fetch --remote <tracking-remote> --branch <active-bookmark> --branch <each-open-dependent-bookmark>
jj rebase --branch <first-dependent-bookmark> --onto <target-bookmark>
jj git push --remote <tracking-remote> --bookmark <each-rewritten-dependent-bookmark>
```

Starting at the first dependent excludes the active target from the cascading rebase, while `--branch` moves that layer's ancestors not already in the destination plus its descendants and advances bookmarks attached to rewritten changes. Quote bookmark names because they may contain shell metacharacters. Immediately record the exact operation ID created by the owned rebase. If the rewritten range contains a conflict, use `jj undo` only when that operation is proven latest and no concurrent operation needs preservation; otherwise use `jj op revert <owned-operation-id>`, or stop with that operation ID in a recoverable `needs-human` / stack-sync residual when safe reversal cannot be established. Push each rewritten bookmark explicitly; never use `--all`.

## Discover order / next open layer

```bash
gh stack view --json
```

## Land one prefix (only under `posture:stack-land`)

Merge the **bottom-most open settled** PR — `gh stack merge <PR>` merges the full stack prefix through that PR atomically. Never merge an upstack active PR while downstack PRs remain open when single-prefix landing is intended.

```bash
gh stack merge <BOTTOM_MOST_OPEN_SETTLED_PR> --yes --squash
gh stack sync --remote <tracking-remote>
```

Re-probe the landed PR before advancing: on merge-queue bases the CLI may succeed after enqueue while the PR stays OPEN — keep watching or return a queued residual until `pr_state` is `MERGED`. Only then treat the just-merged PR as a **layer transition** (stop watcher, re-probe, continue next open non-draft needing work with posture restated) — not a run-level Terminal stop for this babysit invocation.

## Forbidden on managed stack members

```bash
gh pr merge …
```

Use `gh stack merge` only. Under `posture:target` and `posture:stack-ready`, print the exact merge command when reporting ready-as-next; do not execute it. The merge and sync commands are provider operations, not substitutes for Jujutsu fetch, rebase, bookmark, or push behavior.
