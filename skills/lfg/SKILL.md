---
name: lfg
description: Run the full hands-off engineering pipeline from planning through a green PR.
disable-model-invocation: true
argument-hint: "[feature description]"
---

CRITICAL: You MUST execute every step below IN ORDER. Do NOT skip any required step. Do NOT jump ahead to coding or implementation. The plan phase (step 1) MUST be completed and verified BEFORE any work begins. Violating this order produces bad output.

When invoking any skill referenced below, resolve its name against the available-skills list the host platform provides and use that exact entry. Some platforms list skills under a plugin namespace (e.g., `plugin:ce-plan`); others list the bare name. Invoking a short-form guess that isn't in the list will fail — always match a listed entry verbatim before calling the Skill/Task tool.

Use JJ for version-control operations. Require `jj workspace root`; if it fails, stop rather than falling back to another version-control interface. Use `jj status`, `jj diff`, `jj log`, and `jj file annotate` for inspection; use changes and bookmarks instead of commits and branches as mutable local concepts; use `jj workspace` commands instead of alternate worktrees; use `jj git fetch` and `jj git push` for remotes. JJ snapshots the working copy automatically, so never stage files. A JJ workspace is a named working copy sharing the repository and operation log, not an independent clone. Revsets select revisions from the graph: `@` is the working-copy change, `@-` is its parent after `jj commit`, `bookmarks()` is not an active-branch pointer, and `trunk()` is valid only when runtime repository-local instructions or aliases define it unambiguously and `trunk() & ~root()` resolves to exactly one revision. Preserve GitHub integration through `gh`, `.github/`, and `.gitignore`; the required `git log` inspection for message conventions is the only direct history command in this workflow. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime repository-local instructions and actual `git log` take precedence over compatible Go guidance. Do not impose a fixed message, prefix, type, scope, subject/body shape, wording, syntax, template, or example.

Resolve scratch paths once as `workspace_root="$(jj workspace root)"` and use only `$workspace_root/.tmp/pipeline`. If root resolution later fails during recovery, use `$PWD/.tmp/pipeline`. Do not use an OS/global temporary mechanism.

1. Invoke the `ce-plan` skill with `$ARGUMENTS`.

   GATE: STOP. If `ce-plan` reported the task is non-software and cannot be processed in pipeline mode, stop and inform the user that this workflow requires software tasks. Otherwise, verify that the `ce-plan` workflow produced a plan file in `docs/plans/`. If no plan file was created, invoke `ce-plan` again with `$ARGUMENTS`. Do NOT proceed to step 2 until a written plan exists. **Record the plan file path** — it will be passed to `ce-work` in step 2 and `ce-code-review` in step 4.

   Read the plan metadata before continuing. If the plan has `artifact_contract: unified-plan/v1`, proceed only when it has `artifact_readiness: implementation-ready` and `execution: code`. Stop the pipeline for `artifact_readiness: requirements-only`, any unrecognized readiness value, `execution: knowledge-work`, approach-plan outputs, answer-seeking/universal outputs, or invalid progress-like readiness values. This workflow never launches `/goal` directly; when goal-mode or dynamic workflows are appropriate, `ce-work` owns that implementation engine choice and must return control afterward.

2. Invoke the `ce-work` skill with `mode:return-to-caller <plan-path-from-step-1>`.

   GATE: STOP. Verify that implementation work was performed - files were created or modified beyond the plan. Read the structured return and require `status: complete`, the same plan path, changed files, U-IDs attempted/completed when present, verification results, blocker list, behavior-change signal, and `standalone_shipping_skipped: true`. When `behavior_change: true`, also require `verification_evidence` that names the relevant units/tasks, existing tests inspected, tests added/changed or used unchanged, red failure or characterization evidence when applicable, verification run, and any deliberate test exception. Do NOT decide the test strategy here; the evidence is `ce-work`'s contract.

   If `behavior_change: true` but `verification_evidence` is missing or too vague to tell how behavior was protected, invoke `ce-work` one more time with the same `mode:return-to-caller <plan-path-from-step-1>` argument. Do not prompt the user and do not alter the plan path argument. The retry relies on the skill's idempotency path to inspect the already-implemented work, fill the missing evidence, and return without reimplementing. If the second return still lacks coherent verification evidence, stop as blocked and report the missing fields instead of continuing to simplify/review/ship.

3. Invoke the `ce-simplify-code` skill on the current JJ change-stack diff.

   This runs before review so the code-review in step 4 covers the simplified code. **Skip** this step when the change is docs-only (only markdown/docs paths changed) or trivial (roughly under 10 changed lines). Otherwise let `ce-simplify-code` resolve the change-stack scope itself; it preserves behavior and runs the test suite.

   Do not record a new JJ boundary in this step. `ce-simplify-code` leaves its edits in the working copy; step 4's review scopes the working-copy change, and step 8's `ce-commit-push-pr` records whatever remains. Recording here could sweep unrelated implementation edits into a misleading description.

