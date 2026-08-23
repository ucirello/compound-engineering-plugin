# Execution Strategy and Native Dispatch

Read this after the engine is resolved and before dispatching any worker or scheduling a parallel wave. The kernel owns the route-resolution and WIP/write gates; the selected engine owner carries any engine-specific lock. This file owns how native work is scheduled, packaged, dispatched, and integrated.

For the inline/subagent engine, **prefer subagents for any structured multi-unit plan** — each worker gets a fresh context window for one unit. **Parallelize independent units whenever it is safe**; fall back to serial only when parallel isn't safe or the harness can't isolate concurrent writes. Let the plan's `Dependencies` and `Files` drive batching: run an independent dependency layer together, then the next.

| Strategy | When to use |
|----------|-------------|
| **Inline** | Trivial work (1-2 files, no real decomposition), work needing user interaction mid-flight, or bare prompts that lack structured units |
| **Serial subagents** | The default for structured multi-unit plans whose units are dependent, few, or whose parallel-safety is uncertain. Fresh context per unit, executed in dependency order |
| **Parallel subagents** | Independent units (per the Parallel Safety Check) when you want the speed and the harness can isolate concurrent work. Run a dependency layer at once, then the next |

**Parallel Safety Check** — scheduling is separate from engine and workspace selection. Apply this gate to native and cross-model candidates before dispatching a wave:

1. Start only with units whose dependencies are already accepted as canonical Jujutsu changes and whose peers in the same readiness layer do not depend on one another.
2. Map declared files to units from each candidate's `Files:` section, then reason beyond those declarations. File overlap is necessary but not sufficient: shared types/APIs/interfaces, migrations, lockfiles, generated artifacts/clients, registry or config/schema surfaces, and an environment singleton (one dev server/port, shared database, browser session, package install, or rate limit) all create contention.
3. Estimate expected merge and verification cost. Even isolated workers serialize when they share a contract or when reconciling their likely outputs is not obviously smaller and safer than serial authoring.
4. Dispatch together only when dependencies, declared files, semantic surfaces, runtime resources, and expected merge cost all support independence; **decline parallelism on uncertainty**. Speed is optional.
5. Require an isolated workspace for every concurrent worker. A synchronous native unit stays in the active workspace, but a shared-workspace worker runs serially regardless of declared file disjointness.
6. Cap concurrency at a bounded batch (~3-5 workers), even when more units appear independent.
7. Abort criteria: broad unplanned edits, semantic overlap, out-of-scope failures, or repeated collision disables further waves; preserve or finish affected work serially.

Isolation for native workers is the harness's job, under the body's boundary. Probe what your native subagent mechanism provides and pick the parallel path:
- **Harness-native isolated workers** - each worker edits an isolated Jujutsu-aware workspace the harness manages and returns a receipt confirming that isolation. Parallelize only units that pass the Safety Check; isolation makes recovery possible, not overlap safe.
- **Shared workspace only** — subagents edit your working directory. Run them serially. Do not infer isolation from the presence of a subagent API; use only a capability the active harness actually exposes.
- **No subagent mechanism:** run inline.

**Native dispatch (inline/subagent engines only)** uses your harness's subagent/worker mechanism. Once a unit is selected for cross-model execution, use the loaded controller protocol for that unit; it must not re-enter this ordinary subagent dispatch.

Classify a rejected native dispatch by whether a worker launched: correct a pre-launch argument rejection once, leave capacity-limited work queued, and if another launch failure survives correction, execute that unit inline under the same unit packet and verification contract.

**Fresh worker invariant (native subagent dispatch only):** When dispatching an implementation unit to a native subagent worker, create a new worker context with no prior implementation-unit transcript. Bind the worker handle to exactly that unit: it may continue or recover the same unit, but never receive a different unit. Retire each handle after its unit is integrated; never retask it or retain idle implementation workers for reuse. Invoke an explicit close/release operation only when the active harness exposes one and assigns that lifecycle action to the caller. Inline execution creates no worker context or handle, so it has nothing to retire.

