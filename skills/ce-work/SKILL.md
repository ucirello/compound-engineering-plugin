---
name: ce-work
description: Execute a plan or concrete work prompt end-to-end. Use when implementing from docs/plans, a specification path, or a clear build request; use ce-debug for open-ended bugs. Standalone use owns delivery; outer orchestrators use mode:return-to-caller for implementation and local verification only.
argument-hint: "[Plan path, work description, or recovery request with run id; blank uses latest] | [mode:return-to-caller [implementation_engine:<compact-json>] [implementation_run:<safe-id>] <plan path>]"
---

# Work Execution

## Outcome

- Produce a complete, locally verified Jujutsu change set from the supplied authority.
- Keep canonical integration, descriptions, bookmarks, verification, and delivery host-owned.
- Finish every in-scope task or stop with explicit durable recovery evidence.

## Input And Recovery

The input may be a plan/specification path, a mode token followed by a path, a bare work prompt, or a recovery request. Invocation origin supplies no authority.

**Bundled references fail closed.** Resolve every path below from this skill's loaded directory. If a required file cannot be read, stop before its governed action.

Recovery intent wins before all classification. A supplied run id must match `^[A-Za-z0-9._-]{1,128}$` and contain a non-period character. Read `references/cross-model-execution.md`, call the controller with that exact id, and do not select a route, redispatch, reimplement, rerun completed verification, or enter either delivery tail.

For `mode:return-to-caller`, strip the mode token, then accept an optional compact `implementation_engine:` object and optional `implementation_run:` id in that order. The engine object contains exactly `mode`, `target`, `model`, and `source`. Reject malformed or duplicate control data. A recovery carrier invokes `resume --run-id` and returns the normal envelope without another implementation.

Before any non-recovery code write, read `references/execution-engines.md`. Resolve current intent, active session intent, caller binding, active project conventions, and optional `.rocketclaw/config.local.yaml`, in that precedence order. A valid external binding permits only read-only discovery until controller initialization.

## Phase 0: Classify

For a path, inspect metadata before the body:

- `artifact_contract: ce-unified-plan/v1`, `artifact_readiness: implementation-ready`, and `execution: code` proceeds.
- `artifact_readiness: requirements-only` routes to `ce-plan <plan-path>`.
- `execution: knowledge-work` loads `references/non-code-execution.md`.
- Invalid readiness or unclassified execution stops for repair.
- Legacy code plans proceed under their explicit scope.

With blank input, inspect `docs/plans/*.md` and `docs/plans/*.html`; select only the newest implementation-ready code plan. A same-basename implementation-ready sibling supersedes a stale requirements-only format copy.

For a bare prompt, inspect likely files, tests, and local conventions. Proceed directly for trivial work, create tasks for bounded small/medium work, and offer `ce-brainstorm` or `ce-plan` for broad architectural work. Never send an external worker an unclear goal, scope, or verification contract.

## Phase 1: Prepare

### Read The Authority

For a long unified plan, map headings first. Read metadata, Goal Capsule, Verification Contract, Definition of Done, the Implementation Units list, then only the active U-ID and cited R/F/AE/KTD excerpts. Read a legacy plan fully. Preserve Scope Boundaries and session-settled decisions. Do not write progress into the plan.

### Establish Jujutsu State

Read the current working-copy change, nearest bookmarks, status, and repository log with Jujutsu. The working-copy change must be conflict-free before implementation.

- If the current change is already dedicated to this work, continue.
- If it is empty and no meaningful bookmark identifies the work, create a meaningful bookmark derived from the plan title or request.
- If it contains unrelated work, invoke `ce-worktree` to create an isolated Jujutsu workspace or stop for user direction.
- Continuing directly on the repository's delivery bookmark requires explicit user confirmation.
- Refresh remote state only through `jj git fetch`; publish only through `jj git push` in an owned delivery tail.

Use Jujutsu revsets to identify the base and accepted prerequisites. Do not infer identity from filesystem directory names.

### Track Work

Use the active platform's task facility when available. Derive tasks from implementation units, dependencies, files, evidence strategy, and verification. Name tasks by outcome, appending supplied U-IDs. Never invent stable IDs.

### Select Engine And Strategy

