# Cross-Model Execution Contract

Load only after selecting cross-model execution or activating recovery. The host drives the bundled controller, detached runner, and adapter. Worker output or process exit never substitutes for controller and Jujutsu evidence.

## Route And Authority

Resolve target, harness/intermediary, requested model, actual model, and receipt status independently. Fixed route tokens remain `codex`, `claude`, `grok-cli`, `cursor`, `composer`, and `grok-cursor`. A route may adapt to current local help only inside the sanctioned harness/model family while preserving every restriction. Once dispatch starts, it cannot switch recipient or intermediary.

`prefer` may continue natively only after preflight proves all candidates unavailable or the controller authorizes one post-start fallback. `require` asks an interactive standalone caller before native fallback; headless/automatic callers return blocked.

Before egress, disclose and durably record the binding source, recipient and intermediaries, exposed repository/unit material, restrictions, and enforcement posture. A Jujutsu workspace isolates concurrent edits but is not an OS security boundary.

The worker receives one unit and one controller-owned Jujutsu workspace. It cannot broaden scope, finalize or rewrite changes, move bookmarks, publish, open a PR, schedule peers, or choose fallback. The host owns canonical composition, authoritative verification, change description, and the shipping tail.

## Storage And Workspaces

Resolve the canonical root with `jj workspace root`. Controller state lives at `<workspace-root>/.tmp/work-runs/<run-id>/`; bounded prompt and packet sources live at `<workspace-root>/.tmp/work-inputs/<run-id>/`. If no Jujutsu root exists, use `<cwd>/.tmp/` and block repository integration. Never use OS-global temporary storage or environment-selected temporary roots.

The controller creates each external unit as a sibling with `jj workspace add --name <owned-name> -r <recorded-base> <owned-path>`. It records workspace name, path, base change/snapshot IDs, and operation ID. Cleanup uses `jj workspace forget <owned-name>` followed by owner-checked removal of the controller-owned directory. An existing Jujutsu workspace remains eligible because siblings are not nested.

Keep `.tmp` outside automatic snapshots by supplying the controller's Jujutsu auto-track exclusion on every controller invocation. Do not add repository files solely to ignore controller state.

## Bare-Prompt Source

For concrete bare prompts, create a bounded brief under `.tmp/work-inputs/<run-id>/` with Request, Goal, Scope, Acceptance and verification, Constraints and exclusions, and conservative units. Do not include raw conversation history or speculative scope. Compute its SHA-256 and initialize the controller with that source. If goal, scope, or verification cannot be grounded, clarify or plan before egress.

## Controller Protocol

Use separate host calls for state transitions until scope inspection. Runner waits are bounded and followed by controller synchronization. A nonzero controller, runner, Jujutsu, or verification result stops the current transition and enters status/recovery.

1. **Initialize.** Call `unit-workspace.py init` with the canonical workspace, binding, egress sanction, and plan or prompt digest. A selected plan may be checkpointed only when it is the sole canonical working-copy change. Unrelated canonical changes make the external route unavailable. Before supplying its neutral `--change-description` placeholder: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; do not impose a fixed syntax.
2. **Prepare.** Write one bounded packet under `.tmp/work-inputs/<run-id>/`, then call `prepare` with the recorded base, dependencies, wave fields, and activity posture. Use only returned packet, digest, attempt id, workspace name/path, and authorization.
3. **Dispatch.** Start `peer-job-runner.py` with skill `ce-work`, exact packet digest, returned adapter, and returned paths. Use `WORK_RUNS_ROOT`, `PEER_JOBS_ROOT`, `PEER_HARD_SECS`, and `PEER_IDLE_SECS`; controller and runner derive the same repository-local root. The runner exports `PEER_JOB_ID` and `PEER_PYTHON`.
4. **Observe.** Poll runner status/wait and call controller `sync-job`. A live or unreachable attempt remains authoritative until terminal/reaped evidence exists.
5. **Terminalize.** On authoritative completion, controller snapshots the unit workspace with `jj util snapshot`, records the workspace working-copy change and snapshot IDs as immutable transport evidence, and derives actual paths from `jj diff --summary -r <change>`. Inspect actual scope and semantic contention before integration.
6. **Integrate.** Invoke the fail-stop `integrate` transaction with a dynamically composed `--change-description` and direct verification argv.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; do not impose a fixed syntax. The command shape is neutral:

```text
unit-workspace.py integrate --run-id <run-id> --unit-id <unit-id> --change-description <description> --verification-summary <summary> -- <verification-argv>
```

The transaction acquires the canonical lock, snapshots and validates `@`, records an operation checkpoint, restores the accepted transport tree into the canonical working-copy change, runs authoritative verification, proves the resulting change, runs `jj describe -m <description>`, records the finalized change/snapshot IDs, then runs `jj new` for the next unit. A wave advances later units by exact accepted change IDs. Cleanup and lock release follow only after durable receipts.

Verification must not move bookmarks, change workspace identity, rewrite accepted ancestors, or alter the canonical working-copy change beyond expected verification artifacts. On failure, restore canonical content from the recorded pre-fold snapshot with `jj restore --from <pre-fold-snapshot> --into @`, restore the prior description, and prove exact IDs/content before release. If proof fails, retain lock, workspace, operation evidence, and recovery path.

After all units are accepted, run `verify-run` for plan-wide gates. It starts from a clean current working-copy change, records before/after operation and change evidence, removes only verification-created paths under the owned delta, and blocks on graph or bookmark mutation. Untracked cache/assets remain disclosed but are not deleted or restored.

## Parallel Waves

Prepare every independent member from one recorded base and terminalize all before composition. Reject path collisions and semantic contention before canonical mutation. Compose sequentially in dependency order. After each accepted change, record wave advancement with its exact finalized change ID and revalidate every remaining transport against the advancing graph. Any conflict, scope expansion, failed verification, or unprovable restoration stops affected units and dependents.

## Recovery And Fallback

`resume --run-id <id>` is authoritative when supplied. Plan-backed discovery uses canonical workspace identity plus plan digest and must select exactly one unfinished run. Prompt-backed recovery requires the run id. Resume may reconcile recorded jobs, terminalize completed output, continue exact restoration, or finalize a described change whose IDs match evidence; it never redispatches or enters a shipping tail.

Cleanup is idempotent and owner-checked. Explicit abandonment requires the exact transport change ID or terminal job id. A corrected retry keeps the same run id and uses a fresh attempt id after exact restoration, cleanup, and lock release.

Post-start native fallback requires an atomic `claim-fallback`. After native completion, authoritative verification, and a dynamically described Jujutsu change, call `complete-fallback` with the accepted change ID, evidence digest, and summary. Then run `verify-run` before reporting completion.

## Receipts And Tail

Return binding, route/model identities, fallback reason, source kind/digest, run id, per-unit process/composition/verification/change/cleanup receipts, plan checkpoint change, blockers, and recovery path. Standalone use resumes `ce-work` quality/shipping. Return-to-caller sets `standalone_shipping_skipped: true` and yields exactly once.