4. Invoke the `ce-code-review` skill with `mode:agent plan:<plan-path-from-step-1>`.

   Pass the plan file path from step 1 so ce-code-review can verify requirements completeness. Read the **Actionable Findings** summary the skill emits.

   `mode:agent` is report-only **by design** — it surfaces findings but never edits the working copy; the caller applies eligible ones in step 5. When narrating progress to the user, frame this as "review found X; step 5 applied X," not as "code review did not auto-fix." A report-only review followed by caller-applied fixes is the intended contract, not a gap.

**Shipping precondition (steps 5–9).** Inspect `jj status`, `jj log -r 'heads(::@ & bookmarks())' --no-graph`, and `jj bookmark list --all-remotes`; identify exactly one meaningful local bookmark for this change stack, or create one at the revision being shipped. Never move a trunk bookmark. If several plausible feature bookmarks exist, stop and report the ambiguity. A bookmark may point to an ancestor of `@`; JJ has no active bookmark. Run `jj git remote list` once and retain its name/URL mapping. Resolve the expected GitHub head repository with `gh`: query an open PR for the selected bookmark first and use its head repository identity; otherwise use the repository identity from `gh repo view`. Normalize that identity and every JJ remote URL to canonical GitHub `owner/repo` form, treating HTTPS, `ssh://git@github.com/`, SCP-style `git@github.com:`, and an optional `.git` suffix as equivalent. Require exactly one matching JJ remote. Retain it as `<shipping-remote>` for every push in steps 5–9 and review followup; never prefer `origin` or the first remote. If no JJ remote exists or no URL matches, shipping is **local-only**: record each requested JJ change, but skip every push, PR create/edit, and CI-watch action. Zero matches is terminal local-only, not an invitation to retry or choose another remote. If multiple remotes match, stop and report the ambiguity. Before every push, set the selected bookmark to the exact completed revision being shipped, normally `@-` immediately after `jj commit`; pass both `--bookmark <bookmark>` and `--remote <shipping-remote>` to `jj git push`. Pass the bookmark or resolved PR number explicitly to every `gh` PR command; do not let `gh` infer a branch from the checkout.

5. **Apply and persist review fixes** (REQUIRED after step 4, before residual handoff)

   Load `references/review-followup.md` and execute its apply step (mechanical apply plus a described JJ change and push when changes exist). Do not proceed to the residual handoff, run browser tests, or output DONE while eligible review fixes remain only in an undescribed working-copy change.

6. **Autonomous residual handoff** (only when step 4 reported one or more actionable `downstream-resolver` findings not applied in step 5; skip when it reported `Actionable findings: none.`)

   Do not prompt the user. This step embraces the autopilot contract: residuals must become durable before DONE, but the agent never stops to ask.

   1. Load `references/tracker-defer.md` in **non-interactive mode**. Pass the residual actionable findings from step 4/5 (or the run artifact when the summary was truncated).
   2. Collect the structured return: `{ filed: [...], failed: [...], no_sink: [...] }`.
   3. Compose a `## Residual Review Findings` markdown section from the structured return:
      - For each item in `filed`: a bullet with severity, file:line, title, and a link to the tracker ticket URL.
      - For each item in `failed`: a bullet with severity, file:line, title, and the failure reason (e.g., `Defer failed: gh returned 401 — tracker unavailable`).
      - For each item in `no_sink`: a bullet with severity, file:line, and title inlined verbatim so the PR body or fallback file is the durable record.
   4. Detect the shipping bookmark's open PR without prompting:

      ```bash
      gh pr view "$bookmark" --json number,url,body,state
      ```

   5. If an open PR exists, update it directly with `gh`; do not load any confirmation-driven PR update skill. Append or replace the `## Residual Review Findings` section in the current PR body. Write the new body under `$workspace_root/.tmp/pipeline`; if the workspace root cannot be resolved during recovery, use `$PWD/.tmp/pipeline`. Create the directory if needed and remove the body file after use. Never use an OS/global temporary location. Then run:

      ```bash
      gh pr edit "$PR_NUMBER" --body-file "$BODY_FILE"
      ```

    6. If no open PR exists, create a fallback file at `docs/residual-review-findings/<bookmark-or-change-id>.md` containing the composed section and the source PR-review run context. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime repository-local instructions and actual `git log` take precedence over compatible Go guidance. Do not use a fixed prefix, type, scope, subject/body shape, wording, syntax, template, or example. Store the runtime-composed message in `CHANGE_DESCRIPTION`, then record only that path with `jj commit -m "$CHANGE_DESCRIPTION" <fallback-file>`. `jj commit` creates a new working-copy child at `@`, so the completed fallback change is `@-`. When `<shipping-remote>` was proven by the shipping precondition, move the shipping bookmark to `@-` with `jj bookmark set <bookmark> -r @-`, then run `jj git push --bookmark <bookmark> --remote <shipping-remote>`. In local-only mode, do not push; the local completed change is the durable sink. Do not output DONE until the residual findings are durable: either the existing PR body has been updated, or this fallback-file change has been recorded and pushed when a shipping remote was proven. A push failure after proving a shipping remote is a stop-and-report; never retry a push or block DONE in local-only mode.

   Never block DONE on tracker filing failures once residuals have been durably recorded. A `no_sink` outcome is success only when the findings are present in the PR body or in the pushed fallback file.

