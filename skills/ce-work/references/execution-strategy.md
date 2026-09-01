# Execution Strategy

Choose serial or parallel execution from dependencies, file ownership, shared contracts, and verification interference. Isolation changes recovery mechanics, not whether overlapping work is safe.

Runtime-local Jujutsu syntax wins, and fixed message templates are forbidden.

For the inline/subagent engine, **prefer subagents for any structured multi-unit plan** — each worker gets a fresh context window for one unit. **Parallel dispatch of each independent dependency layer is the default, not an optimization to opt into**: serialize writes only where the dependency graph actually demands it, and only for the specific units that demand it. Let the plan's `Dependencies` and `Files` drive batching: run an independent dependency layer together, then the next. Serializing a whole plan is justified only by a genuinely linear dependency chain, or by units that can neither meet the shared-workspace wave contract below nor obtain an isolated workspace — never by blanket caution.

## Safety Check

Parallelize only ready units whose dependencies are accepted and whose expected edits are disjoint across files, interfaces, migrations, lockfiles, generated/registry/config surfaces, environment singletons, and test state. Inspect actual files and contracts to resolve uncertainty. Serialize only the units whose contention survives inspection, and dispatch the rest of the layer together. Cap a wave at 3-5 workers, and batch related work when a unit is too small to repay its worker's context ramp-up.

| Strategy | When to use |
|----------|-------------|
| **Inline** | Trivial work (1-2 files, no real decomposition), work needing user interaction mid-flight, or bare prompts that lack structured units |
| **Parallel subagents** | The default for structured multi-unit plans: dispatch each dependency layer's independent units (per the Parallel Safety Check) together, then the next layer — in harness-isolated workspaces, or in the shared workspace under the wave contract below |
| **Serial subagents** | Units the dependency graph genuinely chains, or units that fail the Parallel Safety Check — including the shared-workspace wave contract, where that is the workspace — after inspection. Fresh context per unit, executed in dependency order |

## Isolation

- Inline and shared-directory workers edit the canonical Jujutsu workspace. Give each a fileset boundary; the orchestrator reviews, verifies, splits/squashes, and describes the resulting change.
- Host-native isolated workers use the host's workspace capability only when its receipt confirms a usable isolated Jujutsu workspace. The orchestrator integrates returned revisions in dependency order.
- External cross-model workers use only the controller-owned Jujutsu workspaces and transaction in `references/cross-model-execution.md`.

Isolation for native workers is the harness's job, under the body's boundary. Probe what your native subagent mechanism provides and pick the parallel path:
- **Harness-native isolated workers** — each worker edits an isolated Jujutsu workspace the harness manages. Being inside an isolated workspace does not block this route, but a harness-supplied workspace is not automatically a faithful snapshot of the active revision and local working-copy state may not survive isolation. Dispatch each worker with the intended base revision; before editing, the worker verifies that base and stops on mismatch. The orchestrator then runs that unit in the shared workspace under the wave contract or serially. A unit that depends on unrecorded local state cannot use this route. Parallelize only units that pass the Safety Check; isolation makes recovery possible, not overlap safe.
- **Shared workspace only** — subagents edit your working directory. Dispatch a parallel wave only when it meets the shared-workspace wave contract below; units that cannot meet it run serially. Do not infer isolation from the presence of a subagent API; use only a capability the active harness actually exposes.
- **No subagent mechanism:** run inline.

Workers receive one unit, its dependencies, expected files, verification, inherited constraints, and explicit exclusions. They may edit and run focused checks within that scope. The orchestrator owns canonical integration, authoritative verification, descriptions, bookmarks, push, and shipping.

**Dispatch a wave in one response.** When a dependency layer clears the Safety Check, first privately list every dispatch-ready unit; then issue every worker dispatch that doesn't depend on another's result in that one response — multiple dispatch tool calls in a single message (e.g. Claude Code `Agent` calls), never one per turn.

