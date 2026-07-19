# Apply Code Review Findings (after `ce-code-review`)

Load this reference when `ce-code-review` has finished and **ce-work** (or another caller) should apply fixes before the Residual Work Gate.

`ce-code-review` is invoked here with `mode:agent`, so it is **review-only** in this context — it reports findings and writes artifacts and does not mutate the workspace, describe changes, move bookmarks, push, or file tickets. **The caller owns apply/fix policy.**

## Consume the completed review (do not re-run it)

This reference loads **after** review has run. In the ce-work shipping flow, step 3a already invoked `ce-code-review`; this apply step **consumes that output** — do not start a second review, which would waste reviewer dispatches and risk overwriting the artifact the Residual Work Gate reconciles.

Reuse the review output already in hand:

- Parsed JSON (`status`, `actionable_findings`, `findings`, `artifact_path`, `run_id`) **or** the markdown Actionable Findings summary captured by the caller
- Run artifact dir: `<workspace-root>/.tmp/rocketclaw/ce-code-review/<run-id>/` (`review.json`, per-reviewer JSON for `why_it_matters`). Resolve `<workspace-root>` with `jj workspace root`, falling back to `pwd -P`.

If `status` is `failed`, stop shipping and surface `reason`. If `degraded`, note partial reviewer coverage before applying anything.

### Fallback — invoke review only for cold callers

Only when the caller reached this file **without** already running review (no review output in hand): invoke `ce-code-review` once, then proceed to apply. Do not invoke when the caller already ran review (e.g., ce-work shipping step 3a).

Invoke the skill explicitly — do not treat a casual "review my changes" prompt as a substitute unless it was routed to `ce-code-review`.

```
ce-code-review mode:agent plan:<plan-path> base:<jj-revision-or-revset>
```

- `mode:agent` — JSON output (`review.json` + primary JSON response) for programmatic parsing; same review pipeline as default.
- `plan:` — when Phase 1 used a plan file (requirements completeness).
- `base:` — when the stack base is already resolved from JJ history; omit when reviewing a pull-request number/URL or the standalone current stack.
- Do **not** pass deprecated `mode:autofix`.

For human / interactive shipping, invoke `ce-code-review` without `mode:agent` if markdown tables are preferred. Capture the same JSON / Actionable Findings and artifact dir listed above before applying.

## Inputs for apply

- `actionable_findings` from JSON, or the Actionable Findings section from markdown
- Full finding detail when needed: `review.json` / artifact `findings`, or `{reviewer}.json` for `why_it_matters` and `evidence`
- Stable finding `#` — reuse in JJ descriptions, residual sinks, and subagent prompts

## What to apply

Default to applying every actionable finding. Applying is a reversible edit to a tracked tree; JJ diffs are reviewed before closing the change boundary and tests run after, so leaving a clear fix unapplied "to be safe" is the failure mode. Bias to act:

- **Apply** any finding with a concrete `suggested_fix` that is a clear improvement — the common case. `confidence` and `autofix_class` tell you what to prioritize and what to flag, not whether you may apply: `autofix_class` is signal, **never permission**.
- **Push back** — keep the finding, don't apply — when the reviewer is wrong; note why.
- **Flag, don't block, green-but-unverifiable edits** — when an applied fix touches auth/authz, a public or cross-service contract/schema, or concurrency, a passing test does not prove safety; apply it when there is a clear `suggested_fix` and confidence, and call it out prominently in the diff review.

There is no precondition safety checklist and no deny-list — downside is controlled after the fact by JJ diff review, tests, and the change-boundary checkpoint, not by gating the apply.

**Evidence still matches the code** — the fix subagent confirms at `file:line` before editing. The orchestrator does **not** open files just to decide eligibility or dispatch.

## What to defer (to the Residual Work Gate)

- `autofix_class: advisory` — report-only.
- Findings with no concrete `suggested_fix` to act on.
- Findings whose right fix depends on a design or product decision — architecture direction, contract shape, or a behavior change needing sign-off. These need a human call before code changes.

Surface what was deferred and why; never silently drop.

## Execution — orchestrator batches, subagents apply

The orchestrator **does not investigate findings** (no pre-read of cited files to judge complexity or inline vs subagent). That would spend the context window you are trying to protect.

**Orchestrator owns:** parse review output -> **eligibility filter on JSON fields only** -> build batches -> dispatch fix subagents -> review JJ diffs -> tests -> close coherent change boundaries -> Residual Work Gate.

**Fix subagents own:** read `file:line`, confirm evidence still matches, apply or skip with reason, return summary.

### Default: batched fix subagents

After eligibility filtering, **dispatch subagents for all remaining applicable findings** unless the optional inline shortcut below applies. Do not classify findings by complexity in the parent thread.

**Batching (primary rule — group by file):**

1. Sort applicable findings by severity (P0 first).
2. **Group by `file`.** All eligible findings on the same file → **one subagent** (it loads the file once and works through its `#` list in severity order).
3. **Parallel waves:** batches with **disjoint file sets** may run in parallel under the isolated-workspace/shared-workspace rules in Phase 1 Step 4.
4. **Same file, many findings:** keep one subagent per file. If the prompt would exceed a comfortable size (~8 findings), split into **serial** passes on that file, each based on the accepted JJ parent.
5. **Cross-file coupling:** do not merge unrelated files into one subagent just to reduce agent count — file grouping is the default. Only co-batch multiple files when findings explicitly reference the same small edit surface (rare); when in doubt, separate by file.

**Subagent prompt (per batch):** the assigned findings only (`#`, severity, file, line, title, `suggested_fix`, `requires_verification`; add `why_it_matters` from `{reviewer}.json` in the run artifact when useful), plus:
- Work through assigned `#` in severity order; at each `file:line`, skip with a one-line reason if evidence no longer matches
- Apply the mechanical bar from § What to apply / What not to apply — skip anything that needs design judgment
- Do not re-run `ce-code-review`
- Shared-workspace fallback: do not describe, split, rebase, or start changes — return which `#` were applied or skipped and which files changed

**After each wave:** the orchestrator reviews `jj diff` for the assigned finding IDs, runs targeted or broader tests as required, and keeps the fixes in one coherent JJ change or splits them by explicit path when independent boundaries are clearer. Before describing each resulting change, active project instructions and description syntax inferred at runtime from `jj log` always win. Apply compatible Go guidance for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example. Use `<description-composed-from-runtime-conventions>` as the neutral placeholder. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repeat until all batches complete.

### Optional inline shortcut (skip subagent spawn)

Use **only** when **all** of the following hold:

- Exactly **one** eligible finding after JSON filtering, **and**
- The orchestrator **already** has that file's relevant region in context from Phase 2 work this session (no new Read/Grep expedition)

Otherwise dispatch a subagent — even for a single finding. When unsure, dispatch.

### Summary (required)

Report: batches dispatched, `#` applied vs skipped (with reasons from subagents), artifact path, tests run.

## Handoff to Residual Work Gate

Any actionable finding not applied in this pass is **residual work** — proceed to the Residual Work Gate with an updated count. Do not re-invoke `ce-code-review` solely to re-apply the same findings unless the diff changed materially after fixes.
