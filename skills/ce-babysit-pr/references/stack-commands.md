# Managed-stack CLI recipes

Load this file when the active run uses a confirmed managed stack (`manager_status == "confirmed"`) and needs `gh stack` command recipes. Soft-depend on the CLI: if `gh stack` is missing or exits unavailable (e.g. code 9), surface a clear residual — do not invent managed membership from topology.

Always non-interactive. Prefer JSON/view probes and explicit branch names; never rely on interactive prompts. Substitute `<tracking-remote>` with the stack branches' actual tracking remote (often `origin`, but may be `upstream` or a fork remote) — never hard-code `origin` when SKILL.md already resolved a different tracking remote.

**JJ execution and manager compatibility.** Run from the target workspace's absolute root with `GIT_DIR=$(jj git root)` exported for every repository-scoped `gh` call. Prefer JJ fetch, ancestry, bookmark movement and push; align layers through `setup.md`, never Git checkout. For confirmed manager-owned dependent propagation, preserve baseline and recovery references, rebase only manager-identified dependent revisions with `jj rebase` onto the newly verified parent in manager order (never the active target), verify target immobility and conflicts, then `jj git push --remote <verified-remote> --bookmark <verified-dependent-bookmark>`. Re-probe manager metadata/order and every remote tip before claiming success. Conflicts stop propagation; preserve attempt and recovery evidence rather than reset/discard. The mutation recipes below and callers' matching recipes are conditional manager-only fallbacks: use them only if JJ cannot preserve required manager metadata and the installed manager demonstrably supports this colocated JJ backend without bypassing its lifecycle. Otherwise surface a precise recoverable stack-sync residual; never use a Git-only workspace bridge or guess membership. JJ cannot replace the manager's atomic prefix-landing API, so authorized `gh stack merge` remains host-owned. After landing prefer JJ fetch and re-probe; `gh stack sync` has the same compatibility gate. See https://docs.jj-vcs.dev/latest/git-command-table/ and https://docs.jj-vcs.dev/latest/cli-reference/ .

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
