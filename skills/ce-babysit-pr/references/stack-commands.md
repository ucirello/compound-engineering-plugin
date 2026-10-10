# Managed-stack CLI recipes

Load this file when the active run uses a confirmed managed stack (`manager_status == "confirmed"`) and needs `gh stack` command recipes. Soft-depend on the CLI: if `gh stack` is missing or exits unavailable (e.g. code 9), surface a clear residual — do not invent managed membership from topology.

Always non-interactive. Prefer JSON/view probes and explicit branch names; never rely on interactive prompts. Substitute `<tracking-remote>` with the stack branches' actual tracking remote (often `origin`, but may be `upstream` or a fork remote) — never hard-code `origin` when SKILL.md already resolved a different tracking remote.

Run these manager-owned operations from the absolute verified colocated workspace root with `GIT_DIR` exported from `jj git root` in that shell call. `gh stack` is retained for its unsupported managed-stack protocol, not as a workspace bridge. Verify its view still matches JJ bookmarks/remote commits after each operation; if it cannot safely operate on this JJ workspace, return a precise stack residual instead of a Git checkout/reset workaround. Local fetch, alignment, status, and commit verification use JJ per setup; a transition means verified bookmark/head alignment, never inferred Git current-branch identity.

## After an owned push on the active layer (dependents exist)

```bash
gh stack rebase "<first-open-dependent-branch>" --upstack --no-trunk --remote <tracking-remote>
gh stack push --remote <tracking-remote>
```

Starting at the first dependent excludes the active target from the cascading rebase. Quote the branch name — git branch names may contain shell metacharacters. On conflict: `gh stack rebase --abort`, then surface a needs-human / stack-sync residual.

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

Use `gh stack merge` only. Under `posture:target` and `posture:stack-ready`, print the exact merge command when reporting ready-as-next; do not execute it.
