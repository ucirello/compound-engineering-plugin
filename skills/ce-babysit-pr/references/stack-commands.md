# Managed-stack JJ recipes

Load this file when the active run uses a confirmed managed stack (`manager_status == "confirmed"`). Soft-depend on the read-only manager probe: if it is unavailable, surface a clear residual — do not invent managed membership from topology. All commands run from the absolute target workspace root; repository-scoped `gh` calls require `export GIT_DIR=$(jj git root)` there. Do not use the manager's Git-checkout mutation bridge; execute the confirmed order with JJ.

Always non-interactive. Prefer JSON/view probes and explicit branch names; never rely on interactive prompts. Substitute `<tracking-remote>` with the stack branches' actual tracking remote (often `origin`, but may be `upstream` or a fork remote) — never hard-code `origin` when SKILL.md already resolved a different tracking remote.

## After an owned push on the active layer (dependents exist)

Record the pre-rebase JJ operation ID, target pushed SHA and each confirmed open dependent's local/remote bookmark OIDs. Revalidate manager membership and the clean workspace. Starting at the first open dependent (never the active target), use `jj rebase -s <dependent-revision> -d <new-parent-revision>` in confirmed order, restricting the selected subtree to authorized open dependents and excluding trunk and unrelated changes. If that restriction cannot be proven, return a residual. Verify the target stayed at its pushed SHA. Push only the affected explicit bookmarks with `jj git push --remote <tracking-remote> --bookmark <dependent-bookmark>`; do not use raw force or assume atomic multi-ref updates. After each result, fetch and reconcile each baseline OID and expected tip, retaining partial progress and naming the first rejected layer. On a conflict before any push, restore only this pass's rebase with `jj op restore <recorded-pre-rebase-operation>` after proving no intervening unrelated operation would be discarded; otherwise park without overwriting work. Never restore across a successful remote push. Return a needs-human / stack-sync residual.

## Discover order / next open layer

```bash
workspace_root="<absolute target workspace root>"
(cd "$workspace_root" && export GIT_DIR=$(jj git root); gh stack view --json)
```

## Land one prefix (only under `posture:stack-land`)

Merge the **bottom-most open settled** PR — `gh stack merge <PR>` merges the full stack prefix through that PR atomically. Never merge an upstack active PR while downstack PRs remain open when single-prefix landing is intended.

**Landing capability is separate from confirmed manager membership.** Layers created externally with `gh stack link` and managed locally with JJ may be confirmed by the GraphQL manager probe without being present in the CLI's local stack tracking. Before issuing the merge below, use a read-only, context-qualified `gh stack view --json` probe to prove that the installed CLI sees this exact PR and the same ordered prefix. If it cannot see externally linked JJ-managed layers, reports missing local tracking, or cannot prove the prefix, explicitly return an unsupported-landing `needs-human`/stack residual naming the PR and capability gap; do not invoke `gh stack merge`, import/create local Git tracking, substitute `gh pr merge`, or claim landing succeeded. Preserve native JJ review/CI, dependent propagation, and `stack-ready` continuation for confirmed externally managed layers; only automatic landing is unsupported. When the CLI does positively see the exact prefix and its host merge route works without a Git-checkout bridge, retain the supported host merge plus native JJ synchronization route below.

```bash
workspace_root="<absolute target workspace root>"
(cd "$workspace_root" && export GIT_DIR=$(jj git root); gh stack merge <BOTTOM_MOST_OPEN_SETTLED_PR> --yes --squash)
```

The merge is a host operation, not local Git checkout management. After verified landing, fetch the resolved remote with `jj git fetch --remote <tracking-remote>`, re-probe the manager order, and reconcile only the authorized next open layer onto the fetched landed base using JJ. Preserve unrelated bookmarks and closed-layer history. If the host merge command cannot operate without a Git-checkout bridge, return a landing residual rather than substituting `gh pr merge` or guessing manager semantics. Any squash-message composition must follow `references/branch-currency.md`'s runtime message standards.

Re-probe the landed PR before advancing: on merge-queue bases the CLI may succeed after enqueue while the PR stays OPEN — keep watching or return a queued residual until `pr_state` is `MERGED`. Only then treat the just-merged PR as a **layer transition** (stop watcher, re-probe, continue next open non-draft needing work with posture restated) — not a run-level Terminal stop for this babysit invocation.

## Forbidden on managed stack members

```bash
gh pr merge …
```

Use `gh stack merge` only. Under `posture:target` and `posture:stack-ready`, print the exact merge command when reporting ready-as-next; do not execute it.
