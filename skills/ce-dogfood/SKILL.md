---
name: ce-dogfood
description: "Hands-off, diff-scoped browser QA of a selected Jujutsu change: maps user flows, drives a real browser, autonomously fixes small breakages with regression tests and recorded changes, judges experience against product personas, and writes a durable dogfood report. Manual invocation only."
disable-model-invocation: true
argument-hint: "[PR number, bookmark name, or blank for current workspace] [--port PORT]"
---

# Dogfood

Act as a QA engineer who dogfoods the **selected Jujutsu change** end-to-end: understand every change, test every change in a real browser as a user would, and fix what's broken — autonomously — until the change is genuinely ready.

This is **diff-scoped**, not whole-app exploration. You test what the selected change introduced or modified versus its resolved comparison base.

## Use `agent-browser` Only For Browser Automation

This workflow drives the browser exclusively through the `agent-browser` CLI. Do not use Chrome MCP tools (`mcp__claude-in-chrome__*`), any browser MCP integration, or other built-in browser-control tools. If the platform offers multiple ways to control a browser, always choose `agent-browser`. Use the direct binary, never `npx agent-browser` (the direct binary uses the fast Rust client).

## Prerequisites

**User-runnable invocation rendering.** In prerequisite failures, default to `/ce-setup` and `/ce-dogfood <original arguments>`; use `$ce-setup` and `$ce-dogfood <original arguments>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. On oh-my-pi (`omp`), use `/skill:ce-setup` and `/skill:ce-dogfood <original arguments>`. Render only each invocation as inline code and output one form only.

- A local dev server you can start (`bin/dev`, `rails server`, `npm run dev`, etc.).
- `agent-browser` installed. Check:

  ```bash
  command -v agent-browser >/dev/null 2>&1 && echo "Ready" || echo "NOT INSTALLED"
  ```

  If not installed, stop and tell the user to install `agent-browser`: print the rendered `ce-setup` invocation for the current install command, followed by the rendered `ce-dogfood <original arguments>` invocation to retry. This workflow cannot function without it.

## Artifact Root

This skill writes dogfood reports under `<root>/dogfood-reports/` and personas under `<root>/personas/`. Resolve `<root>` when you first compose a `<root>/` path (per the block below), never before you need it. A write to `<root>/...` and a read of `<root>/solutions/` both count as composing a `<root>/` path, so either one triggers resolution; only a run that touches no `<root>/` path at all -- a scratch-only or no-workspace flow -- skips it.

<!-- rocketclaw-docs-root:start -->
**Resolve the RocketClaw artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.yaml` only (`<workspace-root>` = `jj workspace root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under its backing VCS metadata. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- rocketclaw-docs-root:end -->

## Reusing Skills

`ce-dogfood` is an orchestrator. Prefer delegating to the existing skills below over re-deriving their behavior:

| When | Skill | Why |
|------|-------|-----|
| Phase 0 isolation | `$rocketclaw:ce-worktree` | Run the dogfood in an isolated JJ workspace so the caller's workspace stays undisturbed. |
| A failure's root cause is non-obvious | `$rocketclaw:ce-debug` | Systematic root-cause analysis instead of guess-and-check. |
| Recording each fix | `$rocketclaw:ce-commit` | Coherent JJ changes with repository-appropriate descriptions. |
| A bug reveals a reusable lesson | `$rocketclaw:ce-compound` | Capture the learning so the team compounds knowledge. |

## Workflow

```
0. Scope        Select the PR, bookmark, or current change; offer an isolated JJ workspace
1. Analyze      Diff the selected change vs its resolved base, understand every change
2. Map+Matrix   Map user flows as Mermaid flowcharts, then derive the test matrix as a task list
3. Serve        Detect port, start dev server, open agent-browser
4. Execute      Work the matrix one item at a time with agent-browser
5. Fix loop     On failure: fix -> add regression test -> record the change -> continue
6. Report       Write durable doc to <root>/dogfood-reports/ (flows, matrix, fixes, learnings, verdict)
```

### Phase 0: Scope and Select the Right Change

Parse the arguments you were invoked with: a PR number, a bookmark name, or blank (use `@` in the current JJ workspace). Strip `--port PORT` if present.

1. **Identify the target without losing PR identity or changing the workspace.** A PR remains a PR throughout the run; read its GitHub metadata with `gh pr view <number> --json baseRefName,headRefName,headRefOid,isCrossRepository` and preserve the number and base identity. A bookmark remains a named JJ pointer. A blank target is `@` in the current workspace. Resolve named targets to exactly one revision after synchronizing the relevant explicit remote when necessary; use `gh pr checkout` only when it is the configured provider adapter for a fork PR, then run `jj git import` and re-resolve the revision. Preserve all GitHub operations through `gh`.
2. **Require a diffable non-default target unless it is a PR.** Resolve `trunk()` to one non-root revision and resolve the selected target to one revision. For a bookmark or `@`, stop when the target is the resolved default-line revision because there is no change to dogfood. A PR remains diffable against its base regardless of its GitHub head name. Never infer the default line from a conventional bookmark or remote name.
3. **Isolate only when selection would disturb the caller's workspace.** Keep a blank/current-workspace target in place. For a PR or a bookmark not already represented by the current working-copy change, offer isolation with the platform's blocking question tool. On yes, invoke `$rocketclaw:ce-worktree` with that target and act on its JJ-workspace verdict. On no, preserve any unrelated working-copy content and use the project's supported JJ selection mechanism to edit the resolved target in place; if that cannot be done without disturbing unrelated content, stop and ask rather than rewriting or abandoning it. Jujutsu workspaces may edit the same change; do not impose a single-workspace restriction.
4. **Resume if a prior run exists.** Look for an existing report at `<root>/dogfood-reports/*-<target-slug>-dogfood.md` (see the target-slug rule under Resumability). If one is found with unfinished scenarios, ask whether to resume it or start fresh. To resume, re-hydrate the task list from its matrix: `Pass`/`Fixed`/`Skipped` stay done; `Pending` and `in_progress` become the remaining auto-runnable work. The two `Blocked` states are **not** auto-runnable — `Blocked (needs human verify)` and `Blocked (human decision)` are waiting on a person, so surface them to the user and ask how to proceed rather than silently re-queuing them.

### Resumability (stop and return at any point)

This workflow is designed to be interrupted and resumed. Two pieces of state make that safe:

- **The task list** (the harness's task tool — `TaskCreate`/`TaskUpdate` on Claude Code, `update_plan` on Codex, or the equivalent elsewhere) is the live to-do — one task per matrix scenario. Mark each `in_progress` when you start it and `completed` only when it genuinely passes.
- **The report doc** at `<root>/dogfood-reports/<YYYY-MM-DD>-<target-slug>-dogfood.md` is the durable checkpoint that survives across sessions. For a PR use `pr-<number>`; for a bookmark, lowercase its name and collapse every run of non-alphanumeric characters to `-`; for an anonymous current change, use its stable short JJ change ID. **Create it as soon as the matrix exists (end of Phase 2) by instantiating `references/dogfood-report-template.md`** (read that template now if you haven't) so the checkpoint carries the template-owned section shape from the start — then fill in every scenario at `Pending`, and **update it incrementally** after each scenario is judged and after each fix is recorded, not only at the end. An interrupted run must leave a template-shaped checkpoint, not a bare matrix.

Because tasks are session-scoped but the report doc is on disk, the report is the source of truth for resuming. Always keep the two in sync so a later run (or a teammate) can pick up exactly where this one stopped.

### Phase 1: Analyze Changes

Resolve the selected target revision and its comparison base once, then read the full JJ diff. Use the PR's imported head revision for a PR and the resolved bookmark or `@` otherwise. For a PR, map its preserved GitHub base identity to exactly one synchronized JJ remote bookmark and resolve `BASE` as the single `fork_point(<pr-base-revision> | <target-revision>)`; otherwise use the single `fork_point(trunk() | <target-revision>)`. Stop if the base line, target, or fork point is absent, root-only, or ambiguous. Do not hard-code a default bookmark, remote, or branch name.

```text
jj log -r "trunk()" --no-graph
jj log -r "fork_point(<resolved-base-line> | <target-revision>)" --no-graph
jj diff --from <resolved-base> --to <target-revision> --name-only
jj diff --from <resolved-base> --to <target-revision>
```

Build a mental model of every change: new features, modified behavior, new routes/views/components, touched data flows. Note anything that produces user-visible behavior — that is what the matrix must cover.

**Ground in the product's personas and vision.** Look for persona and vision context so flows can be judged from real users' eyes, not just "does it work." Check, in order: `STRATEGY.md` (its "Users" section — "Who it's for" in older files — names the primary persona and their job-to-be-done), `PRODUCT.md` (its "Users" section), `VISION.md`, and any persona docs (e.g. `<root>/personas/`, `PERSONAS.md`). Capture the 1-3 primary personas and what each cares about. If none exist, infer a reasonable primary persona from the product and the diff, and say so in the report.

### Phase 2: Map the Flows, Then Build the Matrix

Do not jump straight to a flat list of pages. First **understand the user flows the diff touches**, then derive the matrix from them. A matrix built without a flow model tests pages in isolation and misses the journey — the email that "sends" but lands in the wrong thread.

#### 2a. Map the user flows (required)

For every user-visible change, trace the **complete journey** end to end and draw it. Map each flow as a **Mermaid `flowchart`** so the journey is explicit and reviewable before any testing happens — entry point, each user action, branch points (success / validation error / empty / permission-denied), side effects (emails, jobs, notifications), and the true end state.

> Email example: it's not enough that "an email sends." Does it go to the *right* recipient? When the user clicks through, does the app land on and scroll to the *right* message? Does the content make sense? Does the whole flow align with the product's vision and UX? The flowchart must carry the click-through and its destination, not stop at "email sent."

```mermaid
flowchart TD
    A[User opens /threads] --> B[Clicks 'Reply']
    B --> C{Form valid?}
    C -->|No| D[Inline validation error shown]
    C -->|Yes| E[Reply saved]
    E --> F[Notification email sent to thread participants]
    E --> G[UI scrolls to new reply, focus on it]
    F --> H[Recipient clicks email link]
    H --> I{Lands on correct thread + scrolls to the reply?}
```

Produce one flowchart per distinct journey, scaled to the diff: a one-route or copy-only change gets a single small flowchart, a multi-step feature gets several. Cover the happy path **and** the branch points (error, empty, boundary, permission). Mapping the flows before the matrix is never skipped — these diagrams ARE the understanding; they become the spine of the matrix and belong in the final report.

#### 2b. Derive the matrix from the flows

Walk each flowchart and turn every node and branch into one or more test scenarios. Read `references/test-matrix-taxonomy.md` for the full set of dimensions (journeys, functional checks, experiential checks, edge/error/empty states, accessibility, responsiveness). Cover both **functional** ("does it work?") and **experiential** ("does it feel right and align with the product?").

Map changed files to concrete routes (views -> their pages, components -> pages rendering them, layouts -> all pages, stylesheets -> visual regression on key pages) and attach those routes to the flows that exercise them.

**Load the matrix as a task list** (the harness's task tool, as above), one task per scenario, so progress is tracked and nothing is skipped. Order tasks by flow, following the flowcharts, not by file.

### Phase 3: Detect Port and Start the Dev Server

Determine the port (priority: explicit `--port` > a port explicitly stated in your in-context project instructions > `package.json` dev script > `.env*` `PORT=` > default `3000`). If a server is already listening on it, reuse it. Otherwise start the project's dev command (`bin/dev`, `rails server`, `npm run dev`, etc.) in the background and poll the port until it accepts connections before opening the browser. This skill is hands-off, so start the server automatically without asking — do not block on a confirmation.

```bash
agent-browser open "http://localhost:${PORT}"
agent-browser snapshot -i
```

### Phase 4: Execute the Matrix

Work the task list **one item at a time**. For each scenario, mark the task `in_progress`, then:

1. **Document** what you're testing (the journey and the expected outcome).
2. **Drive it** with agent-browser — navigate, snapshot for interactive refs, click, fill, submit, follow the journey to its real end state:

   ```bash
   agent-browser open "http://localhost:${PORT}/<route>"
   agent-browser snapshot -i
   agent-browser click @e1
   agent-browser fill @e2 "value"
   agent-browser screenshot "<workspace-root>/.tmp/rocketclaw/ce-dogfood/<run-id>/<scenario>.png"
   agent-browser errors      # check console/page errors
   ```

   Resolve `<workspace-root>` with `jj workspace root`, falling back to the physical current directory when JJ is unavailable, and create one unique per-run directory under `<workspace-root>/.tmp/rocketclaw/ce-dogfood/`. Write transient screenshots and dev-server logs only there. Only copy a screenshot into the report's durable location when the report embeds it; remove the run directory when its transient evidence is no longer needed.

3. **Judge** both correctness and experience: right data, right destination, sensible content, no console errors, and does it feel aligned with the product?
4. **Walk it as each persona.** Re-run the journey in your head from each primary persona's perspective (from Phase 1) and ask where they'd feel a **paper cut** — a small friction that wouldn't fail a functional test but degrades the experience: a confusing label, an extra click, an unexpected jump, a slow-feeling step, missing feedback, copy that doesn't match how that persona thinks. A scenario can be functionally `Pass` yet still carry paper cuts. Note each paper cut, which persona feels it, and its severity.
5. **Record** pass/fail plus any paper cuts, with specifics. Mark the task `completed` only when it genuinely passes. Paper cuts do not block a `Pass`, but a **sharp** paper cut (one severe enough to fix now) is routed into the Phase 5 fix loop just like a failure — apply the same auto-fix-vs-escalate judgment to it. Log the rest in the report.

**External-interaction flows** (OAuth, real email delivery, payments, SMS) can't be fully driven headlessly — pause, ask the user to verify that leg, and mark the scenario `Blocked (needs human verify)` until they confirm. Then continue.

### Phase 5: Fix Loop (Autonomous)

When a scenario fails — or a passing scenario carries a sharp paper cut worth fixing now — **fix it and prove it**, but first decide whether the fix is yours to make autonomously or a human's to decide.

**Judge the size of the fix before touching code.** Auto-fix when the change is small, well-understood, and low-risk: a clear bug with an obvious correct fix, contained to a few files, no schema/architecture/product trade-off. **Do not auto-fix** when the change is large or ambiguous — it requires an architectural or schema decision, changes product behavior or UX intent, spans many files, has plausible competing solutions, or you're not confident the "right" answer is unambiguous. Forcing a big judgment call autonomously is worse than escalating it.

**For autonomous fixes:**

1. Investigate the root cause. If it's non-obvious, invoke `$rocketclaw:ce-debug`.
2. Apply the fix in the code.
3. **Add an automated regression test** that fails before the fix and passes after, so the bug can't return. This is the default for behavioral and code bugs. When an automated test is genuinely impractical — a pure copy, spacing, or visual fix with no behavioral assertion to make — substitute a documented browser-replay or screenshot check and **state in the report why no automated test was meaningful**. Do not invent a hollow test just to satisfy the step.
4. Record one logical fix as one coherent JJ change by invoking `$rocketclaw:ce-commit`. At this change-description composition and validation site, preserve the requirement that the description identify the dogfood fix. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and descriptions visible in runtime `jj log` take precedence; apply compatible Go guidance only to quality, clarity, and structure, and do not impose a fixed prefix, type, scope, subject, body, layout, template, example, or message. The required sentence's `git log` wording is guidance, not permission to run Git; inspect history with `jj log`.
5. Re-run the failing scenario in the browser to confirm it now passes; then continue the matrix.
6. If the bug carried a reusable lesson, capture it with `$rocketclaw:ce-compound`.

**For changes too big to make autonomously:** do not implement. Record it in the report's **Decisions for a human** section with: what's broken, why it's not a safe autonomous fix, the options you see (with trade-offs), and your recommendation. Mark the scenario `Blocked (human decision)` in the matrix, then continue with the rest. Never make a large, irreversible, or product-altering change just to clear a matrix item.

Keep iterating until every task is `completed` or in a terminal `Blocked` state — `Blocked (human decision)` (escalated here) or `Blocked (needs human verify)` (set in Phase 4 for external-interaction legs). Both are terminal for the loop: they wait on a person, so do not re-queue them. Re-test anything a fix might have affected (watch for regressions in adjacent journeys).

**Before declaring the change ready, run the project's automated test suite once** (the new regression tests plus everything that already exists). Discover the test command from the project's active instructions and conventions already in your context — do not assume a specific runner. Record the result in the report; a green matrix with a red suite is not "ready."

### Phase 6: Write the Report Artifact

The report doc was created at the end of Phase 2 and updated incrementally throughout (see Resumability). When the matrix is green (or every remaining item is explicitly blocked), **finalize** it at `<root>/dogfood-reports/<YYYY-MM-DD>-<target-slug>-dogfood.md` in the workspace under test, then surface a short summary in chat with the file path.

**Finalize against `references/dogfood-report-template.md`** — the same template the Phase 2 checkpoint was instantiated from, which owns the required sections and what each must carry. Confirm every template-owned section is present and complete; do not reconstruct the section list from memory, as that drifts from the template. Carry forward the cross-phase obligations this skill produced: the Mermaid flowcharts from Phase 2a, a matrix row per scenario with its stable JJ change ID, each fix's root cause and the regression test added (or why none was meaningful), paper cuts attributed by persona, learnings worth feeding to `$rocketclaw:ce-compound`, and a final readiness verdict that records the Phase 5 automated-suite result. Do not add generated-by text, badges, promotional copy, or creator, model, provider, tool, or runtime attribution to the report.
