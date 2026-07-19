# Shipping Workflow

This file contains the shipping workflow (Phase 3-4). It is loaded when all Phase 2 tasks are complete and execution transitions to quality check.

## Phase 3: Quality Check

1. **Run Core Quality Checks**

   Always run before submitting:

   ```bash
   # Run full test suite (use project's test command)
   # Examples: bin/rails test, npm test, pytest, go test, etc.

   # Run linting per the project's active instructions
   ```

2. **Simplify** (conditional — separate from code review)

   Before code review, invoke **`ce-simplify-code`** when the JJ stack diff is non-mechanical and large enough to benefit (default: **>=30 changed lines**). Skip when the diff is purely mechanical (formatting, dependency bumps, lint-only fixes, generated artifacts).

   This step refines reuse, quality, and efficiency on the **current diff** so any later review sees cleaner code. It is not a substitute for code review.

   Pass `plan:<path>` or a scope hint when the plan or user narrowed what changed. If the skill is unavailable, skip or do a brief manual pass for obvious duplicate/dead code — code review still runs regardless.

3. **Code Review**

   Review the JJ stack diff with **`ce-code-review`** as the single path. It self-right-sizes (a lite roster for small, low-risk, code-only diffs; the full roster otherwise), so there is no separate escalation decision.

   **Skip dedicated review only for a purely mechanical diff** — formatting, dependency-version bumps, lint-only fixes, generated artifacts (the same class step 2 skips for simplify). Note in the shipping summary: `Code review: skipped (mechanical diff)`. Everything else gets reviewed.

   **Review is not fix — two steps:**

   **3a. Review (read-only).** Resolve the boundary from JJ history, normally the fork point between the current stack and `trunk()`, and inspect it with `jj log`/`jj diff`. Invoke `ce-code-review` with `mode:agent` (add `plan:<path>` when known; `base:<jj-revision-or-revset>` when resolved). Pass **`depth:full`** when explicitly requested. Do not pass `mode:autofix`. Parse the JSON.

   **3b. Apply fixes (caller-owned).** Load `references/review-findings-followup.md`: filter on JSON, batch by file, dispatch fix subagents. The orchestrator integrates JJ changes, tests, and closes coherent change boundaries. Then proceed to the Residual Work Gate.

   **If `ce-code-review` cannot run at all** after its own fallback, use an available provider review in an interactive session and fix inline. In a non-interactive session, note `Code review: skipped (ce-code-review unavailable)` and add an explicit manual JJ diff scan to Final Validation. Never silently ship a non-mechanical change with no review.

4. **Residual Work Gate** (REQUIRED when `ce-code-review` ran and left actionable residuals)

   After code review and review-findings followup, inspect the **Actionable Findings** summary. If truncated, read `<workspace-root>/.tmp/rocketclaw/ce-code-review/<run-id>/`, where `<workspace-root>` comes from `jj workspace root` with `pwd -P` fallback. If actionable `downstream-resolver` findings remain, do not proceed until they are resolved or durably recorded.

   **Non-interactive / autonomous sessions:** do not call a blocking tool. After step 3b applies eligible findings, take `Accept and proceed` automatically: record remaining residuals verbatim in the pull-request description's Known Residuals section, or `docs/residual-review-findings/<change-id>.md` on the no-pull-request path, then continue. Residuals are never dropped.

   **Interactive sessions:** ask with the provider's blocking question tool. Fall back to numbered chat options only when no blocking tool exists. Never silently skip the gate.

   Stem: `Code review left N actionable finding(s) not yet fixed. How should the agent proceed?`

   Options (four or fewer, self-contained labels):
   - `Apply/fix now` — load `references/review-findings-followup.md`, dispatch batched fix subagents, run tests, and close coherent JJ change boundaries; re-run review only after the diff changed materially.
   - `File tickets via project tracker` — load `references/tracker-defer.md` in Interactive mode; the agent files tickets in the project's detected tracker (or `gh` fallback, or leaves them in the report if no sink exists) and proceeds to Final Validation.
   - `Accept and proceed` — record residuals verbatim in a durable Known Residuals sink before shipping. If a pull request will be created or updated, include them in its description. On the no-pull-request `ce-commit` path, create `docs/residual-review-findings/<change-id>.md`, include source review-run context, keep it in the appropriate JJ change, and report the path.
   - `Stop — do not ship` — abort the shipping workflow. The user will handle findings manually before re-invoking.

   Skip this gate when review reported no actionable findings or dedicated review was skipped. Do not proceed after `Accept and proceed` until the durable sink is recorded as pull-request Known Residuals or `docs/residual-review-findings/<change-id>.md`.

