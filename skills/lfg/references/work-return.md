# Reading ce-work's structured return (LFG step 2)

LFG's SKILL.md lets only a valid `status: complete` return advance; every other status or malformed return stops the pipeline. This file defines how to validate a complete return: what the route binding means, which fields are required, what the verification evidence must contain, and the one recovery invocation.

## Missing-owner blocked return

When `ce-work` cannot re-read the reference file that defines its return after it has already created partial state, it returns a reduced blocked result from its SKILL.md. Accept that reduced result as a valid terminal blocker, not as a malformed complete return. It contains `status: blocked`, `plan_path`, `run_id` when known, `changed_state`, `blockers`, and `recovery_path`. Preserve those recovery facts and stop; the complete-return field inventory below does not apply to this failure shape.

## What each route outcome means

`ce-work` discloses an unavailable route once and continues natively under both `prefer` and `require` (its `cross-model-execution.md` defines that behavior), so LFG decides the route outcome from the return fields rather than expecting `ce-work` to refuse. A return whose `implementation_engine_binding.mode` is `require` and whose `actual_route` differs from `requested_route` stops the pipeline as blocked, reporting `requested_route`, `actual_route`, and `fallback_reason`; `require` is the caller's instruction, and work done natively against it does not ship. A completed `prefer` fallback may continue to step 3 exactly once after prominently disclosing its requested-versus-actual route/model and `fallback_reason` to the user; fallback is not a reason to invoke implementation again.

## What `status: complete` must carry

Verify that implementation work was performed: files were created or modified beyond the plan. Require `status`, `plan_path`, `changed_files`, `u_ids_attempted`, `u_ids_completed`, `verification_results`, `verification_evidence`, `source_kind`, `source_digest`, `settled_decision_conflicts`, `behavior_change`, and `standalone_shipping_skipped: true`. The source fields must identify the same plan authority that entered the implementation run. `source_digest` is the digest the controller recorded, or null on a native run. On a one-pass statement, `plan_path` is null, `source_kind` is `prompt`, and `u_ids_attempted` and `u_ids_completed` are empty arrays. A recovery invocation repeats the statement unchanged in place of the plan path. Evidence and conflict fields are present on every complete return; empty arrays are valid when their conditions did not occur.

Also require the fields that record which route actually ran: `implementation_engine_binding`, `requested_route`, `actual_route`, `requested_model`, `actual_model`, `fallback_reason`, `run_id`, `unit_receipts`, `plan_checkpoint`, `blockers`, and `recovery_path`. These fields are required even when native execution makes some values `null`. Together they carry where the binding came from, requested-versus-actual identity, fallback, the durable run, per-unit process/integration/verification/commit state, checkpoint disclosure, blockers, and recovery. A resumed return must carry the same `run_id`; never treat resume as permission to start a new unit or a second LFG shipping run.

## Native route interpretation

Apply `references/stage-routing.md`'s native dispatch contract before interpreting legacy route labels. Actual execution is native OpenCode; requested harness identity is not evidence that harness ran. Preserve requested/actual model, permission and fallback disclosures, unit receipts, recovery identity and verification. A requirement for an unavailable harness/model or missing required independence stops shipping. A disclosed preference fallback must not cause a second implementation run.

## The work must be committed

Before step 3, confirm the return's `changed_files` are committed in JJ history. JJ automatically tracks eligible files; inspect `jj status`, `jj diff`, ignored/untracked paths and conflicts rather than assuming Git staging semantics. Commit only owned paths with `jj commit <paths> -m <composed-description>` and continue, preserving unrelated edits. Run all repository commands from the target absolute workspace root, never using `-R` as a cwd substitute. Do not create new isolation when an existing harness-owned workspace already supplies it; delegate any needed workspace lifecycle to `ce-worktree` and its dated naming, explicit colocation, ownership and guarded removal rules. Keep scratch and error artifacts under local `.tmp/`.

### Runtime commit composition (all local composition sites)

Read this entire section before composing any local description. Set `workspace_root` to the verified absolute target workspace root.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Verbatim source guidance, subordinate to actual repository syntax and not a mandatory template:

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

Read the full https://go.dev/wiki/CommitMessage at runtime, and read several recent full subjects and bodies from actual verified repository history with `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\\n"')`. Verify the history head first; never assume a fixed remote bookmark. Compare multiple examples for actual repository syntax, which takes precedence over Go guidance. Describe the specific change and rationale, not a canned conventional message. Source guidance only: “The first line of the commit message is conventionally a one-line summary of the change, prefixed by the primary affected package.” Source guidance only: “The rest of the message should provide context for the change and explain what it does.” Do not add attribution or Signed-off-by trailers. Use `jj describe -m <repository-style-description>` only for the verified owned revision, or the path-limited commit above; do not rewrite unrelated history.

## Verification evidence

When `behavior_change: true`, `verification_evidence` must name the relevant units/tasks, existing tests inspected, tests added/changed or used unchanged, red failure or characterization evidence when applicable, verification run, and any deliberate test exception. Do NOT decide the test strategy inside LFG; the evidence is ce-work's contract.

Also read `settled_decision_conflicts` from the return: blocker-routed entries arrive as `status: blocked` and stop the pipeline. **Record any proceeded-and-flagged entries**: they must reach step 6's lasting record of unapplied findings and step 9's PR-description context, since later review may not rediscover them.

## The one recovery invocation

If `behavior_change: true` but `verification_evidence` is missing or too vague to tell how behavior was protected, invoke `ce-work` one more time in recovery mode. Reuse the same `implementation_engine:<compact-json>` carrier when one existed and keep the same plan path. With a safe non-null `run_id`, add `implementation_run:<safe-id>` with that exact value from the first return. When `actual_route` is `native` and `run_id` is `null`, repeat the original ce-work invocation once without an `implementation_run:` carrier; this preserves the pre-existing native idempotency/evidence-reconciliation path. A non-native return without a safe run id remains blocked instead of attempting discovery or a second implementation. Do not prompt the user and do not alter the plan path or engine carrier; this is evidence reconciliation, not a fresh dispatch. The recovery relies on ce-work's reconciliation path to inspect the already-implemented work, fill the missing evidence, and return without reimplementing. If the second return still lacks coherent verification evidence, stop as blocked and report the missing fields instead of continuing to simplify/review/ship.
