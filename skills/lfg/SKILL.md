---
name: lfg
description: Run the full hands-off engineering pipeline from planning through a green PR.
disable-model-invocation: true
argument-hint: "[feature description]"
---

CRITICAL: You MUST execute every step below IN ORDER. Do NOT skip any required step. Do NOT jump ahead to coding or implementation. The plan phase (step 1) MUST be completed and verified BEFORE any work begins. Violating this order produces bad output.

For every functional `ce-*` route below, inspect the available-skills list supplied by the host and invoke the exact listed skill name whose final skill-name component matches that route. Host namespaces and invocation mechanisms vary; never synthesize or shorten a name that the host did not list. Preserve the `ce-*` suffix so routing still selects the intended skill.

1. Invoke the `ce-plan` skill with `$ARGUMENTS`.

   GATE: STOP. If `ce-plan` reported the task is non-software and cannot be processed in pipeline mode, stop the pipeline and inform the user that this pipeline requires software tasks. Otherwise, verify that the planning workflow produced a plan file in `docs/plans/`. If no plan file was created, invoke `ce-plan` again with `$ARGUMENTS`. Do NOT proceed to step 2 until a written plan exists. **Record the plan file path** — it will be passed to `ce-work` in step 2 and `ce-code-review` in step 4.

   Read the plan metadata before continuing. If the plan has `artifact_contract: rocketclaw-unified-plan/v1`, proceed only when it has `artifact_readiness: implementation-ready` and `execution: code`. Stop the pipeline for `artifact_readiness: requirements-only`, any unrecognized readiness value, `execution: knowledge-work`, approach-plan outputs, answer-seeking/universal outputs, or invalid progress-like readiness values. The pipeline never launches `/goal` directly; when goal-mode or dynamic workflows are appropriate, `ce-work` owns that implementation engine choice and must return control to the pipeline afterward.

2. Invoke the `ce-work` skill with `mode:return-to-caller <plan-path-from-step-1>`.

   GATE: STOP. Verify that implementation work was performed - files were created or modified beyond the plan. Read the structured return and require `status: complete`, the same plan path, changed files, U-IDs attempted/completed when present, verification results, blocker list, behavior-change signal, and `standalone_shipping_skipped: true`. When `behavior_change: true`, also require `verification_evidence` that names the relevant units/tasks, existing tests inspected, tests added/changed or used unchanged, red failure or characterization evidence when applicable, verification run, and any deliberate test exception. Do NOT decide the test strategy inside this pipeline; the evidence is the work skill's contract.

   If `behavior_change: true` but `verification_evidence` is missing or too vague to tell how behavior was protected, invoke `ce-work` one more time with the same `mode:return-to-caller <plan-path-from-step-1>` argument. Do not prompt the user and do not alter the plan path argument. The retry relies on the work skill's idempotency path to inspect the already-implemented work, fill the missing evidence, and return without reimplementing. If the second return still lacks coherent verification evidence, stop as blocked and report the missing fields instead of continuing to simplify/review/ship.

3. Invoke the `ce-simplify-code` skill on the `trunk()..@` change-stack diff.

   This runs before review so the code review in step 4 covers the simplified code. **Skip** this step when the change is docs-only (only markdown/docs paths changed) or trivial (roughly under 10 changed lines). Otherwise let `ce-simplify-code` resolve the change-stack scope itself; it preserves behavior and runs the test suite.

   Do not describe or commit a change in this step. `ce-simplify-code` leaves its edits in the JJ working-copy change; step 4's review includes that change, and step 8's `ce-commit-push-pr` describes and commits whatever remains. Committing here could combine still-undescribed work edits under an inaccurate simplification description.

4. Invoke the `ce-code-review` skill with `mode:agent plan:<plan-path-from-step-1>`.

   Pass the plan file path from step 1 so the code-review skill can verify requirements completeness. Read the **Actionable Findings** summary the skill emits.

   `mode:agent` is report-only **by design** — it surfaces findings but never edits the tree; the pipeline applies eligible findings in step 5. Progress narration must state that review findings were applied in step 5 rather than imply that report-only review should have edited the tree. This sequencing is the intended contract.

