# Cross-Model Execution Contract

Load this reference only after the cross-model engine is selected or recovery of an existing external run is activated. It defines fixed-route authority, bounded egress, JJ workspace isolation, operation-backed integration, receipts, and recovery. Detached process completion is never integration evidence.

## Fixed Route And Authority

Use only targets `codex`, `claude`, `grok`, `cursor`, and `composer`. Keep target, harness/intermediary route, requested model, served model, and receipt status separate. Controller route tokens are exactly `codex`, `claude`, `grok-cli`, `cursor`, `composer`, and `grok-cursor`.

Resolve live intent, caller binding, project instruction, and `.rocketclaw` configuration as `references/execution-engines.md` specifies. Preflight ordered candidates without egress. Once dispatch starts, one sanctioned route and model remain fixed until the controller records authoritative terminal or reaped state. A same-host default request collapses to native execution; a distinct same-host model does not.

Both `prefer` and `require` fall back to the current host/session model when the requested route is observably unavailable. `require` forbids substituting another external recipient; it does not elevate permissions, block forever, or prompt for a replacement.

Before egress, disclose and record the binding source, route and intermediaries, requested model, exposed unit material, restrictions, and enforcement posture. JJ workspaces isolate filesystem edits and changes, not OS permissions or secrets. A restriction the adapter cannot enforce makes that route unavailable.

The worker receives one unit, one controller-owned JJ workspace, one fixed recipient, and inherited authority only. It may edit and run scoped checks, but it must not describe, split, squash, rebase, abandon, bookmark, restore operations, push, open a PR, schedule peers, or broaden scope. The host alone inspects the worker's working-copy change, rebases it, resolves or rejects conflicts, verifies it, composes its description, advances the local bookmark, and publishes.

## Durable State And Temporary Paths

All run state, prompt briefs, packets, logs, locks, adapter scratch, and detached-job state live under `$(jj workspace root)/.tmp/ce-work/`. If `jj workspace root` is unavailable before a workspace is established, use local `.tmp/ce-work/`. Create private run directories atomically and point subprocess temporary-directory configuration at the workspace `.tmp`; use no other temporary root or global temporary-file allocator.

The controller records repository identity, canonical workspace name/root, starting operation ID, canonical working-copy change and commit IDs, feature bookmark, source kind/digest, route sanction, and per-unit receipts. Recovery paths always point into the canonical workspace's `.tmp/ce-work/` tree.

A formal plan is optional for a concrete bare prompt. Write its bounded brief under the workspace `.tmp` root with headings `Request`, `Goal`, `Scope`, `Acceptance and verification`, `Constraints and exclusions`, and conservative `Units`. Do not include raw conversation, credentials, unrelated context, or speculative scope. If goal, scope, or authoritative verification cannot be bounded, clarify or plan before egress.

## JJ Preconditions

Require a writable JJ workspace and a uniquely resolved mutable integration base. Record the canonical operation with `jj op log`, inspect `@` and its parents with `jj log`, inspect paths with `jj diff -r @ --name-only`, and inspect conflicts with `jj log -r '@ & conflicts()'`.

The external route starts only when the canonical working-copy change is empty and conflict-free. If the selected plan is the sole working-copy content, checkpoint it as its own described JJ change with an explicit fileset, then create a new empty working-copy change. Unrelated pre-work content makes the external route unavailable; preserve it in its original change or workspace rather than stashing, restoring, or folding it into controller work.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Project instructions and the syntax and style visible in `git log` win. Do not impose fixed types, scopes, prefixes, or canned text. Apply the composed text as the JJ change description.

## External Unit Transaction

Run one ready unit at a time unless the parallel-wave gate below passes. Resolve bundled scripts from this skill's directory. Use `jj -R <canonical-workspace>` for host repository operations and pass only controller-returned paths, IDs, and digests.

