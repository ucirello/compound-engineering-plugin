---
name: lfg
description: "Run the full autonomous shipping pipeline end-to-end, hands-off with no check-ins: plan, implement, review and fix, describe changes, push a bookmark, open a PR, and watch CI to green. Use only when the user explicitly asks to build or ship something autonomously all the way to an open PR, or invokes lfg directly. Not for in-the-loop work where the user reviews each step: use ce-plan to plan, ce-work to implement a plan, ce-debug to fix a bug, or ce-commit to describe existing changes."
argument-hint: "[feature description]"
---

CRITICAL: You MUST execute every step below IN ORDER. Do NOT skip any required step. Do NOT jump ahead to coding or implementation. The plan phase (step 1) MUST be completed and verified BEFORE any work begins. Violating this order produces bad output.

When invoking any skill referenced below, resolve its name against the available-skills list the host platform provides and use that exact entry. Some platforms list skills under a namespace; others list the bare name. Always match a listed entry verbatim before calling the skill or task capability.

**JJ preflight and vocabulary.** LFG operates in a Jujutsu workspace, not through an index, selected bookmark, or legacy alternate-working-directory model.

1. Require `jj workspace root` to succeed and record that path. `@` is the current workspace's working-copy change, `@-` is its parent, and `trunk()` is the repository's configured base revision. Use `jj status`, `jj diff`, and `jj log` for status, diffs, and history.
2. Resolve and retain one `FEATURE_BOOKMARK` for the whole run. A JJ bookmark is only a named revision pointer; there is no active/current bookmark. Inspect `jj bookmark list` and `jj log -r 'bookmarks() & ::@ & ~::trunk()'`. Prefer the sole local bookmark on the current feature stack, or the sole candidate whose forge PR is open. If neither identifies one bookmark, create a unique ASCII `lfg-<short-change-id>` bookmark at `@` with `jj bookmark create <name> -r @`. Never infer a selected bookmark.
3. Compute the complete feature scope against the base with `jj diff --from 'trunk()' --to @`, `jj diff --summary --from 'trunk()' --to @`, and `jj log -r 'trunk()..@'`. A plain `jj diff` is only the current working-copy change, not the whole feature stack.
4. To describe only selected files, pass explicit filesets to `jj commit <fileset> -m "<dynamically-derived-message>"`; selected changes remain in the described revision and unselected changes move to the new working-copy change. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Derive the syntax dynamically from repository-local instructions and the commit syntax visible in `git log`; both win over generic guidance, and apply Go guidance only when compatible. Do not impose fixed prefixes, types, scopes, subjects, templates, or examples. After each such description, point `FEATURE_BOOKMARK` at the described parent with `jj bookmark set "$FEATURE_BOOKMARK" -r @-`.
5. Run `gh` against the retained bookmark and pass the repository explicitly with `--repo`, resolving it from the retained JJ remote.
6. If the feature must be updated from the remote base, use `jj git fetch --remote <remote>`, then `jj rebase -r 'trunk()..@' -o 'trunk()'`; `-r` limits the source to revisions in the current ancestry stack, unlike broader selectors that can include descendants outside it. Do not combine the base into the feature implicitly. If a true merge change is required by the plan, create it explicitly with `jj new <parent-1> <parent-2>`. Resolve any materialized conflicts before continuing and verify with `jj status`.

1. Invoke the `ce-plan` skill with the arguments you were invoked with.

   GATE: STOP. If ce-plan reported the task is non-software and cannot be processed in pipeline mode, stop the pipeline and inform the user that LFG requires software tasks. Otherwise, verify that the `ce-plan` workflow produced a plan file in `docs/plans/`. If no plan file was created, invoke `ce-plan` again with those same arguments. Do NOT proceed to step 2 until a written plan exists. **Record the plan file path** — it will be passed to ce-work in step 2 and ce-code-review in step 4.

   Read the plan metadata before continuing. For a unified plan, proceed only when it has `artifact_readiness: implementation-ready` and `execution: code`. Stop the pipeline for `artifact_readiness: requirements-only`, any unrecognized readiness value, `execution: knowledge-work`, approach-plan outputs, answer-seeking/universal outputs, or invalid progress-like readiness values. LFG never launches `/goal` directly; when goal-mode or dynamic workflows are appropriate, `ce-work` owns that implementation engine choice and must return control to LFG afterward.

