# Cross-Model Execution Contract

Load this reference only after cross-model execution is selected or recovery is activated. The host drives the controller, detached runner, and fixed adapter. A worker response or process exit never substitutes for controller and jj evidence.

## Fixed Route

Use only targets `codex`, `claude`, `grok`, `cursor`, and `composer`. Keep target, harness/intermediary route, requested model, actual model, and receipt status separate. Controller route tokens are exactly `codex`, `claude`, `grok-cli`, `cursor`, `composer`, and `grok-cursor`; preserve the adapter mappings in `execution-engines.md` and `scripts/cross-model-work.sh`.

The adapter mapping is load-bearing: `codex` uses Codex directly, `claude` uses Claude directly, `grok-cli` uses Grok directly, `cursor` means the Cursor harness with its configured default model, `composer` means a Composer-family model through Cursor, and `grok-cursor` means a Grok-family model through Cursor. A model pinned within the current harness is a distinct candidate unless it is the current/default model. Never collapse Cursor to Composer, treat a Grok intermediary as native Grok, or infer served identity from the requested label.

Preflight ordered preferences without egress. Skip an equivalent same-host default and candidates proven unavailable. The first qualified candidate becomes fixed. After dispatch starts, neither adapter nor worker may change recipient, provider, model family, or intermediary. A different recipient requires a separately sanctioned attempt after authoritative terminal state.

For `prefer`, preflight failure falls back to native execution with requested-versus-actual disclosure. For `require`, an interactive standalone run asks whether to continue natively; automatic and headless callers return a blocker. A started attempt is not preflight failure.

Before egress, record the binding source, fixed route and intermediaries, exposed repository/unit material, and each restriction's enforcement posture. A restriction the adapter cannot enforce makes the route unavailable. A jj workspace limits accidental concurrent mutation but is not an OS security sandbox.

## Worker Boundary

The worker receives one unit, one controller-owned jj workspace, one fixed recipient, and inherited authority. It may edit and run scoped checks but may not describe, split, squash, rebase, abandon, or bookmark changes; push; open a PR; schedule peers; switch recipients; or broaden scope. The host alone inspects the complete workspace change, runs authoritative verification, integrates it into the canonical change graph, gives it a final description, advances the feature bookmark, and continues the owning tail.

Ordinary native isolation remains harness-owned. Only the controller may create sibling jj workspaces, each beneath `<canonical-workspace>/.tmp/rocketclaw/ce-work/<run-id>/`. Never create a nested workspace. If that root is unavailable, use `<canonical-workspace>/.tmp/ce-work/<run-id>/`; do not use an OS-level or user-level store.

## Source And Receipts

Receipts retain the resolved binding, requested and actual route/model, fallback reason, source kind/digest, run id, per-unit process/integration/verification/change/cleanup state, optional plan checkpoint change, blockers, and recovery path. Detached completion is authoring evidence only.

Preserve the operational knobs rather than replacing them with provider-specific guesses: `CE_WORK_RUNS_ROOT`, `CE_PEER_JOBS_ROOT`, `CE_PEER_IDLE_SECS`, `CE_PEER_HARD_SECS`, `CROSS_MODEL_HARD_SECS`, `CE_PEER_LOG_MAX_BYTES`, `CE_PEER_RESULT_MAX_BYTES`, `CE_PEER_POLL_SECS`, `CE_PEER_GRACE_SECS`, `CE_PEER_BASH`, `CLAUDE_CODE_GIT_BASH_PATH`, `CE_WORK_MAX_PACKET_BYTES`, `CE_WORK_RAW_MAX_BYTES`, and the controller's fault-injection knob. Overrides for run/job roots remain constrained beneath the canonical jj workspace's `.tmp`; they change placement inside that namespace, not the namespace boundary.

For bare-prompt work, stage the bounded brief in an owner-private file beneath `<canonical-workspace>/.tmp/rocketclaw/ce-work/.inputs/`, then initialize the run and use only the controller-owned `source/bare-prompt.md` copy and digest. Remove the staging file after initialization. Include Request, Goal, Scope, Acceptance and verification, Constraints and exclusions, and conservative Units. Never include raw conversation history, credentials, or speculative scope. If Goal, bounded Scope, or Acceptance cannot be populated, clarify or plan before initialization.

## Host Transaction

Run one ready unit at a time from the canonical jj workspace. Resolve bundled scripts from this skill's directory. Use `jj -R <workspace>` for every repository operation. Invoke one state-changing controller transition per host tool call until scope inspection; then use the controller's fail-stop `integrate` transaction. A nonzero controller, runner, verification, or jj exit stops the sequence until status and recovery are reconciled.

