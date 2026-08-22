# Implementation Loop

For each ready task:

1. Mark it active and read only its referenced plan/code context.
2. Detect already-satisfied work from current files and verification; verify rather than reimplement.
3. Inspect local patterns and existing tests.
4. Choose evidence before behavior changes: existing failure, strengthened test, new focused failure, characterization, or deliberate no-test replacement verification.
5. Observe the intended failure/baseline when the evidence strategy requires it, then implement within scope.
6. Add, update, or remove tests to match behavior and trace callbacks, middleware, persistence failure, parallel interfaces, and cross-layer error handling when applicable.
7. Run focused and system-relevant checks, record observed evidence, inspect `jj diff --summary` and `jj diff`, then mark complete.
8. Finalize a logical Jujutsu change under the incremental-change gate below.

Cross-model execution retains host ownership of ordering, evidence, actual-scope inspection, verification, composition, and final change description. Process completion is only authoring evidence. A preserved or restoration-blocked unit stops the loop.

Parallel waves pause after each canonical composition. Recompute readiness against accepted Jujutsu changes, revalidate semantic independence, and keep dependents queued. A clean content composition is not semantic proof. Repeated collision or broad edits disable later waves.

Use proof-first or characterization-first for behavior-bearing work when a practical seam exists. Skip that order for non-behavioral, generated, or manual-only surfaces only with recorded replacement verification. Prefer strengthening the existing correct test home over duplicate coverage.

## Execution Evidence

When a unit carries an `Execution note`, honor its intent rather than matching a fixed vocabulary. For proof-first work, write or identify the relevant failing test before implementation. For characterization, capture existing behavior before changing it. For replacement verification, run the named check and record why ordinary tests were not the right proof. Without an execution note, make the same decision from code and test discovery.

- Do not write the test and implementation in the same step when working proof-first.
- Verify that a new or changed test fails for the expected reason before implementing.
- Do not over-implement beyond the current behavior slice.
- Update or strengthen the correct existing test instead of adding duplicate coverage.
- For a deliberate no-test path, record the reason and replacement verification before completion.

**Test Discovery:** Before implementing changes to a file, find existing tests that import, reference, or share naming patterns with it. Start with plan-named scenarios and files, then inspect for coverage the plan did not enumerate. New behavior needs proof, changed behavior needs updated proof, and deleted behavior needs stale tests removed or updated.

| Situation | Evidence action |
|---|---|
| Existing test already fails for the intended behavior | Use it as red evidence; do not duplicate it. |
| Existing test asserts the old or wrong expectation | Update it and observe the expected failure before implementation. |
| Existing test is over-mocked or misses the real chain | Strengthen it narrowly and observe the relevant failure. |
| No existing test covers the behavior | Add the smallest focused failing or characterization test. |
| Testing is inappropriate | Record the exception and replacement verification. |

Before writing tests for a feature-bearing unit, cover each applicable category: happy path, boundary/empty/concurrent cases, validation and downstream failures, and integration across callbacks, middleware, services, or other layers. Derive missing scenarios from the unit's Goal and Approach rather than vague labels.

Before marking a task done, inspect what fires around the change, whether tests exercise the real chain, whether failure can leave orphaned or duplicate state, what parallel interfaces expose the behavior, and whether error strategies align across layers. Leaf changes with no callbacks, persistence, or parallel interfaces may record that this system-wide check was not applicable.

## Incremental Jujutsu Changes

Finalize when a complete valuable logical unit has passing relevant checks, before a context switch, or before risky experimentation. Keep scaffolding and partial work in the current change until its logical unit is complete. Plan units guide boundaries, but current evidence decides them.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; do not impose fixed syntax or content. Use dynamic descriptions:

```bash
jj describe -m "<description derived from active project instructions and runtime jj log>"
jj new
```

Before `jj describe`, prove the current change contains only the logical unit with `jj diff --summary` and `jj diff`. If unrelated pre-work shares `@`, finish only owned paths with `jj commit -m "<description derived from active project instructions and runtime jj log>" <owned-paths>`; the unrelated remainder stays in the new working-copy change, so do not run the generic `jj describe` / `jj new` pair afterward. An isolated workspace is also acceptable. Never finalize or rewrite user-owned content.

Resolve conflicts before continuing. Use `jj status`, `jj diff`, Jujutsu conflict materialization, and the graph operation that matches local intent. Do not translate another VCS's staging workflow into Jujutsu.

## Existing Patterns And Continuous Checks

- Read plan-referenced similar code first and match its naming and structure.
- Reuse existing components where appropriate and follow active project conventions.
- Run relevant checks after each significant change and fix failures immediately.
- Use integration coverage as well as isolated tests when callbacks, middleware, persistence, retries, or cross-layer error handling interact.

## Simplification And UI

At natural phase boundaries, review recently changed files for reusable patterns and unnecessary complexity. Invoke `ce-simplify-code` when the substantive code delta meets the repository's normal threshold; do not count generated, fixture, configuration, or mechanical lines as substantive. Preserve `session-settled:` structure pins.

For UI work with Figma designs, read `references/agents/figma-design-sync.md`, dispatch a generic subagent seeded with that prompt, fix observed differences, and repeat until the implementation matches. For UI work without Figma, preserve the existing design system, use real controls and states, maintain responsive layouts, and check for overflow or overlap. Inspect desktop and mobile widths when browser tooling is available; otherwise record the code-level responsive review and the unavailable browser check.

## Progress And Settled Decisions

Keep the task list current and report blockers or material discoveries. Reference supplied U-IDs and stable R/A/F/AE IDs in blockers, deferred-work notes, task summaries, and final verification, not routine updates. Never invent identifiers or write progress into the plan.

A KTD or Product Contract Key Decision carrying a `session-settled:` annotation records a user decision, not an invitation to improve it. A product decision's label reaches a unit through the Key Decision whose `Governs R...` links name that unit's requirements. Details left open remain implementation judgment, and defect evidence is never suppressed. If a settled decision is infeasible, wrong-thing, or destructive, stop with that evidence rather than silently changing it.
