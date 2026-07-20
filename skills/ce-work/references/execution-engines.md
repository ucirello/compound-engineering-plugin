# Execution Engines

`ce-work` can implement an implementation-ready unified plan with one of three engines. The engine is chosen once, after Phase 0 classifies the plan as `artifact_readiness: implementation-ready` plus `execution: code`. The engine decides *how* implementation runs; it never changes *who* owns the shipping tail (see "Tail ownership" below).

Engine selection applies only to code execution. Knowledge-work and legacy plans keep the inline/subagent flow in `SKILL.md`.

## Step 1: Probe host capability

An engine is usable only when the host exposes a callable primitive for it. Do not assume one exists from its name.

| Engine | Usable when | Provider mapping |
|---|---|---|
| **Inline / subagent** | Always. The orchestrator runs units inline or dispatches through the provider's subagent primitive. | Claude Code `Agent` with `isolation: "worktree"` + `run_in_background: true`; Codex `spawn_agent` fork/upload + `wait`/`close_agent`; Cursor `best-of-n-runner` native isolated candidates or shared `Task`; Pi shared `subagent` or an installed isolated-workspace extension. Integrate every isolated result through the provider-specific JJ bridge in `SKILL.md`. |
| **Goal-mode** | The provider exposes a callable goal tool, such as Codex `create_goal`, with a terminal-status operation such as `update_goal`. | A user-only `/goal` command, including Claude Code's, is not callable; emit a copyable prompt or use inline/subagents when no tool exists. |
| **Dynamic-workflow** | The provider exposes a callable dynamic-workflow or ultracode-style primitive that returns structured results and blockers without mid-run user decisions. | A user-prompt-only `ultracode:` or `/effort ultracode` surface is not callable; emit a copyable prompt or use inline/subagents. |

Rule of thumb: **probe for the callable tool, don't infer from a command's existence.** A callable `create_goal` makes goal-mode usable; a user-typed `/goal` makes it prompt-emission only.

**Callable goal semantics.** Codex may expose `create_goal(objective)` and `update_goal(status: complete|blocked)` behind `features.goals`. The first sets and activates the persistent objective for the current session; it does not start a background worker or return an awaitable envelope. The working session, not this skill, calls the terminal update operation when the objective is complete or repeatedly blocked. Claude Code exposes no callable goal tool. Probe rather than assuming either mapping is active.

## Step 2: Pick the engine by plan shape

When more than one engine is callable, choose by the plan's decomposition shape:

| Plan shape | Engine | Why |
|---|---|---|
| Sequential or modest U-ID decomposition; units share files or depend on each other | **Inline / subagent** (default), or a **goal-mode** prompt for sustained focus when callable | The DoD already defines the end condition; ordinary persistence finishes it. |
| Many independent U-IDs with disjoint file ownership; codebase-wide sweep; large migration; adversarial cross-checking | **Dynamic-workflow** when callable; otherwise parallel subagents | Workflow scripts hold branching, loops, and intermediate worker state outside the main context and coordinate many agents. Prefer this over goal-mode for large fan-out. |
| Provider exposes no callable goal/workflow primitive | **Inline / subagent** | Preserve the same heading-scan / DoD / U-ID discipline without relying on unavailable features. |

Recommend exactly one path. Present a non-default engine as an "advanced / large-scale option" only when the plan shape plausibly warrants it — never as an equal coin-flip.

## Step 3: Run the chosen engine

### Inline / subagent (default)

Follow the dispatch strategy and provider table in `SKILL.md` Phase 1 Step 4, then the Phase 2 execution loop. Preserve native parallel isolation: Claude worktree refs enter JJ through parent-side `jj git import`, with an explicit changed/created/deleted-path transfer into a fresh JJ workspace when no ref exists; Codex uploads are applied for JJ to snapshot (or returned refs are imported); Cursor winner refs are imported or native winner applications are snapshotted; Pi shared mode follows shared constraints while isolated extensions return a change/ref for JJ integration. `ce-work` owns task creation, unit sequencing, dispatch, verification, change ordering, and cleanup after recoverability.

### Goal-mode and dynamic-workflow

**With a callable goal tool:** call `create_goal` with the objective — the content of the copyable prompt below, minus the leading `/goal`. The current session works toward it; there is no separate worker or envelope to await. **The skill does not call `update_goal`.** Use `create_goal` only in standalone use; return-to-caller mode must run inline/subagents so it can return control.

