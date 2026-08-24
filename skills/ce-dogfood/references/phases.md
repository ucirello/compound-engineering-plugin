# Dogfood phases 0-6

Required read before Phase 0. Full detail for every phase; the skill body carries the outcome, the boundaries, the phase order, and the terminal states.

### Phase 0: Scope and Get on the Right Revision

Parse the arguments you were invoked with: a PR number, a Jujutsu bookmark/revision, or blank (use the current change `@`). Strip `--port PORT` if present.

1. **Identify the target without moving the working copy.** Preserve a PR number as PR identity. Read its base/head repository, bookmark, and object metadata with `gh pr view`, then resolve those GitHub refs to Jujutsu remote bookmarks after `jj git fetch`; do not reduce a fork PR to an ambiguous bare bookmark. A bookmark/revision target resolves through Jujutsu revset syntax, and a blank target is `@`; Jujutsu has no current or checked-out bookmark. Require each selected revset to resolve to one revision. Record the target revision, stable change ID, display label, and base revision; for non-PR targets the base is `trunk()`.
2. **Refuse a non-PR target that resolves to `trunk()`.** There is no target diff to dogfood. A PR remains diffable against its declared base even when its head bookmark has a trunk-like name.
3. **Decide isolation by what you're testing; let `ce-worktree` own workspace mechanics.** Do not re-derive workspace detection or creation here. For a blank target, dogfood the current workspace in place because the current Jujutsu change is already the target. For a PR or another revision, offer isolation with the platform's blocking question tool. On **yes**, invoke `ce-worktree` with the resolved Jujutsu target revision and act on its verdict. On **no**, use `jj new <target-revision>` to create a working-copy change on the target only after confirming if moving the current working copy would disturb active work; never mutate the primary workspace silently. Use `jj edit <target-revision>` instead only when the user explicitly wants the existing change rewritten.
4. **Resume if a prior run exists.** Look for an existing report at `<root>/dogfood-reports/*-<target-slug>-dogfood.md` (see the target-slug rule under Resumability). If one is found with unfinished scenarios, ask whether to resume it or start fresh. To resume, re-hydrate the task list from its matrix: `Pass`/`Fixed`/`Skipped` stay done; `Pending` and `in_progress` become the remaining auto-runnable work. The two `Blocked` states are **not** auto-runnable: `Blocked (needs human verify)` and `Blocked (human decision)` wait on a person, so surface them to the user and ask how to proceed rather than silently re-queuing them.

### Resumability (stop and return at any point)

This workflow is designed to be interrupted and resumed. Two pieces of state make that safe:

- **The task list** (the harness's task tool — `TaskCreate`/`TaskUpdate` on Claude Code, `update_plan` on Codex, or the equivalent elsewhere) is the live to-do — one task per matrix scenario. Mark each `in_progress` when you start it and `completed` only when it genuinely passes.
- **The report doc** at `<root>/dogfood-reports/<YYYY-MM-DD>-<target-slug>-dogfood.md` is the durable checkpoint that survives across sessions. `<target-slug>` is the selected bookmark, revision label, or short change ID lowercased with every run of non-alphanumeric characters collapsed to a single `-` (e.g. `feature/Foo_Bar` -> `feature-foo-bar`). **Create it as soon as the matrix exists (end of Phase 2) by instantiating `references/dogfood-report-template.md`** so the checkpoint carries the template-owned section shape from the start, fill every scenario at `Pending`, and update it after each scenario is judged and each fix change is finalized. An interrupted run must leave a template-shaped checkpoint, not a bare matrix.

Because tasks are session-scoped but the report doc is on disk, the report is the source of truth for resuming. Always keep the two in sync so a later run (or a teammate) can pick up exactly where this one stopped.

### Phase 1: Analyze Changes

Use the resolved base and target revisions from Phase 0, then read the complete Jujutsu diff. `trunk()` supplies the configured trunk for non-PR targets; a PR uses its declared base remote bookmark.

```bash
jj diff --from '<base-revision>' --to '<target-revision>' --name-only
jj diff --from '<base-revision>' --to '<target-revision>'
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
   agent-browser screenshot "<scratch-dir>/<scenario>.png"
   agent-browser errors      # check console/page errors
   ```

   Resolve `<scratch-dir>` once as `<workspace-root>/.tmp/rocketclaw/dogfood/<run-id>/`, using `$PWD/.tmp/rocketclaw/dogfood/<run-id>/` only when `jj workspace root` is unavailable before repository-bound work begins. Use a collision-resistant run ID, reject a selected root reached through a symlink or outside its physical workspace/current-directory boundary, and create the directory before browser work. Never use OS-global temporary storage. Remove the run directory when it is no longer needed, and only move a screenshot into the report's location when it will be embedded.

3. **Judge** both correctness and experience: right data, right destination, sensible content, no console errors, and does it feel aligned with the product?
4. **Walk it as each persona.** Re-run the journey in your head from each primary persona's perspective (from Phase 1) and ask where they'd feel a **paper cut** — a small friction that wouldn't fail a functional test but degrades the experience: a confusing label, an extra click, an unexpected jump, a slow-feeling step, missing feedback, copy that doesn't match how that persona thinks. A scenario can be functionally `Pass` yet still carry paper cuts. Note each paper cut, which persona feels it, and its severity.
5. **Record** pass/fail plus any paper cuts, with specifics. Mark the task `completed` only when it genuinely passes. Paper cuts do not block a `Pass`, but a **sharp** paper cut (one severe enough to fix now) is routed into the Phase 5 fix loop just like a failure — apply the same auto-fix-vs-escalate judgment to it. Log the rest in the report.

**External-interaction flows** (OAuth, real email delivery, payments, SMS) can't be fully driven headlessly — pause, ask the user to verify that leg, and mark the scenario `Blocked (needs human verify)` until they confirm. Then continue.

### Phase 5: Fix Loop (Autonomous)

When a scenario fails — or a passing scenario carries a sharp paper cut worth fixing now — **fix it and prove it**, but first decide whether the fix is yours to make autonomously or a human's to decide.

**Judge the size of the fix before touching code.** Auto-fix when the change is small, well-understood, and low-risk: a clear bug with an obvious correct fix, contained to a few files, no schema/architecture/product trade-off. **Do not auto-fix** when the change is large or ambiguous — it requires an architectural or schema decision, changes product behavior or UX intent, spans many files, has plausible competing solutions, or you're not confident the "right" answer is unambiguous. Forcing a big judgment call autonomously is worse than escalating it.

**For autonomous fixes:**

1. Investigate the root cause. If it's non-obvious, use `ce-debug`.
2. Apply the fix in the code.
3. **Add an automated regression test** that fails before the fix and passes after, so the bug can't return. This is the default for behavioral and code bugs. When an automated test is genuinely impractical — a pure copy, spacing, or visual fix with no behavioral assertion to make — substitute a documented browser-replay or screenshot check and **state in the report why no automated test was meaningful**. Do not invent a hollow test just to satisfy the step.
4. Finalize one logical Jujutsu change per fix using `ce-commit` with its Jujutsu route. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and descriptions visible in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; do not impose a fixed prefix, type, scope, subject, body, layout, template, or example. Preserve the semantic association with the fix, and do not add branding or attribution.
5. Re-run the failing scenario in the browser to confirm it now passes; then continue the matrix.
6. If the bug carried a reusable lesson, capture it with `ce-compound`.

**For changes too big to make autonomously:** do not implement. Record what's broken, why it is not a safe autonomous fix, the options and trade-offs, and a recommendation in the report's **Decisions for a human** section. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Treat those required facts as substance rather than fixed message syntax, and derive the recommendation's wording and structure from current project conventions. Mark the scenario `Blocked (human decision)` in the matrix, then continue with the rest. Never make a large, irreversible, or product-altering change just to clear a matrix item.

Keep iterating until every task is `completed` or in a terminal `Blocked` state — `Blocked (human decision)` (escalated here) or `Blocked (needs human verify)` (set in Phase 4 for external-interaction legs). Both are terminal for the loop: they wait on a person, so do not re-queue them. Re-test anything a fix might have affected (watch for regressions in adjacent journeys).

**Before declaring the target ready, run the project's automated test suite once** (the new regression tests plus everything that already exists). Discover the test command from the project's active instructions and conventions already in your context; do not assume a specific runner. Record the result in the report; a green matrix with a red suite is not "ready."

### Phase 6: Write the Report Artifact

The report doc was created at the end of Phase 2 and updated incrementally throughout (see Resumability). When the matrix is green or every remaining item is explicitly blocked, finalize it at `<root>/dogfood-reports/<YYYY-MM-DD>-<target-slug>-dogfood.md` in the workspace under test, then surface a short summary in chat with the file path.

**Finalize against `references/dogfood-report-template.md`**, which owns the required information and section coverage. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Validate the report's facts and completeness without enforcing fixed prose, headings, layout, or examples; current project conventions determine its final expression. Carry forward the Mermaid flowcharts, a matrix row per scenario with its Jujutsu change ID, each fix's root cause and regression test or why none was meaningful, paper cuts attributed by persona, reusable learnings, and a final readiness verdict that records the Phase 5 automated-suite result.
