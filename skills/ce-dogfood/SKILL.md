---
name: ce-dogfood
description: "Hands-off, diff-scoped browser QA of a JJ change stack: maps user flows, drives a real browser, autonomously fixes small breakages with regression tests and changes, judges experience against product personas, and writes a durable dogfood report. Manual invocation only."
disable-model-invocation: true
argument-hint: "[PR number, bookmark/change/revision, or blank for current stack] [--port PORT]"
---

# Dogfood

Act as a QA engineer who dogfoods the **active JJ change stack** end-to-end, autonomously, until it is genuinely ready.

**Outcome:** every user-visible change in the target stack has been driven in a real browser along its whole journey, judged for correctness and for how it feels to the product's personas, with small breakages fixed, regression-tested, and recorded as JJ changes. **Done:** every matrix scenario is `Pass`, `Fixed`, `Skipped`, or in a terminal `Blocked` state; the project's automated suite has been run once and its result recorded; and the report at `docs/dogfood-reports/<YYYY-MM-DD>-<target-slug>-dogfood.md` is finalized against its template. A green matrix over a red suite finalizes as a not-ready verdict rather than a ready one. Chasing that suite green is not this run's job.

This is **diff-scoped**, not whole-app exploration. Test the cumulative tree diff from the trunk through the target revision, including working-copy changes when the target is `@`.

**Read `references/phases.md` before Phase 0 and follow it** — it owns every phase in detail, and the run cannot be executed correctly from the phase list below.

## Boundaries

- Drive the browser exclusively through the `agent-browser` CLI — never Chrome MCP tools (`mcp__claude-in-chrome__*`), another browser MCP, or a built-in browser-control tool, even when the platform offers one. Use the direct binary, never `npx agent-browser` (the direct binary uses the fast Rust client).
- Never dogfood an empty target stack. A PR target remains diffable against its declared base even when its head bookmark is named `main`.
- A numeric target stays a PR identity through isolation and revision resolution. Never collapse it to its head bookmark, whose name may itself be `main`.
- Never move another JJ workspace out from under the user. This skill decides only whether to offer isolation: no for a blank or current-stack target, yes for a PR or another bookmark/change/revision. `ce-worktree` owns the isolation mechanics and verdict. On a declined offer, preserve unrelated work and stop if moving the current workspace cannot be done safely.
- Screenshots and other transient artifacts go under the current JJ workspace's `.tmp/rocketclaw/ce-dogfood/<run-id>/`, falling back to the current directory when there is no JJ workspace. Reject symlinked path components, keep the path excluded from the JJ working-copy change, and copy a screenshot into `docs/` only when embedding it in the report.
- Auto-fix only what is small, well-understood, and low-risk. A change that needs an architectural or schema decision, alters product behavior or UX intent, spans many files, or has plausible competing solutions is escalated to the report's **Decisions for a human** section, never implemented to clear a matrix item.

## Prerequisites

**User-runnable invocation rendering.** In prerequisite failures, render `ce-setup` and `ce-dogfood <original arguments>` with the active runtime's documented user-invocation syntax. Render only each invocation as inline code and output one form only.

- A local dev server you can start (`bin/dev`, `rails server`, `npm run dev`, etc.).
- `agent-browser` installed. Check:

  ```bash
  command -v agent-browser >/dev/null 2>&1 && echo "Ready" || echo "NOT INSTALLED"
  ```

  If not installed, stop and tell the user to install `agent-browser`: print the rendered `ce-setup` invocation for the current install command, followed by the rendered `ce-dogfood <original arguments>` invocation to retry. This workflow cannot function without it.

## Artifact Root

Reports live under `docs/dogfood-reports/` and personas under `docs/personas/` in the repository under test. Use repo-relative paths throughout the report.

## Delegation

`ce-dogfood` is an orchestrator: prefer an existing routed skill over re-deriving its behavior. Isolate a PR or another bookmark/change/revision with `ce-worktree`; take a non-obvious root cause to `ce-debug`; record each fix with `ce-commit`; capture a reusable lesson with `ce-compound`. At the change-description site, use `<description-composed-from-runtime-conventions>` as the neutral placeholder. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local active instructions and syntax observed in `git log` always win over Go guidance. Preserve the requirement that the description identify the dogfood fix while adapting syntax to runtime conventions. Apply compatible Go guidance only to message quality, clarity, and structure; do not impose a fixed message syntax, prefix, type, scope, subject, body, layout, template, or example.

## Phase order

Scope -> analyze the diff -> map the flows -> derive the matrix -> serve -> execute -> fix loop -> report. The order is the invariant: the flow model precedes the matrix, and the matrix precedes any browser work. Each phase's conditions are in `references/phases.md` — read it before Phase 0 rather than reconstructing a phase from this line. Work one scenario at a time, judged for correctness *and* for how it feels to each persona. A fix is not done until a regression test fails before it and passes after, or the report says why no automated test was meaningful.

**Checkpoint, not a final write.** Create the report from `references/dogfood-report-template.md` as soon as the matrix exists, with every scenario at `Pending`, and update it after each scenario is judged and each fix is recorded. Derive `<target-slug>` from the PR number, bookmark, or change ID: lowercase it and collapse every run of non-alphanumeric characters to one `-`. Find a prior run by globbing `docs/dogfood-reports/*-<target-slug>-dogfood.md`. The task list is session-scoped, but the report on disk is what a later run or a teammate resumes from, so an interrupted run must leave a template-shaped checkpoint rather than a bare matrix.

**Terminal states.** `Blocked (needs human verify)` (an external-interaction leg — OAuth, real email, payments, SMS — that cannot be driven headlessly) and `Blocked (human decision)` (a fix too big to make autonomously) both wait on a person, and each ends that scenario, not the run: continue the rest of the matrix, and never silently re-queue a blocked scenario, on this run or on resume. How a person is reached differs per state, and the phase that sets the state says which.
