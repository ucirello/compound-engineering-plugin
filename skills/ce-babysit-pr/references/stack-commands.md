# Managed-stack CLI recipes

Load this file when the active run uses a confirmed managed stack (`manager_status == "confirmed"`) and needs `gh stack` command recipes. Soft-depend on the CLI: if `gh stack` is missing or exits unavailable (e.g. code 9), surface a clear residual — do not invent managed membership from topology.

**Execution gate for every recipe below:** repository commands use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Read-only API discovery is supported. Before any manager mutation, prove that its implementation uses JJ natively without invoking Git, including checkout, rebase, push, abort and sync. If not proven, do not execute the recipe: retain its intended bounded transaction as a compatibility residual. Never replace manager membership/order/atomicity with guessed local topology or a different ref. This gate also applies to every caller in `stack.md`, `tick.md`, `setup.md`, `envelope.md` and SKILL.md.

Always non-interactive. Prefer JSON/view probes and explicit branch names; never rely on interactive prompts. Substitute `<tracking-remote>` with the stack branches' actual tracking remote (often `origin`, but may be `upstream` or a fork remote) — never hard-code `origin` when SKILL.md already resolved a different tracking remote.

## After an owned push on the active layer (dependents exist)

```bash
gh stack rebase "<first-open-dependent-branch>" --upstack --no-trunk --remote <tracking-remote>
gh stack push --remote <tracking-remote>
```

Starting at the first dependent excludes the active target from the cascading rebase. Quote the branch name — git branch names may contain shell metacharacters. On conflict: `gh stack rebase --abort`, then surface a needs-human / stack-sync residual.

## Align a layer on a fresh workspace

Follow `setup.md`'s exact repository/bookmark/remote/commit gate, fetch with JJ and create an empty working-copy change above the verified head only when clean and authorized. Never use Git-backed checkout. If the manager cannot recognize the resulting JJ workspace natively, report a compatibility residual rather than importing or guessing stack membership.

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
