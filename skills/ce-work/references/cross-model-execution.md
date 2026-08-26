# Cross-Model Execution Contract

Load this reference only after the cross-model engine is selected or recovery of an existing external run is activated. It defines the fixed-route, authority, fallback, identity, receipt, and serial Jujutsu transaction contract. The host drives the bundled controller, detached runner, and adapter; worker output or process exit never substitutes for controller and repository evidence.

## Resolve One Route

Use only the existing `codex`, `claude`, `grok`, `cursor`, and `composer` targets. Keep target, serving route, requested model, actual model, and receipt status separate. The controller route tokens remain `codex`, `claude`, `grok-cli`, `cursor`, `composer`, and `grok-cursor`; they preserve the existing provider mappings and intermediary restrictions.

For an ordered standing preference, preflight candidates without egress. Skip only an equivalent self-route or a route proven unavailable. The first qualified candidate becomes the fixed recipient. After dispatch starts, no recipient, provider, intermediary, or model substitution is allowed inside the attempt.

Both `prefer` and `require` continue natively when the requested route is proven unavailable, after disclosing requested versus actual route/model and the observed reason. A started attempt is not unavailable until controller evidence makes it terminal or reaped.

## Sanction And Authority

Before egress, disclose and record the binding source, fixed recipient and intermediaries, exposed repository/unit material, inherited restrictions, and whether each restriction is adapter-enforced or cooperative. Treat an unenforceable required restriction as route unavailable.

The worker receives one controller-owned Jujutsu workspace, one unit, one recipient, and only inherited authority. It may edit and run scoped checks there. It must not describe, rebase, squash, bookmark, push, open a PR, switch recipients, schedule peers, or integrate into the canonical workspace. Successful output terminalizes as the workspace's pinned working-copy revision; the host alone applies its recorded fileset, verifies it, describes the canonical change, and advances the canonical workspace.

The workspace is accidental-mutation isolation, not an OS security boundary. Host-only capabilities remain host-owned when a worker sandbox rejects them.

## Receipts

Direct and return-to-caller runs expose:

- `implementation_engine_binding`, requested/actual route and model, and served-model receipt status;
- `fallback_reason` or `null`;
- `source_kind` and controller-recorded digest;
- `run_id` and per-unit process, transport revision, integration, verification, canonical revision, and cleanup state;
- `plan_checkpoint`, when the selected plan was the sole change in the canonical working-copy change;
- blockers and the workspace-local recovery path.

Completion requires every unit to have an accepted canonical revision and the source-wide verification receipt.

## Bare-Prompt Source

When Phase 0 has established a concrete goal, bounded scope, and authoritative verification without a plan, write the bounded brief under `<workspace-root>/.tmp/rocketclaw/ce-work/`. Outside Jujutsu, use `<current-directory>/.tmp/rocketclaw/ce-work/`. Include only Request, Goal, Scope, Acceptance and verification, Constraints and exclusions, and conservative units. Never include raw conversation history, unrelated context, or credentials. Initialize with its digest; the controller-owned copy is authoritative afterward.

## Serial Protocol

Resolve bundled scripts from this skill's directory and run one state-changing controller transition per host tool call until scope inspection. `start` returns before supervision. Bound each wait to 60 seconds, then synchronize and report progress separately. A nonzero controller, runner, verification, or Jujutsu result stops that host call and enters the recorded recovery path.