**No callable goal or workflow tool:** do **not** attempt to invoke one. Instead:

- **Standalone interactive use:** print a copyable prompt block for the user to paste, then continue inline/subagents if the user does not paste it. Do not stall waiting for a paste.
- **Return-to-caller use (e.g. under `lfg`):** do **not** emit a copyable prompt — a manual paste step strands the caller. Run inline/subagents instead, or return a blocker if the plan genuinely requires an unavailable engine.

Whichever path, the goal/workflow must not open a pull request, finalize the session, or bypass the owning workflow's gates.

Copyable goal-mode prompt (standalone — emit verbatim, substituting only the literal plan path). **It must be plan-agnostic: it should read identically for any plan except the substituted path.** Deletion test before emitting — if your draft names a specific command, file path, U-ID dependency relationship, stop condition, or Definition-of-Done item, cut it. For shipping, carry the precedence line below rather than hardcoding whether to open a pull request.

```text
/goal Implement <plan-path> to its Definition of Done.

The plan is the authority — don't read it whole. Scan headings, read the Goal Capsule, then work the units in dependency order, reading each unit plus its cited R/F/AE/KTD as you go. Run the plan's Verification Contract gates and satisfy each unit's test scenarios. Track progress outside the plan file, not in it.

This top-level goal owns the implementation tail: run simplification and code review when the JJ diff meets the repo's normal criteria, apply eligible fixes, and surface residual findings. Follow the plan's pull-request/landing strategy if it defines one; the repo's conventions and the user's preferences override it. Surface a genuine blocker — something that changes scope or contradicts the plan — instead of guessing; use your judgment on details the plan leaves open.

Done when the transcript shows: every non-deferrable Per-Unit DoD row has an observed verification result; the Verification Contract's required checks passed or are documented as not applicable; applicable simplification/review gates ran or were explicitly skipped with reason; dead-end or experimental code has been removed from the JJ diff; and no progress/status was written into the plan file. Before declaring done, re-open the plan and re-check the active units, Verification Contract, and Definition of Done against the diff.
```

Copyable dynamic-workflow prompt (large fan-out — emit verbatim):

```text
ultracode: Execute <plan-path> as an end-to-end dynamic workflow.

Use the plan as authority. Build the workflow around the Implementation Units and Definition of Done. Parallelize only independent U-IDs with disjoint file ownership, keep intermediate agent results inside the workflow, run simplification/review/verification gates inside the workflow tail, and return a final summary with changed files, U-IDs completed, verification results, residual findings, and blockers.
```

Keep emitted prompts under 4,000 characters and always substitute the literal plan path.

## Step 4: Resume the correct tail

After any engine finishes implementation, inspect `jj status`, the current change, and the stack diff, then continue at the tail that matches the caller. The engine never owns more than implementation plus local verification on its own.

| Mode | After implementation, `ce-work` ... |
|---|---|
| **Standalone** (user invoked `ce-work` directly, or `ce-plan` handed off interactively) | Resumes its normal post-implementation tail — Phase 3-4 quality gates, simplification, review, JJ description/change finalization, and handoff in `references/shipping-workflow.md`. A goal-mode run does not skip these. |
| **Return-to-caller** (`mode:return-to-caller`, e.g. under `lfg`) | Performs implementation and local verification only, then returns the structured summary in `SKILL.md` § Return-to-Caller Mode (`standalone_shipping_skipped: true`). Does not run simplify/review/pull-request/CI work — the caller owns those. |

Using goal-mode or a dynamic workflow is a way to get better sustained implementation focus, not a way to skip the owning workflow's finish discipline.

## Progress visibility (independent of tail ownership)

Tail ownership decides who opens the **final** pull request; it does not forbid progress signals during a long run. For long goals, coherent described JJ changes and an optional progress artifact under `<workspace-root>/.tmp/rocketclaw/work/<run-id>/` keep the trajectory observable. Resolve `<workspace-root>` with `jj workspace root`, falling back to `pwd -P`. Only final pull-request creation is gated: a standalone top-level goal may open a draft only when it owns that channel; return-to-caller mode must not open one. Never write progress into the plan body — JJ history and the envelope carry it.

Whenever this workflow composes or recommends a JJ description, active project instructions and description syntax inferred at runtime from `jj log` always win. Apply compatible Go guidance for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example. Use `<description-composed-from-runtime-conventions>` as the neutral placeholder. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