2. Invoke the `ce-work` skill with `mode:return-to-caller <plan-path-from-step-1>`.

   GATE: STOP. Verify that implementation work was performed - files were created or modified beyond the plan. Read the structured return and require `status: complete`, the same plan path, changed files, U-IDs attempted/completed when present, verification results, blocker list, behavior-change signal, and `standalone_shipping_skipped: true`. When `behavior_change: true`, also require `verification_evidence` that names the relevant units/tasks, existing tests inspected, tests added/changed or used unchanged, red failure or characterization evidence when applicable, verification run, and any deliberate test exception. Do NOT decide the test strategy inside LFG; the evidence is ce-work's contract.

   If `behavior_change: true` but `verification_evidence` is missing or too vague to tell how behavior was protected, invoke `ce-work` one more time with the same `mode:return-to-caller <plan-path-from-step-1>` argument. Do not prompt the user and do not alter the plan path argument. The retry relies on ce-work's idempotency path to inspect the already-implemented work, fill the missing evidence, and return without reimplementing. If the second return still lacks coherent verification evidence, stop as blocked and report the missing fields instead of continuing to simplify/review/ship.

   Before review or shipping, re-anchor `FEATURE_BOOKMARK` to the implementation tip. Resolve `heads(trunk()..@ & ~empty())`; require exactly one revision, stop if the set is empty or has multiple tips, then run `jj bookmark set "$FEATURE_BOOKMARK" -r '<resolved-tip>'` and verify `jj bookmark list -r '<resolved-tip>'` names exactly that bookmark. This prevents an earlier bookmark target from excluding changes produced by `ce-work` without guessing across an ambiguous stack.

3. Invoke the `ce-simplify-code` skill on the complete feature-stack diff from `trunk()` to `@`.

   This runs before review so the code-review in step 4 covers the simplified code. Use `jj diff --summary --from 'trunk()' --to @` and `jj diff --stat --from 'trunk()' --to @` to classify scope. **Skip** this step when the change is docs-only (only markdown/docs paths changed) or trivial (roughly under 10 changed lines). Otherwise tell `ce-simplify-code` that the scope is the JJ feature-stack diff `trunk()..@`; it preserves behavior and runs the test suite.

   Do not run `jj commit` in this step. `ce-simplify-code` leaves its edits in the working-copy change; step 4 reviews the complete feature-stack diff (including `@`), and step 8 describes and advances whatever remains. Describing here would combine still-undescribed implementation edits under an inaccurate description and could stall on a working-copy change that never becomes empty.

4. Invoke the `ce-code-review` skill with `mode:agent plan:<plan-path-from-step-1>`.

   Pass the plan file path from step 1 so ce-code-review can verify requirements completeness. Read the **Actionable Findings** summary the skill emits.

   `mode:agent` is report-only **by design** — it surfaces findings but never edits the tree; LFG applies the eligible ones in step 5. When narrating progress to the user, frame this as "review found X → applied X in step 5," not as "code review did not auto-fix." A report-only review followed by an LFG-applied fix is the intended contract, not a gap.

**Shipping precondition (steps 5–9).** Run `jj git remote list` once before the shipping steps. If it lists **no remote**, shipping is **local-only**: make every local change description the steps below call for, but **skip every push, PR create/edit, and CI-watch action**. A missing remote is a terminal local-only state, not an error: persist the local changes and proceed to step 10. When remotes exist, select and retain one `SHIPPING_REMOTE`: use `origin` when present, otherwise the sole remote. If multiple remotes remain ambiguous, stop rather than push to an arbitrary repository. Resolve and retain `REPOSITORY` from that remote for explicit `gh --repo` calls. Run `jj git fetch --remote "$SHIPPING_REMOTE"` before the first push; if push safety rejects a stale remote bookmark, fetch that same remote, resolve any bookmark conflict, and retry once.

5. **Apply and persist review fixes** (REQUIRED after step 4, before residual handoff)

   Load `references/review-followup.md` and execute its apply step (mechanical apply + describe/advance/push when changes exist). Do not proceed to the residual handoff, run browser tests, or output DONE while eligible review fixes remain only in the working-copy change undescribed.