Read `references/execution-engines.md` before any write or worker dispatch. If external execution is selected, read `references/cross-model-execution.md` before content or authority crosses the route. A successful controller `init` locks the unit to that route until the controller authorizes fallback.

For native execution:

- Inline for trivial or interaction-heavy work.
- Serial workers for dependent or uncertain units.
- Parallel workers only for independent units with isolated Jujutsu workspaces.

Parallel safety requires committed dependencies, disjoint files and semantic contracts, independent runtime resources, bounded reconciliation cost, and a batch cap of 3-5. Uncertainty selects serial work. Repeated collisions disable later waves.

Native isolation is platform-owned. Do not create a workspace manually for an ordinary worker. Give each worker one bounded unit packet, evidence requirements, expected files, exclusions, and instructions not to describe, split, squash, rebase, bookmark, fetch, or push. The host inspects the actual Jujutsu diff and owns canonical operations.

After each serial unit, inspect `jj status` and `jj diff`, run focused verification, record evidence, and describe the complete logical change before the next unit. For an isolated parallel batch, inspect each workspace, reject path or semantic collisions, then integrate one result in dependency order. Rebase a stale result onto the advancing accepted revision only after rechecking independence; stop on conflicts. Release every worker and workspace after acceptance.

## Phase 2: Execute

Read `references/implementation-loop.md` before the first task. For every behavior-bearing unit, choose proof-first, characterization-first, existing-failure, or an explicit no-test exception before production edits. Capture evidence that cannot be reconstructed later.

### Incremental Jujutsu Changes

Keep each complete logical unit in one Jujutsu change. Use `jj split` when an active change contains multiple independently valuable units; use `jj squash` only to fold a verified subordinate change into its intended parent; use `jj rebase` when an accepted prerequisite advances. Stop on conflicts and resolve them before further work.

Before every complete change-description composition, edit, validation, or recommendation, apply this rule exactly:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active runtime instructions and conventions are required input. Inspect descriptions with `jj log`; syntax observed there takes precedence over generic guidance and over the wording of the sentence above. Apply the linked Go guidance only where it is compatible with those project instructions and the repository's `jj log` history. Do not use fixed types, scopes, templates, examples, or identity footers. Compose a neutral description for the actual complete change, then run `jj describe -m <dynamically-composed-description>`. Start the next unit with `jj new` only after verification and description succeed.

### Continuous Checks

- Follow existing code and naming patterns.
- Run relevant checks after meaningful edits and fix failures before proceeding.
- Inspect callbacks, middleware, state persistence, alternate interfaces, and cross-layer error handling.
- Simplify at natural boundaries; invoke `ce-simplify-code` when appropriate.
- For Figma work, load `references/agents/figma-design-sync.md` into a generic worker.
- For UI work, preserve the existing design system, responsive behavior, real controls, and visible states.
- Keep task status, blockers, and verification evidence current outside the plan.

## Phase 3-4: Review And Delivery

When implementation completes, read `references/shipping-workflow.md`.

Review every non-mechanical diff with `ce-code-review`. Review is read-only; then load `references/review-findings-followup.md` to apply eligible fixes. Process residual findings through the shipping reference's durable gate.

## Return-To-Caller

Return implementation and local verification only:

- `status`, `plan_path`, `changed_files`, `u_ids_attempted`, `u_ids_completed`
- `verification_results` and per-unit `verification_evidence`
- `implementation_engine_binding`, requested/actual route and model receipts, and `fallback_reason`
- `run_id`, `source_kind`, `source_digest`, `unit_receipts`, and `plan_checkpoint`
- `blockers`, `recovery_path`, `settled_decision_conflicts`, and `behavior_change`
- `standalone_shipping_skipped: true`

Return complete only with behavior evidence or a deliberate exception. External receipts distinguish process completion, pinned Jujutsu change, canonical squash, verification, canonical description, workspace cleanup, and run-wide verification.

## Fail-Stops

- Never bypass a live, terminal-but-unreconciled, or restoration-blocked controller attempt.
- Never infer success from worker prose or process exit alone.
- Never continue after an unknown working-copy change, conflict, bookmark movement, verification mutation, or failed exact restoration.
- Never broaden worker scope, recipient, or delivery authority.
- Never write progress into the plan.
- Never leave an accepted unit undescribed or an isolated workspace unreleased.
