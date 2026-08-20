# Shipping Workflow

Load after implementation tasks complete.

## Phase 3: Quality

1. Run the project's full relevant test and lint gates from active instructions.
2. Invoke `ce-simplify-code` when the substantive code delta meets the repository's normal threshold; skip mechanical/small deltas with reason.
3. Invoke `ce-code-review` as the portable review path. Retain a completed receipt or one documented mechanical/unavailable/harness-fallback skip phrase. Non-complete receipts enter the unavailable path; mental self-review is not a receipt.
4. Apply eligible findings through `references/review-findings-followup.md`. Unresolved actionable findings must be fixed, filed through `references/tracker-defer.md`, accepted into a durable PR Known Residuals section, or explicitly reported when no durable sink exists. Settlement-invalidating findings block.
5. Reconcile every plan requirement, deferred implementation question, test/lint result, design check, runtime warning, and changed path against the Jujutsu delta.
6. Prepare `Post-Deploy Monitoring & Validation` PR content with signals, failure/rollback triggers, window, and owner, or a one-line no-runtime-impact rationale.

Interactive residual decisions use the harness blocking question capability and offer apply, file, accept-and-record, or stop. Headless runs automatically apply mechanically eligible findings and durably route the remainder without prompting.

## Phase 4: Ship

### Validation Context

Record observable behavior and manual validation. Use harness-native evidence capture only when requested or already available. Do not launch a branded evidence workflow.

### Final Change Descriptions

Before editing, validating, recommending, or handing off any final Jujutsu change description:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; do not impose a fixed syntax. Use neutral operations such as `jj describe -m "<description derived from active project instructions and runtime jj log>"`. Confirm every described change is scoped, verified, and free of unrelated pre-work.

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