**Shipping precondition (steps 5–9).** Run `jj git remote list` once before the shipping steps. If it lists **no remote**, shipping is **local-only**: make every JJ commit the steps below call for, but **skip every push, PR create/edit, and CI-watch action** — the pushes in steps 5 and 6, the push and PR creation in step 8, and step 9 in full. A missing remote is a terminal local-only state, not an error: never retry a push or hunt for a remote; make the local commits and proceed to step 10.

When a remote exists, resolve one **shipping bookmark** and reuse it throughout steps 5–9. Prefer the local bookmark matching an existing PR's `headRefName`; otherwise use the nearest meaningful non-trunk local bookmark shown by `jj log -r 'heads(::@ & bookmarks() & ~trunk())'`. Never move the trunk bookmark. If no shipping bookmark exists, derive a meaningful name from the plan. JJ has no implicit active bookmark.

Resolve the push remote by repository identity, never by a conventional default name or list order. For an existing PR, obtain the PR head repository URL from GitHub metadata; otherwise obtain the current GitHub repository URL with `GIT_DIR="$(jj git root)" gh repo view --json url`. Compare it with every URL from `jj git remote list`, normalizing only equivalent HTTPS and SSH/scp forms and an optional conventional repository suffix. Require exactly one match and use that configured JJ remote name. If GitHub metadata is unavailable or URL matching returns zero or multiple remotes, stop and report the ambiguity instead of guessing. After each `jj commit`, create a missing shipping bookmark at the completed change with `jj bookmark create <shipping-bookmark> -r @-`, or advance an existing one with `jj bookmark move <shipping-bookmark> --to @-`; then push exactly that bookmark with `jj git push --remote <remote> --bookmark <shipping-bookmark>`. A push failure with a configured remote is a stop-and-report; do not retry blindly.

Before any step writes under `.tmp/`, inspect the repository's root ignore rules. If `.tmp/` is not already covered, add `.tmp/` to the root `.gitignore` while preserving all existing entries; only then create or write the artifact directory.

5. **Apply and persist review fixes** (REQUIRED after step 4, before residual handoff)

   Load `references/review-followup.md` and execute its apply step (mechanical apply + JJ commit/push when changes exist). Do not proceed to the residual handoff, run browser tests, or output DONE while eligible review fixes remain only in the undescribed working-copy change.

6. **Autonomous residual handoff** (only when step 4 reported one or more actionable `downstream-resolver` findings not applied in step 5; skip when it reported `Actionable findings: none.`)

   Do not prompt the user. This step embraces the autopilot contract: residuals must become durable before DONE, but the agent never stops to ask.

   1. Load `references/tracker-defer.md` in **non-interactive mode**. Pass the residual actionable findings from step 4/5 (or the run artifact when the summary was truncated).
   2. Collect the structured return: `{ filed: [...], failed: [...], no_sink: [...] }`.
   3. Compose a `## Residual Review Findings` markdown section from the structured return:
      - For each item in `filed`: a bullet with severity, file:line, title, and a link to the tracker ticket URL.
      - For each item in `failed`: a bullet with severity, file:line, title, and the failure reason returned by the tracker interface.
      - For each item in `no_sink`: a bullet with severity, file:line, and title inlined verbatim so the PR body or fallback file is the durable record.
   4. Detect the shipping bookmark's open PR without prompting:

      ```bash
      GIT_DIR="$(jj git root)" gh pr view <shipping-bookmark> --json number,url,body,state,headRefName
      ```

   5. If an open PR exists, update it directly with `gh`; do not load any confirmation-driven PR update skill. Append or replace the `## Residual Review Findings` section in the current PR body. Create the body file under `$(jj workspace root)/.tmp/pipeline/`; if JJ is unavailable, use the local `./.tmp/pipeline/` fallback. Then run:

      ```bash
      GIT_DIR="$(jj git root)" gh pr edit PR_NUMBER --body-file BODY_FILE
      ```

   6. If no open PR exists, create a tracked fallback file at `docs/residual-review-findings/<bookmark-or-change-id>.md` containing the composed section and the source PR-review run context. Commit only that file with a JJ `root-file:` fileset. At this `jj commit` composition site, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. Do not impose fixed message syntax or examples, while retaining the semantic constraint that the message describes recording residual review findings. When a remote is configured, create or move the shipping bookmark at `@-` as specified by the shipping precondition and push it with `jj git push --remote <remote> --bookmark <shipping-bookmark>`; otherwise the local JJ commit is the durable sink. Do not output DONE until the residual findings are durable: either the existing PR body has been updated, or this fallback-file change has been committed and, when applicable, pushed. A configured-remote push failure is a stop-and-report; a missing remote never blocks DONE.

   Never block DONE on tracker filing failures once residuals have been durably recorded. A `no_sink` outcome is success only when the findings are present in the PR body or in the committed fallback file, pushed when a remote exists.

