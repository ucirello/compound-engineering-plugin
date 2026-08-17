# Shipping Workflow

This file contains the shipping workflow (Phase 3-4). It is loaded when all Phase 2 tasks are complete and execution transitions to quality check.

## Phase 3: Quality Check

1. **Run Core Quality Checks**

   Always run before submitting:

   ```bash
   # Run full test suite (use project's test command)
   # Examples: bin/rails test, npm test, pytest, go test, etc.

   # Run linting (per the project's configured lint command / active instructions)
   # Use linting-agent before pushing to origin
   ```

2. **Simplify** (conditional — separate from code review)

   Before code review, invoke **`ce-simplify-code`** when the diff has enough substantive code to benefit (default: **>=30 substantive changed code lines** — count human-authored code, not total diff lines). Skip when the diff is purely mechanical (formatting, dependency bumps, lint-only fixes, generated artifacts) or when substantive code stays under the floor even though the total diff is larger.

   This step refines reuse, quality, and efficiency on the **current diff** so any later review sees cleaner code. It is not a substitute for code review.

   Pass `plan:<path>` or a scope hint when the plan or user narrowed what changed. If the skill is unavailable on the harness, skip or do a brief manual pass for obvious duplicate/dead code — code review (step 3) still runs regardless.

3. **Code Review**

   Review the diff with **`ce-code-review`** — the plugin's portable review skill — as the single path. It self-right-sizes (a lite roster for small, low-risk, code-only diffs; the full roster otherwise), so there is no "escalate to a heavier reviewer" decision and **no harness-specific review detection** — it behaves identically on every harness. (This replaces the former Tier 1 harness-native `/review` / Tier 2 escalation split: the size and sensitive-surface judgment that used to live here now lives inside `ce-code-review`'s own reviewer selection and small-diff gate.)

   **Completion gate (standalone shipping).** This shipping tail is **not done** until exactly one of: (1) a **completed review receipt** from an actual `ce-code-review` invocation — `mode:agent` JSON with **`status: complete`** plus `artifact_path` or `run_id`, or default-mode markdown containing Actionable Findings, Coverage, and Verdict — or (2) an **explicit skip phrase** in the shipping summary: `Code review: skipped (mechanical diff)`, `Code review: skipped (ce-code-review unavailable)`, or (interactive only) `Code review: harness-native fallback`, each with a one-line reason. Silent omit is invalid. Do **not** accept `status: failed`, `degraded`, or `skipped` as a completed receipt even when `artifact_path`/`run_id` is present — route those through the unavailable path below. **Never substitute** mental self-review, "external / prior findings already applied," or ad-hoc skimming. Harness-native `/review` alone is **not** a substitute when `ce-code-review` can load; it only counts after the unavailable path below, via the `harness-native fallback` phrase.

   **Skip dedicated review only for a purely mechanical diff** — formatting, dependency-version bumps, lint-only fixes, generated artifacts (the same class step 2 skips for simplify), including multi-file mechanical-only diffs (e.g. package + lockfile, formatter across files). **Not mechanical:** behavior-bearing edits (single- or multi-file), control-flow / error-class / tests-for-behavior changes, or applying external or prior review findings. Note the exact skip phrase above. Everything else gets reviewed.

   **Review is not fix — two steps:**

   **3a. Review (read-only).** Invoke `ce-code-review` through the host's normal skill-invocation mechanism with `mode:agent` (add `plan:<path>` when known; `base:<ref>` when the diff base is resolved). Pass **`depth:full`** when the plan, the task, or the user explicitly asked for a full / deep / thorough review — that is the one escalation signal `ce-code-review` cannot infer from the diff alone. Do not pass `mode:autofix`. Parse the JSON and retain the receipt only when `status` is `complete` (plus `artifact_path` / `run_id`).

   **3b. Apply fixes (caller-owned).** Load `references/review-findings-followup.md`: filter on JSON, batch by file, dispatch fix subagents. The orchestrator integrates, tests, and describes the resulting Jujutsu changes. Then proceed to the Residual Work Gate.

   **If `ce-code-review` cannot run at all** — subagent dispatch unavailable, unauthenticated, hard-capped, or returns `status: failed`/`degraded`/`skipped` with no completed coverage even after its own sequential Fallback: in an **interactive** session, run the harness-native review if one exists (e.g. `/review`), fix inline, and note `Code review: harness-native fallback` with a one-line reason (that phrase is the gate satisfaction — not a silent mental review); in a **non-interactive** session (autonomous pipeline, or no native review available), skip the dedicated step, note `Code review: skipped (ce-code-review unavailable)`, and add an explicit manual diff scan to Final Validation. Never silently ship a non-mechanical change with no review of any kind.

