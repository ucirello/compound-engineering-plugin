# Execution Engines

`ce-work` supports inline/worker, goal-mode, dynamic-workflow, and fixed-route external execution. The engine owns implementation only; standalone or return-to-caller mode owns the tail.

## Resolve Authority

Resolve one binding in this order: current request, active session intent, typed caller binding, active project conventions, enabled `.rocketclaw/config.local.yaml`, then native execution. Narrower current authority wins. Incidental provider mentions do not activate routing. Equal-authority conflicts stop for resolution.

A direct preference yields `prefer`; explicit exclusivity yields `require`. Preserve an ordered live preference list. A typed caller binding remains exactly:

- `mode`: `prefer | require`
- `target`: `codex | claude | grok | cursor | composer`
- `model`: explicit selector or `null`
- `source`: caller-visible provenance

Accept it only beside `mode:return-to-caller`. Recovery may separately carry `implementation_run:<safe-id>`. Neither carrier enters product planning or review input.

Standing configuration is:

```yaml
work_engine_mode: prefer
work_engine_preferences:
  - harness: cursor
    model: composer
  - harness: codex
```

`work_engine_mode` is `off`, `prefer`, or `require`. Candidate objects name a provider and optional model, never shell syntax. Normalize candidates to fixed routes: `codex`, `claude`, `grok-cli`, `cursor`, `composer`, or `grok-cursor`. Skip a same-provider default route, record unavailable candidates, and stop traversal at the first qualified route. Dispatch locks that recipient.

`prefer` falls back natively only after authoritative unavailability. `require` asks only in an interactive run; headless use blocks. A live external attempt never falls back.

## Capability Gate

Use an engine only when the active platform exposes a callable primitive:

| Engine | Gate |
|---|---|
| Inline/worker | Always available; use native worker dispatch when exposed |
| Goal-mode | A callable goal primitive exists; a user-only command is not callable |
| Dynamic-workflow | A callable structured workflow primitive exists |
| External | A fixed write-capable adapter and every required restriction qualify |

If a requested route is the current provider's default and no distinct model was requested, collapse to native and record requested versus actual identity.

Choose inline/serial workers for sequential or shared-file units. Choose dynamic workflow or parallel workers only for large independent fan-out. Bare prompts qualify externally only after goal, scope, exclusions, and authoritative verification are concrete.

## Engine Execution

Native execution follows `SKILL.md`. External execution loads `cross-model-execution.md`. Goal and dynamic workflow never gain PR or delivery authority.

In standalone use, a callable goal may activate the current session. When the host exposes `create_goal`, call it with the objective below without the leading `/goal`; it activates the current session rather than a background worker, so continue through the normal implementation and tail. Do not call terminal-only `update_goal` from the skill. Never activate goal-mode in return-to-caller mode.

If goal-mode is only a user-runnable invocation, emit the following copyable block in standalone interactive use, substituting only the literal plan path, then continue inline/workers if the user does not use it. Do not wait for a paste. Return-to-caller mode never emits a manual-paste prompt and instead uses inline/workers or returns a genuine blocker.

```text
/goal Implement <plan-path> to its Definition of Done.

The plan is the authority — don't read it whole. Scan headings, read the Goal Capsule, then work the units in dependency order, reading each unit plus its cited R/F/AE/KTD as you go. Run the plan's Verification Contract gates and satisfy each unit's test scenarios. Track progress outside the plan file, not in it.

This top-level goal owns the implementation tail: run simplification and code review when the diff meets the repo's normal criteria, apply eligible fixes, and surface residual findings. Follow the plan's PR/landing strategy if it defines one; the repo's conventions and the user's preferences override it. Surface a genuine blocker — something that changes scope or contradicts the plan — instead of guessing; use your judgment on details the plan leaves open.

Done when the transcript shows: every non-deferrable Per-Unit DoD row has an observed verification result; the Verification Contract's required checks passed or are documented as not applicable; applicable simplification/review gates ran or were explicitly skipped with reason; dead-end or experimental code from approaches that did not pan out has been removed from the diff; and no progress/status was written into the plan file. Before declaring done, re-open the plan and re-check the active units, Verification Contract, and Definition of Done against the diff — context may have been compacted to a summary that dropped detail.
```

When a callable dynamic-workflow primitive exists and the plan has large independent fan-out, execute this protocol through that primitive. If dynamic workflow is user-prompt-only, emit the block only in standalone interactive use and continue inline/workers if unused; never emit it in return-to-caller mode.

```text
ultracode: Execute <plan-path> as an end-to-end dynamic workflow.

Use the plan as authority. Build the workflow around the Implementation Units and Definition of Done. Parallelize only independent U-IDs with disjoint file ownership, keep intermediate agent results inside the workflow, run simplification/review/verification gates inside the workflow tail, and return a final summary with changed files, U-IDs completed, verification results, residual findings, and blockers.
```

Keep either emitted prompt under 4,000 characters. Goal-mode and dynamic-workflow must not open a PR, finalize the session, bypass verification, or take authority from the standalone or return-to-caller tail.

Any emitted objective remains plan-agnostic. Except for substituting `<plan-path>`, emit the applicable block verbatim; do not copy plan-specific commands, files, dependencies, stop conditions, or Definition-of-Done rows into it.

After any engine completes, inspect `jj status` and `jj diff`. Standalone resumes review and delivery; return-to-caller returns local implementation and evidence only.

Long-running work may expose described Jujutsu changes and a workspace-local `.tmp/rocketclaw/ce-work` progress artifact. Never write progress into the plan.