Give each native worker:
- The plan path plus a **bounded unit packet** and inherited authority — Goal Capsule, Definition of Done, the unit's section, the Verification Contract entries relevant to it, any referenced R/F/AE/KTD excerpts, **plus any Product Contract Key Decision whose `Governs R…` links name the unit's cited R-IDs** (its `session-settled:` annotation reaches the worker only through this reverse link — cited KTDs alone carry only planning-decision labels). A downstream worker may narrow that unit and authority, never broaden either. Do not send "read the whole plan" as the worker prompt. (For a legacy non-unified plan, the plan path for reference is acceptable.)
- The unit's Goal, Files, Approach, Execution note, Patterns, Test scenarios, Verification, and any resolved deferred questions for it.
- Instruction to check whether the unit's test scenarios cover all applicable categories (happy paths, edge cases, error paths, integration) and supplement gaps before writing tests.
- **Instruction to choose the unit's evidence strategy and gather the evidence** (see Evidence Strategy in Phase 2) — for behavior-bearing changes, honor the Execution note and default to proof-first or characterization-first: create/update/strengthen the test and observe the red failure or characterization baseline **before** changing production code. The worker is the only party that witnesses this, so it must capture it as it goes.
- **Instruction to report, in its final message, both (a) the file paths it changed and (b) the unit's verification evidence** — `behavior_changed`, existing tests inspected, tests added/changed or used unchanged, the red failure or characterization observed (when applicable), the verification run and result, and any deliberate no-test exception with its reason. The handoff is a text summary on most harnesses with no guaranteed diff, so reported paths are the orchestrator's starting hint (it still verifies the actual tree); the evidence fields are **not** reconstructable from the tree afterward, so a worker that omits them forces the orchestrator to re-derive or leave `verification_evidence` incomplete.
- **Do not finalize changes.** Ordinary native workers implement and may run their own unit's focused tests in isolation, but the orchestrator owns authoritative verification and final Jujutsu descriptions. External workers leave the working-copy change undescribed; controller snapshots are transport evidence, never canonical accepted changes. If a harness destroys isolated work on completion, follow its explicit persistence contract rather than inventing one.

**Parallel subagent mode:** Description and composition ownership remains with the orchestrator. Harness-isolated workers return their workspace result for dependency-ordered composition; shared-workspace workers run serially.

**Shared-workspace constraints** - workers must not describe/finalize changes, move bookmarks, rewrite the change graph, or run the full test suite concurrently. A worker may run one focused unit check only when it touches no shared state. Shared-workspace execution is serial.

**Permission mode:** Omit the `mode` parameter when dispatching subagents so the user's configured permission settings apply. Do not pass `mode: "auto"` — it overrides user-level settings like `bypassPermissions`.

**After each serial inline/subagent unit:** inspect `jj diff --summary` and `jj diff` against the unit scope, run authoritative checks, fix before the next unit, record verification evidence, update the task list, and finalize the logical Jujutsu change through `references/implementation-loop.md`. If a native worker ran, retire its handle before dispatching the next unit.

**After a parallel inline/subagent batch — the orchestrator integrates; never trust the handoff summary alone:**
1. Wait for every worker in the batch to finish.
2. **Inspect the actual change, not reported paths.** Use `jj status`, `jj diff --summary`, and `jj diff` in its workspace. Reported paths are a hint; declared `Files:` are often incomplete.
3. **Detect real collisions and semantic contention** — compare actual paths plus shared contracts, generated/config surfaces, and verification effects. A clean merge is not proof of compatibility. Preserve or re-run colliding units on the advancing canonical base; never blind-merge them.
4. **Review, test, compose, describe, and retire each unit in dependency order.** Integrate one result, inspect actual scope, run authoritative verification, accept its canonical Jujutsu change with a dynamic description, then retire that worker. Clean up only when the harness assigns cleanup to the caller and only after proving composition. Revalidate every remaining result against the advancing change graph. Capture worker evidence without fabricating observations the worker omitted.
5. Update the task list; progress lives in task state and described changes.
6. Dispatch the next dependency layer only after every unit in the batch has been integrated and its worker retired. Any remaining isolated-workspace cleanup follows the active harness's ownership and lifecycle contract.

**Per-harness integration (examples — the universal flow above is the contract):**
- **Harness-owned Jujutsu workspace:** compose one working-copy change in dependency order, verify, and describe it before the next; on conflict preserve evidence and rerun or explicitly resolve against the advanced graph.
- **Harness-owned uploaded change set:** accept one isolated result, inspect and verify it, compose it canonically, then release the worker before the next result.
- **Shared workspace:** no parallel batch is permitted; use the serial path.
- **External cross-model workspace:** follow the conditionally loaded cross-model parallel-wave protocol and controller receipts; ad hoc graph operations do not apply.
