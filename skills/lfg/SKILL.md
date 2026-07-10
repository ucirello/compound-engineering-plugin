---
name: lfg
description: Run the full hands-off engineering pipeline from planning through a green PR.
disable-model-invocation: true
argument-hint: "[feature description]"
---

CRITICAL: You MUST execute every step below IN ORDER. Do NOT skip any required step. Do NOT jump ahead to coding or implementation. The plan phase (step 1) MUST be completed and verified BEFORE any work begins. Violating this order produces bad output.

When invoking any skill referenced below, resolve its name against the available-skills list the host platform provides and use that exact entry. Some platforms list skills under a plugin namespace (e.g., `compound-engineering:ce-plan`); others list the bare name. Invoking a short-form guess that isn't in the list will fail — always match a listed entry verbatim before calling the Skill/Task tool.

**JJ preflight and vocabulary.** LFG operates in a Jujutsu workspace, not through Git's index, `HEAD`, current-branch, or worktree model.

1. Require `jj workspace root` to succeed and record that path. `@` is the current workspace's working-copy change, `@-` is its parent, and `trunk()` is the repository's configured base revision. Use `jj status`, `jj diff`, and `jj log`; never use Git commands for status, diffs, or history.
2. Resolve and retain one `FEATURE_BOOKMARK` for the whole run. A JJ bookmark is only a named revision pointer; there is no active/current bookmark. Inspect `jj bookmark list` and `jj log -r 'bookmarks() & ::@ & ~::trunk()'`. Prefer the sole local bookmark on the current feature stack, or the sole candidate whose GitHub PR is open. If neither identifies one bookmark, create a unique ASCII `lfg-<short-change-id>` bookmark at `@` with `jj bookmark create <name> -r @`. Never infer identity from Git `HEAD` or invent a “current branch.”
3. Compute the complete feature scope against the base with `jj diff --from 'trunk()' --to @`, `jj diff --summary --from 'trunk()' --to @`, and `jj log -r 'trunk()..@'`. A plain `jj diff` is only the current working-copy change, not the whole feature stack.
4. JJ has no staging area. “Commit only these files” means pass explicit filesets to `jj commit <files> -m <message>`; selected changes remain in the described commit and unselected changes move to the new working-copy change. After each such commit, point `FEATURE_BOOKMARK` at the committed parent with `jj bookmark set "$FEATURE_BOOKMARK" -r @-`.
5. Run `gh` against the retained bookmark, never an inferred current branch. In a non-colocated JJ repository, prefix `gh` commands with `GIT_DIR="$(jj git root)"`; the same prefix is harmless as a documented fallback whenever repository discovery is uncertain.
6. If the feature must be updated from the remote base, use `jj git fetch --remote <remote>`, then `jj rebase -r 'trunk()..@' -o 'trunk()'`; `-r` limits the source to revisions in the current ancestry stack, unlike branch mode, which can also select descendants outside it. Do not pull or merge a base branch. If a true merge change is required by the plan, create it explicitly with `jj new <parent-1> <parent-2>`. Resolve any materialized conflicts before continuing and verify with `jj status`.

1. Invoke the `ce-plan` skill with `$ARGUMENTS`.

   GATE: STOP. If ce-plan reported the task is non-software and cannot be processed in pipeline mode, stop the pipeline and inform the user that LFG requires software tasks. Otherwise, verify that the `ce-plan` workflow produced a plan file in `docs/plans/`. If no plan file was created, invoke `ce-plan` again with `$ARGUMENTS`. Do NOT proceed to step 2 until a written plan exists. **Record the plan file path** — it will be passed to ce-work in step 2 and ce-code-review in step 4.

   Read the plan metadata before continuing. If the plan has `artifact_contract: ce-unified-plan/v1`, proceed only when it has `artifact_readiness: implementation-ready` and `execution: code`. Stop the pipeline for `artifact_readiness: requirements-only`, any unrecognized readiness value, `execution: knowledge-work`, approach-plan outputs, answer-seeking/universal outputs, or invalid progress-like readiness values. LFG never launches `/goal` directly; when goal-mode or dynamic workflows are appropriate, `ce-work` owns that implementation engine choice and must return control to LFG afterward.

