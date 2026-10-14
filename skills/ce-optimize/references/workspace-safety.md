# Native experiment isolation and lifecycle

Use https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace and https://docs.jj-vcs.dev/latest/git-command-table/ for JJ operations. Run every JJ command with its working directory set to the applicable workspace's absolute root; `-R` alone is insufficient. File lists stay repository-relative.

Detect existing isolation first. Reuse verified harness-owned or run-owned isolation under its existing name; never rename, recreate, reset or silently change colocation. Concurrent experiments must have distinct isolated working copies. Respect the harness's supported workspace creation, session adoption and lifecycle authority. If it supports colocated JJ isolation, request and verify it. Unsupported required naming or colocation is a compatibility blocker, not permission to bypass ownership or fall back to Git-only isolation.

For new `ce-worktree` experiment workspaces capture the local date once and persist it before creation. Derive a meaningful kebab-case slug from the spec and experiment, e.g. `20261014-optimize-search-exp-001`; task, PR and revision callers use `20261014-fix-search`, `20261014-pr-214`, or `20261014-review-efcb657`. Normalize supplied names without double-prefixing. Use the same dated identity as workspace name and destination basename under the source workspace's local `.tmp/`; check both registrations and directories and append `-2`, `-3`, etc. on collision. Persist the chosen identity for retries, resumes and midnight crossings. Preserve existing source/PR bookmarks and the separate `optimize-exp/<spec>/exp-<NNN>` bookmark namespace.

Resolve the current-best optimization bookmark to an exact verified revision before dispatch; persist that base with the experiment. From the source absolute root:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$selected_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Verify registered name, absolute destination and base; adopt the workspace through the harness session API where required. Never reset stale isolation on retries. Recover its result markers and inspect its edits first; stop on unexpected ownership or state. Copy needed `.env` files (except `.env.example`) and declared shared resources to private per-experiment destinations, without overwriting unrelated content. Check copied databases, lock files, fixed ports and caches for sharing hazards. Preserve configured port parameterization. Record ownership, workspace identity, experiment bookmark and copied resources in recovery state outside the experiment directory.

## Native dispatch

This skill explicitly requests experiment, research and independent judge subagents. Under a host rule permitting user OR loaded-skill-requested delegation, these instructions satisfy that exception; no second approval is needed. A stronger prohibition, missing tool or actual denial still applies. Do not bypass it with shell or another harness.

Read configured model choices and tiers (including judge model and legacy backend/security intent) from the spec and `.rocketclaw/config.yaml` / `config.local.yaml`. Resolve available models with `opencode.models`, then use native subagents and shell for measurement. Delegation permission does not grant model-override permission: when overrides require an explicit user model request, omit the optional model argument and use an adequate inherited model. Disclose unmet fixed routes or tiers. Same-model agents remain independent actors but are not cross-model coverage.

Check effective nesting capacity separately. Classify actual failures as capacity/depth, permission denial, model-argument rejection or missing capability. Capacity backpressure may wait for a slot; do not retry a denial or evade depth through another harness. Parent-coordinator fallback is allowed only if it preserves the experiment and judge contracts. Judges must remain separate from authors and blind to other scores; an undispatchable independent judge is an error, not an inline score. Preserve bounded queues, costs, receipts, failure reasons and recovery markers.

## Integration and retirement

Read `change-descriptions.md` before describing a winning experiment. Verify only mutable-scope edits remain; snapshot the winning change, describe it with `jj describe`, and retain its exact revision under the experiment bookmark before integration. Rebase that change onto the verified current optimization head using `jj rebase -r <experiment-revision> -d <verified-head>`; resolve conflicts without discarding unrelated work and advance the optimization bookmark only after verifying the integrated diff. Use `jj new <verified-head>` for the next clean working-copy change. Disjoint runners-up need a fresh combined measurement and distinct persisted integrated pairing, exactly as the loop requires. For rejected combinations restore the optimization bookmark to its recorded pre-combination revision while retaining recovery references; do not reset or discard unrelated edits.

Every cleanup instruction in this skill invokes this procedure. Completion alone does not authorize deleting user or harness-owned isolation. For authorized run-owned disposable workspaces: stop all workers, leave the target and move active harness sessions to a surviving workspace first. Verify exact registered name, absolute path and run ownership. Prove winning integration when required. Preserve best/archive/recovery bookmarks and all still-needed references. Copy required logs, result.yaml, receipts and evidence outside the target and read them back before removal. Inspect `jj status`, conflicts and tracked changes, plus ignored and untracked content, including copied secrets/databases/caches: removal snapshots the working copy, but ignored and left-untracked files are not protected. Never remove unrelated, ambiguous, still-referenced or non-disposable content.

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
(cd "$surviving_workspace_root" && jj workspace list)
test ! -e "$verified_absolute_path"
```

Require both deregistration and directory disappearance; successful exit can still include deletion warnings. On failure retain remaining state and report the blocker; no force deletion or Git cleanup fallback. Delete disposable experiment bookmarks separately only after integration/evidence/recovery checks; never delete best/archive/recovery references. `jj workspace forget` is reserved solely for authorized unregister-only operations that intentionally preserve files.
