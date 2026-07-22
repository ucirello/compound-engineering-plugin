---
name: lfg
description: Run the full hands-off engineering pipeline from planning through a green PR.
disable-model-invocation: true
argument-hint: "[feature description]"
---

CRITICAL: You MUST execute every step below IN ORDER. Do NOT skip any required step. Do NOT jump ahead to coding or implementation. The plan phase (step 1) MUST be completed and verified BEFORE any work begins. Violating this order produces bad output.

When invoking any skill referenced below, resolve its name against the available-skills list the host platform provides and use that exact entry. Platforms may list a skill under a provider namespace or by its bare name. Invoking a short-form guess that isn't in the list will fail — always match a listed entry verbatim before calling the Skill/Task tool.

Use JJ for version-control operations: changes instead of commits, bookmarks instead of branches, `jj workspace` instead of alternate worktrees, and `jj git ...` for remotes. Preserve GitHub integration through `gh`, `.github/`, and `.gitignore`. The only direct Git command in this workflow is the required `git log` inspection for change-description style.

Keep scratch files under `$(jj workspace root)/.tmp`; if `jj workspace root` fails during recovery, use `$PWD/.tmp`. Never use an OS/global temporary API or path.

1. Invoke the `ce-plan` skill with `$ARGUMENTS`.

   GATE: STOP. If ce-plan reported the task is non-software and cannot be processed in pipeline mode, stop the pipeline and inform the user that this workflow requires software tasks. Otherwise, verify that the `ce-plan` workflow produced a plan file in `docs/plans/`. If no plan file was created, invoke `ce-plan` again with `$ARGUMENTS`. Do NOT proceed to step 2 until a written plan exists. **Record the plan file path** — it will be passed to ce-work in step 2 and ce-code-review in step 4.

   Read the plan metadata before continuing. If the plan has `artifact_contract: unified-plan/v1`, proceed only when it has `artifact_readiness: implementation-ready` and `execution: code`. Stop the pipeline for `artifact_readiness: requirements-only`, any unrecognized readiness value, `execution: knowledge-work`, approach-plan outputs, answer-seeking/universal outputs, or invalid progress-like readiness values. This workflow never launches `/goal` directly; when goal-mode or dynamic workflows are appropriate, `ce-work` owns that implementation engine choice and must return control afterward.

2. Invoke the `ce-work` skill with `mode:return-to-caller <plan-path-from-step-1>`.

   GATE: STOP. Verify that implementation work was performed - files were created or modified beyond the plan. Read the structured return and require `status: complete`, the same plan path, changed files, U-IDs attempted/completed when present, verification results, blocker list, behavior-change signal, and `standalone_shipping_skipped: true`. When `behavior_change: true`, also require `verification_evidence` that names the relevant units/tasks, existing tests inspected, tests added/changed or used unchanged, red failure or characterization evidence when applicable, verification run, and any deliberate test exception. Do NOT decide the test strategy inside this workflow; the evidence is ce-work's contract.

   If `behavior_change: true` but `verification_evidence` is missing or too vague to tell how behavior was protected, invoke `ce-work` one more time with the same `mode:return-to-caller <plan-path-from-step-1>` argument. Do not prompt the user and do not alter the plan path argument. The retry relies on ce-work's idempotency path to inspect the already-implemented work, fill the missing evidence, and return without reimplementing. If the second return still lacks coherent verification evidence, stop as blocked and report the missing fields instead of continuing to simplify/review/ship.

3. Invoke the `ce-simplify-code` skill on the current JJ change-stack diff.

   This runs before review so the code-review in step 4 covers the simplified code. **Skip** this step when the change is docs-only (only markdown/docs paths changed) or trivial (roughly under 10 changed lines). Otherwise let `ce-simplify-code` resolve the JJ change-stack scope itself; it preserves behavior and runs the test suite.

   Do not record a separate JJ change in this step. `ce-simplify-code` leaves its edits in the working-copy change; step 4 reviews that change, and step 8's `ce-commit-push-pr` records whatever remains. Recording here could separate edits that belong to the implementation and stall a workflow waiting for an empty working-copy change.