2. Invoke the `ce-work` skill with `mode:return-to-caller <plan-path-from-step-1>`.

   GATE: STOP. Verify that implementation work was performed - files were created or modified beyond the plan. Read the structured return and require `status: complete`, the same plan path, changed files, U-IDs attempted/completed when present, verification results, blocker list, behavior-change signal, and `standalone_shipping_skipped: true`. When `behavior_change: true`, also require `verification_evidence` that names the relevant units/tasks, existing tests inspected, tests added/changed or used unchanged, red failure or characterization evidence when applicable, verification run, and any deliberate test exception. Do NOT decide the test strategy inside LFG; the evidence is ce-work's contract.

   If `behavior_change: true` but `verification_evidence` is missing or too vague to tell how behavior was protected, invoke `ce-work` one more time with the same `mode:return-to-caller <plan-path-from-step-1>` argument. Do not prompt the user and do not alter the plan path argument. The retry relies on ce-work's idempotency path to inspect the already-implemented work, fill the missing evidence, and return without reimplementing. If the second return still lacks coherent verification evidence, stop as blocked and report the missing fields instead of continuing to simplify/review/ship.

   Before review or shipping, re-anchor `FEATURE_BOOKMARK` to the implementation head. Resolve `heads(trunk()..@ & ~empty())`; require exactly one revision, stop if the set is empty or has multiple heads, then run `jj bookmark set "$FEATURE_BOOKMARK" -r '<resolved-head>'` and verify `jj bookmark list -r '<resolved-head>'` names exactly that bookmark. This prevents an earlier bookmark target from excluding changes produced by `ce-work` without guessing across an ambiguous stack.

3. Invoke the `ce-simplify-code` skill on the complete feature-stack diff from `trunk()` to `@`.

   This runs before review so the code-review in step 4 covers the simplified code. Use `jj diff --summary --from 'trunk()' --to @` and `jj diff --stat --from 'trunk()' --to @` to classify scope. **Skip** this step when the change is docs-only (only markdown/docs paths changed) or trivial (roughly under 10 changed lines). Otherwise tell `ce-simplify-code` that the scope is the JJ feature-stack diff `trunk()..@`; it preserves behavior and runs the test suite.

   Do not run `jj commit` in this step. `ce-simplify-code` leaves its edits in the working-copy change; step 4 reviews the complete feature-stack diff (including `@`), and step 8 describes and advances whatever remains. Committing here would sweep any still-undescribed `ce-work` edits into a misleading `refactor` change and could stall on a working-copy change that never becomes empty.

4. Invoke the `ce-code-review` skill with `mode:agent plan:<plan-path-from-step-1>`.

   Pass the plan file path from step 1 so ce-code-review can verify requirements completeness. Read the **Actionable Findings** summary the skill emits.

   `mode:agent` is report-only **by design** — it surfaces findings but never edits the tree; LFG applies the eligible ones in step 5. When narrating progress to the user, frame this as "review found X → applied X in step 5," not as "code review did not auto-fix." A report-only review followed by an LFG-applied fix is the intended contract, not a gap.

**Shipping precondition (steps 5–9).** Run `jj git remote list` once before the shipping steps. If it lists **no remote**, shipping is **local-only**: make every local change description the steps below call for, but **skip every push, PR create/edit, and CI-watch action**. A missing remote is a terminal local-only state, not an error: never retry a push or hunt for a remote — persist the local changes and proceed to step 10. When remotes exist, select and retain one `SHIPPING_REMOTE`: read `jj config get git.push`; use that configured remote when present, otherwise `origin` when present, otherwise the sole remote. If multiple remotes remain ambiguous, stop rather than push to an arbitrary repository. Run `jj git fetch --remote "$SHIPPING_REMOTE"` before the first push; if push safety rejects a stale remote bookmark, fetch that same remote, resolve any bookmark conflict, and retry once. Never substitute `git fetch`, `git pull`, or `git push`.

5. **Apply and persist review fixes** (REQUIRED after step 4, before residual handoff)

   Load `references/review-followup.md` and execute its apply step (mechanical apply + describe/advance/push when changes exist). Do not proceed to the residual handoff, run browser tests, or output DONE while eligible review fixes remain only in the working-copy change undescribed.

6. **Autonomous residual handoff** (only when step 4 reported one or more actionable `downstream-resolver` findings not applied in step 5; skip when it reported `Actionable findings: none.`)

   Do not prompt the user. This step embraces the autopilot contract: residuals must become durable before DONE, but the agent never stops to ask.

   1. Load `references/tracker-defer.md` in **non-interactive mode**. Pass the residual actionable findings from step 4/5 (or the run artifact when the summary was truncated).
   2. Collect the structured return: `{ filed: [...], failed: [...], no_sink: [...] }`.
   3. Compose a `## Residual Review Findings` markdown section from the structured return:
      - For each item in `filed`: a bullet with severity, file:line, title, and a link to the tracker ticket URL.
      - For each item in `failed`: a bullet with severity, file:line, title, and the failure reason (e.g., `Defer failed: gh returned 401 — tracker unavailable`).
      - For each item in `no_sink`: a bullet with severity, file:line, and title inlined verbatim so the PR body or fallback file is the durable record.
   4. Detect `FEATURE_BOOKMARK`'s open PR without prompting; do not rely on Git `HEAD` or implicit branch discovery:

      ```bash
      GIT_DIR="$(jj git root)" gh pr view "$FEATURE_BOOKMARK" --json number,url,body,state
      ```

   5. If an open PR exists, update it directly with `gh`; do not load any confirmation-driven PR update skill. Append or replace the `## Residual Review Findings` section in the current PR body, write the new body to an OS temp file, then run:

      ```bash
      GIT_DIR="$(jj git root)" gh pr edit PR_NUMBER --body-file BODY_FILE
      ```

   6. If no open PR exists, create a tracked fallback file at `docs/residual-review-findings/<feature-bookmark-or-change-id>.md` containing the composed section and the source PR-review run context. Commit only that fileset with `jj commit docs/residual-review-findings/<file>.md -m "docs(review): record residual review findings"`, run `jj bookmark set "$FEATURE_BOOKMARK" -r @-`, and push with `jj git push --bookmark "$FEATURE_BOOKMARK" --remote "$SHIPPING_REMOTE"` **when a remote is configured**. If there is no remote at all, do not push — the locally committed fallback file is the durable sink. Do not output DONE until the residual findings are durable.

   Never block DONE on tracker filing failures once residuals have been durably recorded. A `no_sink` outcome is success only when the findings are present in the PR body, in the pushed fallback file, or in the locally committed fallback file during local-only shipping.