6. **Autonomous residual handoff** (only when step 4 reported one or more actionable `downstream-resolver` findings not applied in step 5; skip when it reported `Actionable findings: none.`)

   Do not prompt the user. This step embraces the autopilot contract: residuals must become durable before DONE, but the AI Assistant never stops to ask.

   1. Load `references/tracker-defer.md` in **non-interactive mode**. Pass the residual actionable findings from step 4/5 (or the run artifact when the summary was truncated).
   2. Collect the structured return: `{ filed: [...], failed: [...], no_sink: [...] }`.
   3. Compose a `## Residual Review Findings` markdown section from the structured return (this goes into the described record file in step 4, **not** the PR body):
      - For each item in `filed`: a bullet with severity, file:line, title, and a link to the tracker ticket URL.
      - For each item in `failed`: a bullet with severity, file:line, title, and the failure reason (e.g., `Defer failed: gh returned 401 — tracker unavailable`).
      - For each item in `no_sink`: a bullet with severity, file:line, and title inlined verbatim so the described record file is the durable record.
   4. **Durable record — never the PR body.** Do not write a `## Residual Review Findings` section into the PR description; it duplicates tracker state and goes stale as items resolve. Create or replace `docs/residual-review-findings/<feature-bookmark-or-change-id>.md` with the composed section, ticket links, and source run context. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Derive the syntax dynamically from repository-local instructions and the commit syntax visible in `git log`; both win over generic guidance, and apply Go guidance only when compatible. Do not impose fixed prefixes, types, scopes, subjects, templates, or examples. Describe only that fileset with `jj commit <residual-review-fileset> -m "<dynamically-derived-message>"`, run `jj bookmark set "$FEATURE_BOOKMARK" -r @-`, and push with `jj git push --bookmark "$FEATURE_BOOKMARK" --remote "$SHIPPING_REMOTE"` when a remote is configured. If there is no remote, the locally described revision is the durable sink.

   Do not output DONE until the residuals are durable. Never block DONE on tracker filing failures once the record file exists. A push failure when a remote exists is a stop-and-report outcome.

7. Invoke the `ce-test-browser` skill with `mode:pipeline`.

8. Persist and publish the feature. If `@` is non-empty, invoke `ce-commit` to finish the remaining logical changes. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Derive the syntax dynamically from repository-local instructions and the commit syntax visible in `git log`; both win over generic guidance, and apply Go guidance only when compatible. Do not impose fixed prefixes, types, scopes, subjects, templates, or examples. Resolve `heads(trunk()..@ & ~empty())`, require exactly one publishable tip, set `FEATURE_BOOKMARK` to it, and verify the target. When a remote exists, push only that bookmark with `jj git push --remote "$SHIPPING_REMOTE" --bookmark "exact:$FEATURE_BOOKMARK"`.

   Detect an existing PR explicitly with `gh pr view "$FEATURE_BOOKMARK" --repo "$REPOSITORY" --json number,url,state`. If none exists, use `$(jj workspace root)/.tmp`; if no JJ repository exists, use the local fallback `.tmp`. Preserve existing `.gitignore` entries while ensuring `.tmp/` is ignored, refuse the selected `.tmp` path when it is a symlink or non-directory, create it with parent-directory creation enabled, and compose the title and body from the plan, verification, monitoring, and residual context in `<workspace-local-pr-body-file>`. Then run `gh pr create` with explicit `--repo "$REPOSITORY"`, `--head "$FEATURE_BOOKMARK"`, `--base <base-bookmark>`, `--title`, and `--body-file "<workspace-local-pr-body-file>"`. If one exists, update it by PR number with `gh pr edit --repo "$REPOSITORY"`. Never use implicit repository or bookmark discovery. When no remote is configured, persist local changes and advance the bookmark, but skip push and PR creation.

9. **Drive CI to green via `ce-babysit-pr`** (only when an open PR exists for `FEATURE_BOOKMARK`)

   Detect the PR; if none exists or `gh` is unavailable, skip this step entirely and proceed to step 10.

   ```bash
   gh pr view "$FEATURE_BOOKMARK" --repo "$REPOSITORY" --json number,url,state
   ```

   Invoke **`ce-babysit-pr mode:pipeline <pr-url>`**. It runs the bounded pipeline loop: watches CI, repairs real (convergent) failures via `ce-debug mode:pipeline` — never weakening, skipping, or mocking an assertion — resolves any review comments that arrived via `ce-resolve-pr-feedback mode:pipeline`, and stops when CI is decided or its budget (default 3 fix rounds) is hit. This replaces LFG's former hand-rolled CI loop; do not reimplement CI-watching here.

   Collect its structured result (`{ status, fixes_applied, residuals }`). It surfaces unfixable CI as a **run-report comment on the PR** and returns residuals — do **NOT** write a `## CI Failures Unresolved` PR-body section. A `needs-human` residual (a fix that would need a product/design decision) is deferred, not applied — that is the autopilot contract, unchanged. Do not block DONE once babysit has surfaced residuals.

10. Output `<promise>DONE</promise>` when complete

    If step 8 reported new concepts, first print one line per concept with its name and the functional `/ce-explain <name>` route for deeper explanation.

    If an open PR exists, add one line pointing the user to the interactive watch-to-merge (pipeline mode stopped at "CI decided," not "merged"): `PR is moving — run /ce-babysit-pr <pr-url> to watch it through review to merge.` Then output the DONE promise.

Start with step 1 now. Remember: plan FIRST, then work. Never skip the plan.
