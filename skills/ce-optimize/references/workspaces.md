# Native experiment workspaces and dispatch

Run every JJ command from the absolute target workspace root, using shell `cd` or subprocess `cwd`, never by repairing returned file paths. Use latest native JJ only, never the Git executable or another harness as a fallback. Reference: https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace and https://docs.jj-vcs.dev/latest/git-command-table/. Repository-scoped `gh` commands require `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Keep all temporary prompts, errors and receipts under the workspace-local ignored `.tmp/`.

## Isolation

First detect existing isolation and harness ownership. Reuse a verified existing workspace under its existing name without renaming, recreating, resetting or silently changing colocation. Respect harness lifecycle/adoption; if its supported workspace capability cannot meet required colocation or naming for new creation, stop safely and report the compatibility blocker.

For each new experiment, capture local `YYYYMMDD` once and normalize a meaningful task/spec/experiment slug. Normalize caller-provided names without double-prefixing. Persist the selected identity for retries, resumes and midnight boundaries. Use the same `YYYYMMDD-<slug>` identity for both workspace name and directory basename beneath the existing local `.tmp/` parent; check registered names and destination paths, suffix collisions `-2`, `-3`, etc. Never overwrite, use random/PID/timestamp substitutes, or rename PR/source bookmarks.

Resolve the exact optimization bookmark to a unique verified commit ID, record it as `base_sha`, and create from that revision from the source absolute root:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Verify registration, absolute path, base and colocation, then record them in the ledger before dispatch. Copy declared shared files and environment inputs with containment checks (resolved source/destination must stay inside their intended roots), preserving hierarchy and never overwriting unexpected existing content. Parameterize ports as configured. Count registrations with `jj workspace list` for the workspace budget. Workspace names and optimization/result bookmarks are separate identities.

## Retirement

Completion does not grant cleanup authority. With explicit authority, stop workers, move active sessions out to a surviving workspace through the supported harness lifecycle, and verify the exact registration/name/path and run ownership. Prove integration for kept candidates. Preserve archive/best/recovery bookmarks; copy and read back required metrics, receipts, markers and recovery evidence outside the target. Inspect `jj status`, conflicts and tracked changes, plus ignored/untracked content separately: snapshots do not protect ignored or untracked files. Retain ambiguously owned, still-referenced or non-disposable content.

From a surviving absolute workspace root only:

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
```

Verify both deregistration and directory disappearance. Warnings or partial failure retain remaining state and are blockers; no manual deletion, force deletion or Git fallback. `jj workspace forget` is only for unregistering while retaining files. Bookmark deletion is separate; never remove needed recovery refs.

## Native dispatch

Installation prerequisite: users must merge `"experimental": { "subagent_depth": 3 }` into their existing `~/.config/opencode/opencode.json`, or locate the actual global configuration using `opencode debug paths` / `opencode debug paths config` and update its existing `opencode.json(c)`. Preserve higher integer depths, unrelated settings and sibling experimental fields; do not create competing JSON/JSONC files. Plugin installation and package-local configuration do not merge this setting into consumers, and higher-precedence configuration must not lower the effective depth below 3. Document this action, never edit host configuration automatically.

This skill explicitly requests experiment, research and independent judge subagents. Under a user-OR-skill delegation rule that is sufficient permission; genuine higher-priority prohibitions and actual denials still apply. Discover configured models/tiers using `opencode.models`; configuration remains authoritative. Delegate through native subagents, and use shell only for mechanical measurement/transport, not another harness dispatcher. The legacy `codex` backend retains its configured route/tier intent but executes through native subagents, not `codex exec`. If a required route is unavailable, report incomplete coverage or a blocker rather than silently claiming it ran.

Delegation permission, model-override permission and remaining nesting capacity are independent. If explicit user model permission is required and absent, omit the model argument and use a suitable inherited model. Preserve independent judge contexts; never grade one's own experiment inline or claim same-model reviewers provide required cross-model coverage. Classify actual capacity/depth errors, permission denials, model rejections and missing tools separately. Queue transient active-slot pressure until a slot frees; do not retry genuine denials or evade depth limits through shell/another harness. Preserve receipts, result validation, bounded recovery and spend caps in `loop.md` and `persistence.md`.