7. Invoke the `ce-test-browser` skill with `mode:pipeline`.

8. Invoke the `ce-commit-push-pr` skill with `mode:pipeline`.

   This describes and commits any remaining JJ working-copy edits, moves and pushes the shipping bookmark with `jj git push`, and opens a pull request non-interactively. At every `jj describe`, `jj split`, or `jj commit` composition site reached by this handoff, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. Do not impose fixed message syntax or examples, and preserve the remaining change's semantics and prohibition on decorative markers or identity metadata. If it prints a `New concepts:` trailer after the PR URL, record the concept name(s) for step 10. If step 6 found an existing PR (check with `GIT_DIR="$(jj git root)" gh pr view <shipping-bookmark> --json number,url,state 2>/dev/null`), skip PR creation but still invoke the skill so remaining edits are committed and the bookmark is pushed. **Per the shipping precondition, when no remote is configured, do NOT invoke `ce-commit-push-pr`. Instead commit any remaining edits locally with JJ filesets and skip the push and PR creation entirely, applying the same guidance and repository-first precedence.**

9. **CI watch and autofix loop** (only when an open PR exists for the shipping bookmark)

   Detect the PR; if none exists or `gh` is unavailable, skip this step entirely and proceed to step 10.

   ```bash
   GIT_DIR="$(jj git root)" gh pr view <shipping-bookmark> --json number,url,state,headRefName
   ```

   For up to **3 fix iterations**, repeat:

   1. Wait for CI to complete:

      ```bash
      GIT_DIR="$(jj git root)" gh pr checks <shipping-bookmark> --watch
      ```

      If the command exits 0, all checks passed. Break out of the loop and proceed to step 10.

      If it exits non-zero, one or more checks failed. Continue to (2).

   2. Identify failing checks and pull their failure logs. Use `GIT_DIR="$(jj git root)" gh pr checks <shipping-bookmark> --json name,state,conclusion,workflow,link` to enumerate failures, then for each failing check read the run logs:

      ```bash
      GIT_DIR="$(jj git root)" gh run view <run-id> --log-failed
      ```

      where `<run-id>` is parsed from the check's details URL or workflow run.

   3. Read the failure logs, identify the root cause, and apply a fix in the JJ working-copy change. Do NOT weaken, skip, or mock the failing assertion to make it pass — repair the actual issue. If the failure is a flaky test that has no fix path, document that as the residual outcome below rather than retrying without a code change.

   4. Commit only the files changed for this repair with a JJ fileset, move the shipping bookmark, and push it. At this `jj commit` composition site, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. Do not impose fixed message syntax or examples, and retain the semantic constraint that the message identifies the CI failure repaired without decorative markers or identity metadata.

      ```bash
       jj commit <changed-files-fileset> -m <message>
      jj bookmark move <shipping-bookmark> --to @-
      jj git push --remote <remote> --bookmark <shipping-bookmark>
      ```

   5. Return to iteration (1) with the next attempt counter.

   GATE: STOP iterating after 3 failed attempts. If CI is still red after 3 fix cycles:

   - Compose a `## CI Failures Unresolved` markdown section listing each remaining failing check, the failure summary, and the run/check URL.
   - Append or replace this section in the PR body. Write the body under `$(jj workspace root)/.tmp/pipeline/`; if JJ is unavailable, use the local `./.tmp/pipeline/` fallback. Then run:

     ```bash
     GIT_DIR="$(jj git root)" gh pr edit PR_NUMBER --body-file BODY_FILE
     ```

   - Do NOT continue looping. The autopilot contract is "make residuals durable, then exit." Proceed to step 10.

10. Output `<promise>DONE</promise>` when complete

    If step 8 recorded a `New concepts:` trailer, first echo one line per concept: `New concept introduced: <name> — run /ce-explain <name> to go deeper.` This is an executable skill handoff, so retain the leading slash. Then output the DONE promise.

Start with step 1 now. Remember: plan FIRST, then work. Never skip the plan.
