# Native execution and workspace lifecycle

Run repository commands with cwd set to the absolute target workspace root. Use current JJ only; never invoke the Git executable, including through helpers. `jj git` and Git-format diffs remain valid. Repository-scoped GitHub CLI calls require `GIT_DIR=$(jj git root)` in that workspace. See https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-command-table/ . Temporary prompts, exports, errors and fallback state belong under the workspace's `.tmp/rocketclaw/optimize/`, never system temporary storage.

## Isolation

Detect existing isolation first through harness context and `jj workspace list`. Reuse verified run-owned isolation and its name unchanged; do not reset or recreate it for naming or colocation. Verify the exact experiment base against the ledger; preserve mismatches and stop rather than rewriting work. Retain optimization, archive, best and recovery bookmarks.

For new isolation capture the local date ONCE in the ledger, stable across retry, resume and midnight. Derive a meaningful kebab slug from the spec and experiment index. Normalize caller names without double date prefixes. Use `YYYYMMDD-optimize-<spec>-exp-<NNN>`, e.g. `20261008-optimize-parser-exp-003`, as both workspace name and destination basename. Check BOTH registrations and destinations; collisions use `-2`, `-3`, never random/PID/timestamp suffixes. Record exact owner, verified base, name and absolute destination under `$workspace_root/.tmp/rocketclaw/optimize/workspaces/` before creation.

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$new_workspace_root" && jj git colocation status)
```

Verify registration, absolute destination, base and colocation before adopting the workspace in the harness session or dispatching work. Harness-native creation must support explicit colocation and the required name; otherwise report a compatibility blocker, not a bypass. Preserve source/PR bookmarks. Count registered workspaces for the existing budget. Copy configured shared resources only after symlink-resolved source/destination containment checks; never overwrite existing experiment data. Preserve configured port parameterization.

## Native dispatch

Use native subagents with filled experiment/judge prompts and shell for measurement. Legacy `codex` backend values remain accepted compatibility inputs but map to native subagents with the same limits; log that mapping, never call another harness. Resolve configured tier intent with `opencode.models` when available. This skill's explicit research, experiment and judge requests authorize delegation under the user-OR-loaded-skill exception, not model overrides. If host rules require an explicit user model request, omit optional model arguments absent one, use appropriate inherited reviewers and disclose unmet routes. Same-model separate contexts are not cross-model independence.

Respect prohibitions/tool denial; never evade through shell or another harness. Distinguish permission, effective nesting and capacity errors. Queue capacity failures until a slot frees; preserve receipts, checkpoints, cost/time caps, independent confirmation and bounded retries. Three consecutive legacy-route failures still disable that route and log the native fallback. Required judge independence blocks scoring when unavailable; never inline-score. Mandatory coverage remains incomplete if unavailable.

When setup is needed, explain that consumers must merge `experimental.subagent_depth` >=3 into existing user config `~/.config/opencode/opencode.json` (discover actual config with `opencode debug paths` / `opencode debug paths config`). Preserve higher integers, unrelated keys, sibling experimental settings and existing JSONC; never replace the whole file or create competing configs. Package installation/config alone does not enable consumer depth, and higher-precedence config must not lower it. Never edit host config yourself.

## Guarded removal

The loop's commit/branch/merge/cherry-pick terminology means JJ changes/bookmarks: inspect with `jj log`, `jj show` and `jj diff`; transport with `jj git fetch` / `jj git push`. Capture immutable commit IDs before comparisons. Merge verified candidate parents with `jj new <verified-integrated-head> <verified-candidate>`; for a runner-up use `jj duplicate <verified-candidate> --onto <verified-integrated-head>` in its owned isolation. Verify mutable-only changes and absence of conflicts, measure the integrated bytes independently, and advance the optimization bookmark only after eligibility is confirmed. Keep failed combinations off that bookmark and preserve recovery references; do not reset or discard unrelated work. Compose descriptions for candidates, result-only children, integration changes and exported reports using `references/messages.md` before advancing or pushing. Remote collection uses `jj file show -r <verified-result-tip> result.yaml`, verifies the exact parent and mutable-only range through JJ, and retains the existing paired/holdout/cache/independent-confirmation contract.

Cleanup needs explicit run-owned disposal authorization, not merely experiment completion. Stop workers, leave the target and move the active harness session to a surviving absolute root. Verify exact registration/name/path/run ownership/authorization; stop for ambiguity, unrelated work, active references or non-disposable content. Inspect tracked, conflicted, ignored and untracked files: snapshots do not protect ignored/untracked data. Prove winner integration where needed, retain best/archive/recovery refs, and copy then read back necessary result markers, evidence and logs outside the target.

```bash
(cd "$surviving_workspace_root" && jj workspace remove "$verified_name")
(cd "$surviving_workspace_root" && jj workspace list)
test ! -e "$verified_absolute_path"
```

Verify BOTH deregistration and directory disappearance; warnings can leave files behind. On failure preserve/report, never force filesystem deletion or use Git cleanup. `jj workspace forget` unregisters while preserving files, not removal. Bookmark deletion is separate; preserve best, archive, recovery, evidence and integration refs. Never bulk-remove by a name glob.