1. Resolve, preflight, sanction, and encode exact `route`, `intermediaries`, and `restrictions` fields.
2. Initialize with `unit-workspace.py init`. The selected plan may be the sole working-copy change; `checkpoint-plan` seals that path into a dedicated described jj change. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Local instructions and observed history win; apply compatible Go clarity and structure without imposing a fixed form. Other pre-existing changes block the route. A prompt-backed run starts clean.
3. Prepare one bounded unit packet directly under the returned run directory. Pass the recorded base change, dependencies, wave fields, and activity posture. Use only the returned attempt id, packet path, packet digest, authorization path, workspace, and adapter.
4. Start `peer-job-runner.py` with `--no-sweep`, the exact packet digest, label equal to unit id, and result path `<result-dir>/implementation-result.json`. Invoke the returned adapter path directly as the first worker argv. Set the documented hard and idle windows. Before egress, the adapter must obtain `authorize-dispatch` using the runner-exported job id and exact returned paths.
5. Observe with bounded runner status/wait calls and separate controller sync calls. Report route, elapsed time, activity posture, terminal state, and recovery path. Do not steer, duplicate, or infer failure from silence on a hard-only route.
6. On authoritative `done`, call `terminalize`. It snapshots the worker workspace as a pinned transport change and records its change ID, commit ID, parent, operation ID, complete diff inventory, and digest. Inspect actual paths, file types, conflicts, and scope before integration.
7. Compose the final change description before integration. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Local instructions and observed history win; apply compatible Go clarity and structure. Do not impose fixed syntax, stock messages, or product-origin metadata.
8. Invoke `unit-workspace.py integrate --run-id <run-id> --unit-id <unit-id> --change-description <description> --verification-summary <summary> [--allowed-change <recorded-change>] -- <verification-command-and-argv>`. Use direct argv unless the verification contract requires shell syntax, in which case invoke an explicit shell with pipe-failure handling.
9. The transaction acquires the canonical lock, records the current operation and change snapshots, rebases the transport change onto the accepted canonical change, checks for conflicts and exact scope, runs authoritative verification, restores the recorded operation on failure, squashes the verified transport into a new canonical change, applies the final description, advances the feature bookmark, records receipts, forgets the worker workspace, and releases the lock.
10. After all units are accepted, run plan-wide gates through `verify-run`. It records the canonical operation/change snapshot, runs the command, and restores the operation if tracked state changes. Ignored artifacts are inventoried and disclosed but never copied, restored, or deleted.

For route-qualified incremental output, set `CE_PEER_IDLE_SECS=600` and `CE_PEER_HARD_SECS=7200`; progress resets the idle window. For hard-only or untrusted activity, set idle to `0` while retaining the hard cap. Keep command, exit status, output path/size, stderr or blocker, ignored-state counts, and retained-log status in short reports; do not replace these receipts with a generic success sentence.

## Parallel Waves

Use a wave only after the always-loaded safety check proves independence across dependencies, paths, interfaces, generated/config surfaces, runtime resources, and expected integration cost. Record one wave base. Create distinct jj workspaces with transport changes sharing that base. Terminalize and inspect every member before integrating any. Integrate sequentially in dependency order; rebase each transport change onto the advancing accepted change and stop on conflicts or semantic contention. Repeated collision, broad edits, or unprovable restoration disables further waves.

## Recovery And Fallback

Recovery by run id is authoritative and activates before ordinary input classification. Plan-backed discovery matches canonical workspace identity, bookmark, and plan digest; never select by listing a shared root. Multiple matches block selection. Completed runs are observation-only and reuse stored receipts.

Resume may adopt one matching runner job, monitor it, terminalize authoritative output, reconcile an accepted change, restore a recorded jj operation, or finish workspace cleanup. It must not redispatch, reapply, redescribe, or run either shipping tail.

Preserve all attempts under one scalar run id. A corrected retry gets a fresh attempt id only after the prior attempt is terminal, its transport is exactly abandoned or its integration operation is exactly restored, and the integration lock is released. Cleanup remains idempotent and guarded by the exact recorded transport change or terminal job when abandoning output.

After authoritative failure and exact operation restoration, `claim-fallback` authorizes native fallback once. `require` still needs interactive confirmation. After native implementation is described, verified, and bookmarked, `complete-fallback` records its accepted change and evidence. Run `verify-run` before reporting completion.

Standalone use resumes quality and shipping. `mode:return-to-caller` returns implementation and local-verification receipts with `standalone_shipping_skipped: true`; workers inherit neither tail.
