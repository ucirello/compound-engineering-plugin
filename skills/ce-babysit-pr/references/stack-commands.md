# Managed-stack CLI recipes

Load this file when the active run uses a confirmed managed stack (`manager_status == "confirmed"`) and needs manager discovery or JJ propagation recipes. Soft-depend on `GIT_DIR="$(jj git root)" gh stack view` / `GIT_DIR="$(jj git root)" gh stack merge`: if the extension is missing or exits unavailable (e.g. code 9), surface a clear residual — do not invent managed membership from topology.

Always non-interactive. Prefer JSON/view probes and explicit bookmark names; never rely on interactive prompts. Substitute `<tracking-remote>` with the stack bookmarks' actual tracking remote — never assume a remote name when SKILL.md already resolved a different one.

## After an owned push on the active layer (dependents exist)

```bash
jj git fetch --remote <tracking-remote>
jj rebase -s <first-open-dependent-bookmark> -o <active-target-bookmark>
jj resolve --list -r <first-open-dependent-bookmark>::
jj git push --remote <tracking-remote> --bookmark <affected-dependent-bookmark> [--bookmark <affected-dependent-bookmark> ...]
```

Starting at the first dependent excludes the active target from the cascading rebase. Quote bookmark names because provider-compatible names may contain shell metacharacters. JJ materializes conflicts instead of pausing for a continuation; if `jj resolve --list` reports any, do not push and surface a needs-human / stack-sync residual with the rebase operation evidence.

## Discover order / next open layer

```bash
GIT_DIR="$(jj git root)" gh stack view --json
```

## Land one prefix (only under `posture:stack-land`)

Merge the **bottom-most open settled** PR — `GIT_DIR="$(jj git root)" gh stack merge <PR>` merges the full stack prefix through that PR atomically. Never merge an upstack active PR while downstack PRs remain open when single-prefix landing is intended.

```bash
GIT_DIR="$(jj git root)" gh stack merge <BOTTOM_MOST_OPEN_SETTLED_PR> --yes --squash
jj git fetch --remote <tracking-remote>
```

Re-probe the landed PR before advancing: on merge-queue bases the CLI may succeed after enqueue while the PR stays OPEN — keep watching or return a queued residual until `pr_state` is `MERGED`. Only then treat the just-merged PR as a **layer transition** (stop watcher, re-probe, continue next open non-draft needing work with posture restated) — not a run-level Terminal stop for this babysit invocation.

## Forbidden on managed stack members

```bash
GIT_DIR="$(jj git root)" gh pr merge …
```

Use the manager's provider-side `GIT_DIR="$(jj git root)" gh stack merge` only. Under `posture:target` and `posture:stack-ready`, print the exact merge command when reporting ready-as-next; do not execute it.
