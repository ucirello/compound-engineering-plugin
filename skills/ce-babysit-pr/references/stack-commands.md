# Managed-stack CLI recipes

Load this file when the active run uses a confirmed managed stack (`manager_status == "confirmed"`) and needs `gh stack` command recipes. Soft-depend on the CLI: if `gh stack` is missing or exits unavailable (e.g. code 9), surface a clear residual — do not invent managed membership from topology.

Always non-interactive. Prefer JSON/view probes and explicit branch names; never rely on interactive prompts. Substitute `<tracking-remote>` with the stack branches' actual tracking remote (often `origin`, but may be `upstream` or a fork remote) — never hard-code `origin` when SKILL.md already resolved a different tracking remote.

## After an owned push on the active layer (dependents exist)

```bash
gh stack rebase "<first-open-dependent-branch>" --upstack --no-trunk --remote <tracking-remote>
gh stack push --remote <tracking-remote>
```

Starting at the first dependent excludes the active target from the cascading rebase. Quote the bookmark name — names may contain shell metacharacters. Run from the absolute target workspace root with `GIT_DIR=$(jj git root)` for repository-scoped `gh`. Require a manager compatible with the JJ-only lifecycle; if it requires a direct Git executable or incompatible checkout, stop with a compatibility residual rather than bypassing ownership/session adoption. On conflict: `gh stack rebase --abort`, then surface a needs-human / stack-sync residual.

## Check out a layer on a fresh checkout

```bash
# Prove the installed manager supports the JJ-only owned workspace lifecycle.
# Otherwise report a compatibility blocker; do not run a checkout fallback.
```

Use the PR number with a verified compatible manager's lifecycle, preserving manager membership and harness session ownership. A bookmark name alone only resolves stacks already known locally. Never invoke a checkout helper that requires the Git executable; align the exact verified JJ head as described in `setup.md` only when that preserves the manager's lifecycle, otherwise stop with a compatibility residual.

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

Run the sync only after the merge succeeded. A sync after a failed merge rebases and pushes every layer, which restarts their CI and review. If the merge says another process is editing the stack, retry it shortly: that lock is temporary, and all worktrees of one clone share it.

Re-probe the landed PR before advancing: on merge-queue bases the CLI may succeed after enqueue while the PR stays OPEN — keep watching or return a queued residual until `pr_state` is `MERGED`. Only then treat the just-merged PR as a **layer transition** (stop watcher, re-probe, continue next open non-draft needing work with posture restated) — not a run-level Terminal stop for this babysit invocation.

## Forbidden on managed stack members

```bash
gh pr merge …
```

Use `gh stack merge` only. Under `posture:target` and `posture:stack-ready`, print the exact merge command when reporting ready-as-next; do not execute it.
