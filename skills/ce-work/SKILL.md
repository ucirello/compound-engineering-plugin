---
name: ce-work
description: Execute a plan or concrete work prompt end-to-end. Use when implementing from a plan document, a spec path, or a clear build request; use ce-debug for open-ended bugs. Standalone use owns the shipping tail; outer orchestrators pass `mode:return-to-caller <plan path>` for implementation and local verification only.
argument-hint: "[Plan path or work description; blank uses latest] | [mode:return-to-caller <plan path> for outer orchestrators]"
---

# Work Execution Command

## Outcome

- **Result:** A fully implemented, locally verified change set from a plan, specification, or concrete work prompt.
- **Next consumer:** In standalone use, the shipping workflow takes the verified change through review and delivery. In Return-to-Caller Mode, the invoking workflow receives the structured implementation and verification envelope and owns its remaining gates.
- **Done:** Every in-scope task is complete, required verification evidence is recorded, relevant checks pass, and the run reaches either its owned shipping handoff, a complete return envelope, or an explicit blocker.
- **Intent:** Finish the requested feature without renegotiating the plan or transferring integration authority. Workers receive bounded units; the orchestrator inspects actual changes and owns authoritative verification and coherent JJ change boundaries.

## Input Document

The **input document** for this run is the input this skill was invoked with — present in the current prompt or conversation, whether the user provided it directly or a calling skill passed it (e.g. `lfg` in `mode:pipeline`, which passes a plan path). It may be a plan or spec path, a `mode:` token followed by a path, or a bare work prompt. The rest of this skill refers to it as `<input_document>`; if nothing was provided, treat `<input_document>` as blank.

Invocation origin is not observable or relevant: apply the same source-resolution rules whether the user invoked `ce-work` explicitly or the host selected it automatically.

## Artifact Root

