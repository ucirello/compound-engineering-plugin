# Managed-stack CLI recipes

Load this file when the active run uses a confirmed managed stack (`manager_status == "confirmed"`) and needs `gh stack` recipes. All recipes require a proven native JJ-compatible manager implementation, not an extension that invokes the Git executable. Run from the absolute workspace root with per-call `GIT_DIR=$(jj git root)`. Missing/denied/incompatible capability is a clear residual; never invent membership from topology or bypass with Git. Apply the same gate to every stack recipe cited in this skill.

Always non-interactive. Prefer JSON/view probes and explicit branch names; never rely on interactive prompts. Substitute `<tracking-remote>` with the stack branches' actual tracking remote (often `origin`, but may be `upstream` or a fork remote) — never hard-code `origin` when SKILL.md already resolved a different tracking remote.

## After an owned push on the active layer (dependents exist)

```bash
GIT_DIR=$(jj git root) gh stack rebase "<first-open-dependent-branch>" --upstack --no-trunk --remote <tracking-remote>
GIT_DIR=$(jj git root) gh stack push --remote <tracking-remote>
```

Starting at the first dependent excludes the active target from the cascading rebase. Quote the branch name — git branch names may contain shell metacharacters. On conflict: `gh stack rebase --abort`, then surface a needs-human / stack-sync residual.

## Align a layer in a JJ workspace

```bash
jj git fetch --remote <verified-head-remote> --branch <verified-head-bookmark>
jj new <verified-remote-head-commit>
```

Resolve the layer's PR number, head repository/bookmark and exact remote commit first; apply `references/setup.md`'s clean-state and authority gate. Existing empty `@` above the exact head needs no new change. Require the manager to recognize that layer through a native JJ capability; unsupported recognition is a compatibility residual, never a reason to run a Git checkout.

## Discover order / next open layer

```bash
GIT_DIR=$(jj git root) gh stack view --json
```

## Land one prefix (only under `posture:stack-land`)

Merge the **bottom-most open settled** PR — `gh stack merge <PR>` merges the full stack prefix through that PR atomically. Never merge an upstack active PR while downstack PRs remain open when single-prefix landing is intended.

```bash
GIT_DIR=$(jj git root) gh stack merge <BOTTOM_MOST_OPEN_SETTLED_PR> --yes --squash
GIT_DIR=$(jj git root) gh stack sync --remote <tracking-remote>
```

Run the sync only after the merge succeeded. A sync after a failed merge rebases and pushes every layer, which restarts their CI and review. If the merge says another process is editing the stack, retry it shortly: that lock is temporary, and all worktrees of one clone share it.

Re-probe the landed PR before advancing: on merge-queue bases the CLI may succeed after enqueue while the PR stays OPEN — keep watching or return a queued residual until `pr_state` is `MERGED`. Only then treat the just-merged PR as a **layer transition** (stop watcher, re-probe, continue next open non-draft needing work with posture restated) — not a run-level Terminal stop for this babysit invocation.

## Forbidden on managed stack members

```bash
gh pr merge …
```

Use `gh stack merge` only. Under `posture:target` and `posture:stack-ready`, print the exact merge command when reporting ready-as-next; do not execute it.
