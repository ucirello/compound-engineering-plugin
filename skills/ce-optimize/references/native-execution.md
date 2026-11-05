# Native execution and workspace lifecycle

Read this for every local or remote experiment and cleanup. Use latest JJ, never the Git executable, including transport and history. See https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace and https://docs.jj-vcs.dev/latest/git-command-table/. Run each JJ command with its working directory set to the target workspace's absolute root, not merely `jj -R`. Repository-scoped `gh` requires `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Temporary prompts, fallback files and receipts belong under the local workspace `.tmp/`; ensure `.tmp/` is ignored.

## Isolation and integration

Detect existing isolation first. Reuse verified existing isolation without renaming, recreating or modifying it to enforce new conventions. For harness-owned isolation use its supported colocated JJ capability and adoption/lifecycle contract; unsupported required capabilities are blockers, not permission workarounds.

For a new experiment resolve exactly one base commit from the optimization bookmark. Capture the local creation date once and persist a meaningful `YYYYMMDD-<spec>-exp-<NNN>` identity in the ledger. Normalize caller names without double-prefixing; use the same identity as the workspace name and destination basename beneath the source root's `.tmp/optimize/`. Check registrations and destinations; append `-2`, `-3`, etc. for collisions without overwriting anything. Persist the final selection across retries/resumes and midnight. When calling `ce-worktree`, pass this identity and require it to verify the name. Existing isolation retains its existing name.

From the absolute source root:

```sh
(cd "$workspace_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify registration, absolute destination and exact base, and adopt the destination using the harness session's supported directory mechanism before work. Never reset an existing experiment on retry. Copy declared shared files and immutable harness resources with symlink-resolved containment checks, without overwriting unrelated content. Retain port parameterization and record copied resources.

Before integration describe the mutable-scope candidate under `change-descriptions.md`, excluding recovery markers and immutable resources; verify its exact diff against the captured base. Use native JJ merge/rebase operations to integrate only that candidate, resolve conflicts through the existing safe decision path, and move the optimization bookmark only after verification. For runner-ups rebase their candidate onto the verified winner, measure the integrated pairing independently, and retain only eligible combinations. Preserve the pre-integration recovery revision so an unsuccessful combination can be left aside without discarding other work. Remote fetch/push uses `jj git fetch` / `jj git push` with exact verified refs; validate the result marker's sole-file tip, candidate parent, base, scope and paired snapshots before accepting it. Never fetch a substitute ref.

## Native dispatch

These experiment/research/judge instructions explicitly request native subagents. Under a user-or-loaded-skill delegation rule this satisfies the skill-requested exception; no second approval is needed. An unconditional prohibition, actual denial or missing tool still applies. Discover available models with `opencode.models`; configuration remains authoritative intent for routes and tiers. Model-choice permission is separate: if overrides require an explicit user model request, omit the optional model argument and use an inherited model only when suitable. Report unmet fixed-model or cross-model requirements as incomplete, not silently satisfied. Same-model separate contexts are not cross-model independence.

Check effective depth separately from permission using OpenCode configuration discovery; deep delegation requires at least 3. Installation must merge `experimental.subagent_depth: 3` into the existing user global `~/.config/opencode/opencode.json(c)` (locate it with `opencode debug paths` / `opencode debug paths config`), preserving higher integers, unrelated settings and sibling fields, without competing config files. Installing a plugin or bundled package config alone does not configure the consumer; higher-precedence configuration must not lower depth. Do not mutate global configuration during execution. Classify actual dispatch errors as permission, model selection, depth/capacity or missing tool; never evade them through another harness. Capacity backpressure may wait for a slot; depth exhaustion is not a capacity retry loop.

Keep the existing receipts, pending waits, durable evidence, cost caps and bounded recovery. Independent judges and held-out confirmation remain separate contexts with no access to other judges' scores; when required independence cannot run, mark coverage blocked, never score inline. A legacy `codex` route now executes natively with the same intended tier/security constraints; do not invoke another harness's dispatcher.

## Retirement

Completion alone is not authorization to delete a workspace. Stop its workers, leave the target and move any active session to a surviving absolute workspace root. Respect harness-owned lifecycle authority. Verify the exact registered name, absolute path and run ownership; prove required integration, preserve best/archive/recovery bookmarks, and copy/read back logs, result markers and required evidence outside the target. Inspect tracked changes, conflicts, ignored and untracked files: removal snapshots working-copy state but does not protect ignored or untracked bytes. Do not remove unrelated, ambiguous, still-referenced or non-disposable content.

Only after those checks and existing cleanup authorization, run `(cd "$surviving_root" && jj workspace remove "$verified_name")`. Verify both deregistration with `jj workspace list` and absolute directory disappearance; warnings can leave files behind despite success. On failure preserve remaining state and report the blocker, never force-delete or use Git cleanup. `jj workspace forget` is unregister-only, preserving files. Bookmark deletion is separate; preserve all references still required for recovery, best results or archives.