4. Invoke the `ce-code-review` skill with `mode:agent plan:<plan-path-from-step-1>`.

   Pass the plan file path from step 1 so ce-code-review can verify requirements completeness. Read the **Actionable Findings** summary the skill emits.

   `mode:agent` is report-only **by design** — it surfaces findings but never edits the tree; step 5 applies the eligible ones. When narrating progress to the user, frame this as "review found X → applied X in step 5," not as "code review did not auto-fix." A report-only review followed by a workflow-applied fix is the intended contract, not a gap.

**Shipping identity and precondition (steps 5–9).** Run `jj bookmark list -r @` once. Resolve the intended PR bookmark from that output and retain its exact local name as `BOOKMARK` for every later step. If exactly one local bookmark points to `@`, select it. If zero or multiple local bookmarks point to `@`, require explicit user input naming the intended PR bookmark; do not infer one from recency, tracking state, Git configuration, or another revision. Verify an existing selected bookmark points to `@`; create a new bookmark at `@` only when the user explicitly supplied that new name.

Run `jj git remote list` once and retain the intended remote's exact name as `REMOTE`. If exactly one remote exists, select it. If multiple remotes exist, require explicit user input naming one of the listed remotes; do not infer it from bookmark tracking state, remote order, or a conventional name such as `origin`. If it lists **no remote** (for example, in a sandbox or throwaway workspace), shipping is **local-only**: record every JJ change the steps below call for, but **skip every push, PR create/edit, and CI-watch action** — the pushes in steps 5 and 6, the push and PR creation in step 8, and step 9 in full. A missing remote is a terminal local-only state, not an error: never retry a push or hunt for a remote; record the local changes and proceed to step 10. When `REMOTE` exists, every push in this workflow must target only the retained shipping identity with `jj git push --remote "$REMOTE" --bookmark "exact:$BOOKMARK"`.

5. **Apply and persist review fixes** (REQUIRED after step 4, before residual handoff)

   Load `references/review-followup.md`, pass the retained `BOOKMARK` and `REMOTE` (or the explicit local-only state), and execute its apply step (mechanical apply + record/push when changes exist). Do not proceed to the residual handoff, run browser tests, or output DONE while eligible review fixes remain only in the working-copy change and unrecorded.

6. **Autonomous residual handoff** (only when step 4 reported one or more actionable `downstream-resolver` findings not applied in step 5; skip when it reported `Actionable findings: none.`)

   Do not prompt the user. This step embraces the autopilot contract: residuals must become durable before DONE, but the agent never stops to ask.

   1. Load `references/tracker-defer.md` in **non-interactive mode**. Pass the residual actionable findings from step 4/5 (or the run artifact when the summary was truncated).
   2. Collect the structured return: `{ filed: [...], failed: [...], no_sink: [...] }`.
   3. Compose a `## Residual Review Findings` markdown section from the structured return:
      - For each item in `filed`: a bullet with severity, file:line, title, and a link to the tracker ticket URL.
      - For each item in `failed`: a bullet with severity, file:line, title, and the failure reason (e.g., `Defer failed: gh returned 401 — tracker unavailable`).
      - For each item in `no_sink`: a bullet with severity, file:line, and title inlined verbatim so the PR body or fallback file is the durable record.
   4. Detect the retained PR bookmark's open PR without prompting:

      ```bash
      gh pr view "$BOOKMARK" --json number,url,body,state
      ```

   5. If an open PR exists, update it directly with `gh`; do not load any confirmation-driven PR update skill. Append or replace the `## Residual Review Findings` section in that PR body. Resolve `WORKSPACE_ROOT="$(jj workspace root)"`; if that fails during recovery, use `WORKSPACE_ROOT="$PWD"`. Create `BODY_DIR="$WORKSPACE_ROOT/.tmp/rocketclaw"`, write the new body to a file under that directory, then run:

      ```bash
      gh pr edit PR_NUMBER --body-file BODY_FILE
      ```

   6. If no open PR exists, create a tracked fallback file at `docs/residual-review-findings/<bookmark-or-change-id>.md` containing the composed section and the source PR-review run context. Record only that file as a JJ change, move the retained `BOOKMARK` to the recorded revision when needed, and push **when `REMOTE` exists** (per the shipping precondition). The description must identify that residual review findings were recorded. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and message syntax found in actual `git log` output take precedence; apply compatible Go guidance only to quality, clarity, and structure. Do not impose fixed message syntax or examples. Push only with `jj git push --remote "$REMOTE" --bookmark "exact:$BOOKMARK"`. If there is no remote at all, do not push — the locally recorded JJ change suffices. This is the durable no-PR sink. Do not output DONE until the residual findings are durable: either the existing PR body has been updated, or this fallback-file change has been recorded (and pushed when a remote exists). A push that fails when a remote exists is a stop-and-report; never retry a push, or block DONE, when no remote exists.

   Never block DONE on tracker filing failures once residuals have been durably recorded. A `no_sink` outcome is success only when the findings are present in the PR body or in the pushed fallback file.

