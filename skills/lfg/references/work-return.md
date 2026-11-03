# Reading ce-work's structured return (LFG step 2)

LFG's SKILL.md lets only a valid `status: complete` return advance; every other status or malformed return stops the pipeline. This file defines how to validate a complete return: what the route binding means, which fields are required, what the verification evidence must contain, and the one recovery invocation.

## Missing-owner blocked return

When `ce-work` cannot re-read the reference file that defines its return after it has already created partial state, it returns a reduced blocked result from its SKILL.md. Accept that reduced result as a valid terminal blocker, not as a malformed complete return. It contains `status: blocked`, `plan_path`, `run_id` when known, `changed_state`, `blockers`, and `recovery_path`. Preserve those recovery facts and stop; the complete-return field inventory below does not apply to this failure shape.

## What each route outcome means

`ce-work` discloses an unavailable route once and continues natively under both `prefer` and `require` (its `cross-model-execution.md` defines that behavior), so LFG decides the route outcome from the return fields rather than expecting `ce-work` to refuse. A return whose `implementation_engine_binding.mode` is `require` and whose `actual_route` differs from `requested_route` stops the pipeline as blocked, reporting `requested_route`, `actual_route`, and `fallback_reason`; `require` is the caller's instruction, and work done natively against it does not ship. A completed `prefer` fallback may continue to step 3 exactly once after prominently disclosing its requested-versus-actual route/model and `fallback_reason` to the user; fallback is not a reason to invoke implementation again.

## What `status: complete` must carry

Verify that implementation work was performed: files were created or modified beyond the plan. Require `status`, `plan_path`, `changed_files`, `u_ids_attempted`, `u_ids_completed`, `verification_results`, `verification_evidence`, `source_kind`, `source_digest`, `settled_decision_conflicts`, `behavior_change`, and `standalone_shipping_skipped: true`. The source fields must identify the same plan authority that entered the implementation run. On a one-pass statement, `plan_path` is null, `source_kind` is `prompt`, `source_digest` is the digest the controller recorded or null on a native run, and `u_ids_attempted` and `u_ids_completed` are empty arrays. A recovery invocation repeats the statement unchanged in place of the plan path. Evidence and conflict fields are present on every complete return; empty arrays are valid when their conditions did not occur.

Also require the fields that record which route actually ran: `implementation_engine_binding`, `requested_route`, `actual_route`, `requested_model`, `actual_model`, `fallback_reason`, `run_id`, `unit_receipts`, `plan_checkpoint`, `blockers`, and `recovery_path`. These fields are required even when native execution makes some values `null`. Together they carry where the binding came from, requested-versus-actual identity, fallback, the durable run, per-unit process/integration/verification/commit state, checkpoint disclosure, blockers, and recovery. A resumed return must carry the same `run_id`; never treat resume as permission to start a new unit or a second LFG shipping run.

## The work must be committed

`ce-code-review` leaves out untracked files, so files this run added go unreviewed until they are committed. Before step 3, confirm the return's `changed_files` are committed. If any are not, commit only those paths from the absolute target workspace using `jj commit <owned-paths> -m "<message composed from the standards above>"` and continue. Before composing, follow the runtime full Go-guide read and recent full subject/body history comparison in `references/review-followup.md`: **Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.** Resolve the actual history head and run `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Repository instructions/history syntax win; no invented precedent if history is unavailable. Do not stop for this.

### Illustrative Go source for message composition — not a mandatory template

These verbatim source excerpts supplement, but never replace, the mandatory FULL runtime Go-guide read before composing. Repository instructions and observed history determine the emitted syntax; do not copy this example as a prescribed message.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,
```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```
> Notably, for the subject (the first line of description):
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).
> For the body (the rest of the description):
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.

## Verification evidence

When `behavior_change: true`, `verification_evidence` must name the relevant units/tasks, existing tests inspected, tests added/changed or used unchanged, red failure or characterization evidence when applicable, verification run, and any deliberate test exception. Do NOT decide the test strategy inside LFG; the evidence is ce-work's contract.

Also read `settled_decision_conflicts` from the return: blocker-routed entries arrive as `status: blocked` and stop the pipeline. **Record any proceeded-and-flagged entries**: they must reach step 6's lasting record of unapplied findings and step 9's PR-description context, since later review may not rediscover them.

## The one recovery invocation

If `behavior_change: true` but `verification_evidence` is missing or too vague to tell how behavior was protected, invoke `ce-work` one more time in recovery mode. Reuse the same `implementation_engine:<compact-json>` carrier when one existed and keep the same plan path. With a safe non-null `run_id`, add `implementation_run:<safe-id>` with that exact value from the first return. When `actual_route` is `native` and `run_id` is `null`, repeat the original ce-work invocation once without an `implementation_run:` carrier; this preserves the pre-existing native idempotency/evidence-reconciliation path. A non-native return without a safe run id remains blocked instead of attempting discovery or a second implementation. Do not prompt the user and do not alter the plan path or engine carrier; this is evidence reconciliation, not a fresh dispatch. The recovery relies on ce-work's reconciliation path to inspect the already-implemented work, fill the missing evidence, and return without reimplementing. If the second return still lacks coherent verification evidence, stop as blocked and report the missing fields instead of continuing to simplify/review/ship.
