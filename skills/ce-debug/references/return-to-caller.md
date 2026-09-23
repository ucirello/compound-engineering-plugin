# ce-debug — return-to-caller mode (non-interactive, caller owns the steps after the fix)

Loaded when `ce-debug` is invoked with `mode:return-to-caller` by an orchestrator such as `lfg` on its defect route. The caller asked for the bug fixed and owns everything after the fix: simplify, review, compound, commit of anything further, push, PR, and CI. This skill investigates, fixes, verifies, commits on a feature branch, and returns a structured result. It never pushes and never asks.

This is not `mode:pipeline`. Pipeline mode serves the babysitter on a PR branch it already owns: it is seeded with failing jobs, pushes its own commit, and skips review because the babysitter scopes review. Here nothing is pushed and the caller reviews.

## What stays the same

Phases 0 through 3 run as the body defines them, with the investigation rigor unchanged: the causal-chain gate, reproduction, the escalation table, the test-first fix sequence in `references/fix.md`, and the issue-of-record rule. The **Branch** rule in Phase 3 applies in full: on the default bookmark, without a feature bookmark, or unsure, prepare a feature change and bookmark named from the bug before the first edit and say which bookmark carries the fix. A defect request invoked on `main` must not move `main`. An empty `@` above a feature bookmark's tip at `@-` does not mean that bookmark is absent. The pre-fix scope record and the fix-owned file list are kept, because the return is built from them: the caller ships only what the user offered, and this return is the only place it can learn what was already in the tree or on the branch before the fix.

## What changes

- **Phase 0:** if an issue fetch fails, continue with the input you have and record the gap in the return. Never ask the user to paste content.
- **Phase 2 gate:** there is no fix-choice question. The caller's invocation authorized the fix, so proceed to Phase 3 with a **convergent** fix only. A **divergent** fix, one that would reverse a deliberate contract, behavior, or product decision, including a "failing" test that asserts intended behavior, is deferred as `needs-human` with a `decision_context`, never applied. Never route to `ce-brainstorm`; a design problem is a `needs-human` residual. When reproduction cannot run in this environment, continue on the best evidence in reach; if the causal chain still has a gap, return `needs-human` naming what reproduction requires and what was tried.
- **Phase 3:** apply the fix on the feature change, verify it as `references/fix.md` defines (red then green where a test can run here; otherwise the reproduction check or characterization that file allows, recorded in the evidence), and commit only the fix-owned files with JJ. Point the feature bookmark at that fix commit without moving the default bookmark. Do not push. A file the fix must touch that already carries the user's in-progress edits stops the run before the first edit to it: return `blocked` naming the file, with nothing applied, since file-scoped committing cannot separate their edits from the fix and the caller cannot answer for the user. The pre-fix scope record makes this known before Phase 3 edits anything.
- **Phase 4:** skip the Debug Summary block, the post-fix polish and review steps (`references/post-fix-handoff.md`), the commit/PR routing, and the learning-capture offer. Emit the structured return below as the last thing this skill writes. The return ends this skill, not the turn. The caller runs in this same session, and its next step follows the return.

**Commit message:** "Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards." Here the quoted history command means history inspected using `jj log` for this JJ workflow. Active project instructions and observed history syntax override the Go guidance. Preserve the bug, causal fix, and relevant issue/PR references without imposing a fixed prefix. The message argument for any JJ commit/description command is `<message composed from the standards above>`.

Run every JJ subprocess from the absolute workspace root. Preserve the return field names below for callers: `branch` means the feature bookmark, `head_sha` is the full fix commit ID (not an empty `@` child or a change ID), and `pre_fix_scope.head` is the full recorded pre-fix commit ID. Resolve these through `jj log` and `jj bookmark list`, never metadata files.

## Structured return

The return is machine-readable; the caller parses it and branches on the exact `status` spellings, so never rename, abbreviate, or add to them.

```json
{
  "status": "fixed | diagnosed-no-fix | needs-human | blocked",
  "summary": "<one line: what happened>",
  "root_cause": "<the causal chain, trigger to symptom, with file:line references>",
  "changed_files": ["<fix-owned files, tests included>"],
  "head_sha": "<sha of the fix commit, when fixed>",
  "branch": "<feature bookmark pointing to the fix commit, when fixed>",
  "pre_fix_scope": {
    "head": "<full working-copy commit ID recorded before the fix>",
    "dirty_files": ["<files already modified or untracked before Phase 3 that are not fix-owned; left untouched>"],
    "commits_beyond_base": ["<commits beyond the default remote bookmark before the fix, oldest first; omit only an empty working-copy child, never pre-existing work>"],
    "started_on_default_branch": false
  },
  "behavior_change": true,
  "verification_evidence": {
    "regression_test": "<file and case>",
    "existing_tests_inspected": ["..."],
    "tests_added_or_changed": ["..."],
    "red_before_fix": "<the failure observed before the fix, or the characterization when a red run was impossible>",
    "verification_run": "<commands and results>",
    "exception_reason": null
  },
  "residuals": [ { "type": "needs-human", "sources": [ ... ], "decision_context": { ... }, "thread_urls": [] } ],
  "issue_of_record": { "id": "<identifier>", "url": "<url>" },
  "blockers": [],
  "standalone_shipping_skipped": true
}
```

- `fixed`: a convergent fix is applied, its regression test went red then green, and the fix-owned files are committed on the feature branch. Nothing was pushed.
- `diagnosed-no-fix`: the root cause is established but no safe convergent fix exists this run; `residuals` says why.
- `needs-human`: the fix would be divergent, or the causal chain could not be closed without a decision only a person can make; nothing applied; `residuals` carries the `decision_context` in the same typed residual contract `references/pipeline-mode.md` defines.
- `blocked`: a required read failed, a fix-owned file carried the user's edits, or the workspace could not be prepared; `blockers` names it and nothing was committed.

`pre_fix_scope` is present on every return and records what the bookmark ancestry and working copy carried before the fix, as observed facts: the full pre-fix commit ID, the files that were already dirty and are not fix-owned (the fix never touched them), and the commits beyond the default remote bookmark, pushed or not. A new bookmark is not proof that this ancestry is empty. `started_on_default_branch` records whether the effective starting tip was the default bookmark. It carries no verdict about what the user offered; the caller decides that, and this record is what it decides from. `issue_of_record` is `null` when the input carried no ticket. `verification_evidence` is present on every `fixed` return; when `behavior_change` is `false` (a pure test or tooling fix), `exception_reason` says why no red-then-green was possible. `residuals` is an empty array when there are none.
