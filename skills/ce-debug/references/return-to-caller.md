# ce-debug — return-to-caller mode (non-interactive, caller owns the steps after the fix)

Loaded when `ce-debug` is invoked with `mode:return-to-caller` by an orchestrator such as `lfg` on its defect route. The caller asked for the bug fixed and owns everything after the fix: simplify, review, compound, commit of anything further, push, PR, and CI. This skill investigates, fixes, verifies, commits on a feature branch, and returns a structured result. It never pushes and never asks.

This is not `mode:pipeline`. Pipeline mode serves the babysitter on a PR branch it already owns: it is seeded with failing jobs, pushes its own commit, and skips review because the babysitter scopes review. Here nothing is pushed and the caller reviews.

## What stays the same

Phases 0 through 3 run as the body defines them, with the investigation rigor unchanged: the causal-chain gate, reproduction, the escalation table, the test-first fix sequence in `references/fix.md`, and the issue-of-record rule. The **Branch/bookmark** rule in Phase 3 applies in full: on the default bookmark, detached, or unsure, create a feature bookmark named from the bug before the first edit and report it. `/lfg fix this bug` invoked on `main` must not advance `main`. The pre-fix scope record and the fix-owned file list are kept, because the return is built from them: the caller ships only what the user offered, and this return is the only place it can learn what was already in the tree or on the bookmark before the fix. Preserve the structured field names for callers: `branch` carries the feature bookmark, `head_sha` the immutable fix commit ID, and `pre_fix_scope.head` the captured pre-fix JJ commit ID; these are not instructions to use Git HEAD.

## What changes

- **Phase 0:** if an issue fetch fails, continue with the input you have and record the gap in the return. Never ask the user to paste content.
- **Phase 2 gate:** there is no fix-choice question. The caller's invocation authorized the fix, so proceed to Phase 3 with a **convergent** fix only. A **divergent** fix, one that would reverse a deliberate contract, behavior, or product decision, including a "failing" test that asserts intended behavior, is deferred as `needs-human` with a `decision_context`, never applied. Never route to `ce-brainstorm`; a design problem is a `needs-human` residual. When reproduction cannot run in this environment, continue on the best evidence in reach; if the causal chain still has a gap, return `needs-human` naming what reproduction requires and what was tried.
- **Phase 3:** apply the fix on the feature bookmark, verify it as `references/fix.md` defines (red then green where a test can run here; otherwise the reproduction check or characterization that file allows, recorded in the evidence), and commit only the fix-owned files using `(cd "$workspace_root" && jj commit <fix-owned-paths> -m "<message composed from the standards below>")`. Record the immutable resulting fix commit ID and advance only the feature bookmark to it; preserve all other work. Do not push. A file the fix must touch that already carries the user's uncommitted edits stops the run before the first edit to it: return `blocked` naming the file, with nothing applied, since no commit could separate their edits from the fix and the caller cannot answer for the user. A caller's statement that the user offered those edits does not change this. Edits the caller made itself for the work the user asked for, before invoking this skill, are not the user's. When they sit in a fix-owned file, commit that file with the fix and list it in `pre_fix_scope.caller_edits`; caller edits in other files stay untouched in `dirty_files`. The pre-fix scope record makes this known before Phase 3 edits anything.
- **Phase 4:** skip the Debug Summary block, the post-fix polish and review steps (`references/post-fix-handoff.md`), the commit/PR routing, and the learning-capture offer. Emit the structured return below as the last thing this skill writes. The return ends this skill, not the turn. The caller runs in this same session, and its next step follows the return.

### Message composition standards

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing, read the full Go guide and compare several recent full subjects AND bodies from the actual task's verified history head: `(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')`. Resolve that head from the actual task, including an empty `@` above it; do not assume a default remote bookmark or substitute this style sample for a reviewed base/head range. Determine repository prefixes, casing, tense, subject/body separation, wrapping and issue-reference placement. Repository-local instructions and observed syntax always win; apply compatible Go clarity/structure guidance within that pattern. Without history, use explicit project/user instructions and Go guidance, never invent precedent. Describe the actual bug fix and preserve required issue references without imposing fixed syntax.

The following verbatim Go excerpts are source guidance, not a mandatory repository template:

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,

```text
net/http: handle foo when bar

[longer description here in the body]

Fixes #12345
```

> Notably, for the subject (the first line of description):
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).

> For the body (the rest of the description):
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.

## Structured return

The return is machine-readable; the caller parses it and branches on the exact `status` spellings, so never rename, abbreviate, or add to them.

```json
{
  "status": "fixed | diagnosed-no-fix | needs-human | blocked",
  "summary": "<one line: what happened>",
  "root_cause": "<the causal chain, trigger to symptom, with file:line references>",
  "changed_files": ["<fix-owned files, tests included>"],
  "head_sha": "<sha of the fix commit, when fixed>",
  "branch": "<branch the fix was committed on, when fixed>",
  "prevention_signal": "<the proposed log field, metric, or assertion, or null>",
  "pre_fix_scope": {
    "head": "<HEAD before the fix commit>",
    "dirty_files": ["<files already modified or untracked before Phase 3 that are not fix-owned; left untouched>"],
    "caller_edits": ["<fix-owned files that already carried the calling session's own uncommitted edits, committed with the fix>"],
    "commits_beyond_base": ["<commits the branch carried beyond the default branch before the fix, oldest first; empty on a fresh branch>"],
    "started_on_default_branch": false
  },
  "behavior_change": true,
  "verification_evidence": {
    "regression_test": "<file and case, plus one line on what this seam catches and misses>",
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

`pre_fix_scope` is present on every return and records what the branch and tree carried before the fix, as observed facts: the pre-fix `HEAD`, the files that were already dirty and are not fix-owned (the fix never touched them), the fix-owned files that carried the calling session's own edits, and the commits beyond the default branch, pushed or not. It carries no verdict about what the user offered; the caller decides that, and this record is what it decides from. `issue_of_record` is `null` when the input carried no ticket. `verification_evidence` is present on every `fixed` return; when `behavior_change` is `false` (a pure test or tooling fix), `exception_reason` says why no red-then-green was possible. `prevention_signal` is present on every return. It carries the always-on signal proposal that SKILL.md's Phase 2 findings block describes, because this mode skips the handoff that would otherwise show it, and it is `null` when that block's condition does not hold. It is a proposal, not a residual, and it is not added to the fix. `residuals` is an empty array when there are none. Do not invent a residual type; a non-blocking follow-up goes in `summary`.
