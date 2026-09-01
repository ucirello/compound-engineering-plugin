---
name: lfg
description: "Run the full autonomous shipping pipeline end-to-end, hands-off with no check-ins. Use only when the user explicitly asks to build or ship something autonomously all the way to an open PR, or invokes lfg directly — it pushes and opens a PR without stopping. Not for in-the-loop work where the user reviews each step: use ce-plan, ce-work, ce-debug, or ce-commit-push-pr instead."
argument-hint: "[feature description; optionally assign planning and/or implementation to a model or harness]"
---

CRITICAL: You MUST execute every step below IN ORDER. Do NOT jump ahead to coding or implementation. The plan phase (step 1) MUST be completed and verified BEFORE any work begins.

LFG runs hands-off, from schedulers, loops, and nested orchestrators with no user to answer, so no step stops to ask. The one exception is the upfront routing question `references/stage-routing.md` defines.

Resolve every skill named below against the host's available-skills list and invoke that exact entry. Preserve `ce-*` route names; do not invent a namespaced alias that is absent from the list.

Read `references/task-visibility.md` before step 1: it owns the stage-level view this pipeline publishes through the platform's task-tracking capability, the per-step chat narration, and the completion discipline — a step is done only after it ran, and the turn does not end before DONE or a GATE stop.

## Per-stage routing carriers

Before step 1, judge whether the conversation expresses semantic intent to assign a stage — planning or implementation — to a model or harness; a plain mention in feature content, quotes, comparisons, or a filename is not an assignment. When one exists, read `references/stage-routing.md` before step 1: only it carries the routable stages, scope and strength resolution, the `implementation_engine` grammar, ordered fallback, the sanitization that keeps routing out of planning and review inputs, and both seams' carrier strings. An improvised carrier drops the user's instruction or contaminates the plan with routing.

1. **Read `references/plan-brief.md` first**, then invoke the `ce-plan` skill with the sanitized feature request — or the arguments you were invoked with, unchanged, when no routing directive was present — prefixed with the `plan_model:<alias>` carrier when a planning-stage directive resolved, and with the settled-decisions brief that file specifies. Only it carries the artifact-root rule this step's gate reads, the brief's required fields, demotion rule, topical scope bar, and skip-entirely case, and the readiness values the gate applies.

   GATE: STOP. Stop the pipeline and tell the user why when `ce-plan` reports the task is non-software (LFG requires software tasks), returns any explicit `status: blocked` report (including `settled-decision-invalidated`), or when the plan it wrote fails the readiness check in `references/plan-brief.md`. Blocked status outranks an existing artifact and is never retried. Only absence of both a blocker and a plan file `ce-plan` reported writing this run invokes `ce-plan` again with those same arguments, reusing the composed brief verbatim; never proceed to step 2 without a written plan.

   **Record the plan file path** — it is passed to ce-work in step 2 and ce-code-review in step 4. LFG never launches `/goal` directly; `ce-work` owns any goal-mode or dynamic-workflow engine choice and returns control to LFG afterward.

2. **Read `references/work-return.md` first**, then invoke the `ce-work` skill with `mode:return-to-caller <plan-path-from-step-1>`, or with the carrier form from `references/stage-routing.md` when a routing carrier resolved. Only it carries what each return status means, the receipt fields a `status: complete` return must contain, the verification-evidence contract, how `settled_decision_conflicts` route, and the one recovery invocation. Accepting a return without it ships work that nothing protected.

   GATE: STOP. Read the structured return before continuing. Only a valid `status: complete` may advance; every other status or malformed return stops the pipeline.

3. **Read `references/review-followup.md` now**, then invoke `ce-simplify-code` on the active Jujutsu stack diff. Skip only the invocation, never the read, when the change is docs-only or trivial (roughly under 10 changed lines). That file governs steps 3 through 6, including scope, structure pins, review read-back, focused review changes, and the durable residual record.

4. Invoke the `ce-code-review` skill with `mode:agent plan:<plan-path-from-step-1>`.

   GATE: STOP. A `settled_conflict`-stamped finding whose evidence is invalidating — the settled decision cannot work: infeasible, wrong-thing, or destructive — stops the pipeline as blocked, with the finding reported, before the shipping precondition.

**Shipping precondition (steps 5–9).** Run `jj git remote list` once before shipping. No remote means shipping is local-only: finish every local Jujutsu change the steps require, but skip every push, PR create/edit, and CI-watch action, including step 9. That is terminal, not an error.

5. **Apply and persist review fixes** (REQUIRED after step 4, before residual handoff)

   Execute the apply step of `references/review-followup.md`. Do not proceed to the residual handoff, run browser tests, or output DONE while eligible review fixes remain mixed into an unfinished working-copy change.

6. **Autonomous residual handoff** — run it whenever anything divergent is left to make durable: an actionable `downstream-resolver` finding step 5 did not apply, a `settled_conflict` stamp from step 4, or a proceeded-and-flagged `settled_decision_conflicts` entry from step 2. Skip only when none of the three exists — `Actionable findings: none.` does not decide it alone.

   Do not prompt the user.

   **Durable record — the PR body.** Compose the `## Unapplied review findings` checklist per `references/review-followup.md`; step 8 renders it. Do not output DONE until the residuals are durable: in the PR body, else (no PR) in tickets or the DONE report. Never block DONE on tracker filing failures once the report states them.

7. Invoke the `ce-test-browser` skill with `mode:pipeline`.

8. Ship: the goal is the remaining work described, pushed with Jujutsu, and in an open PR whose URL you hold. **Read `references/shipping-tail.md` first**, then invoke `ce-commit-push-pr mode:pipeline` unless that file routes elsewhere. It owns project-defined process precedence, context, ticket back-fill, the no-remote substitution, and stack handoff.

9. **Watch the PR to CI-decided via `ce-babysit-pr`** only when an open PR exists for the pushed bookmark.

   Detect the PR with `GIT_DIR="$(jj git root)" gh pr view --json number,url,state`; if none exists or `gh` is unavailable, skip to step 10. When step 8 already handed off a stack babysit, `references/shipping-tail.md` decides this step. Otherwise invoke **`ce-babysit-pr mode:pipeline <pr-url>`** and preserve its structured result.

10. Output `<promise>DONE</promise>` when complete, after the close-out in `references/shipping-tail.md`, which owns the two user-runnable handoff lines, their per-host rendering, and the next-work offer gate.

Start with step 1 now. Remember: plan FIRST, then work. Never skip the plan.