7. Invoke the `ce-test-browser` skill with `mode:pipeline`.

8. Invoke the `ce-commit-push-pr` skill with `mode:pipeline bookmark:<exact-BOOKMARK> remote:<exact-REMOTE>`.

   This records any remaining changes, pushes only the explicitly passed PR bookmark to the explicitly passed remote with `jj git push --remote "$REMOTE" --bookmark "exact:$BOOKMARK"`, and opens a pull request — non-interactively, per the mode token. Do not permit `ce-commit-push-pr` to select or substitute a bookmark or remote. If it prints a `New concepts:` trailer after the PR URL, record the concept name(s) for step 10. If step 6 already found an open PR (check with `gh pr view "$BOOKMARK" --json number,url,state`), skip PR creation but still record and push any unrecorded changes. **Per the shipping precondition, when no remote is configured, do NOT invoke `ce-commit-push-pr`; instead invoke the listed `ce-commit` skill to record any remaining changes locally and skip the push and PR creation entirely.** Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and message syntax found in actual `git log` output take precedence; apply compatible Go guidance only to quality, clarity, and structure. Do not impose fixed message syntax or examples.

9. **CI watch and autofix loop** (only when an open PR exists for the retained `BOOKMARK`)

   Detect the PR; if none exists or `gh` is unavailable, skip this step entirely and proceed to step 10.

   ```bash
   gh pr view "$BOOKMARK" --json number,url,state
   ```

   For up to **3 fix iterations**, repeat:

   1. Wait for CI to complete:

      ```bash
      gh pr checks "$BOOKMARK" --watch
      ```

      If the command exits 0, all checks passed. Break out of the loop and proceed to step 10.

      If it exits non-zero, one or more checks failed. Continue to (2).

   2. Identify failing checks and pull their failure logs. Use `gh pr checks "$BOOKMARK" --json name,state,conclusion,workflow,link` to enumerate failures, then for each failing check read the run logs:

      ```bash
      gh run view <run-id> --log-failed
      ```

      where `<run-id>` is parsed from the check's details URL or workflow run.

   3. Read the failure logs, identify the root cause, and apply a fix in the JJ working-copy change. Do NOT weaken, skip, or mock the failing assertion to make it pass — repair the actual issue. If the failure is a flaky test that has no fix path, document that as the residual outcome below rather than retrying without a code change.

   4. Record only the files you changed as a JJ change, move the retained `BOOKMARK` to the recorded revision when needed, and push only with `jj git push --remote "$REMOTE" --bookmark "exact:$BOOKMARK"`. The description must identify the CI failure that was repaired. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and message syntax found in actual `git log` output take precedence; apply compatible Go guidance only to quality, clarity, and structure. Do not impose fixed message syntax or examples.

   5. Return to iteration (1) with the next attempt counter.

   GATE: STOP iterating after 3 failed attempts. If CI is still red after 3 fix cycles:

   - Compose a `## CI Failures Unresolved` markdown section listing each remaining failing check, the failure summary, and the run/check URL.
   - Append or replace this section in the PR body. Resolve `WORKSPACE_ROOT="$(jj workspace root)"`; if that fails during recovery, use `WORKSPACE_ROOT="$PWD"`. Create `BODY_DIR="$WORKSPACE_ROOT/.tmp/rocketclaw"`, and write the new body to a file under that directory, then run:

     ```bash
     gh pr edit PR_NUMBER --body-file BODY_FILE
     ```

   - Do NOT continue looping. The autopilot contract is "make residuals durable, then exit." Proceed to step 10.

10. Output `<promise>DONE</promise>` when complete

    If step 8 recorded a `New concepts:` trailer, first echo one line per concept: `New concept introduced: <name> — run /ce-explain <name> to go deeper.` Then output the DONE promise.

Start with step 1 now. Remember: plan FIRST, then work. Never skip the plan.
