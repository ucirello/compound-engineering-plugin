# Execution Engines

An implementation-ready unified plan can run with one of three engines. The engine is chosen once, after Phase 0 classifies the plan as `artifact_readiness: implementation-ready` plus `execution: code`. The engine decides *how* implementation runs; it never changes *who* owns the shipping tail (see "Tail ownership" below).

Engine selection applies only to code execution. Knowledge-work and legacy plans keep the inline/subagent flow in `SKILL.md`.

## Step 1: Probe host capability

An engine is usable only when the host exposes a callable primitive for it. Do not assume one exists from its name.

| Engine | Usable when | Non-callable host behavior |
|---|---|---|
| **Inline / subagent** | Always. The orchestrator runs units inline or dispatches subagents via the platform's subagent primitive. | Always callable in-session. This is the default. |
| **Goal-mode** | The host exposes a callable goal tool such as `create_goal`, with terminal status managed by the goal lifecycle. | If only a user-typed `/goal` exists, emit a copyable prompt or run inline/subagents. |
| **Dynamic-workflow** | The host exposes a callable dynamic-workflow / ultracode-style orchestration primitive that returns structured results and blockers without mid-run user decisions. | If it is user-prompt-only (`ultracode:` or `/effort ultracode`), emit a copyable prompt block. |

Rule of thumb: **probe for the callable tool, don't infer from the command's existence.** If the host exposes `create_goal`, goal-mode is a real callable engine. If it exposes only a user-typed `/goal`, goal-mode is prompt-emission only. The literal `/goal` slash command is not skill-invocable; the tool path makes goal-mode callable.

When `features.goals` exposes goal tools, `create_goal(objective)` sets and activates a persistent objective for the current session; it is not a background worker and returns no awaitable envelope. The goal lifecycle reports terminal status. Call `create_goal` with the objective below and do not call `update_goal` from this skill; the working session handles terminal status.

## Step 2: Pick the engine by plan shape

When more than one engine is callable, choose by the plan's decomposition shape:

| Plan shape | Engine | Why |
|---|---|---|
| Sequential or modest U-ID decomposition; units share files or depend on each other | **Inline / subagent** (default), or a **goal-mode** prompt for sustained focus when callable | The DoD already defines the end condition; ordinary persistence finishes it. |
| Many independent U-IDs with disjoint file ownership; codebase-wide sweep; large migration; adversarial cross-checking | **Dynamic-workflow** when callable; otherwise parallel subagents | Workflow scripts hold branching, loops, and intermediate worker state outside the main context and coordinate many agents. Prefer this over goal-mode for large fan-out. |
| Host exposes no callable goal/workflow primitive | **Inline / subagent** | Preserve the same heading-scan / DoD / U-ID discipline without relying on unavailable host features. |

Recommend exactly one path. Present a non-default engine as an "advanced / large-scale option" only when the plan shape plausibly warrants it — never as an equal coin-flip.

## Step 3: Run the chosen engine

### Inline / subagent (default)

Follow the dispatch strategy in `SKILL.md` Phase 1 Step 4 (inline, serial subagents, or parallel subagents) and the Phase 2 execution loop. The caller owns task creation, unit sequencing, dispatch, verification, and change boundaries.

### Goal-mode and dynamic-workflow

**With a callable goal tool:** call `create_goal` with the objective — the content of the copyable prompt below, minus the leading `/goal`. This activates the objective and the current session works toward it; there is no separate worker and no envelope to await, so the session continues to its tail (Step 4) and the goal lifecycle marks completion. Do not call `update_goal` from this skill. Use `create_goal` only in standalone use, never in return-to-caller mode; run inline/subagents there.

**No callable goal tool, or prompt-only dynamic-workflow:** do **not** attempt to invoke them. Instead:

- **Standalone interactive use:** print a copyable prompt block for the user to paste, then continue inline/subagents if the user does not paste it. Do not stall waiting for a paste.
- **Return-to-caller use:** do **not** emit a copyable prompt — a manual paste step strands the caller. Run inline/subagents instead, or return a blocker if the plan genuinely requires an unavailable engine.

Whichever path, the goal/workflow must not open a PR, finalize the session, or bypass the owning workflow's gates.

