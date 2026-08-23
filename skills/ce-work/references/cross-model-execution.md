# Cross-Model Execution Contract

Load only after selecting cross-model execution or activating recovery. The host drives the bundled controller, detached runner, and adapter. Worker output or process exit never substitutes for controller and Jujutsu evidence.

## Route And Authority

Use targets `codex`, `claude`, `grok`, `cursor`, and `composer`. Fixed controller route tokens are exactly `codex`, `claude`, `grok-cli`, `cursor`, `composer`, and `grok-cursor`. Keep target, harness/intermediary route, requested model, actual model, and receipt status separate.

For an ordered preference, preflight candidates in order without egress. Skip only an equivalent same-host default or an observed unavailable route. Local help may refine a compatible adapter only inside the sanctioned harness/model family while preserving every restriction. An explicit model pin cannot become another model. Once dispatch starts, the recipient and intermediary are fixed.

Cross-model routes are write- and shell-capable. Never broaden host permissions merely to make one reachable. `prefer` and `require` both disclose an unavailable route once and continue on the current harness and session model without elevating or substituting another external recipient. Requirement strength keeps the requested external identity fixed while viable; a started attempt remains authoritative until terminal or reaped evidence permits fallback.

Before egress, disclose and durably record the binding source, fixed recipient/provider/harness/intermediaries, exposed repository and unit material, caller restrictions, and enforcement posture. A Jujutsu workspace isolates concurrent edits but is not an OS security boundary. An unenforceable required restriction makes the route unavailable rather than silently weaker.

The worker receives one unit and one controller-owned Jujutsu workspace. It cannot broaden scope, describe/finalize or rewrite changes, move bookmarks, publish, open a PR, schedule peers, or choose fallback. The host owns canonical composition, authoritative verification, dynamic description, and the shipping tail. A sandbox permission failure is evidence about that sandbox, not proof that the host lacks the capability.

## Storage And Workspaces

Resolve the canonical root with `jj workspace root`. Controller state lives at `<workspace-root>/.tmp/rocketclaw/work-runs/<run-id>/`; bounded prompt and packet sources live at `<workspace-root>/.tmp/rocketclaw/work-inputs/<run-id>/`. Outside Jujutsu, use `<cwd>/.tmp/rocketclaw/` and block repository integration. Never use OS-global or environment-selected temporary storage.

The controller creates each external unit as a sibling with `jj workspace add --name <owned-name> -r <recorded-base> <owned-path>`. It records workspace name/path, base change and snapshot IDs, and operation ID. Cleanup uses `jj workspace forget <owned-name>` followed by owner-checked removal. Existing workspaces remain eligible because siblings are not nested.

Every controller invocation excludes `.tmp/rocketclaw/**` from Jujutsu automatic tracking. Do not add repository files solely to ignore controller state.

## Bare-Prompt Source

For a concrete bare prompt, create a bounded brief under `.tmp/rocketclaw/work-inputs/<run-id>/` with Request, Goal, Scope, Acceptance and verification, Constraints and exclusions, and conservative units. Do not include raw conversation history, credentials, unrelated context, or speculative scope. Compute its SHA-256 and initialize from that source. If goal, scope, or verification cannot be grounded, clarify or plan before egress.

## Controller Protocol

Use separate host calls for transitions until scope inspection. Runner waits are bounded and followed by controller synchronization. A nonzero controller, runner, Jujutsu, or verification result stops that transition and enters status/recovery.

1. **Resolve, preflight, and sanction.** Apply `execution-engines.md`. Record every rejected ordered candidate. The `init` egress object uses exact plural keys `route`, `intermediaries`, and `restrictions`; direct routes use `intermediaries: []`, while `composer` and `grok-cursor` use `intermediaries: ["cursor"]`.
2. **Initialize.** Call `unit-workspace.py init` with the canonical workspace, binding, egress sanction, and plan or prompt digest. A selected plan may be checkpointed only when it is the sole canonical working-copy change. Unrelated canonical changes make the route unavailable. The controller creates its own run directory; do not pre-create it. A successful `READY` locks that unit to the selected engine until explicit controller fallback authority.
3. **Checkpoint the plan when eligible.** Supply a dynamically composed `--change-description` only for the exact plan-only checkpoint.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; do not impose fixed syntax or content.

