---
name: ce-work
description: Execute a plan or concrete work prompt end-to-end. Use when implementing from docs/plans, a spec path, or a clear build request; use ce-debug for open-ended bugs.
argument-hint: "[Plan doc path or description of work. Blank to auto use latest plan doc]"
---

# Work Execution Command

Execute work efficiently while maintaining quality and finishing features.

## Introduction

This command takes a work document (plan or specification) or a bare prompt describing the work, and executes it systematically. The focus is on **shipping complete features** by understanding requirements quickly, following existing patterns, and maintaining quality throughout.

## Input Document

The **input document** for this run is the input this skill was invoked with — present in the current prompt or conversation, whether the user provided it directly or a calling skill passed it (e.g. `lfg` in `mode:pipeline`, which passes a plan path). It may be a plan or spec path, a `mode:` token followed by a path, or a bare work prompt. The rest of this skill refers to it as `<input_document>`; if nothing was provided, treat `<input_document>` as blank.

## Execution Workflow

### Phase 0: Input Triage

**First, parse a leading mode token.** If `<input_document>` begins with `mode:return-to-caller` (or the legacy aliases `mode:caller-owned-tail` / `caller:lfg`), strip that token before anything else: the remainder of the string is the plan path, and this run executes in **Return-to-Caller Mode** (see § Return-to-Caller Mode) — implement and locally verify only, then return the structured envelope instead of running the standalone shipping tail. Classify the stripped plan path with the rules below. A mode token with no following path is an error: report it rather than treating `mode:return-to-caller` as a bare prompt.

Determine how to proceed based on what was provided in `<input_document>` (after any mode token is stripped).

**Plan document** (input is a file path to an existing plan or specification): read the plan's metadata first — YAML frontmatter for a markdown plan, or the visible header text for an HTML plan (both formats carry the same fields).

- If it carries `artifact_contract: ce-unified-plan/v1`, classify `artifact_readiness` before reading the body.
  - `artifact_readiness: requirements-only` -> stop and tell the user this Product Contract needs `ce-plan` enrichment before implementation. Offer the exact `ce-plan <plan-path>` handoff.
  - `artifact_readiness: implementation-ready` plus `execution: code` -> continue to Phase 1 using the unified-plan reader strategy below.
  - Any other readiness value or any non-code/unclassified execution mode -> do not auto-execute as code. Route `execution: knowledge-work` to the non-code carve-out; otherwise ask the user to return to `ce-plan` to produce an implementation-ready code plan.
  - Progress-like values (`active`, `in_progress`, `completed`, `done`) are invalid readiness values. Stop and ask for plan repair rather than guessing.
- If it carries `execution: knowledge-work`, this is a **non-code plan** — read `references/non-code-execution.md` and follow that carve-out instead of the rest of this workflow.
- Otherwise (legacy plan, field absent, or `execution: code`) -> continue to Phase 1 and run the normal code lifecycle.

**Blank invocation latest-plan discovery:** when `<input_document>` is blank, glob `docs/plans/*.md` and `docs/plans/*.html`, inspect metadata for the newest candidates, and only auto-select a plan that is `artifact_readiness: implementation-ready` plus `execution: code` or a legacy code plan. Stop instead of silently executing when the newest matching artifact is requirements-only, `execution: knowledge-work`, an approach-plan, or an unclassified universal/answer-seeking output. Ask for an explicit path or a `ce-plan` enrichment step. **Superseded sibling:** if a requirements-only candidate has a same-basename file in the other format (`<basename>.md` / `<basename>.html`) that is `implementation-ready`, a format conversion left the requirements-only copy stale — select the implementation-ready sibling and execute it rather than stopping.

**Bare prompt** (input is a description of work, not a file path):

1. **Scan the work area**

   - Identify files likely to change based on the prompt
   - Find existing test files for those areas (search for test/spec files that import, reference, or share names with the implementation files)
   - Note local patterns and conventions in the affected areas

