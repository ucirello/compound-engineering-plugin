# Apply Code Review Findings

Load when `ce-code-review` has finished and the caller should apply fixes before the Residual Work Gate. Review is read-only in this context; the caller owns apply policy, authoritative verification, and Jujutsu change descriptions.

## Consume The Existing Review

Do not rerun review when its output is already in hand. Reuse parsed `mode:agent` JSON or the markdown Actionable Findings summary plus the artifact directory. If status is `failed`, stop shipping and surface the reason. If it is `degraded`, preserve the lost-coverage disclosure before applying anything.

Only a cold caller with no review output invokes `ce-code-review` once:

```text
ce-code-review mode:agent plan:<plan-path> base:<merge-base-or-revision>
```

Use `plan:` when a plan governed implementation, `base:` when the comparison base is already resolved, and never pass deprecated autofix modes. Human-facing callers may use the default markdown output but must retain its Actionable Findings and artifact path.

## Inputs

- `actionable_findings` from JSON or the markdown Actionable Findings section
- Full finding details from `review.json` or the relevant reviewer artifact when needed
- Stable finding number/fingerprint for worker prompts, descriptions, and residual sinks

## Apply Or Defer

Default to applying every actionable finding whose evidence still matches and whose concrete suggested fix is a clear improvement. Confidence and autofix classification prioritize and flag work; they do not grant authority. Push back when the reviewer is wrong. Apply clear fixes involving sensitive surfaces only with prominent verification evidence.

Defer advisory findings, findings without a concrete fix, and findings whose correct resolution needs product, design, architecture, or contract authority. Surface each deferral and its reason; never silently drop one.

## Batched Fix Workers

The orchestrator filters structured fields, groups eligible findings by file, dispatches disjoint file groups in parallel only when the active harness provides isolated Jujutsu-aware workspaces, inspects actual changes, verifies them, and dynamically describes accepted fix changes. It does not pre-investigate cited files merely to decide whether to dispatch.

For each batch, give the worker only assigned finding IDs, severity, file/line, title, suggested fix, verification requirement, and useful evidence. The worker:

- processes findings in severity order;
- confirms evidence still matches before editing;
- applies only fixes within inherited authority and skips others with a reason;
- does not rerun `ce-code-review`;
- does not describe/finalize changes, move bookmarks, publish, or ship; and
- returns applied/skipped IDs, reasons, and changed paths.

Group all eligible findings for one file into one worker. Split more than about eight findings for one file into serial passes. Co-batch multiple files only when findings explicitly share one small edit surface. Shared-workspace execution is serial.

After each wave, inspect `jj diff --summary` and `jj diff` against assigned findings, run targeted checks whenever an applied finding requires verification and broader checks for multi-file behavior changes, then finalize the accepted logical fix change with a dynamic description.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; do not impose fixed syntax or content. Use `jj describe -m "<description derived from active project instructions and runtime jj log>"`, followed by `jj new` only after the accepted change is described.

## Optional Inline Shortcut

Apply inline only when exactly one eligible finding remains and the orchestrator already has that file's relevant region in context from this run. Otherwise dispatch a worker, even for one finding.

## Required Summary And Handoff

Report batches, finding IDs applied or skipped with reasons, review artifact, checks, and resulting change IDs. Every actionable finding not applied enters the Residual Work Gate. Rerun review only after fixes materially changed the reviewed delta.