7. Invoke the `ce-test-browser` skill with `mode:pipeline`.

8. Persist and publish the feature. If `@` is non-empty, invoke `ce-commit` to finish the remaining logical changes. Resolve `heads(trunk()..@ & ~empty())`, require exactly one publishable head, set `FEATURE_BOOKMARK` to it, and verify the target. When a remote exists, push only that bookmark with `jj git push --remote "$SHIPPING_REMOTE" --bookmark "exact:$FEATURE_BOOKMARK"`.

   Detect an existing PR explicitly with `GIT_DIR="$(jj git root)" gh pr view "$FEATURE_BOOKMARK" --json number,url,state`. If none exists, compose the title and body from the plan, verification, monitoring, and residual context, then run `gh pr create` with explicit `--head "$FEATURE_BOOKMARK"`, `--base <base-bookmark>`, `--title`, and `--body-file`. If one exists, update it by PR number with `gh pr edit`. Never infer a branch from Git `HEAD` or use argumentless `gh pr view`. When no remote is configured, persist local changes and advance the bookmark, but skip push and PR creation.

9. **CI watch and autofix loop** (only when an open PR exists for `FEATURE_BOOKMARK`)

   Detect the PR; if none exists or `gh` is unavailable, skip this step entirely and proceed to step 10.

   ```bash
   GIT_DIR="$(jj git root)" gh pr view "$FEATURE_BOOKMARK" --json number,url,state
   ```

   For up to **3 fix iterations**, repeat:

   1. Wait for CI to complete:

      ```bash
      GIT_DIR="$(jj git root)" gh pr checks "$FEATURE_BOOKMARK" --watch
      ```

      If the command exits 0, all checks passed. Break out of the loop and proceed to step 10.

      If it exits non-zero, one or more checks failed. Continue to (2).

   2. Identify failing checks and retrieve their failure logs. Use `GIT_DIR="$(jj git root)" gh pr checks "$FEATURE_BOOKMARK" --json name,state,bucket,workflow,link` to enumerate failures (`bucket` is `pass`, `fail`, `pending`, `skipping`, or `cancel`), then for each failing check read the run logs:

      ```bash
      GIT_DIR="$(jj git root)" gh run view <run-id> --log-failed
      ```

      where `<run-id>` is parsed from the check's details URL or workflow run.

   3. Read the failure logs, identify the root cause, and apply a fix in the current working-copy change. Do NOT weaken, skip, or mock the failing assertion to make it pass — repair the actual issue. If the failure is a flaky test that has no fix path, document that as the residual outcome below rather than retrying without a code change.

   4. Verify the fileset with `jj diff --summary`, commit only the files you changed, advance the bookmark to the committed parent, and push that bookmark to the retained remote. There is no staging step:

      ```bash
      jj commit <changed-files> -m "fix(ci): <one-line summary of the failure repaired>"
      jj bookmark set "$FEATURE_BOOKMARK" -r @-
      jj git push --bookmark "$FEATURE_BOOKMARK" --remote "$SHIPPING_REMOTE"
      ```

   5. Return to iteration (1) with the next attempt counter.

   GATE: STOP iterating after 3 failed attempts. If CI is still red after 3 fix cycles:

   - Compose a `## CI Failures Unresolved` markdown section listing each remaining failing check, the failure summary, and the run/check URL.
   - Append or replace this section in the PR body, write the new body to an OS temp file, then run:

     ```bash
     GIT_DIR="$(jj git root)" gh pr edit PR_NUMBER --body-file BODY_FILE
     ```

   - Do NOT continue looping. The autopilot contract is "make residuals durable, then exit." Proceed to step 10.

10. Output `<promise>DONE</promise>` when complete

    If step 8 recorded a `New concepts:` trailer, first echo one line per concept: `New concept introduced: <name> — run /ce-explain <name> to go deeper.` Then output the DONE promise.

Start with step 1 now. Remember: plan FIRST, then work. Never skip the plan.
