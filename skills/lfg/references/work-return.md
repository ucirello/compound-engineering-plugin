# Reading ce-work's structured return (LFG step 2)

LFG's SKILL.md lets only a valid `status: complete` return advance; every other status or malformed return stops the pipeline. This file defines how to validate a complete return: what the route binding means, which fields are required, what the verification evidence must contain, and the one recovery invocation.

## Missing-owner blocked return

When `ce-work` cannot re-read the reference file that defines its return after it has already created partial state, it returns a reduced blocked result from its SKILL.md. Accept that reduced result as a valid terminal blocker, not as a malformed complete return. It contains `status: blocked`, `plan_path`, `run_id` when known, `changed_state`, `blockers`, and `recovery_path`. Preserve those recovery facts and stop; the complete-return field inventory below does not apply to this failure shape.

## What each route outcome means

`ce-work` resolves configured/requested routes with `opencode.models` and native subagents, preserving legacy route labels as intent rather than launching another harness. An unavailable requirement-strength route must block; a permission denial must not trigger an evasion or repeated call. LFG also checks the returned evidence: a return whose `implementation_engine_binding.mode` is `require` and whose actual route/model fails the requested requirement stops as blocked, reporting `requested_route`, `actual_route`, and `fallback_reason`. A completed permitted `prefer` fallback may continue to step 3 exactly once after prominently disclosing its requested-versus-actual route/model and `fallback_reason`; fallback is not a reason to invoke implementation again. Required cross-model coverage that did not run remains incomplete.

## What `status: complete` must carry

Verify that implementation work was performed: files were created or modified beyond the plan. Require `status`, `plan_path`, `changed_files`, `u_ids_attempted`, `u_ids_completed`, `verification_results`, `verification_evidence`, `source_kind`, `source_digest`, `settled_decision_conflicts`, `behavior_change`, and `standalone_shipping_skipped: true`. The source fields must identify the same plan authority that entered the implementation run. `source_digest` is the digest the controller recorded, or null on a native run. On a one-pass statement, `plan_path` is null, `source_kind` is `prompt`, and `u_ids_attempted` and `u_ids_completed` are empty arrays. A recovery invocation repeats the statement unchanged in place of the plan path. Evidence and conflict fields are present on every complete return; empty arrays are valid when their conditions did not occur.

Also require the fields that record which route actually ran: `implementation_engine_binding`, `requested_route`, `actual_route`, `requested_model`, `actual_model`, `fallback_reason`, `run_id`, `unit_receipts`, `plan_checkpoint`, `blockers`, and `recovery_path`. These fields are required even when native execution makes some values `null`. Together they carry where the binding came from, requested-versus-actual identity, fallback, the durable run, per-unit process/integration/verification/commit state, checkpoint disclosure, blockers, and recovery. A resumed return must carry the same `run_id`; never treat resume as permission to start a new unit or a second LFG shipping run.

## The work must be committed

Before step 3, confirm the return's `changed_files` are tracked in JJ and included in the implementation change. Inspect `jj status` and `jj diff` from the absolute workspace root, including ignored/untracked files that were not automatically tracked. Explicitly track only intended new files with `jj file track -- <owned-paths>` when necessary. If the implementation still needs a described checkpoint, read `message-standards.md` and commit only those files using its dynamically composed message; preserve unrelated edits. Do not stop merely because a checkpoint is needed.

## Verification evidence

When `behavior_change: true`, `verification_evidence` must name the relevant units/tasks, existing tests inspected, tests added/changed or used unchanged, red failure or characterization evidence when applicable, verification run, and any deliberate test exception. Do NOT decide the test strategy inside LFG; the evidence is ce-work's contract.

Also read `settled_decision_conflicts` from the return: blocker-routed entries arrive as `status: blocked` and stop the pipeline. **Record any proceeded-and-flagged entries**: they must reach step 6's lasting record of unapplied findings and step 9's PR-description context, since later review may not rediscover them.

## The one recovery invocation

If `behavior_change: true` but `verification_evidence` is missing or too vague to tell how behavior was protected, invoke `ce-work` one more time in recovery mode. Reuse the same `implementation_engine:<compact-json>` carrier when one existed and keep the same plan path. With a safe non-null `run_id`, add `implementation_run:<safe-id>` with that exact value from the first return. When `actual_route` is `native` and `run_id` is `null`, repeat the original ce-work invocation once without an `implementation_run:` carrier; this preserves the pre-existing native idempotency/evidence-reconciliation path. A non-native return without a safe run id remains blocked instead of attempting discovery or a second implementation. Do not prompt the user and do not alter the plan path or engine carrier; this is evidence reconciliation, not a fresh dispatch. The recovery relies on ce-work's reconciliation path to inspect the already-implemented work, fill the missing evidence, and return without reimplementing. If the second return still lacks coherent verification evidence, stop as blocked and report the missing fields instead of continuing to simplify/review/ship.
