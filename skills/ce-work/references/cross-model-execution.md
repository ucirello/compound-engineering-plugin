# Cross-Model Execution Contract

Load this reference only after selecting a cross-model engine or activating recovery. It defines fixed-route authority, worker isolation, durable receipts, fail-stop integration, fallback, and tail ownership. Controller evidence and Jujutsu state, not worker prose or process exit alone, decide every transition.

The official Jujutsu [working-copy/workspace documentation](https://jj-vcs.github.io/jj/latest/working-copy/) and [CLI reference](https://jj-vcs.github.io/jj/latest/cli-reference/) define the semantics; inspect local `jj --help` and the relevant subcommand help before adapting syntax for the installed version. Local help wins on available flags, while the conditions in this contract remain unchanged.

## Route And Authority

Supported targets remain `codex`, `claude`, `grok`, `cursor`, and `composer`; supported fixed route tokens remain `codex`, `claude`, `grok-cli`, `cursor`, `composer`, and `grok-cursor`. Keep target, harness/intermediary, requested model, actual model, and receipt status separate. Preserve provider-specific operational mappings and inspect local CLI help when compatibility must be refined within the already sanctioned provider/model family.

Resolve ordered preferences before egress. Skip a candidate only when it is equivalent to the current host or observed preflight evidence makes it unavailable. Once dispatch starts, the route, provider, model family, intermediaries, packet, workspace, and restrictions are fixed. A different recipient requires a separately sanctioned attempt after authoritative terminal or reaped state.

- `prefer`: a preflight-unavailable route may fall back to native execution with requested-versus-actual disclosure.
- `require`: an interactive standalone run asks before native fallback; a headless or automatic caller returns a blocker.
- A started attempt is authoritative until terminalized or explicitly reaped. Latency and silence are not preflight unavailability.

Before egress, disclose and durably record the binding source, recipient and intermediaries, exposed source/unit/workspace material, and which restrictions are enforced versus cooperative. If a required restriction cannot be enforced, the route is unavailable. A Jujutsu workspace isolates concurrent working copies but is not an OS security sandbox.

The worker receives one unit, one named workspace, and inherited authority only. It may narrow but not broaden scope. It may edit and run scoped verification, but must not change descriptions, ancestry, bookmarks, operations, remotes, publication state, recipients, fallback state, peers, or another workspace. The host alone inspects the actual Jujutsu delta, integrates it, runs authoritative verification, describes canonical changes, and owns the shipping tail.

## Workspace-Root State

All reusable controller state, job state, packet sources, prompt briefs, logs, locks, and external workspaces live under `<workspace-root>/.tmp`, where `<workspace-root>` is `jj workspace root`. If that command is unavailable before a workspace has been established, use the current directory's `.tmp`; once initialized, the manifest-recorded workspace root is authoritative. No alternate scratch root or environment-selected temporary directory is permitted.

Every controller-owned Jujutsu call applies a command-local `snapshot.auto-track` exclusion for `.tmp/**`; workspace-root discovery uses `--ignore-working-copy`. This namespace rule prevents controller state from entering a working-copy change without editing the project's ignore files or persistent Jujutsu configuration.

The default run root is `<workspace-root>/.tmp/ce-work/<run-id>`. `ROCKETCLAW_WORK_RUNS_ROOT` and `ROCKETCLAW_PEER_JOBS_ROOT` may override it only when their resolved path remains inside the same workspace-root `.tmp`; reject every escaping override. Controller directories remain owner-only and symlink-safe.

Ordinary native workers use only harness-owned isolation. The external controller alone may run `jj workspace add --name <controller-derived-name> -r <recorded-base> <run-root>/units/<unit-id>/workspace`. The workspace is named and independently registered in the same Jujutsu repo; cleanup uses `jj workspace forget <name>` and removes only the controller-owned directory after integration or exact abandonment is proven.

## Source And Dispatch

For a repository plan, record its workspace-relative path and SHA-256. If it is the only delta in `@`, isolate it as a plan checkpoint change with a dynamic description, then create a fresh child change for implementation. For bare-prompt work, write a bounded brief under the run root containing only Request, Goal, Scope, Acceptance and verification, Constraints and exclusions, and conservative units. Do not transmit raw conversation history.

Initialize with `unit-workspace.py init`, then call `checkpoint-plan` when the source is a plan. A successful `READY` closes engine selection for that run. Before every unit, re-read workspace identity, source digest, canonical change/commit IDs, operation ID, parent IDs, bookmarks, conflicts, and `jj status`.

Create one bounded unit packet under the returned run root. `prepare` records the canonical base, dependencies, wave information, packet digest, and controller-generated workspace name; it creates the isolated Jujutsu workspace. Start the returned `cross-model-work.sh` adapter through `peer-job-runner.py` with the exact authorization path, packet path/digest, workspace, result directory, and provider route. Preserve `ROCKETCLAW_PEER_HARD_SECS=7200`; use `ROCKETCLAW_PEER_IDLE_SECS=600` only for trustworthy incremental activity and `0` for terminal-only routes.

Observe with bounded runner waits followed by controller `sync-job`. Never steer, duplicate, or silently substitute a live attempt. On authoritative completion, `terminalize` snapshots the worker workspace through Jujutsu, records its change ID and commit ID, and inventories the complete `jj diff --summary`/name-only delta. Scope expansion, unexplained files, conflicts, or a mismatched receipt remain preserved for host resolution.

## Canonical Integration

The controller's `integrate` command owns the transaction. Invoke it with the run/unit, a dynamic `--description`, a verification summary, any recorded allowed change, and direct verification argv. Use an explicit shell only when the verification contract itself requires shell syntax.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Runtime local conventions and visible local history win. Apply compatible Go guidance only where it agrees with those conventions. Never force a type, scope, subject form, body layout, decorative metadata, or canned example. Leave a new change undescribed until authoritative verification, then apply the validated semantic description through `jj describe` using the installed JJ syntax.

`integrate` must:

1. Acquire the repository/run integration lock and prove canonical workspace identity, operation continuity, allowed ancestry, clean active change, and ready dependencies.
2. Record the pre-integration operation ID plus canonical change/commit/parent IDs and delta.
3. Integrate only the terminalized worker change into the work-owned canonical change using Jujutsu; never substitute another VCS mutation path or provider shortcut.
4. Prove the resulting delta and changed paths equal the expected transport content, with no unresolved conflict.
5. Run authoritative verification from the canonical workspace with Python bytecode disabled; inventory ignored artifacts by metadata but do not restore or delete them.
6. If verification or reconciliation fails, restore the exact pre-integration Jujutsu operation with `jj op restore <recorded-operation>`, update the workspace if stale, and prove exact equality before releasing the lock. Preserve the worker workspace and blocker if equality cannot be proven.
7. Compose and validate the description under the rule above, apply it with `jj describe` using the installed JJ syntax, record canonical change and commit IDs, create a fresh undescribed child only when another unit remains, then clean the isolated workspace and release the lock.

A crash after description or child creation is recoverable from change IDs, commit IDs, operation IDs, and manifests. It never authorizes redispatch. Jujutsu operations are the restoration authority; commit ancestry alone is insufficient because descriptions, bookmarks, and workspace assignments are repository state too.

After all units are integrated, run `verify-run` through the controller. It starts from a recorded canonical operation and clean active change, captures direct exit status, restores any verification-created tracked delta through the recorded operation, discloses ignored-state divergence, and stores a durable receipt. A failing gate blocks the return or shipping tail.

## Parallel Waves

Use a wave only when dependencies, declared paths, shared contracts/interfaces, generated/configuration surfaces, migrations, lockfiles, runtime singletons, and expected integration cost all support independence. Cap a wave at 3-5 isolated workspaces.

Every member starts from the same recorded base change. Terminalize and inspect all members before integrating any. Integrate sequentially in dependency order; after each canonical change, rebase or re-dispatch later isolated changes onto the advancing canonical change only through an explicit host decision. Conflict-free rebasing is not semantic proof. A collision, broad edit, scope expansion, conflict, failed verification, or unprovable restoration disables affected concurrency and preserves inspectable state.

## Recovery And Fallback

With a supplied run ID, `resume --run-id <id>` is authoritative and may only reconcile recorded evidence. Without one, plan-backed discovery requires the canonical workspace identity plus plan digest and must select exactly one unfinished run. Prompt-backed runs require the disclosed run ID. Ambiguity blocks; never choose by directory recency.

Completed recovery is read-only when every unit has an accepted canonical change and a successful plan-wide receipt. Resume may adopt one matching unbound job, monitor a live job, terminalize done output, restore a recorded operation, reconcile a canonical description/change receipt, finish workspace cleanup, or release a proven lock. It must not redispatch, reimplement, rerun completed verification, publish, or start either tail.

Post-start fallback requires `claim-fallback` after authoritative failure/reap or exact operation restoration and lock release. The claim is single-use. After native implementation, authoritative verification, and a properly described accepted canonical change, `complete-fallback` records the accepted change ID and commit ID plus evidence digest. Plan-wide `verify-run` remains required.

## Tail Ownership

The engine changes implementation authorship only. Standalone execution resumes quality and shipping. `mode:return-to-caller` returns source, route, model, run, unit, integration, verification, canonical-change, cleanup, blocker, and recovery receipts with `standalone_shipping_skipped: true`. External workers inherit neither tail.
