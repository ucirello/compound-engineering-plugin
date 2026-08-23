---
name: ce-work
description: Execute a plan or concrete work prompt end-to-end. Use when implementing from a plan document, a specification path, or a clear build request; use ce-debug for open-ended bugs. Standalone use owns the shipping tail; use when an outer orchestrator needs implementation, recovery, and local verification only, without the shipping tail.
argument-hint: "[Plan path, work description, or recovery request with run id; blank uses latest] | [mode:return-to-caller [implementation_engine:<compact-json>] [implementation_run:<safe-id>] <plan path> for outer orchestrators]"
---

# Work Execution

## Setup

Run this once at invocation start, before subagent dispatch. Follow its directives unless they conflict with this skill's question policy. Run the fence as one unfiltered command. Its output begins with `=== skill context` and ends with `WORK_CONTEXT_END`; if exactly one boundary appears, rerun the fence once. If Node is unavailable, proceed unchanged.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
NODE="$(for c in node nodejs; do command -v "$c" >/dev/null 2>&1 && "$c" -e '' >/dev/null 2>&1 && { echo "$c"; break; }; done)";
if [ -n "$NODE" ]; then
  "$NODE" "$SKILL_DIR/scripts/context.mjs" || echo "context script failed; continue with the skill's normal behavior";
else
  echo "no Node runtime; continue with the skill's normal behavior";
fi
```

## Outcome

- **Result:** A fully implemented, locally verified Jujutsu change set from a plan, specification, or concrete work prompt.
- **Next consumer:** Standalone use hands the verified changes to the shipping workflow. Return-to-Caller Mode returns a structured implementation and verification envelope to its invoking workflow.
- **Done:** Every in-scope task is complete, required verification evidence is recorded, relevant checks pass, and the run reaches its owned shipping handoff, complete return envelope, or explicit blocker.
- **Intent:** Finish the requested feature without renegotiating the plan or transferring canonical composition authority. Workers receive bounded units; the host inspects actual changes and owns authoritative verification and canonical changes.

## Runtime Roots

Resolve the Jujutsu workspace root with `jj workspace root` only when first composing a workspace path. Plans live under `<root>/plans/`; `references/input-triage.md` owns artifact-root resolution. Ordinary configuration lives under `.rocketclaw/`, with `config.local.yaml` overriding `config.yaml` as defined by the owning reference and `docs_root` remaining team-file-only.

All transient state belongs under the current Jujutsu workspace root's `.tmp/rocketclaw/`. The controller uses `.tmp/rocketclaw/work-runs/<run-id>/`; one-off packet and prompt sources use `.tmp/rocketclaw/work-inputs/<run-id>/`. Outside a Jujutsu repository, use `<cwd>/.tmp/rocketclaw/`. Never default to an OS-global temporary directory or environment-selected temporary root. Atomic publications reserve a temporary file in the destination directory and replace it there.

Repository writes require a writable Jujutsu workspace. A harness-provided remote work surface is acceptable only when it exposes one. Otherwise report the blocker and perform no repository writes.

**Bundled reference loading is fail-closed.** Resolve every bundled reference or script from this skill's loaded directory, never by searching the target workspace. Read a phase's owner when that phase is entered; an earlier read does not satisfy an explicit reread. If a required owner cannot load, stop before its governed action rather than approximating it.

## Phase 0: Input Triage

**Recovery comes first.** Before normal input classification, recognize requests to resume, inspect, reap, or clean an existing external run. Recovery never dispatches, selects a route, discovers another plan, repeats completed verification, or enters either shipping tail; request a missing safe run id rather than guessing.

Before any other input decision, read `references/input-triage.md`. It owns source resolution, artifact roots, control grammar, recovery, read-only discovery, plan readiness, non-code routing, blank discovery, and bare-prompt intake.

When triage enters Return-to-Caller Mode, immediately read `references/return-to-caller.md` and record that tail owner. If it cannot load, stop before mutation rather than reverting to standalone behavior.

## Phase 1: Prepare

1. **Establish the workspace.** Before a Jujutsu graph move, edit, dispatch, or finalized change, read `references/workspace-setup.md`. It owns writable-workspace selection, plan clarification, feature-change placement, pre-work inventory, collision handling, and task setup.

   **WIP/write gate.** Nothing the user did not offer may be described, composed, rewritten, abandoned, or published. When a unit needs a path already changed before the run, standalone mode asks once whether to include or exclude it; Return-to-Caller Mode does not ask or edit it and returns blocked with the collision and recovery path.

2. **Resolve the engine, then strategy.** After bounded intake and task derivation, but before selecting a unit, writing, dispatching, or finalizing a change, read `references/execution-engines.md` and complete its route-resolution gate. It applies with or without a typed binding. Engine choice never changes the Phase 0 tail owner.

   If cross-model execution is selected, read `references/cross-model-execution.md` before content or authority crosses that route. It owns controller initialization, the post-init engine lock, bounded egress, transactions, recovery, and receipts; do not approximate it with native dispatch.

   Before choosing inline, serial, or parallel execution or dispatching a worker, read `references/execution-strategy.md`. It owns scheduling, isolation, unit packets, worker lifecycle, and composition. The host keeps authoritative verification and canonical-change ownership.

## Phase 2: Execute

Before the first implementation write, including a Trivial route, read `references/implementation-loop.md`. It owns evidence choice, implementation, verification, completion stops, incremental Jujutsu changes, pattern-following, continuous testing, simplification boundaries, UI work, progress tracking, and settled-decision handling.

The write gate remains active. Before finalizing any logical unit, inspect `jj diff --summary` and `jj diff`; use a dynamically composed description derived from active project instructions and runtime `jj log`, and keep unrelated pre-work outside the finalized change.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; do not impose fixed syntax or content.

## Phase 3-4: Quality And Shipping

After tasks and local verification complete, standalone mode must read `references/shipping-workflow.md` before quality checks or delivery. It owns simplify, review receipts and fallback mechanics, residuals, final validation, and delivery.

**Code-review completion gate (standalone only).** The run is not done and must not call a finalization or shipping skill, or report ship-complete, until `shipping-workflow.md` records either a completed `ce-code-review` receipt or one exact authorized skip state. Mental self-review and already-applied findings are not substitutes. This gate does not apply in Return-to-Caller Mode.

## Return-to-Caller Mode

Return-to-Caller Mode performs implementation and local verification only. It must not enter Phase 3-4 or run final simplify, code review, PR creation, CI watching, babysitting, or another standalone shipping action; the caller owns those gates.

Immediately before emitting the result, read `references/return-to-caller.md` again. It alone owns the complete envelope, evidence completion gate, route and model receipts, recovery semantics, and `standalone_shipping_skipped: true`.

If that read fails after work created state, preserve every changed path, Jujutsu change, workspace, and controller receipt. Return the minimum blocked recovery result from this kernel: `status: blocked`, `plan_path`, `run_id` when known, `changed_state`, `blockers` naming the missing owner, and `recovery_path`. Do not erase partial state, report success, or enter the standalone tail.

## Failure Direction

Stop with preserved evidence when scope, route identity, workspace ownership, Jujutsu graph state, exact restoration, authoritative verification, or review completion cannot be proven. Never abandon or rewrite unknown changes, guess a bookmark target, publish an unoffered change, or silently cross an authority boundary.