2. **Assess complexity and route**

   | Complexity | Signals | Action |
   |-----------|---------|--------|
   | **Trivial** | 1-2 files, no behavioral change (typo, config, rename) | Proceed to Phase 1 step 2 (environment setup), then implement directly — no task list, no execution loop. Apply Test Discovery if the change touches behavior-bearing code |
   | **Small / Medium** | Clear scope, under ~10 files | Build a task list from discovery. Proceed to Phase 1 step 2 |
   | **Large** | Cross-cutting, architectural decisions, 10+ files, touches auth/payments/migrations | Inform the user this would benefit from `/ce-brainstorm` or `/ce-plan` to surface edge cases and scope boundaries. Honor their choice. If proceeding, build a task list and continue to Phase 1 step 2 |

---

### Phase 1: Quick Start

1. **Read Plan and Clarify** _(skip if arriving from Phase 0 with a bare prompt)_

   - For unified plans, size your read. A short plan (lightweight or requirements-only, a screen or two) can be read in full. For a long implementation-ready plan, do **not** read the whole document first — it is expensive and unnecessary. Build a section map, then read only what the active unit needs: metadata, then `Goal Capsule`, `Verification Contract`, `Definition of Done`, the `Implementation Units` heading list, and only the active U-ID section plus referenced R/F/AE/KTD excerpts. Read appendices or unrelated U-IDs only when the active unit cites them. To build the map: in **markdown** scan headings (`rg -n '^#{1,3} ' <plan>` — top-level sections plus `### U<N>.` units); in **HTML** scan the `<h1>`–`<h3>` heading elements and their anchor ids. Match on the stable section names / unit IDs (`Goal Capsule`, `Verification Contract`, `### U<N>.`, …), ignoring HTML wrapper tags — not on a format-specific pattern.
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
   - **Do not edit the plan body during execution.** The plan is a decision artifact; progress lives in JJ changes and the task tracker, not the plan. `ce-work` does not mutate the plan — whether it shipped is derived from JJ history, not recorded in the doc. Legacy plans may contain `- [ ]` / `- [x]` marks on unit headings or a `status:` field — ignore them as state; per-unit completion is determined during execution by reading the current file state.

2. **Setup Environment**

   First, inspect the current workspace change, its nearest bookmark ancestors, and the trunk-relative stack:

   ```bash
   jj status
   jj workspace list
   jj log -r '@ | @- | trunk() | heads(::@ & bookmarks())'
   jj log -r 'trunk()..@'
   jj log -r 'trunk()..@ & ~empty()'
   ```

   `@` is this workspace's working-copy change and `trunk()` resolves the configured default remote bookmark. JJ has no active/current bookmark: a bookmark is only a named pointer, and `jj commit` does not advance it. Treat `heads(::@ & bookmarks())` as naming context, not as a selected line of development.

   **If `trunk()..@ & ~empty()` contains feature work:**

   Check whether the nearest non-trunk bookmark, if any, is **meaningful** — a name like `feat/crowd-sniff` or `fix/email-validation` tells future readers what the stack is about. Auto-generated workspace names (e.g., `workspace-jolly-beaming-raven`) or other opaque names do not imply a meaningful bookmark. If there is no feature bookmark, continuing the unnamed stack is valid; create one only when naming or pushing the stack is useful.

   If an existing feature bookmark is meaningless or auto-generated, suggest renaming it before continuing:
   ```bash
   jj bookmark rename <old-name> <meaningful-name>
   ```
   Derive the new name from the plan title or work description (e.g., `feat/crowd-sniff`). Present the rename as a recommended option alongside continuing as-is.

   Then ask: "Continue the current change stack, or start a new change/workspace from `trunk()`?"
   - If continuing (with or without a bookmark rename), proceed to step 3
   - If starting new, follow Option A or B below

   **If `trunk()..@ & ~empty()` has no feature work**, choose how to proceed. Do not edit `trunk()` itself; create a mutable descendant change.

   **Option A: Create a new change in the current workspace**
   ```bash
   jj git fetch
   jj new 'trunk()'
   ```
   A bookmark is optional until shipping. If one is useful for naming the stack early, create it explicitly with `jj bookmark create <meaningful-name> -r @`, then remember that later `jj commit` calls leave it behind until `jj bookmark move <name> --to @-` or `jj bookmark advance <name> --to @-`.

   **Option B: Use a workspace (recommended for parallel development)**
   ```bash
   skill: ce-worktree
   # Ensures isolation: detects an existing workspace, prefers the harness's
   # native workspace tool, else creates one from the default bookmark
   ```

   **Recommendation**: Use workspace if:
   - You want to work on multiple features simultaneously
   - You want to keep the default bookmark clean while experimenting
   - You plan to switch between changes frequently