**Native dispatch (inline/subagent engines only)** uses your harness's subagent/worker mechanism. Once a unit is selected for cross-model execution, use the loaded controller protocol for that unit; it must not re-enter this ordinary subagent dispatch.

## Unit Completion

After each serial unit, inspect `jj diff -r @` against the unit scope, run authoritative checks, repair failures before starting the next unit, record verification evidence, and update the task list without editing the plan body. Finish the logical unit as a focused Jujutsu change, then start a new working-copy change for subsequent work.

**Fresh worker invariant (native subagent dispatch only):** When dispatching an implementation unit to a native subagent worker, create a new worker context with no prior implementation-unit transcript. Bind the worker handle to exactly that unit: it may continue or recover the same unit, but never receive a different unit. Retire each handle after its unit is integrated; never retask it or retain idle implementation workers for reuse. Invoke an explicit close/release operation only when the active harness exposes one and assigns that lifecycle action to the caller; otherwise completion is the worker's release boundary. Inline execution creates no worker context or handle, so it has nothing to retire.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Use the repository's current local syntax; do not impose a fixed type, scope, prefix, footer, or body template.

Give each native worker:
 - The plan path plus a **bounded unit packet** and inherited authority — Goal Capsule, Definition of Done, the unit's section, the Verification Contract entries relevant to it, any referenced R/F/AE/KTD excerpts, **plus any Product Contract Key Decision whose `Governs R…` links name the unit's cited R-IDs** (its `session-settled:` annotation reaches the worker only through this reverse link — cited KTDs alone carry only planning-decision labels). A downstream worker may narrow that unit and authority, never broaden either. Do not send "read the whole plan" as the worker prompt. (For a legacy non-unified plan, the plan path for reference is acceptable.)
 - The unit's Goal, Files, Approach, Execution note, Patterns, Test scenarios, Verification, and any resolved deferred questions for it.
 - Instruction to check whether the unit's test scenarios cover all applicable categories (happy paths, edge cases, error paths, integration) and supplement gaps before writing tests.
 - **Instruction to choose the unit's evidence strategy and gather the evidence** (see Evidence Strategy in Phase 2) — for behavior-bearing changes, honor the Execution note and default to proof-first or characterization-first: create/update/strengthen the test and observe the red failure or characterization baseline **before** changing production code. The worker is the only party that witnesses this, so it must capture it as it goes.
 - **Instruction to report, in its final message, both (a) the file paths it changed and (b) the unit's verification evidence** — `behavior_changed`, existing tests inspected, tests added/changed or used unchanged, the red failure or characterization observed (when applicable), the verification run and result, and any deliberate no-test exception with its reason. The handoff is a text summary on most harnesses with no guaranteed diff, so reported paths are the orchestrator's starting hint (it still verifies the actual tree); the evidence fields are **not** reconstructable from the tree afterward, so a worker that omits them forces the orchestrator to re-derive or leave `verification_evidence` incomplete.
 - **Do not perform repository operations.** Ordinary native workers implement and may run their own unit's focused tests in isolation as a self-check, but the orchestrator owns descriptions, splits, squashes, rebases, bookmarks, integration, and authoritative test runs. External cross-model workers leave their Jujutsu working-copy changes for the controller transaction.

## Parallel Completion

**Shared-workspace wave contract** — a parallel wave in a shared working directory is permitted only while all of these hold; a unit that cannot meet one serializes or gets isolation:

