# Native per-stage routing

A stage assignment selects the model for planning or implementation, not a different harness. Use native `opencode.models` to resolve available provider/model IDs and native subagents/shell for execution. Preserve applicable session/project intent and existing model configuration when the user gives no override; never invent a model-family-to-harness mapping or invoke a dispatcher/model-elevation/work-engine bridge.

## Detect scope and strength

Interpret semantic intent, not keyword matches. An explicit instruction such as "plan with opus" assigns a stage; model names in feature content, quotations, comparisons, or filenames do not.

1. An explicitly scoped instruction applies only to its named stage. Multiple stage assignments may coexist.
2. An unscoped model assignment defaults to implementation only. Disclose that binding before step 1; planning keeps its applicable configuration.
3. Only when an unscoped assignment credibly belongs to several stages and mis-binding would be materially costly, ask one upfront question on an interactive host. Headless runs use and disclose the implementation default instead.

Infer `prefer` versus `require` from the whole instruction. Preserve every candidate in an ordered fallback list, in order; never truncate it. A request explicitly requiring another harness is an unsupported-route blocker, not permission to launch it. A model name also used by a harness must be resolved through the native model catalog; if the intent is unclear, do not silently reinterpret it.

## Pass structured stage intent

Keep stage routing beside product input, never inside the feature request, plan, settled-decisions brief, or review product. Planning receives only its own assignment; implementation receives only its own assignment. Retain mode, ordered requested provider/model IDs, source, and resolved-versus-unavailable evidence in caller context. Pass that context through the child's native invocation with the unchanged sanitized request or plan path. If the host cannot preserve the assignment, stop as a routing-carrier blocker rather than dropping it.

For planning, retain the child-compatible `plan_model:<resolved-model-id>` carrier when explicitly assigned. For implementation use `mode:return-to-caller <plan-path-from-step-1>` (or the one-pass statement) with native stage intent in caller context. Do not emit a legacy `implementation_engine:` dispatcher carrier. Each child applies existing configuration when no explicit assignment exists.

## Permission, execution, and receipts

This skill requests native stage delegation where needed. Honor actual higher prohibitions and tool denials; do not ask redundantly under a user-or-loaded-skill exception. Model override is separate: where explicit user model authorization is required, omit optional model arguments without it, use the suitable inherited model, and disclose unmet configured routes. Preserve configured tier intent. Never claim cross-model independence for separate reviewers using the same model.

Preflight native availability and effective nesting/capacity, distinct from permission. A required unavailable route blocks; an allowed preferred fallback discloses requested/actual route and model plus the reason, once. Do not rerun completed implementation merely to change its route. Actual permission, capacity, tool, and model errors must be classified rather than routed through another harness. Mandatory incomplete coverage remains incomplete.

Retain requested/actual route/model, binding source and strength, run ID, per-unit receipts, checkpoint, blockers, and recovery path in the child return. Preserve bounded retries, integration/verification evidence, and exact source authority. These are execution receipts, not a reason to keep bridge scripts.

The optional `implementation_run:<safe-id>` carrier is recovery-only. Never include it on the initial step-2 call. On the one evidence-reconciliation recovery, reuse the same native assignment and unchanged plan/statement with `mode:return-to-caller implementation_run:<safe-id> <plan-path-from-step-1>`. A safe ID matches `^[A-Za-z0-9._-]{1,128}$` and contains at least one non-period character. Reject malformed or duplicate recovery carriers rather than launching fresh work.