1. Resolve and sanction the fixed route. If none qualifies, disclose the candidate outcomes and continue natively without initializing a controller run.
2. Initialize with `unit-workspace.py init`. State lives under `<workspace-root>/.tmp/rocketclaw/ce-work/<run-id>/`; do not pre-create the run directory. A plan may be the sole change. Checkpoint it with `checkpoint-plan --description "<message composed from the standards above>"`. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Local conventions and visible history win. A prompt-backed run requires an empty canonical working-copy change.
3. Prepare one bounded unit packet beneath the controller-returned recovery path. Call `prepare` with the canonical revision, dependencies, wave fields, and activity posture. Use only returned packet, digest, authorization, attempt, workspace, and result paths.
4. Start one fixed author through `peer-job-runner.py start --no-sweep --input-digest <digest>`. Use the returned adapter directly with its controller arguments. The adapter must complete `authorize-dispatch` before egress, and `record-job` must bind the same runner job. Use the existing hard and idle windows; never hold one host call open for the runtime.
5. Observe with bounded runner `status`/`wait` calls and separate `sync-job` calls. Do not steer, duplicate, or fall back while the attempt is live.
6. On authoritative `done`, call `terminalize`. Inspect the pinned worker revision, complete changed-path inventory, binary/type evidence, result receipt, packet scope, and any scope-expansion request in a later host call. Unexpected scope blocks integration while preserving the workspace.
7. Call `integrate --run-id <run-id> --unit-id <unit-id> --description "<message composed from the standards above>" --verification-summary <summary> [--allowed-revision <revision>] -- <verification argv>`. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Local conventions and visible history win. Use direct verification argv unless the check genuinely requires shell syntax, in which case invoke an explicit pipefail-capable shell.
8. `integrate` acquires the lock, preflights repository and wave state, restores only the pinned worker fileset into the canonical working-copy change, records application, runs authoritative verification, proves the fileset unchanged, records verification, describes the canonical change, records its revision, starts a new empty canonical change, cleans the worker workspace, and releases the lock.
9. A failed verification or pre-description transition restores the exact pre-integration revision under the lock. If restoration cannot be proven, preserve the lock, worker workspace, transport revision, and recovery path. Ignored files are inventoried by metadata and disclosed but never copied, restored, or deleted.
10. After all units are accepted, run source-wide checks with `verify-run`. It requires an empty canonical working-copy change, captures exit status directly, restores tracked verification artifacts to the recorded revision, discloses ignored-state divergence, and records a durable receipt.

Project each transition into commentary or the return envelope: source, route, checkpoint, dispatch, activity, terminal result, transport/scope inspection, integration, restoration, authoritative verification, canonical revision, cleanup, blocker, and recovery path.

## Parallel Waves

Use a wave only when the always-loaded safety check proves units independent across dependencies, paths, shared contracts, migrations, lockfiles, generated/config surfaces, environment singletons, and expected integration cost. Uncertainty selects serial execution. Cap a wave at 3-5 workers.

Prepare all members from one canonical revision and terminalize all of them before integrating any. Inspect every fileset first; same-path or semantic contention blocks the wave. Integrate sequentially in dependency order. After each accepted revision, pass that exact revision through `wave-advance`; later members may preflight only against controller-recorded allowed revisions. Every member gets independent scope inspection, verification, description, and canonical revision. Any conflict or failed restoration stops dependent work.

## Resume And Fallback

Use an explicit run id when supplied. Otherwise discover a plan-backed run by canonical repository identity, workspace name, and plan digest. Zero matches permits a new run; multiple matches block selection. Prompt-backed runs require their disclosed id.

Resume reconciles durable evidence but never redispatches accepted work or runs a shipping tail. It may synchronize a recorded job, terminalize authoritative output, report preserved integration state, or expose the exact recovery command. A completed run with a successful source-wide receipt is observation-only.

Cleanup is idempotent and forgets the Jujutsu workspace before removing its filesystem tree. Explicit abandonment requires the exact pinned revision or terminal job id. A retry keeps the run id and uses a fresh attempt id without changing dependency or wave/base contracts.

After authoritative failure or exact restoration and lock release, `claim-fallback` authorizes native implementation once. After local verification, describe the native change and advance the canonical workspace to a new empty change. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Local conventions and visible history win. Call `complete-fallback --accepted-revision <revision>`, then run `verify-run` after all units are terminal.

The engine changes implementation authorship only. Standalone use resumes `ce-work`'s quality and shipping tail. Return-to-caller mode returns local implementation evidence with `standalone_shipping_skipped: true`. External workers inherit neither tail.