4. **Residual Work Gate** (REQUIRED when `ce-code-review` ran and left actionable residuals)

   After code review and review-findings followup, inspect the **Actionable Findings** summary (or read the absolute `<artifact-path>` returned by `ce-code-review` if the summary was truncated). If one or more actionable `downstream-resolver` findings were not applied in followup, do not proceed to Final Validation until they are resolved or durably recorded.

   **Non-interactive / autonomous sessions (no human can answer — e.g. an `lfg`-style pipeline or a headless run):** do **not** call the blocking tool — that would hang the pipeline. After step 3b auto-applied every mechanically-eligible finding, take the `Accept and proceed` path automatically: record the remaining actionable residuals to a durable sink and continue to Final Validation. When a PR will be created or updated, that sink is the PR description's Known Residuals section. On the no-PR path, file them via `references/tracker-defer.md` in non-interactive mode — one tracker ticket per finding, with enough background to action it standalone; any findings the tracker chain could not durably file — its `failed` or `no_sink` buckets — are returned verbatim in the run's structured result and stated in its report, so none are silently dropped. Residuals are recorded, never dropped — this keeps autonomous shipping unblocked without losing findings.

   A settlement-invalidating conflict — evidence a `session-settled:`-labeled decision cannot work — is never auto-accepted as a residual; it is a blocker (`status: blocked` return in return-to-caller mode; stop-and-surface in standalone runs).

   **Interactive sessions:** Ask the user using the platform's blocking question tool (`AskUserQuestion` in Claude Code with `ToolSearch select:AskUserQuestion` pre-loaded if needed, `request_user_input` in Codex, `ask_question` in Antigravity CLI (`agy`), `ask_user` in Pi (requires the `pi-ask-user` extension)). Fall back to numbered options in chat only when the harness genuinely lacks a blocking tool. Never silently skip the gate.

   Stem: `Code review left N actionable finding(s) not yet fixed. How should the agent proceed?`

   Options (four or fewer, self-contained labels):
   - `Apply/fix now` — load `references/review-findings-followup.md`, dispatch batched fix subagents, run tests, and describe a complete fix change; optionally re-run review only after the delta changed materially.
   - `File tickets via project tracker` — load `references/tracker-defer.md` in Interactive mode; the agent files tickets in the project's detected tracker (or `gh` fallback, or leaves them in the report if no sink exists) and proceeds to Final Validation.
   - `Accept and proceed` — record residual findings in a durable sink before shipping. Put them in the PR's Known Residuals section when a PR is planned; otherwise file tracker tickets through `references/tracker-defer.md`. If no sink is reachable, state that plainly in the final summary.
   - `Stop — do not ship` — abort the shipping workflow. The user will handle findings manually before re-invoking.

   Skip this gate entirely when the review reported `Actionable findings: none.` (and followup applied everything mechanical), or when dedicated review was skipped (mechanical diff or `ce-code-review` unavailable). Do not proceed past this gate on an `Accept and proceed` decision (including the autonomous auto-accept above) until the agent has recorded which durable sink held the residuals — `PR Known Residuals`, a tracker ticket, or an explicit statement in the run report when neither was reachable.

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
   - Add a `## Post-Deploy Monitoring & Validation` section to the PR description for every change.
   - Include concrete:
     - Log queries/search terms
     - Metrics or dashboards to watch
     - Expected healthy signals
     - Failure signals and rollback/mitigation trigger
     - Validation window and owner
   - If there is truly no production/runtime impact, still include the section with: `No additional operational monitoring required` and a one-line reason.

## Phase 4: Ship It

1. **Prepare Validation Context**

   Do not launch a dedicated evidence-capture workflow. Use the active harness's browser, screenshot, terminal recording, and artifact tools only when the user asks or the artifact already exists.

   Note whether the completed work has observable behavior and summarize manual validation. Carry user-supplied evidence into the PR description context.