5. **Final Validation**
   - All tasks marked completed
   - Testing addressed -- tests pass and new/changed behavior has corresponding test coverage (or an explicit justification for why tests are not needed)
   - Linting passes
   - Code follows existing patterns
   - Figma designs match (if applicable)
   - No console errors or warnings
   - If the plan has a `Requirements` section (or legacy `Requirements Trace`), verify each requirement is satisfied by the completed work
   - If any `Deferred to Implementation` questions were noted, confirm they were resolved during execution

6. **Prepare Operational Validation Plan** (REQUIRED)
   - Add a `## Post-Deploy Monitoring & Validation` section to the pull-request description for every change.
   - Include concrete:
     - Log queries/search terms
     - Metrics or dashboards to watch
     - Expected healthy signals
     - Failure signals and rollback/mitigation trigger
     - Validation window and owner
   - If there is truly no production/runtime impact, still include the section with: `No additional operational monitoring required` and a one-line reason.

## Phase 4: Ship It

1. **Prepare Validation Context**

   Use available browser, screenshot, terminal recording, and artifact-capture tools directly only when the user asks or when an artifact already exists.

   Note whether the completed work has observable behavior and summarize manual validation. If the user supplied evidence, pass it to `ce-commit-push-pr` as pull-request-description context.

2. **Finalize JJ Changes and Create Pull Request**

   Before handoff, run `jj status`, inspect the stack with `jj log`, and inspect the intended boundary with `jj diff`. Ensure every change is coherent and described; use `jj split` for mixed changes. Do not move or create bookmarks directly here.

   Load `ce-commit-push-pr` to finalize descriptions, create or update the publication bookmark, push it, and create or update the pull request. Load `ce-commit` instead when the user wants local JJ changes without publication.

   For every JJ description composed, edited, validated, or recommended in this phase, active project instructions and description syntax inferred at runtime from `jj log` always win. Apply compatible Go guidance for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example. Use `<description-composed-from-runtime-conventions>` as the neutral placeholder. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

   When providing pull-request-description context, include:
   - The plan's summary and key decisions
   - Testing notes (tests added/modified, manual testing performed)
   - Evidence context from step 1
   - Figma design link (if applicable)
   - The Post-Deploy Monitoring & Validation section (see Phase 3 Step 6)
   - Any Known Residuals accepted in Phase 3, rendered as a dedicated section with severity, file:line, and title per finding

   Do not add creator, model, provider, tool, runtime attribution, or badges to descriptions or pull-request text.

3. **Notify User**
   - Summarize what was completed
   - Link to the pull request (if one was created)
   - Report the JJ change IDs included and the publication bookmark, if any
   - Note any follow-up work needed
   - Suggest next steps if applicable

## Quality Checklist

Before creating a pull request, verify:

- [ ] All clarifying questions asked and answered
- [ ] All tasks marked completed
- [ ] Testing addressed -- tests pass AND new/changed behavior has corresponding test coverage (or an explicit justification for why tests are not needed)
- [ ] Linting passes (use linting-agent)
- [ ] Code follows existing patterns
- [ ] Figma designs match implementation (if applicable)
- [ ] Validation/evidence context passed to `ce-commit-push-pr` when the change has observable behavior
- [ ] JJ changes are coherent, independently reviewable, and described according to repo-local history and instructions
- [ ] Description validation used `<description-composed-from-runtime-conventions>` as its neutral placeholder; active project instructions and description syntax inferred at runtime from `jj log` won; compatible Go guidance was used for quality, clarity, and structure; and no fixed prefix, type, scope, subject, body, layout, template, or example was imposed. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.
- [ ] Pull-request description includes Post-Deploy Monitoring & Validation section (or explicit no-impact rationale)
- [ ] Simplify: `ce-simplify-code` when diff >=30 lines (or skipped with reason)
- [ ] Code review: `ce-code-review` ran (self-sized), or skipped (mechanical diff / unavailable — noted in summary); residuals handled via the Residual Work Gate
- [ ] Pull-request description includes summary, testing notes, and evidence when captured
- [ ] Pull-request description contains no creator, model, provider, tool, runtime attribution, or badges

## Code Review

Single portable path: **`ce-code-review`** self-sizes (lite roster for small low-risk code-only diffs, full roster otherwise). The size/sensitive-surface judgment lives inside `ce-code-review`.

**Skip** only for a purely mechanical diff (formatting, dep-bumps, lint-only, generated). Everything else is reviewed.

**Two steps — review is not fix.** (3a) Review-only via `mode:agent`; add `depth:full` when the plan/task/user explicitly asked for a deep review. (3b) Batched fix subagents per `references/review-findings-followup.md`; residuals → Residual Work Gate.

**If `ce-code-review` can't run**: interactive -> provider review if present, fix inline; non-interactive -> skip-with-note plus manual JJ diff scan in Final Validation. Never silently ship a non-mechanical change unreviewed.