This skill discovers plans under `<root>/plans/` and may write review residuals under `<root>/residual-review-findings/`. Resolve `<root>` when you first compose a `<root>/` path (per the block below), never before you need it. A write to `<root>/...` and a read of `<root>/solutions/` both count as composing a `<root>/` path, so either one triggers resolution; only a run that touches no `<root>/` path at all -- a scratch-only or no-repo flow -- skips it; pass the resolved path to any subagent, not the config.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.local.yaml`, then `config.yaml`; first non-empty value wins (`<workspace-root>` = `jj workspace root`, with `pwd -P` fallback). Unset -> `<root>` is `docs`.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is not the workspace root. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Execution Workflow

**Bundled reference loading is fail-closed.** Resolve every bundled reference or script path named below from this skill's loaded `SKILL.md` directory, using the skill full path supplied by the harness; never glob the target repository to find a bundled file. If the harness does not expose that directory or a required file cannot be read, stop before the action governed by it and report the missing reference instead of approximating the protocol or continuing natively.

### Phase 0: Input Triage

**First, parse a leading mode token.** If `<input_document>` begins with `mode:return-to-caller` (or the legacy aliases `mode:caller-owned-tail` / `caller:lfg`), strip that token before anything else and enter **Return-to-Caller Mode**. The entire remainder is the plan path. A mode token with no following path is an error; report it instead of treating control data as a bare prompt.

**Resolve a session-carried plan before blank or bare-prompt classification.** When the current request is continuation language such as "proceed" and the conversation identifies exactly one current plan/spec path that was authored, selected, or accepted for this work, treat that path as `<input_document>`. If multiple session plans are plausible, ask which one; do not choose by recency. Do not replace a concrete new work request with an unrelated earlier plan. This rule depends only on visible conversation state, never on whether invocation was explicit or automatic.

Determine how to proceed based on what was provided in `<input_document>` (after any mode token is stripped).

**Plan document** (input is a file path to an existing plan or specification): read the plan's metadata first — YAML frontmatter for a markdown plan, or the visible header text for an HTML plan (both formats carry the same fields).

- If it carries `artifact_contract: ce-unified-plan/v1`, classify `artifact_readiness` before reading the body.
  - `artifact_readiness: requirements-only` -> stop and tell the user this Product Contract needs `ce-plan` enrichment before implementation. Offer the exact `ce-plan <plan-path>` handoff.
  - `artifact_readiness: implementation-ready` plus `execution: code` -> continue to Phase 1 using the unified-plan reader strategy below.
  - Any other readiness value or any non-code/unclassified execution mode -> do not auto-execute as code. Route `execution: knowledge-work` to the non-code carve-out; otherwise ask the user to return to `ce-plan` to produce an implementation-ready code plan.
  - Progress-like values (`active`, `in_progress`, `completed`, `done`) are invalid readiness values. Stop and ask for plan repair rather than guessing.
- If it carries `execution: knowledge-work`, this is a **non-code plan** — read `references/non-code-execution.md` and follow that carve-out instead of the rest of this workflow.
- Otherwise (legacy plan, field absent, or `execution: code`) -> continue to Phase 1 and run the normal code lifecycle.

**Blank invocation latest-plan discovery:** when `<input_document>` is blank, glob `<root>/plans/*.md` and `<root>/plans/*.html`, inspect metadata for the newest candidates, and only auto-select a plan that is `artifact_readiness: implementation-ready` plus `execution: code` or a legacy code plan. Stop instead of silently executing when the newest matching artifact is requirements-only, `execution: knowledge-work`, an approach-plan, or an unclassified universal/answer-seeking output. Ask for an explicit path or a `ce-plan` enrichment step. **Superseded sibling:** if a requirements-only candidate has a same-basename file in the other format (`<basename>.md` / `<basename>.html`) that is `implementation-ready`, a format conversion left the requirements-only copy stale — select the implementation-ready sibling and execute it rather than stopping.

**Bare prompt** (input is a description of work, not a file path):

1. **Scan the work area**

   - Identify files likely to change based on the prompt
   - Find existing test files for those areas (search for test/spec files that import, reference, or share names with the implementation files)
   - Note local patterns and conventions in the affected areas

2. **Assess complexity and route**

   | Complexity | Signals | Action |
   |-----------|---------|--------|
   | **Trivial** | 1-2 files, no behavioral change (typo, config, rename) | Proceed to Phase 1 step 2 (environment setup), skip the task list, then implement directly. Apply Test Discovery if the change touches behavior-bearing code |
   | **Small / Medium** | Clear scope, under ~10 files | Build a task list from discovery. Proceed to Phase 1 step 2 |
   | **Large** | Cross-cutting, architectural decisions, 10+ files, touches auth/payments/migrations | Inform the user this would benefit from `ce-brainstorm` or `ce-plan` to surface edge cases and scope boundaries. Honor their choice. If proceeding, build a task list and continue to Phase 1 step 2 |

   If discovery cannot state a concrete goal, bounded scope, and authoritative verification, clarify or route to `ce-plan` before implementation.

---

### Phase 1: Quick Start

1. **Read Plan and Clarify** _(skip if arriving from Phase 0 with a bare prompt)_

   - For unified plans, size your read. A short plan (lightweight or requirements-only, a screen or two) can be read in full. For a long implementation-ready plan, do **not** read the whole document first — it is expensive and unnecessary. Build a section map, then read only what the active unit needs: metadata, then `Goal Capsule`, `Verification Contract`, `Definition of Done`, the `Implementation Units` heading list, and only the active U-ID section plus referenced R/F/AE/KTD excerpts and any Product Contract Key Decision whose `Governs R…` links name those Rs (that reverse link is how a product decision's `session-settled:` label reaches you). Read appendices or unrelated U-IDs only when the active unit cites them. To build the map: in **markdown** scan headings (`rg -n '^#{1,3} ' <plan>` — top-level sections plus `### U<N>.` units); in **HTML** scan the `<h1>`–`<h3>` heading elements and their anchor ids. Match on the stable section names / unit IDs (`Goal Capsule`, `Verification Contract`, `### U<N>.`, …), ignoring HTML wrapper tags — not on a format-specific pattern.
   - For legacy plans, read the work document completely. Both formats (`.md`, `.html`) carry the same section names and IDs; HTML just wraps them in semantic elements (`<section>`, `<article>`, etc.).
   - Treat the plan as a decision artifact, not an execution script
   - If the plan includes sections such as `Implementation Units`, `Work Breakdown`, `Requirements` (or legacy `Requirements Trace`), `Files`, `Test Scenarios`, or `Verification`, use those as the primary source material for execution
   - Check for `Execution note` on each implementation unit — these carry the plan's natural-language execution direction for that unit (for example, start from failing proof, characterize legacy behavior, or prefer smoke/runtime verification). Note them when creating tasks, but do not reduce them to keyword matching.
   - Check for a `Deferred to Implementation` or `Implementation-Time Unknowns` section — these are questions the planner intentionally left for you to resolve during execution. Note them before starting so they inform your approach rather than surprising you mid-task
   - Check for a `Scope Boundaries` section — these are explicit non-goals. Refer back to them if implementation starts pulling you toward adjacent work
   - Review any references or links provided in the plan
   - If the user explicitly asks for TDD, test-first, characterization-first execution, or a specific verification style in this session, honor that direction even if the plan has no `Execution note`
   - If anything is unclear or ambiguous, ask clarifying questions now
   - If clarifying questions were needed above, get user approval on the resolved answers. If no clarifications were needed, proceed without a separate approval step — plan scope is the plan's authority, not something to renegotiate
   - **Do not skip this** - better to ask questions now than build the wrong thing
   - **Do not edit the plan body during execution.** The plan is a decision artifact; progress lives in JJ changes and the task tracker, not the plan. `ce-work` does not mutate the plan; whether it shipped is derived from `jj log` and the current tree. Legacy plan progress marks are not execution state.

2. **Setup Environment**

   Resolve the workspace root and inspect the current JJ change before editing:

   ```bash
   workspace_root=$(jj workspace root 2>/dev/null || pwd -P)
   jj status
   jj log -r 'ancestors(@, 3)' --no-graph
   jj log -r 'trunk()..@'
   jj diff --from 'fork_point(@ | trunk())' --to @
   jj bookmark list
   ```

   Treat the current change ID, not a branch name, as the work boundary. Bookmarks are optional publication pointers and do not need to exist during implementation.

   - If `@` is empty and undescribed, use it for the first logical unit.
   - If `@` already contains work for this plan, continue only when its description and diff match the requested scope.
   - If `@` contains unrelated work, recommend `ce-worktree` for isolation. If the user elects to remain in this workspace, start a descendant with `jj new` only after confirming the current change is a sound parent; never rewrite or mix unrelated work.
   - If the requested base is not the current parent, use `ce-worktree` to attach an isolated workspace at the intended revision. Do not fetch, rebase, abandon, or move bookmarks implicitly.
   - Resolve every run artifact under `"$workspace_root/.tmp/rocketclaw/<workflow>/<run-id>/"`. If `jj workspace root` is unavailable, the local `pwd -P` fallback above is authoritative. Do not use process-global temporary locations or generators.

   Use a separate workspace when parallel work, experiments, or an existing unrelated `@` would make the change boundary ambiguous. Workspace names are operational identifiers, not change-description or bookmark conventions.

3. **Create Task List** _(skip if Phase 0 already built one, or if Phase 0 routed as Trivial)_
   - Use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent on other harnesses) to break the plan into actionable tasks. If none is available, continue normally without simulating a task list in chat
   - Derive tasks from the plan's implementation units, dependencies, files, test targets, and verification criteria
   - When the plan defines U-IDs for Implementation Units, name each task from a brief, outcome-led form of the unit's Goal and append the stable U-ID (e.g., "Add parser coverage (U3)"). Never use a bare U-ID or lead with the identifier; the user should understand the work before the traceability label. Aim for five words or fewer before the ID
   - When the full unit list is visible, do not repeat ordinal counts such as "unit 1 of 5" in every task. Add an ordinal only when the harness exposes the current task without the surrounding list and the count materially improves orientation
   - Carry each unit's `Execution note` into the task when present
   - For each unit, read the `Patterns to follow` field before implementing — these point to specific files or conventions to mirror
   - Use each unit's `Verification` field as the primary "done" signal for that task
   - Do not expect the plan to contain implementation code, micro-step TDD instructions, or exact shell commands
   - Include dependencies between tasks
   - Prioritize based on what needs to be done first
   - Include testing and quality check tasks
   - Keep tasks specific and completable

4. **Choose Execution Engine, then Strategy**

   For an implementation-ready unified code plan, choose inline/subagent, goal-mode, or dynamic-workflow. Read `references/execution-engines.md` for the capability probe, provider mappings, plan-shape selection, copyable prompts, and tail rules. Legacy and bare-prompt work use inline/subagent execution directly.

   For the inline/subagent engine, **prefer subagents for any structured multi-unit plan** — each worker gets a fresh context window for one unit. **Parallelize independent units whenever it is safe**; fall back to serial only when parallel isn't safe or the harness can't isolate concurrent writes. Let the plan's `Dependencies` and `Files` drive batching: run an independent dependency layer together, then the next.

   | Strategy | When to use |
   |----------|-------------|
   | **Inline** | Trivial work (1-2 files, no real decomposition), work needing user interaction mid-flight, or bare prompts that lack structured units |
   | **Serial subagents** | The default for structured multi-unit plans whose units are dependent, few, or whose parallel-safety is uncertain. Fresh context per unit, executed in dependency order |
   | **Parallel subagents** | Independent units (per the Parallel Safety Check) when you want the speed and the harness can isolate concurrent work. Run a dependency layer at once, then the next |

   **Parallel Safety Check:**

   1. Start only with units whose dependency changes are accepted and whose peers in the same readiness layer do not depend on one another.
   2. Map declared files to units from each candidate's `Files:` section, then reason beyond those declarations. File overlap is necessary but not sufficient: shared types/APIs/interfaces, migrations, lockfiles, generated artifacts/clients, registry or config/schema surfaces, and an environment singleton (one dev server/port, shared database, browser session, package install, or rate limit) all create contention.
   3. Estimate expected integration and verification cost. Even isolated workers serialize when they share a contract or when reconciling their likely outputs is not obviously smaller and safer than serial authoring.
   4. Dispatch together only when dependencies, declared files, semantic surfaces, runtime resources, and expected integration cost all support independence; **decline parallelism on uncertainty**. Speed is optional.
   5. Require an isolated workspace for every concurrent worker. A synchronous native unit stays in the active JJ workspace, but a shared-workspace worker runs serially regardless of declared file disjointness.
   6. Cap concurrency at a bounded batch (~3-5 workers), even when more units appear independent.
   7. Abort criteria: broad unplanned edits, semantic overlap, out-of-scope failures, or repeated collision disables further waves; preserve or finish affected work serially.

   **Use each provider's native isolation and integrate through JJ.** Claude Code may create Git worktrees; Codex may return fork uploads; Cursor may return a winner ref or applied result; Pi may be shared or extension-isolated. Preserve those provider-managed mechanisms only as compatibility boundaries. Import returned colocated refs with `jj git import`, inspect the resulting revision, and rebase it onto the accepted JJ parent. When a provider returns only changed/created/deleted paths from a Git worktree, create a JJ workspace at the accepted parent, transfer exactly those paths, and inspect the complete JJ diff. Never create, merge, remove, or clean a Git worktree yourself. Shared-workspace workers run serially. No subagent mechanism means run inline.

   **Dispatch** uses the provider's subagent/worker mechanism. Give each worker:
   - The plan path plus a **bounded unit packet** and inherited authority — Goal Capsule, Definition of Done, the unit's section, the Verification Contract entries relevant to it, any referenced R/F/AE/KTD excerpts, **plus any Product Contract Key Decision whose `Governs R…` links name the unit's cited R-IDs** (its `session-settled:` annotation reaches the worker only through this reverse link — cited KTDs alone carry only planning-decision labels). A downstream worker may narrow that unit and authority, never broaden either. Do not send "read the whole plan" as the worker prompt. (For a legacy non-unified plan, the plan path for reference is acceptable.)
   - The unit's Goal, Files, Approach, Execution note, Patterns, Test scenarios, Verification, and any resolved deferred questions for it.
   - Instruction to check whether the unit's test scenarios cover all applicable categories (happy paths, edge cases, error paths, integration) and supplement gaps before writing tests.
   - **Instruction to choose the unit's evidence strategy and gather the evidence** (see Evidence Strategy in Phase 2) — for behavior-bearing changes, honor the Execution note and default to proof-first or characterization-first: create/update/strengthen the test and observe the red failure or characterization baseline **before** changing production code. The worker is the only party that witnesses this, so it must capture it as it goes.
   - **Instruction to report, in its final message, both (a) the file paths it changed and (b) the unit's verification evidence** — `behavior_changed`, existing tests inspected, tests added/changed or used unchanged, the red failure or characterization observed (when applicable), the verification run and result, and any deliberate no-test exception with its reason. The handoff is a text summary on most harnesses with no guaranteed diff, so reported paths are the orchestrator's starting hint (it still verifies the actual tree); the evidence fields are **not** reconstructable from the tree afterward, so a worker that omits them forces the orchestrator to re-derive or leave `verification_evidence` incomplete.
   - **Do not publish or move bookmarks.** Shared workers leave edits in `@`; isolated workers return one coherent provider checkpoint, upload, ref, patch, or JJ change ID. The orchestrator owns authoritative tests, integration, and boundaries.
   - Before writing a JJ description, active project instructions and description syntax inferred at runtime from `jj log` always win. Use `<description-composed-from-runtime-conventions>` as the neutral placeholder. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Preserve every semantic content requirement stated by this site while adapting syntax to runtime conventions. Apply compatible Go guidance only for quality, clarity, and structure; do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.

   **Shared-workspace constraints:** workers must not run `jj describe`, `jj new`, `jj split`, `jj squash`, `jj rebase`, `jj abandon`, move bookmarks, or run the full test suite concurrently. A worker may run one focused test only if it touches no shared state.

   **Permission mode:** Omit the `mode` parameter when dispatching subagents so the user's configured permission settings apply. Do not pass `mode: "auto"` — it overrides user-level settings like `bypassPermissions`.

   **After each serial unit:** review `jj diff`, run relevant tests, record evidence, update tasks, describe the coherent change, and run `jj new` before the next unit. Active project instructions and description syntax inferred at runtime from `jj log` always win. Use `<description-composed-from-runtime-conventions>` as the neutral placeholder. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Preserve every semantic content requirement stated by this site while adapting syntax to runtime conventions. Apply compatible Go guidance only for quality, clarity, and structure; do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.

   **After a parallel inline/subagent batch — the orchestrator integrates; never trust the handoff summary alone:**
   1. Wait for every worker in the batch to finish.
   2. **Inspect the actual result, not reported paths.** Use `jj status` and `jj diff` on imported/native JJ changes or the parent after provider upload/application.
   3. **Detect real collisions and semantic contention** — compare actual paths plus shared contracts, generated/config surfaces, and verification effects. Conflict-free JJ integration is not proof of compatibility. Preserve or re-run colliding units on the advancing accepted parent; never integrate blindly.
   4. **Review, test, and integrate each unit in dependency order.** Rebase imported JJ changes onto the accepted parent; use `jj split` with explicit paths when provider uploads mix units. Capture evidence and mark omissions unverified.
   5. Describe each accepted coherent change and run `jj new`. Active project instructions and description syntax inferred at runtime from `jj log` always win. Use `<description-composed-from-runtime-conventions>` as the neutral placeholder. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Preserve every semantic content requirement stated by this site while adapting syntax to runtime conventions. Apply compatible Go guidance only for quality, clarity, and structure; do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.
   6. **Release workers** through provider-native cleanup only after each result is represented by a verified, recoverable JJ change. Never abandon accepted changes or delete bookmarks as cleanup.
   7. Dispatch the next dependency layer.

### Phase 2: Execute

For every task, inspect analogous code and tests, choose an evidence strategy before changing behavior, observe the expected failing proof or characterization when applicable, implement only the bounded unit, run focused and system-wide checks, record verification evidence, and stop on an unresolved failure before closing the JJ change boundary.

2. **Incremental JJ Changes**

   After completing each task, evaluate whether to close the current change boundary:

   | Close and describe when... | Keep working when... |
   |----------------|---------------------|
   | Logical unit complete (model, service, component) | Small part of a larger unit |
   | Tests pass + meaningful progress | Tests failing |
   | About to switch contexts (backend → frontend) | Purely scaffolding with no behavior |
   | About to attempt risky/uncertain changes | Current state is partial or incoherent |

   **Heuristic:** close the boundary only when the current change is complete, reviewable, and independently valuable.

   If the plan has Implementation Units, use them as a starting guide for change boundaries, but adapt based on what you find.

   **Change-boundary workflow:**
   ```bash
   jj status
   jj diff
   jj describe -m "<description-composed-from-runtime-conventions>"
   jj new
   ```

   Active project instructions and description syntax inferred at runtime from `jj log` always win. Use `<description-composed-from-runtime-conventions>` as the neutral placeholder. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Preserve every semantic content requirement stated by this site while adapting syntax to runtime conventions. Apply compatible Go guidance only for quality, clarity, and structure; do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.

   Inspect relevant history with `jj log`. If unrelated edits are present, use `jj split` with explicit paths, inspect both changes, and describe each independently. Never stage files: JJ snapshots the working copy automatically. Resolve JJ conflicts immediately when intent is clear; otherwise undo the integration or rerun the unit serially from the accepted parent.

   Do not add creator, model, provider, tool, or runtime attribution to JJ descriptions or pull-request text.

3. **Follow Existing Patterns**

   - The plan should reference similar code - read those files first
   - Match naming conventions exactly
   - Reuse existing components where possible
   - Follow the project's coding standards already in your context
   - When in doubt, grep for similar implementations

4. **Test Continuously**

   - Run relevant tests after each significant change
   - Don't wait until the end to test
   - Fix failures immediately
   - Add new tests for new behavior, update tests for changed behavior, remove tests for deleted behavior
   - **Unit tests with mocks prove logic in isolation. Integration tests with real objects prove the layers work together.** If your change touches callbacks, middleware, or error handling — you need both.

5. **Simplify as You Go**

   After completing a cluster of related implementation units (or every 2-3 units), review recently changed files for simplification opportunities — consolidate duplicated patterns, extract shared helpers, and improve code reuse and efficiency. This is especially valuable when using subagents, since each agent works with isolated context and can't see patterns emerging across units.

   Don't simplify after every single unit — early patterns may look duplicated but diverge intentionally in later units. Wait for a natural phase boundary or when you notice accumulated complexity.

   If **`ce-simplify-code`** is available, invoke it at phase boundaries (especially before Phase 3 when the accumulated cluster has >=30 substantive changed code lines — count human-authored code, not total diff lines, so a mostly test-fixture/config/generated/mechanical cluster does not trip the gate). Otherwise, review the changed files yourself for reuse and consolidation opportunities.

   When the plan carries `session-settled:`-labeled KTDs or Key Decisions, pass the plan path as structure-pin context, not as the simplification scope, with the one-line constraint that labeled entries are structure pins the simplification must preserve (e.g., deliberate duplication stays duplicated).

6. **Figma Design Sync** (if applicable)

   For UI work with Figma designs:

   - Implement components following design specs
   - Read `references/agents/figma-design-sync.md` and dispatch a generic subagent seeded with that local prompt to compare implementation against the Figma design. Do not dispatch a standalone agent by type/name.
   - Fix visual differences identified
   - Repeat until implementation matches design

7. **Frontend Design Guidance** (if applicable)

   For UI tasks without a Figma design -- where the implementation touches view, template, component, layout, or page files, creates user-visible routes, or the plan contains explicit UI/frontend/design language:

   - Apply the frontend guidance embedded in this skill and the active repo instructions: preserve existing design-system conventions, use real UI controls and states, keep layouts responsive, and verify text does not overflow or overlap.
   - When browser tooling is available, inspect the changed UI at desktop and mobile widths before final validation. If no browser access is available, do a code-level responsive/layout review and record that browser verification was unavailable.
   - Phase 4's screenshot capture still applies when the change is user-visible.

8. **Track Progress**
   - Keep the task list updated as you complete tasks
   - Note any blockers or unexpected discoveries
   - Create new tasks if scope expands
   - Keep user informed of major milestones
   - When the plan defines U-IDs for Implementation Units, or the plan or origin document carries stable R-IDs (and optionally A/F/AE IDs), reference them in blockers, deferred-work notes, task summaries, and final verification — not routine status updates. U-IDs anchor units across plan edits; R/A/F/AE anchor product intent across the brainstorm-plan handoff. Use the IDs the plan supplies and do not invent ones it does not. This preserves traceability without burying signal under noise.

### Phase 3-4: Quality Check and Finishing Work

When all Phase 2 tasks are complete and execution transitions to quality check, you must read `references/shipping-workflow.md` for the full shipping workflow. Do not skip this.

**Code review: one portable path.** Review with `ce-code-review`, which self-sizes (lite roster for small low-risk code-only diffs, full roster otherwise). No harness-native review detection and no escalation tiers — the size/sensitive-surface judgment lives inside `ce-code-review`. Skip dedicated review only for a purely mechanical diff (formatting, dep-bumps, lint-only, generated). Full rules (autonomous Residual Gate, infra fallback) in `shipping-workflow.md`.

**Review is two steps — review, then fix.** `ce-code-review` is review-only. It returns findings (markdown or `mode:agent` JSON); it never edits the workspace, changes JJ boundaries, or applies fixes.

1. **Review** — Invoke the `ce-code-review` skill (invocation command in `references/review-findings-followup.md` § Fallback). Use `mode:agent` in orchestrated workflows; pass `plan:<path>` when you have a plan, `base:<jj-revision-or-revset>` when the stack base is known, and `depth:full` when a deep/thorough review was explicitly requested.
2. **Apply fixes** — Load `references/review-findings-followup.md`. Filter eligibility on JSON only, **batch applicable findings by file**, dispatch fix subagents (parallel when file sets are disjoint). The orchestrator integrates JJ changes, runs tests, and closes coherent boundaries; it does not pre-investigate findings.
3. **Residual Work Gate** — Only after followup; unresolved actionable findings go through the gate in `shipping-workflow.md` (autonomous sessions auto-accept + record residuals; interactive sessions ask).

## Return-to-Caller Mode

`mode:return-to-caller <plan-path>` (legacy alias: `mode:caller-owned-tail`) is
reserved for orchestrators such as `lfg` that own the post-implementation
shipping gates (final simplify, code review, pull-request creation, and CI watching).
In this mode `ce-work` performs implementation and local verification only —
including mid-implementation Phase 2 "Simplify as You Go" — then returns a
structured summary instead of running the standalone shipping tail.

Return:

- `status`: `complete`, `blocked`, or `failed`
- `plan_path`
- `changed_files`
- `u_ids_attempted`
- `u_ids_completed`
- `verification_results`
- `verification_evidence`: one entry per attempted behavior-bearing unit, plus any non-behavioral unit where tests were intentionally skipped. Each entry states the unit/task, `behavior_changed`, `existing_tests_inspected`, `tests_added_or_changed`, tests used unchanged, red failure or characterization observed when applicable, verification commands/results, and any exception reason. For units executed by subagents, this entry is assembled from each worker's returned evidence (Phase 1 Step 4), not reconstructed from the diff — the red-before-implementation observation exists only in the worker's report.
- `blockers`
- `settled_decision_conflicts`: conflicts with `session-settled:`-labeled KTDs or Key Decisions encountered during implementation — each entry names the labeled entry, the evidence, and how it was routed (proceeded-and-flagged vs blocker); empty when none
- `behavior_change`: whether behavior-bearing code changed
- `standalone_shipping_skipped: true`

Return `status: complete` only when behavior-bearing work has verification evidence or a deliberate exception. If a previous return-to-caller run implemented code but omitted evidence, a later same-plan return-to-caller run should use the idempotency check to inspect the existing work, complete the evidence, and return without reimplementing.

Engine selection (`references/execution-engines.md`) still applies in this mode,
but only for implementation. In return-to-caller mode do not emit a copyable
goal/workflow prompt — a manual paste step strands the caller; run
inline/subagents or return a blocker instead. Any goal/workflow engine used here
must not open a pull request, run the owner workflow tail, or bypass the caller-owned
gates.

## Key Principles

### Start Fast, Execute Faster

- Get clarification once at the start, then execute
- Don't wait for perfect understanding - ask questions and move
- The goal is to **finish the feature**, not create perfect process

### The Plan is Your Guide

- Work documents should reference similar code and patterns
- Load those references and follow them
- Don't reinvent - match what exists
- A KTD or Product Contract Key Decision carrying a `session-settled:` annotation (classes `user-directed` / `user-approved`) records a decision the user already made — it is not yours to improve. A product decision's label arrives through the Key Decision whose `Governs R…` links name your unit's Rs, not through a KTD. This scopes to labeled entries only: details the plan leaves open remain your judgment, and a real defect discovered inside a settled approach is still surfaced at full strength — the label never suppresses defect evidence. If implementation reveals a labeled decision is invalidating-grade unworkable (infeasible, wrong-thing, destructive), that is a genuine blocker: surface it rather than silently working around or "fixing" the decision

### Test As You Go

- Run tests after each change, not at the end
- Fix failures immediately
- Continuous testing prevents big surprises

### Quality is Built In

- Review every non-mechanical diff with `ce-code-review` (it self-sizes; see `shipping-workflow.md`)

### Ship Complete Features

- Mark all tasks completed before moving on
- Don't leave features 80% done
- A finished feature that ships beats a perfect feature that doesn't

## Common Pitfalls to Avoid

- **Analysis paralysis** - Don't overthink, read the plan and execute
- **Skipping clarifying questions** - Ask now, not after building wrong thing
- **Ignoring plan references** - The plan has links for a reason
- **Testing at the end** - Test continuously or suffer later
- **Forgetting to track progress** - Update task status as you go or lose track of what's done
- **80% done syndrome** - Finish the feature, don't move on early
- **Skipping review without reason** — review every non-mechanical diff with `ce-code-review`; skip only for a purely mechanical diff or when it is genuinely unavailable, and document the skip reason
- **Re-scoping the plan into human-time phases** - The plan's Implementation Units define the scope of execution. Do not estimate human-hours per unit, propose multi-day breakdowns, or ask the user to pick a subset of units for "this session". Agents execute at agent speed, and context-window pressure is addressed by subagent dispatch (Phase 1 Step 4), not by phased sessions. If a plan-file input is genuinely too large for a single execution, say so plainly and suggest the user return to `ce-plan` to reduce scope — don't invent session phases as a workaround. For bare-prompt input, Phase 0's Large routing already handles oversized work