2. **Describe, Publish, and Create Pull Request**

   **Ship-handoff gate.** Before changing a publication bookmark, pushing, or mutating a PR, confirm the Phase 3 code-review completion gate is satisfied. If not, stop and complete review or record the legitimate exact skip phrase. Carry the receipt or skip phrase into the shipping summary and PR context.

   **Do not publish what the user did not offer.** Compare the work-owned revset with the tracked remote bookmark and any open GitHub PR. If publication would include unrelated local ancestry, leave the work as local described changes and report what stayed local and why.

   **Project-defined shipping process wins.** If the project's active instructions name a process that owns Jujutsu publication and PR creation, use it. It must preserve user-owned changes and accept the plan summary, testing notes, evidence, review receipt, Known Residuals, and any stated stack topology. If it is not Jujutsu-native or cannot exclude user-owned changes, use the default below. Precedence is the user's current preference, then the project-defined process, then this default.

   **Description rule:** Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

   Runtime local conventions and visible local history win; apply compatible Go quality guidance and no fixed type, scope, decorative metadata, or example. Inspect every work-owned revision with `jj show`, apply each locally derived description with `jj describe` using the installed JJ syntax, and reject empty, generic, WIP, or convention-breaking descriptions.

   Ensure the work-owned revisions form the intended stack above the preserved base. Create or move a dynamically named bookmark to the stack tip, then publish with `jj git push --bookmark <bookmark>` (or the project-defined equivalent). Use `gh pr view` to detect an existing GitHub PR and `gh pr create` or `gh pr edit` for the PR. Never publish the user's pre-work change merely because it is an ancestor; if the intended stack cannot be represented without unrelated unpublished ancestry, keep the work local and report the blocker.

   When providing context for the PR description, include:
   - The plan's summary and key decisions
   - Testing notes (tests added/modified, manual testing performed)
   - Evidence context from step 1
   - Figma design link (if applicable)
   - The Post-Deploy Monitoring & Validation section (see Phase 3 Step 6)
   - Code-review receipt (`status` + `artifact_path`/`run_id`) or the exact skip phrase from the completion gate
   - Any "Known Residuals" accepted in the Phase 3 Residual Work Gate, rendered as a dedicated section in the PR body with severity, file:line, and title per finding

   If the Residual Work Gate filed residual findings as tracker tickets, back-fill the opened PR's URL into those tickets once it exists — best-effort, so each ticket links to the PR carrying the finding.

   If the user prefers no PR, retain the properly described local Jujutsu changes without creating or moving a publication bookmark.

3. **Notify User**
   - Summarize what was completed
   - Link to PR (if one was created)
   - Note any follow-up work needed
   - Suggest next steps if applicable

## Quality Checklist

Before creating PR, verify:

- [ ] All clarifying questions asked and answered
- [ ] All tasks marked completed
- [ ] Testing addressed -- tests pass AND new/changed behavior has corresponding test coverage (or an explicit justification for why tests are not needed)
- [ ] Linting passes (use linting-agent)
- [ ] Code follows existing patterns
- [ ] Figma designs match implementation (if applicable)
- [ ] Validation/evidence context included when the change has observable behavior
- [ ] Every work-owned description follows runtime local conventions and the description rule above
- [ ] PR description includes Post-Deploy Monitoring & Validation section (or explicit no-impact rationale)
- [ ] Simplify: `ce-simplify-code` when the diff has >=30 substantive changed code lines (or skipped with reason)
- [ ] Code review completion gate: completed receipt (`status: complete` + `artifact_path`/`run_id` or markdown Actionable/Coverage/Verdict) **or** exact phrase (`Code review: skipped (mechanical diff)` / `Code review: skipped (ce-code-review unavailable)` / `Code review: harness-native fallback`); residuals handled via the Residual Work Gate
- [ ] Ship-handoff gate passed before bookmark publication or PR mutation
- [ ] PR description includes summary, testing notes, and evidence when captured

## Code Review

Single portable path: **`ce-code-review`** self-sizes (lite roster for small low-risk code-only diffs, full roster otherwise). No harness-native review detection, no escalation tiers — the size/sensitive-surface judgment lives inside `ce-code-review` now.

**Completion gate:** shipping is not done without a **completed** review receipt (`status: complete`) or an exact skip / harness-native-fallback phrase. **Skip** only for a purely mechanical diff (formatting, dep-bumps, lint-only, generated — including multi-file mechanical-only) — not for applying external findings or behavior-bearing work. Everything else is reviewed.

**Two steps — review is not fix.** (3a) Review-only via `mode:agent`; add `depth:full` when explicitly requested. (3b) Batched fix subagents per `references/review-findings-followup.md`; residuals -> Residual Work Gate. Re-check completion before bookmark publication or PR mutation.

**If `ce-code-review` can't run** (or returns non-complete): interactive → harness-native review if present, fix inline, note `Code review: harness-native fallback`; non-interactive → exact unavailable skip phrase + manual diff scan in Final Validation. Never silently ship a non-mechanical change unreviewed.