4. **Prepare one bounded packet.** Write it directly under `.tmp/rocketclaw/work-inputs/<run-id>/`, then call `prepare` with the recorded base, dependencies, wave fields, and activity posture. Include only the active unit's authority, expected paths, evidence strategy, and explicit exclusions. Use only the returned attempt id, packet path/digest, workspace name/path, authorization, and adapter.
5. **Dispatch one fixed author.** Call `peer-job-runner.py start --no-sweep --input-digest <controller-packet-digest>` with skill `ce-work`; the label equals the unit id and the result path is `<controller-result-dir>/implementation-result.json`. The adapter receives the same digest and only controller-returned paths. Set `PEER_HARD_SECS=7200`; use `PEER_IDLE_SECS=600` for qualified incremental activity and `PEER_IDLE_SECS=0` for hard-only activity. Invoke the adapter directly, without a shell prefix. The runner exports `PEER_JOB_ID` and `PEER_PYTHON`. Before egress, the adapter must obtain `authorize-dispatch`; then `record-job` idempotently confirms the same binding.
6. **Observe without steering.** Interleave runner `status` or waits capped at 60 seconds with controller `sync-job`. Every bare job query carries `--skill ce-work` under the same `WORK_RUNS_ROOT` / `PEER_JOBS_ROOT` selection. Report route, elapsed time, activity posture, meaningful activity, and terminal state. A live or temporarily unreachable attempt is authoritative; do not duplicate it. Hard-only silence is not failure.
7. **Terminalize.** On authoritative completion, the controller runs `jj util snapshot`, records immutable working-copy change and snapshot evidence, and derives actual paths with `jj diff --summary -r <change>`. Inspect actual scope, modes, renames, deletions, result evidence, and semantic contention before composition. Unexplained scope remains preserved and blocks composition.
8. **Integrate.** Invoke the fail-stop transaction with a dynamic description and direct verification argv:

```text
unit-workspace.py integrate --run-id <run-id> --unit-id <unit-id> --change-description <description> --verification-summary <summary> [--allowed-change <change-id>] -- <verification-argv>
```

The compatibility interface also accepts `--commit-message` for `--change-description` and `--allowed-head` for `--allowed-change`; these names do not change Jujutsu semantics. Shell syntax in a verification command requires an explicit shell with pipe-failure handling rather than passing the expression as literal argv.

9. **Let the transaction own canonical mutation.** It acquires the composition lock, snapshots and validates `@`, restores the accepted transport snapshot into the canonical working-copy change, verifies, proves the resulting change, runs `jj describe -m <dynamic-description>`, records finalized change/snapshot IDs, runs `jj new`, and then cleans up and releases. Compatibility command names `integration-acquire`, `mark-applied`, `mark-committed`, and `integration-release` alias the Jujutsu-native composition transitions; they do not introduce a separate staging model.
10. **Treat its outcome as authoritative.** Capture exit status directly. Bookmark, workspace identity, accepted-ancestor, description, parent, or changed-path divergence fails reconciliation. Untracked/ignored state is inventoried and disclosed separately as both `untracked_state` and the compatibility field `ignored_state`; the controller does not delete or restore user caches. On failure, restore from the recorded pre-fold snapshot with `jj restore --from <snapshot> --into @`, restore the prior description, and prove exact state before release. If proof fails, retain lock, workspace, evidence, and recovery path.
11. **Verify the run.** After all units are accepted, call `verify-run` for source-wide gates. It starts from a clean current working-copy change, records before/after operation and change evidence, restores only verification-created owned tracked state, blocks on graph/bookmark mutation, and stores a durable receipt. A failing gate retains its private log and blocks either tail.

Project every transition into commentary or the return envelope: source, route, plan checkpoint, dispatch, activity, terminal result, transport/scope inspection, composition, restoration, authoritative verification, canonical change, cleanup, blocker, and recovery path.

## Parallel Waves

Prepare independent members from one recorded base and terminalize all before the first composition. Reject path collisions and semantic contention before canonical mutation. Compose sequentially in dependency order. After each accepted change, record `wave-advance` with the exact finalized change ID and revalidate remaining transports against the advancing graph. The compatibility option `--canonical-commit` aliases `--canonical-change`. Conflict, scope expansion, failed verification, or unprovable restoration stops affected units and dependents; repeated collision or broad edits disables later waves.

## Recovery And Fallback

`resume --run-id <id>` is authoritative when supplied. Otherwise plan-backed discovery uses canonical workspace identity plus plan digest and selects exactly one unfinished run; prompt-backed recovery requires the run id. Resume may adopt one matching unbound job, monitor a live job, terminalize completed output, continue exact restoration, or reconcile a dynamically described change whose IDs match evidence. It never redispatches, repeats completed verification, or enters a shipping tail.

Completed recovery is observation-only when all units are terminal and a successful source-wide receipt exists. Missing evidence is a blocker, not authority for improvised verification. Ambiguous matching runs are listed with recovery paths and block selection.

Cleanup is idempotent and owner-checked. Explicit abandonment requires the exact transport change ID or terminal job id. A corrected retry keeps the same run id and uses a fresh attempt id after exact restoration, cleanup, and lock release.

Post-start native fallback requires an atomic `claim-fallback`. After authoritative failure, timeout, `died-without-result`, or exact restoration and lock release, disclose the unavailable route once. The first `prefer` or `require` claim authorizes exactly one fallback on the current harness and session model; a live job or successful unreconciled output refuses it. After native completion, authoritative verification, and a dynamically described Jujutsu change, call `complete-fallback` with the accepted change ID, evidence digest, and summary. The compatibility option `--accepted-head` aliases `--accepted-change`. Then run `verify-run` before completion.

## Receipts And Tail

Return the exact engine binding; requested and actual route/model identities and receipt status; fallback reason; source kind/digest; run id; per-unit process, composition, verification, canonical-change, and cleanup receipts; plan checkpoint change; blockers; and recovery path. Standalone use resumes quality/shipping. Return-to-caller sets `standalone_shipping_skipped: true` and yields exactly once. External workers inherit neither tail.