7. Invoke the `ce-test-browser` skill with `mode:pipeline`.

8. Invoke the `ce-commit-push-pr` skill with `mode:pipeline remote:<shipping-remote>`.

   Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime repository-local instructions and actual `git log` take precedence over compatible Go guidance. Do not use a fixed prefix, type, scope, subject/body shape, wording, syntax, template, or example. This records any remaining changes, pushes the shipping bookmark only to the supplied `<shipping-remote>`, and opens a pull request non-interactively, per the mode token. If the skill reports new concepts after the PR URL, retain their names for step 10. If step 6 already found a PR by explicitly querying its bookmark, skip PR creation but still record and push remaining changes. **Per the shipping precondition, in local-only mode, do NOT invoke `ce-commit-push-pr`. Instead inspect `jj status`; if the working-copy change has content, compose its description under the rules above, store it in `CHANGE_DESCRIPTION`, run `jj describe -m "$CHANGE_DESCRIPTION"`, then `jj new`. The described change becomes `@-`; do not move a bookmark or push.**

9. **CI watch and autofix loop** (only when an open PR exists for the shipping bookmark)

   Detect the PR; if none exists or `gh` is unavailable, skip this step entirely and proceed to step 10. Set `PR_REF` to the resolved PR number, or to the shipping bookmark if the metadata response does not expose a number. Pass `PR_REF` explicitly to every `gh pr checks` invocation below. Never let `gh pr checks` infer a PR from the current checkout.

   ```bash
   gh pr view "$bookmark" --json number,url,state
   ```

   For up to **3 fix iterations**, repeat:

   1. Wait for CI to complete:

      ```bash
      gh pr checks "$PR_REF" --watch
      ```

      If the command exits 0, all checks passed. Break out of the loop and proceed to step 10.

      If it exits non-zero, one or more checks failed. Continue to (2).

   2. Identify failing checks and pull their failure logs. Use `gh pr checks "$PR_REF" --json name,state,conclusion,workflow,link` to enumerate failures, then for each failing check read the run logs:

      ```bash
      gh run view <run-id> --log-failed
      ```

      where `<run-id>` is parsed from the check's details URL or workflow run.

   3. Read the failure logs, identify the root cause, and apply a fix in the working copy. Do NOT weaken, skip, or mock the failing assertion to make it pass — repair the actual issue. If the failure is a flaky test that has no fix path, document that as the residual outcome below rather than retrying without a code change.

   4. Record only the files changed by the fix and push. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime repository-local instructions and actual `git log` take precedence over compatible Go guidance. Do not use a fixed prefix, type, scope, subject/body shape, wording, syntax, template, or example. Store the runtime-composed message in `CHANGE_DESCRIPTION` before running the command below. `jj commit` creates a new working-copy child, so move the bookmark to completed revision `@-`.

      ```bash
      jj commit -m "$CHANGE_DESCRIPTION" <changed-files>
      jj bookmark set <bookmark> -r @-
      jj git push --bookmark <bookmark> --remote <shipping-remote>
      ```

   5. Return to iteration (1) with the next attempt counter.

   GATE: STOP iterating after 3 failed attempts. If CI is still red after 3 fix cycles:

   - Compose a `## CI Failures Unresolved` markdown section listing each remaining failing check, the failure summary, and the run/check URL.
   - Append or replace this section in the PR body. Write the new body under `$workspace_root/.tmp/pipeline`; if the workspace root cannot be resolved during recovery, use `$PWD/.tmp/pipeline`. Create the directory if needed and remove the body file after use. Never use an OS/global temporary location. Then run:

     ```bash
     gh pr edit "$PR_NUMBER" --body-file "$BODY_FILE"
     ```

   - Do NOT continue looping. The autopilot contract is "make residuals durable, then exit." Proceed to step 10.

10. Output `<promise>DONE</promise>` when complete

    If step 8 reported new concepts, first tell the user that each can be explored with `/ce-explain <name>`. Then output the DONE promise.

Start with step 1 now. Remember: plan FIRST, then work. Never skip the plan.