1. Initialize with `unit-workspace.py init`, the repository source or bounded prompt brief, exact digest, binding object, and egress object. The egress object uses exact plural keys `route`, `intermediaries`, and `restrictions`.
2. If the selected plan is the only working-copy content, call `checkpoint-plan --change-description <composed-description>`. Otherwise require an empty canonical `@` with no `conflicts()`.
3. Prepare one bounded packet. `prepare` creates a sibling JJ workspace under `<root>/.tmp/ce-work/runs/<run-id>/units/<unit-id>/workspace` with a unique workspace name and a new working-copy change parented to the recorded base change. Include dependencies, expected fileset, evidence strategy, wave identity/position, and activity posture.
4. Start the fixed adapter through `peer-job-runner.py` using the controller-returned authorization path, workspace, packet path/digest, result directory, run ID, unit ID, and attempt ID. Set `CE_PEER_HARD_SECS=7200`; use `CE_PEER_IDLE_SECS=600` only for trustworthy incremental activity and `0` for hard-only routes.
5. Observe in separate calls with runner `status`/bounded `wait` and controller `sync-job`. A live or temporarily unreachable job remains authoritative. Never duplicate work or switch recipient in flight.
6. On authoritative `done`, call `terminalize`. It snapshots the worker workspace through JJ, rejects divergent or conflicted worker changes and unexplained fileset expansion, and pins stable change ID plus current commit ID, parent, fileset, and diff digest. The workspace change itself is the transport; no synthetic transport reference exists.
7. Inspect the complete change with `jj diff -r <change-id>`, `jj show`, root-relative filesets, and `conflicts()`. A worker summary is evidence, not scope authority.
8. Call `integrate --change-description <composed-description> --verification-summary <summary> -- <verification argv>`. The controller acquires the integration lock, records the pre-integration operation, rebases the stable worker change ID onto the advancing accepted change, and blocks if the resulting change is divergent or has first-class conflicts.
9. The controller switches the canonical workspace to a new empty change on top of the rebased unit change, runs authoritative verification there, and proves the working-copy change stayed empty and conflict-free. It then applies the composed description, records the rewritten commit ID, moves the feature bookmark, records acceptance, and releases the integration lock. Only after acceptance is durable does it forget and remove the worker workspace; cleanup failure remains resumable and never rolls back accepted work.
10. Any failed graph mutation, conflict, verification, or description/bookmark step restores the recorded repository operation with `jj op restore`, updates stale workspaces with `jj workspace update-stale`, proves the canonical operation view and working-copy snapshot match the pre-integration receipt, and preserves the worker change/recovery path. If exact restoration cannot be proved, retain the lock and block.
11. After all units are accepted, run source-wide gates through `verify-run`. It requires an empty conflict-free canonical working-copy change atop every accepted unit, records the starting operation, runs direct argv, and restores the operation if verification mutates repository state. Ignored artifacts are disclosed, not deleted.

When a verification expression needs shell syntax, invoke an explicit shell with pipe-failure behavior as the verification argv. Do not rely on shell expansion inside a direct argv element.

## Parallel Waves

Use a wave only when dependencies, declared filesets, shared contracts/interfaces, migrations, lockfiles, generated/config surfaces, runtime singletons, and expected reconciliation cost all support independence. Cap concurrency at 3-5.

Every member starts from one recorded base change in its own JJ workspace and terminalizes before any integration. Reject path collisions before mutation and treat semantic overlap as a host decision even when filesets are disjoint. Integrate sequentially in dependency order by rebasing each stable change ID onto the advancing accepted change. JJ may record conflicts without failing the rebase; `conflicts()` is therefore a mandatory stop, not an optional error check. Repeated collision or restoration failure disables further waves.

## Recovery And Fallback

Direct recovery uses the supplied safe run ID. Plan-backed discovery uses exact repository identity plus plan digest and blocks on multiple matches; prompt-backed runs require their disclosed run ID. Never enumerate a shared global run root or select a sibling clone's run.

Resume may adopt one matching runner job, monitor it, terminalize completed output, finish a recorded integration, restore a recorded operation, finalize accepted-change cleanup, or report stored receipts. It must not redispatch, reimplement, rerun completed verification, or enter a shipping tail.

After authoritative failure/reap and any exact operation restoration, `claim-fallback` authorizes native implementation once. Live jobs, successful unreconciled output, unresolved conflicts, or retained integration locks refuse fallback. After native implementation is accepted and verified, `complete-fallback` records stable change/commit IDs, operation evidence, fileset, and evidence digest; then `verify-run` closes the run.

Explicit abandonment requires the exact terminal job ID or stable transport change ID. Cleanup forgets only the controller-owned JJ workspace and removes only controller-owned `.tmp` artifacts after accepted or explicitly abandoned state.

## Receipts And Tail Ownership

Return the binding, requested/actual route and model, fallback reason, source kind/digest, run ID, workspace/change/operation receipts, plan checkpoint change, blockers, and recovery path. A unit is complete only when its accepted stable change ID, current commit ID, parent relationship, description, bookmark target, verification receipt, cleanup receipt, and operation evidence reconcile.

Standalone mode resumes quality review and shipping. Return-to-caller mode returns implementation and local-verification receipts with `standalone_shipping_skipped: true`. External workers inherit neither tail.
