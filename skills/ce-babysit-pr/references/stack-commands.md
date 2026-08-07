# Managed-stack recipes

Load this file when the active run uses a confirmed managed stack (`manager_status == "confirmed"). Membership and order come from the helper's host-qualified GitHub API snapshot, never local topology. If `gh stack` is unavailable, surface a clear residual instead of inventing managed membership or a merge fallback.

Always non-interactive. Resolve `<tracking-remote>` from API ownership, the project's active instructions, and `jj git remote list`; stop when more than one writable remote remains plausible.

## After an owned publication on the active layer

```bash
jj git fetch --remote <tracking-remote> --branch <dependent-bookmark>
jj rebase -s <dependent-bookmark> -d <updated-bookmark-below>
jj git push --remote <tracking-remote> --bookmark <dependent-bookmark>
```

Process open dependents bottom-up in API order, one bookmark at a time. Before each rebase, require the fetched remote bookmark to match the baseline; after each publication, re-fetch and re-snapshot. Quote bookmark names because they may contain shell metacharacters. On conflict, abandon only the known attempted rebase result or restore it with Jujutsu operations, then surface a `needs-human` residual.

## Discover order / next open layer

Use `pr_chain.entries` from a fresh helper snapshot. Do not infer order from local bookmarks.

## Land one prefix (only under `posture:stack-land`)

Merge the **bottom-most open settled** PR — `gh stack merge <PR>` merges the full stack prefix through that PR atomically. Never merge an upstack active PR while downstack PRs remain open when single-prefix landing is intended.

```bash
gh stack merge <BOTTOM_MOST_OPEN_SETTLED_PR> --yes --squash
jj git fetch --remote <tracking-remote>
```

Re-probe the landed PR before advancing: on merge-queue bases the CLI may succeed after enqueue while the PR stays OPEN — keep watching or return a queued residual until `pr_state` is `MERGED`. Only then treat the just-merged PR as a **layer transition** (stop watcher, re-probe, continue next open non-draft needing work with posture restated) — not a run-level Terminal stop for this babysit invocation.

## Forbidden on managed stack members

```bash
gh pr merge …
```

Use the GitHub stack merge operation only. Under `posture:target` and `posture:stack-ready`, print the exact merge command when reporting ready-as-next; do not execute it.