3. **Create Task List** _(skip if Phase 0 already built one, or if Phase 0 routed as Trivial)_
   - Use the platform's task tracking tool (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent on other harnesses) to break the plan into actionable tasks
   - Derive tasks from the plan's implementation units, dependencies, files, test targets, and verification criteria
   - When the plan defines U-IDs for Implementation Units, preserve the unit's U-ID as a prefix in the task subject (e.g., "U3: Add parser coverage"). This keeps blocker references, deferred-work notes, and final summaries anchored to the same identifier the plan uses, so progress and traceability remain unambiguous across plan edits
   - Carry each unit's `Execution note` into the task when present
   - For each unit, read the `Patterns to follow` field before implementing — these point to specific files or conventions to mirror
   - Use each unit's `Verification` field as the primary "done" signal for that task
   - Do not expect the plan to contain implementation code, micro-step TDD instructions, or exact shell commands
   - Include dependencies between tasks
   - Prioritize based on what needs to be done first
   - Include testing and quality check tasks
   - Keep tasks specific and completable

4. **Choose Execution Engine, then Strategy**

   For an implementation-ready unified code plan, first pick the **engine** that runs implementation: inline/subagent (default and only callable engine on Claude Code), goal-mode, or dynamic-workflow. Goal-mode and dynamic-workflow are usable only when the host exposes a callable primitive for them — Codex exposes `create_goal` (a skill can start a goal directly), while Claude Code exposes no goal tools, so on Claude Code they are prompt-emission only (never invoked from inside this skill). Prefer dynamic-workflow over goal-mode for large fan-out plans (many independent U-IDs, codebase-wide sweeps, migrations, adversarial cross-checking). Read `references/execution-engines.md` for the host-capability probe, the plan-shape selection table, the copyable goal-mode/`ultracode:` prompts, and the resume-tail rules. An engine choice never changes tail ownership — after implementation, resume standalone quality gates in normal use, or return the return-to-caller envelope when invoked by `lfg`. Legacy and bare-prompt work skip this and use the inline/subagent engine directly.

   For the inline/subagent engine, **prefer subagents for any structured multi-unit plan** — each worker gets a fresh context window for one unit. **Parallelize independent units whenever it is safe**; fall back to serial only when parallel isn't safe or the harness can't isolate concurrent writes. Let the plan's `Dependencies` and `Files` drive batching: run an independent dependency layer together, then the next.

   | Strategy | When to use |
   |----------|-------------|
   | **Inline** | Trivial work (1-2 files, no real decomposition), work needing user interaction mid-flight, or bare prompts that lack structured units |
   | **Serial subagents** | The default for structured multi-unit plans whose units are dependent, few, or whose parallel-safety is uncertain. Fresh context per unit, executed in dependency order |
   | **Parallel subagents** | Independent units (per the Parallel Safety Check) when you want the speed and the harness can isolate concurrent work. Run a dependency layer at once, then the next |

   **Parallel Safety Check** — before dispatching a batch in parallel:

   1. Map files to units from each candidate unit's `Files:` section (Create/Modify/Test paths).
   2. **File overlap is necessary but not sufficient.** Also serialize units that contend on things absent from `Files:`: shared types/APIs/interfaces, DB migrations, generated artifacts or clients, lockfiles, snapshots, shared config/schema — or an **environment singleton** (one dev server/port, a shared database, browser sessions, package installs, MCP rate limits). Reason about these; don't just diff paths.
   3. **No contention:** dispatch the batch in parallel.
   4. **Contention with harness-native isolation:** parallel is *recoverable* (isolated workers don't lose each other's writes) but **not automatically safe** — overlapping edits still need deliberate reconciliation after rebasing the JJ changes together. Serialize contending units by default; run them parallel-isolated only when the expected reconciliation is trivial. Log the predicted overlap.
   5. **Contention without isolation (shared workspace):** serialize — in a shared directory only the last writer survives.
   6. **Cap concurrency** at a bounded batch (~3-5 workers) even when more units are independent; over-parallelizing costs more in contention, conflict resolution, and integration than it saves.
   7. **Abort criteria:** if a batch produces broad unplanned edits, out-of-scope test failures, or repeated conflicts, stop parallelizing and finish the rest serially.

   **Isolation is the harness's job, never ce-work's** — never run `jj workspace add` yourself. Probe what your subagent mechanism provides and pick the parallel path:
   - **Harness-native isolated workers** — each worker edits an isolated workspace the harness manages: a native isolated-agent tool, a coding worker with a forked workspace, or an equivalent best-of-N runner. When a repository-local harness path is needed, use `.rocketclaw/workspaces/`. Parallelize freely here, including overlapping-file units (subject to the Safety Check's reconciliation-cost judgment). This works even when you are *already* inside a workspace — harness workspaces are peers of one repository, not nested, and their working-copy changes can be addressed as `<workspace>@`.
   - **Shared workspace only** — subagents run in your working directory (Cursor `Task` default, or any harness without isolation). Parallelize **disjoint-file units only**, under the shared-workspace constraints below; contending units run serial.
   - **No subagent mechanism:** run inline.

   **Dispatch** uses your harness's subagent/worker mechanism. Give each worker:
   - The plan path plus a **bounded unit packet** — Goal Capsule, Definition of Done, the unit's section, the Verification Contract entries relevant to it, and any referenced R/F/AE/KTD excerpts. Do not send "read the whole plan" as the worker prompt. (For a legacy non-unified plan, the plan path for reference is acceptable.)
   - The unit's Goal, Files, Approach, Execution note, Patterns, Test scenarios, Verification, and any resolved deferred questions for it.
   - Instruction to check whether the unit's test scenarios cover all applicable categories (happy paths, edge cases, error paths, integration) and supplement gaps before writing tests.
   - **Instruction to choose the unit's evidence strategy and gather the evidence** (see Evidence Strategy in Phase 2) — for behavior-bearing changes, honor the Execution note and default to proof-first or characterization-first: create/update/strengthen the test and observe the red failure or characterization baseline **before** changing production code. The worker is the only party that witnesses this, so it must capture it as it goes.
   - **Instruction to report, in its final message, both (a) the file paths it changed, (b) its JJ workspace name when isolated, and (c) the unit's verification evidence** — `behavior_changed`, existing tests inspected, tests added/changed or used unchanged, the red failure or characterization observed (when applicable), the verification run and result, and any deliberate no-test exception with its reason. The handoff is a text summary on most harnesses with no guaranteed diff, so reported paths are the orchestrator's starting hint (it still verifies the actual change); the evidence fields are **not** reconstructable from the tree afterward, so a worker that omits them forces the orchestrator to re-derive or leave `verification_evidence` incomplete.
   - **Do not run `jj commit`, `jj split`, `jj describe`, or move/create bookmarks.** JJ automatically snapshots edits into the worker workspace's working-copy change. Leave the unit in that single change; the **orchestrator owns describing, splitting, rebasing, and authoritative test runs**. (Capability note: a harness that reaps its isolated workspace on completion would need a different handoff; confirm before assuming it.)

   **Shared-workspace constraints** — when subagents share your working directory (no isolation): they must not run `jj commit`, `jj split`, `jj describe`, `jj rebase`, or bookmark commands, and must not run the full test suite concurrently; the orchestrator separates the combined `@` with filesets after the batch. A worker may run a single focused unit test only if it touches no shared state.

   **Permission mode:** Omit the `mode` parameter when dispatching subagents so the user's configured permission settings apply. Do not pass `mode: "auto"` — it overrides user-level settings like `bypassPermissions`.

   **After each serial unit:** review `jj diff` against the unit's scope and `Files:`, run the relevant tests, fix before dispatching the next, record the worker's verification evidence, then integrate it using the isolated-workspace describe/rebase/new sequence below or fileset-commit shared `@`. Update the task list; never edit the plan body. Then dispatch the next unit from the integrated tip.

   **After a parallel batch — the orchestrator integrates JJ changes; never trust the handoff summary alone:**
   1. Wait for every worker in the batch to finish.
   2. **Inspect the actual change, not reported paths.** For an isolated JJ workspace, use `jj -R <workspace-root> status`, `jj diff -r '<workspace-name>@'`, and `jj diff -r '<workspace-name>@' --name-only`; for a shared workspace inspect `jj status` and `jj diff -r @`. Reported paths are a hint; declared `Files:` are often incomplete.
   3. **Detect real collisions** — 2+ workers that actually modified the same file. In a shared workspace only the last writer survived: fileset-commit the non-colliding work first, then re-run colliding units serially. With isolated workspaces, serialize overlapping changes and expect JJ to record any conflict when the later change is rebased onto the integrated tip.
   4. **Review, test, and integrate each unit in dependency order — the orchestrator owns change history.** Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local conventions take precedence; otherwise retain compatible Go guidance such as a concise imperative summary. For an isolated worker, set its description with `jj describe -r '<workspace-name>@' -m '<message describing the completed unit>'`, then `jj rebase -s '<workspace-name>@' -o @` and advance the orchestrator with `jj new '<workspace-name>@'`; this preserves the worker's change identity and creates a fresh `@` for the next unit. For shared-workspace edits, commit only the unit's fileset with `jj commit <filesets> -m '<message describing the completed unit>'`. Run relevant tests and resolve any recorded conflicts before the next unit. Capture each worker's returned verification evidence into the roll-up; never fabricate a red-before-implementation observation.
   5. Update the task list (progress lives in the described changes).
   6. **Release the workers** — close each worker handle, obtain its root with `jj workspace root --name <workspace>`, run `jj workspace forget <workspace>`, then remove that harness-created workspace directory. Delete a bookmark only if the harness explicitly created a disposable one; JJ workspaces do not inherently require bookmarks.
   7. Dispatch the next dependency layer.

   **Per-harness integration (examples — the universal flow above is the contract):**
   - **Claude `Agent` `isolation:"workspace"`:** address each worker by its `<workspace-name>@` revset and use the describe/rebase/new sequence above. If the rebased change is conflicted, inspect with `jj status`/`jj diff`, resolve deliberately, and verify; if intent cannot be preserved confidently, `jj abandon <worker-change>` and re-run the unit serially from the integrated tip.
   - **Codex `spawn_agent` worker:** integrate the worker's "uploaded changes," then `close_agent`.
   - **Cursor `Task` (shared workspace):** edits are already in your tree — review and commit per step 4; **`best-of-n-runner`:** integrate its workspace.

### Phase 2: Execute

1. **Task Execution Loop**

   For each task in priority order:

   ```
   while (tasks remain):
     - Mark task as in-progress
     - Read any referenced files from the plan or discovered during Phase 0
     - **If the unit's work is already present and matches the plan's intent** (files exist with the expected capability, or the unit's `Verification` criteria are already satisfied by the current code), the work has likely shipped on a prior bookmark or session. Verify it matches, mark the task complete, and move on. Do not silently reimplement.
     - Look for similar patterns in codebase
     - Find existing test files for implementation files being changed (Test Discovery — see below)
     - Choose the evidence strategy for this task before changing behavior: use an existing failing test, update or strengthen an existing test, add a new failing test, add characterization coverage, or record a deliberate no-test exception with replacement verification
     - For behavior-bearing changes, default to test-first or characterization-first when the current code and test surface make that practical, even if the plan has no `Execution note`
     - When the evidence strategy calls for pre-implementation proof, create/update/strengthen the test or characterization coverage now and verify the expected failure or baseline capture before changing production code
     - Implement following existing conventions
     - Add, update, or remove any remaining tests needed to match implementation changes (see Test Discovery below)
     - Run System-Wide Test Check (see below)
     - Run tests after changes
     - Assess testing coverage: did this task change behavior? If yes, were existing tests inspected and were tests written, updated, strengthened, or deliberately left unchanged with a reason? If no tests were added or changed, is the justification deliberate (e.g., pure config, no behavioral change, manual-only surface) and paired with replacement verification?
     - Record verification evidence for the task: behavior-change signal, existing tests inspected, tests added/changed/used unchanged, red failure or characterization observed when applicable, verification run, and any exception reason
     - Mark task as completed
     - Evaluate for incremental commit (see below)
   ```

   When a unit carries an `Execution note`, honor its intent rather than matching a fixed vocabulary. For notes that ask for proof-first work, write or identify the relevant failing test before implementation for that unit. For notes that ask for characterization, capture existing behavior before changing it. For notes that point away from unit coverage, run the named replacement verification and record why ordinary tests were not the right proof. For units without an `Execution note`, make the same decision from code and test discovery: upgrade to proof-first or characterization-first when behavior changes and the seam is practical; proceed pragmatically only when the task is non-behavioral or the exception is deliberate.

   Guardrails for execution evidence:
   - Do not write the test and implementation in the same step when working proof-first
   - Do not skip verifying that a new or changed test fails for the expected reason before implementing the fix or feature
   - Do not over-implement beyond the current behavior slice when working proof-first
   - Do not add a duplicate regression test when an existing test is the right home; update or strengthen that test instead, then observe the failure before changing code
   - Skip proof-first discipline for trivial renames, pure configuration, pure styling, generated artifacts, and manual-only surfaces, but record the reason and replacement verification while continuing execution

   **Test Discovery** — Before implementing changes to a file, find its existing test files (search for test/spec files that import, reference, or share naming patterns with the implementation file). When a plan specifies test scenarios or test files, start there, then check for additional test coverage the plan may not have enumerated. Changes to implementation files should be accompanied by corresponding test updates — new tests for new behavior, modified tests for changed behavior, removed or updated tests for deleted behavior.

   **Evidence Strategy** — Test discovery decides where proof belongs:

   | Situation | Action |
   |-----------|--------|
   | Existing test already fails for the intended behavior | Use that as the red evidence; do not add a duplicate test |
   | Existing test covers the contract but asserts the old or wrong expectation | Update that test, run it, and verify the expected failure before implementation |
   | Existing test is over-mocked or misses the real chain | Strengthen/refactor it narrowly, then verify it fails for the right reason |
   | No existing test covers the behavior | Add the smallest focused failing test or characterization test that proves the behavior slice |
   | Testing is inappropriate for the task | Record the no-test exception and replacement verification before marking the task complete |

   **Test Scenario Completeness** — Before writing tests for a feature-bearing unit, check whether the plan's `Test scenarios` cover all categories that apply to this unit. If a category is missing or scenarios are vague (e.g., "validates correctly" without naming inputs and expected outcomes), supplement from the unit's own context before writing tests:

   | Category | When it applies | How to derive if missing |
   |----------|----------------|------------------------|
   | **Happy path** | Always for feature-bearing units | Read the unit's Goal and Approach for core input/output pairs |
   | **Edge cases** | When the unit has meaningful boundaries (inputs, state, concurrency) | Identify boundary values, empty/nil inputs, and concurrent access patterns |
   | **Error/failure paths** | When the unit has failure modes (validation, external calls, permissions) | Enumerate invalid inputs the unit should reject, permission/auth denials it should enforce, and downstream failures it should handle |
   | **Integration** | When the unit crosses layers (callbacks, middleware, multi-service) | Identify the cross-layer chain and write a scenario that exercises it without mocks |

   **System-Wide Test Check** — Before marking a task done, pause and ask:

   | Question | What to do |
   |----------|------------|
   | **What fires when this runs?** Callbacks, middleware, observers, event handlers — trace two levels out from your change. | Read the actual code (not docs) for callbacks on models you touch, middleware in the request chain, `after_*` hooks. |
   | **Do my tests exercise the real chain?** If every dependency is mocked, the test proves your logic works *in isolation* — it says nothing about the interaction. | Write at least one integration test that uses real objects through the full callback/middleware chain. No mocks for the layers that interact. |
   | **Can failure leave orphaned state?** If your code persists state (DB row, cache, file) before calling an external service, what happens when the service fails? Does retry create duplicates? | Trace the failure path with real objects. If state is created before the risky call, test that failure cleans up or that retry is idempotent. |
   | **What other interfaces expose this?** Mixins, DSLs, alternative entry points (Agent vs Chat vs ChatMethods). | Grep for the method/behavior in related classes. If parity is needed, add it now — not as a follow-up. |
   | **Do error strategies align across layers?** Retry middleware + application fallback + framework error handling — do they conflict or create double execution? | List the specific error classes at each layer. Verify your rescue list matches what the lower layer actually raises. |

   **When to skip:** Leaf-node changes with no callbacks, no state persistence, no parallel interfaces. If the change is purely additive (new helper method, new view partial), the check takes 10 seconds and the answer is "nothing fires, skip."

   **When this matters most:** Any change that touches models with callbacks, error handling with fallback/retry, or functionality exposed through multiple interfaces.


2. **Incremental Changes**

   After completing each task, evaluate whether to describe an incremental change:

   | Describe when... | Wait when... |
   |----------------|---------------------|
   | Logical unit complete (model, service, component) | Small part of a larger unit |
   | Tests pass + meaningful progress | Tests failing |
   | About to switch contexts (backend → frontend) | Purely scaffolding with no behavior |
   | About to attempt risky/uncertain changes | The change does not yet express complete value |

   **Heuristic:** describe the change when it expresses complete, valuable work; otherwise wait.

   If the plan has Implementation Units, use them as a starting guide for change boundaries, but adapt based on what you find during implementation. A unit might need multiple changes if it is larger than expected, or small related units might land together. Use each unit's Goal to inform the description.

   **Change-description workflow:**

   Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local conventions take precedence; otherwise retain compatible Go guidance such as a concise imperative summary.
   ```bash
   # 1. Verify tests pass (use project's test command)
   # Examples: bin/rails test, npm test, pytest, go test, etc.

   # 2. Select only files related to this logical unit with JJ filesets.
   # There is no staging area; positional filesets remain in the described
   # change while all other edits move to the new working-copy change.

   # 3. Describe the completed logical unit without imposing a fixed syntax.
   jj commit <filesets for this logical unit> -m "<message describing the completed logical unit>"
   ```

   Use workspace-relative `root:`/`root-file:` filesets when commands may run below the workspace root; quote fileset expressions containing operators. Verify the remainder with `jj status` and the committed unit with `jj show @-`.

   **Handling conflicts:** `jj rebase` and multi-parent `jj new <left> <right>` can succeed while recording first-class conflicts; there is no `--continue` step. Inspect `jj status` and `jj diff`, resolve markers or use `jj resolve`, and verify `conflicts()` is empty for the shipping stack before proceeding. Incremental changes keep resolution scoped.

   **Note:** Change descriptions contain only repository-relevant semantic content; do not add non-project footers or identity metadata.

   **Parallel subagent mode:** History ownership stays with the orchestrator (see Phase 1 Step 4):
   - **Workspace-isolated:** each subagent leaves one working-copy change; the orchestrator describes and rebases `<workspace>@` changes in dependency order.
   - **Shared-workspace fallback:** subagents leave combined edits in `@`; the orchestrator separates each unit with fileset arguments to `jj commit`.

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

   If **`ce-simplify-code`** is available, invoke it at phase boundaries (especially before Phase 3 when the diff is >=30 lines). Otherwise, review the changed files yourself for reuse and consolidation opportunities.

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

**Review is two steps — review, then fix.** `ce-code-review` is review-only. It returns findings (markdown or `mode:agent` JSON); it never edits the workspace change, describes/commits it, or applies fixes.

1. **Review** — Invoke the `ce-code-review` skill (invocation command in `references/review-findings-followup.md` § Fallback). Use `mode:agent` in orchestrated workflows; pass `plan:<path>` when you have a plan, `base:trunk()` (or the explicit base revset) when known, and `depth:full` when a deep/thorough review was explicitly requested. Inspect the same range directly with `jj diff --from 'trunk()' --to @` and `jj log -r 'trunk()..@'`.
2. **Apply fixes** — Load `references/review-findings-followup.md`. Filter eligibility on JSON only, **batch applicable findings by file**, dispatch fix subagents (parallel when file sets are disjoint). The orchestrator integrates JJ changes, runs tests, and commits logical units — it does not pre-investigate findings.
3. **Residual Work Gate** — Only after followup; unresolved actionable findings go through the gate in `shipping-workflow.md` (autonomous sessions auto-accept + record residuals; interactive sessions ask).

## Return-to-Caller Mode

`mode:return-to-caller <plan-path>` (legacy alias: `mode:caller-owned-tail`) is
reserved for orchestrators such as `lfg` that own simplification, code review,
PR creation, and CI watching after implementation. In this mode `ce-work`
performs implementation and local verification only, then returns a structured
summary instead of running the standalone shipping tail.

Return:

- `status`: `complete`, `blocked`, or `failed`
- `plan_path`
- `changed_files`
- `u_ids_attempted`
- `u_ids_completed`
- `verification_results`
- `verification_evidence`: one entry per attempted behavior-bearing unit, plus any non-behavioral unit where tests were intentionally skipped. Each entry states the unit/task, `behavior_changed`, `existing_tests_inspected`, `tests_added_or_changed`, tests used unchanged, red failure or characterization observed when applicable, verification commands/results, and any exception reason. For units executed by subagents, this entry is assembled from each worker's returned evidence (Phase 1 Step 4), not reconstructed from the diff — the red-before-implementation observation exists only in the worker's report.
- `blockers`
- `behavior_change`: whether behavior-bearing code changed
- `standalone_shipping_skipped: true`

Return `status: complete` only when behavior-bearing work has verification evidence or a deliberate exception. If a previous return-to-caller run implemented code but omitted evidence, a later same-plan return-to-caller run should use the idempotency check to inspect the existing work, complete the evidence, and return without reimplementing.

Engine selection (`references/execution-engines.md`) still applies in this mode,
but only for implementation. In return-to-caller mode do not emit a copyable
goal/workflow prompt — a manual paste step strands the caller; run
inline/subagents or return a blocker instead. Any goal/workflow engine used here
must not open a PR, run the owner workflow tail, or bypass the caller-owned
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
- **Re-scoping the plan into human-time phases** - The plan's Implementation Units define the scope of execution. Do not estimate human-hours per unit, propose multi-day breakdowns, or ask the user to pick a subset of units for "this session". Agents execute at agent speed, and context-window pressure is addressed by subagent dispatch (Phase 1 Step 4), not by phased sessions. If a plan-file input is genuinely too large for a single execution, say so plainly and suggest the user return to `/ce-plan` to reduce scope — don't invent session phases as a workaround. For bare-prompt input, Phase 0's Large routing already handles oversized work