Copyable goal-mode prompt (standalone — emit verbatim, substituting only the literal plan path). **It must be plan-agnostic: it should read identically for any plan except the substituted path.** Deletion test before emitting — if your draft names a specific command, file path, U-ID dependency relationship, stop condition, or Definition-of-Done item, it copied from the plan; cut it (the goal reads those from the plan). For PR/shipping, don't hardcode an open-a-PR or do-not-open-a-PR directive; instead carry the precedence line below — the goal follows the plan's PR/landing strategy if it has one, with the repo's conventions and the user's preferences overriding it (both of which the executing agent already has).

```text
/goal Implement <plan-path> to its Definition of Done.

The plan is the authority — don't read it whole. Scan headings, read the Goal Capsule, then work the units in dependency order, reading each unit plus its cited R/F/AE/KTD as you go. Run the plan's Verification Contract gates and satisfy each unit's test scenarios. Track progress outside the plan file, not in it.

This top-level goal owns the implementation tail: run simplification and code review when the diff meets the repo's normal criteria, apply eligible fixes, and surface residual findings. Follow the plan's PR/landing strategy if it defines one; the repo's conventions and the user's preferences override it. Surface a genuine blocker — something that changes scope or contradicts the plan — instead of guessing; use your judgment on details the plan leaves open.

Done when the transcript shows: every non-deferrable Per-Unit DoD row has an observed verification result; the Verification Contract's required checks passed or are documented as not applicable; applicable simplification/review gates ran or were explicitly skipped with reason; dead-end or experimental code from approaches that did not pan out has been removed from the diff; and no progress/status was written into the plan file. Before declaring done, re-open the plan and re-check the active units, Verification Contract, and Definition of Done against the diff — context may have been compacted to a summary that dropped detail.
```

Copyable dynamic-workflow prompt (large fan-out — emit verbatim):

```text
ultracode: Execute <plan-path> as an end-to-end dynamic workflow.

Use the plan as authority. Build the workflow around the Implementation Units and Definition of Done. Parallelize only independent U-IDs with disjoint file ownership, keep intermediate agent results inside the workflow, run simplification/review/verification gates inside the workflow tail, and return a final summary with changed files, U-IDs completed, verification results, residual findings, and blockers.
```

Keep emitted prompts under 4,000 characters and always substitute the literal plan path.

## Step 4: Resume the correct tail

After any engine finishes implementation, inspect the diff and continue at the tail that matches the caller. The engine never owns more than implementation + local verification on its own.

| Mode | After implementation, the workflow ... |
|---|---|
| **Standalone** (direct invocation, or an interactive `ce-plan` handoff) | Resumes its normal post-implementation tail — Phase 3-4 quality gates, simplification, review, change recording, and handoff in `references/shipping-workflow.md`. A goal-mode run does not skip these; verify they ran or were explicitly skipped with reason. |
| **Return-to-caller** (`mode:return-to-caller`) | Performs implementation and local verification only, then returns the structured summary in `SKILL.md` § Return-to-Caller Mode (`standalone_shipping_skipped: true`). Does not run simplify/review/PR/CI — the caller owns those. |

Using goal-mode or a dynamic workflow is a way to get better sustained implementation focus, not a way to skip the owning workflow's finish discipline.

## Progress visibility (independent of tail ownership)

Tail ownership decides who opens the **final** PR; it does not forbid progress signals during a long run. For multi-hour goals, meaningful recorded changes as units complete and an optional scratch progress artifact under `$(jj workspace root)/.tmp/work` (or `$PWD/.tmp/work` when the workspace root is unavailable during recovery) are encouraged so a long trajectory stays observable. Do not use OS/global temporary locations. Only final PR creation is gated: a standalone top-level goal may open a **draft** PR only when it explicitly owns that channel; in return-to-caller mode the workflow must not open any PR, but may record changes and return a progress report in its structured envelope. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime repository-local instructions and actual `git log` take precedence over compatible Go guidance. Do not prescribe a fixed message, prefix, type, scope, subject/body shape, template, or example. Never write progress or status into the plan body — JJ changes and the envelope carry it.
