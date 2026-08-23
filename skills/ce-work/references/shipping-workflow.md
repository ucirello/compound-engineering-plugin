# Shipping Workflow

Load after implementation tasks complete.

## Phase 3: Quality

1. Run the project's full relevant test and lint gates from active instructions.
2. Invoke `ce-simplify-code` when the substantive code delta meets the repository's normal threshold; skip mechanical/small deltas with reason.
3. Invoke `ce-code-review` as the portable review path, with `mode:agent`, `plan:<path>` when known, `base:<revision>` when resolved, and `depth:full` when the plan, task, or user explicitly requested a deep review. Retain a completed receipt (`status: complete` plus `artifact_path` or `run_id`) or exactly one authorized skip phrase with a one-line reason: `Code review: skipped (mechanical diff)`, `Code review: skipped (ce-code-review unavailable)`, or, interactive only after a real harness-native review, `Code review: harness-native fallback`. A `failed`, `degraded`, or `skipped` response is not a completed receipt. Mental self-review, prior findings, and ad hoc skimming are not receipts.
4. Apply eligible findings through `references/review-findings-followup.md`. Unresolved actionable findings must be fixed, filed through `references/tracker-defer.md`, accepted into a durable PR Known Residuals section, or explicitly reported when no durable sink exists. Settlement-invalidating findings block.
5. Reconcile every plan requirement, deferred implementation question, test/lint result, design check, runtime warning, and changed path against the Jujutsu delta.
6. Prepare `Post-Deploy Monitoring & Validation` PR content with signals, failure/rollback triggers, window, and owner, or a one-line no-runtime-impact rationale.

Interactive residual decisions use the harness blocking question capability and offer apply, file, accept-and-record, or stop. Headless runs automatically apply mechanically eligible findings and durably route the remainder without prompting.

Purely mechanical means formatting, dependency-version bumps, lint-only fixes, or generated artifacts, including multi-file mechanical changes. Behavior, control flow, error classes, behavior tests, and review-finding fixes are not mechanical.

When review cannot complete, interactive runs may use a real harness-native review and the exact fallback phrase. Headless runs use the unavailable phrase and add an explicit manual diff scan to final validation. Never silently ship a non-mechanical change without review evidence or an authorized skip.

## Residual Work Gate

After applying findings, every unapplied actionable finding must be resolved or durably recorded before final validation. Settlement-invalidating evidence is a blocker and is never auto-accepted.

In an interactive run, ask once with these choices: apply/fix now; file tickets through `references/tracker-defer.md`; accept and record in the PR's `Known Residuals` section or another durable sink; or stop without shipping. In a headless run, apply mechanically eligible findings, then record the remainder in the PR's `Known Residuals` section or through `references/tracker-defer.md`. When no durable sink is reachable, return the findings verbatim and state that they are recorded nowhere else.

Do not leave this gate until the destination of every residual is known. Skip it only when there are no actionable findings or dedicated review itself was legitimately skipped.

## Phase 4: Ship

### Validation Context

Record observable behavior and manual validation. Use harness-native evidence capture only when requested or already available. Do not launch a branded evidence workflow.

### Final Change Descriptions

Before editing, validating, recommending, or handing off any final Jujutsu change description:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; do not impose fixed syntax or content. Use neutral operations such as `jj describe -m "<description derived from active project instructions and runtime jj log>"`. Confirm every described change is scoped, verified, and free of unrelated pre-work.

### Publish Handoff

The review completion gate must pass before publishing. Do not publish changes the user did not offer: compare the recorded pre-work change IDs/paths, local bookmark targets, and remote bookmark targets. If unpublished pre-work is not already part of the intended review stack, keep this run local and offer publishing on request.

Project-defined shipping instructions win. Otherwise route through the existing `ce-commit-push-pr` provider for publishing/PR creation or `ce-commit` for local-only finalization, while explicitly telling the provider that the authoritative local state is Jujutsu changes/bookmarks/workspaces and that it must use only Jujutsu operations. If a provider cannot honor that constraint, stop and report the unavailable handoff rather than translating repository state through another VCS.

Pass plan summary, checks, evidence, review receipt/skip, monitoring plan, accepted residuals, excluded pre-work paths/change IDs, and any requested stack topology. Do not add workflow identity metadata.

Publishing moves or creates only the intended Jujutsu bookmark at the accepted final change, then uses the configured Jujutsu remote publishing operation. Jujutsu has no active bookmark; never publish `@` by assumption. Re-fetch and resolve bookmark conflicts before retrying. PR creation follows project conventions and spans only the intended bookmark ancestry.

Back-fill the resulting PR URL into filed residual tickets when possible. Report completed work, accepted change IDs, bookmark/PR URL when created, checks, residuals, and blockers.

## Completion Checklist

- Tasks, requirements, and deferred questions reconciled
- Tests, lint, behavior coverage, design/runtime checks recorded
- Simplification and review gates completed or explicitly skipped
- Residual findings durably resolved or recorded
- Jujutsu delta contains no unoffered pre-work
- Every final description follows active project instructions, runtime `jj log` syntax, and compatible Go quality guidance
- Intended bookmark target verified explicitly before publishing
- PR includes summary, checks, evidence, monitoring, and residuals