- **Recorded baseline.** Dispatch the wave from a known Jujutsu revision, so each worker's output is attributable by fileset and an aborted wave can restore worker-owned changes to that baseline.
- **Exclusive ownership, including hidden write surfaces.** Beyond the disjoint declared files the Safety Check already verified, every hidden write surface — lockfiles, generated artifacts, snapshots, formatter sweeps, package manifests — is either excluded from all workers or assigned to exactly one.
- **No worker repository operations.** Workers must not describe, split, squash, rebase, bookmark, or advance changes. The orchestrator separates worker-owned filesets after the batch.
- **Orchestrator-owned verification.** Workers run no mutating verification (full suites, installs, builds that write shared state); a worker may run a single focused unit test only if it touches no shared state. The authoritative run happens after the wave on the integrated tree.
- **Abort on unowned writes.** A write outside every worker's exclusive set aborts the wave and disables further shared-workspace waves for the run. Restore to the baseline only changes attributable to a worker; a change no worker accounts for may be the user's — preserve it and stop for reconciliation rather than discarding it.

Inspect actual Jujutsu filesets rather than trusting reported paths. Same-path edits or shared-contract contention stop automatic integration. Integrate one accepted result at a time, revalidate remaining results against the advancing canonical revision, run authoritative checks, describe the focused canonical change, and release the worker only after integration is proven.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Use the repository's current local syntax; do not impose a fixed type, scope, prefix, footer, or body template.

**After each serial inline/subagent unit:** review `jj diff -r @` against the unit's scope and `Files:`, run relevant tests, repair failures before starting the next unit, record verification evidence, and update the task list without editing the plan body. Finish the unit as a focused Jujutsu change. If a native subagent ran it, retire its handle per the fresh worker invariant before dispatching the next unit in a new worker context. Inline units have no worker handle.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Use the repository's current local syntax; do not impose a fixed type, scope, prefix, footer, or body template.

**After a parallel inline/subagent batch — the orchestrator integrates; never trust the handoff summary alone:**
 1. Wait for every worker in the batch to finish.
 2. **Inspect actual Jujutsu filesets, not reported paths.** Reported paths are a hint; declared `Files:` are often incomplete.
 3. **Detect real collisions and semantic contention** — compare actual paths plus shared contracts, generated/config surfaces, and verification effects. A clean merge is not proof of compatibility. Preserve or re-run colliding units on the advancing canonical base; never blind-merge them.
 4. **Review, verify, describe, and retire each unit in dependency order.** Integrate one result, inspect actual scope, run authoritative verification, describe its focused canonical change, and immediately retire that worker per the fresh worker invariant. Clean up an isolated workspace only when the harness assigns cleanup to the caller and integration is proven. Revalidate every remaining result against the advancing canonical revision. Capture returned verification evidence; if a worker omitted evidence, re-derive only what the fileset proves and mark the rest unverified.
 5. Update the task list without editing the plan body.
 6. Dispatch the next dependency layer only after every unit in the batch has been integrated and its worker retired. Any remaining isolated-workspace cleanup follows the active harness's ownership and lifecycle contract.

In a shared canonical workspace, workers never describe, split, squash, rebase, bookmark, or advance changes. The orchestrator separates each owned fileset after the wave. In isolated workspaces, workers leave their working-copy changes undescribed unless the host's isolation contract explicitly requires a described revision for return; even then, the orchestrator applies local description standards before publication.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Use the repository's current local syntax; do not impose a fixed type, scope, prefix, footer, or body template.

**Per-harness integration (examples — the universal flow above is the contract):**
- **Harness-owned isolated workspace:** apply one returned revision in dependency order, verify, and describe the canonical change before the next.
- **Harness-owned uploaded fileset:** accept one result, inspect and verify it, describe it canonically, then release the worker before the next result.
- **Shared workspace:** ownership decides who may write a path, never what a delta is. Attribute each delta from worker reports and fileset inspection, and split or restore only worker-attributed changes. Preserve any unaccounted delta and stop for reconciliation. Verify and describe in dependency order.
- **External cross-model workspace:** follow the conditionally loaded cross-model parallel-wave protocol and controller receipts; ordinary revision-application shortcuts do not apply.

On conflict, preserve the isolated revision and either rerun it on the new base or resolve it explicitly. Never treat a conflict-free fileset application as semantic compatibility.
