# Pre-ship quality steps (LFG steps 3–7)

These are the quality steps that run after implementation and before shipping. On the defect route the implementation was `ce-debug`'s fix; `references/debug-return.md` names what each step below receives in place of the plan path. `ce-code-review` is review-only. LFG applies eligible fixes itself, then commits.

## The shipping precondition, in these steps

When the repo has no remote, the run finishes locally. That is a final state, not an error: never retry a push or hunt for a remote. Step 5 still makes every commit it calls for; only the pushes and the records that would live on the PR are dropped. With no PR to hold the unapplied findings, step 6 files them as tracker tickets and the DONE report states the rest. Never write them to a committed file nobody will read.

## Step 3 — simplify before review

Simplification runs before review so the code-review in step 4 covers the simplified code. Let `ce-simplify-code` resolve the branch-diff scope itself; it preserves behavior and runs the test suite. Pass the plan path from step 1 as context about structure the simplification must keep, not as the simplification scope (the branch diff remains the scope); on the defect route pass the debug return's `root_cause` and `changed_files` instead, so the fix is not simplified away. Add a one-line constraint: KTDs labeled `session-settled:` describe structure the simplification must preserve, so deliberate duplication stays duplicated.

Do not commit in this step. `ce-simplify-code` leaves its changes in the working tree; step 4's review scopes the working tree (uncommitted changes included), and step 9's `ce-commit-push-pr` commits whatever remains. Committing here would sweep any still-uncommitted `ce-work` edits into a misleading `refactor` commit and could stall on a tree that never goes clean.

## Step 4 — invoke `ce-code-review`

Load `ce-code-review` from the host catalog's listed path. A host skill named `review` is not this step; do not invent `skills/review/SKILL.md` under this plugin.

```
ce-code-review mode:agent plan:<plan-path-from-step-1>
```

Read the **Actionable Findings** summary and artifact path. Do not pass `mode:autofix`.

Pass the plan file path from step 1 so `ce-code-review` can verify requirements completeness. On the defect route there is no plan: omit `plan:` and pass the `root_cause` summary as review context; the requirements check is additive by `ce-code-review`'s own contract and review still covers the diff. Also read any findings stamped `settled_conflict` (each names the conflicting KTD). Stamped findings that are matters of preference do not stop the pipeline (they are report-only), but they must reach step 6's record of unapplied findings.

`mode:agent` is report-only **by design**: it reports findings but never edits the tree, and LFG applies the eligible ones in step 5. When narrating progress to the user, frame this as "review found X -> applied X in step 5," not as "code review did not auto-fix." A report-only review followed by an LFG-applied fix is the intended contract, not a gap.

Capture parsed JSON (`status`, `actionable_findings`, `findings`, `artifact_path`, `run_id`) or the markdown Actionable Findings section. If `status` is `failed`, stop and report `reason`.

## Step 5 — apply and persist review fixes

### What to apply

Apply a finding in the working tree only when **all** of the following hold:

1. **`suggested_fix` is present** — concrete change shape from the reviewer.
2. **`confidence` is `100`, or `75` with cross-persona agreement noted in the report** — do not apply anchor-50 findings.
3. **The fix is mechanical** — one coherent change; no change to a contract, permission, or security stance; no new public API shape; no behavior change that needs product sign-off.
4. **Evidence still matches the code** at the cited `file:line` before editing.

Do not treat `autofix_class` as permission to auto-apply.

### What not to apply

- `autofix_class: manual` without a clear mechanical `suggested_fix`
- `autofix_class: advisory` — report-only
- `gated_auto` findings that change behavior, contracts, auth, or permissions
- Anything that needs a design conversation

### Execution

1. Filter `actionable_findings` (or markdown Actionable Findings) with the bar above.
2. Apply eligible fixes in the working tree in severity order (`#` stable from the review).
3. Run targeted tests when `requires_verification: true` on any applied finding.
   If review-owned files also contain unrelated pre-existing or implementation hunks, use JJ's interactive selection to isolate the review fixes or stop safely; a path list alone does not separate shared-file hunks.
4. Inspect `(cd "$workspace_root" && jj status)` and `(cd "$workspace_root" && jj diff --summary)`. If eligible fixes changed files, persist only the review-driven paths with `(cd "$workspace_root" && jj commit -m "<message composed from the standards below>" -- <review-driven-paths>)`; unrelated changes remain in the working copy. The message describes the review fixes, not unrelated implementation work. Then push before step 6 **when a remote is configured** (per LFG's shipping precondition) and, on the defect route, when everything the push would publish is work the user offered (`references/debug-return.md`). Resolve the exact source bookmark and authorized writable remote from the PR and tracked remote-bookmark state. Prefer `origin` when creating a new route; otherwise inspect `(cd "$workspace_root" && jj git remote list)` and verify the selected remote's authority. Move only the verified source bookmark to the intended completed head with `(cd "$workspace_root" && jj bookmark set "<bookmark>" -r "<verified-head>")`, then `(cd "$workspace_root" && jj git push --remote "<remote>" --bookmark "<bookmark>")`; use `--allow-new` only for an authorized new remote bookmark. Never guess a bookmark from an empty `@`. If no remote exists, the local commit suffices. If no eligible fixes were applied, say so explicitly and skip the commit.

**Message standards for step 5:** Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Before composing, read the full Go guide and compare several recent subjects AND bodies with `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)`. Establish actual prefix/package, case, tense, subject/body separation, wrapping, and issue placement. Repository instructions and observed history always win differing syntax; apply compatible Go quality guidance. Without history, use explicit project/user instructions and Go guidance without inventing precedent.

**Review dispatch gate:** This skill explicitly requests the reviewers required by `ce-code-review`. Under a user-or-loaded-skill delegation rule, that satisfies delegation permission without a second ask. Actual prohibitions, missing tools, and denials remain binding. Model override permission is separate: configuration tiers alone do not authorize an optional model argument when the host requires explicit user model selection; suitable inherited-model reviewers may run, with unmet routes disclosed. Inspect runtime configuration discovery and its precedence for effective `experimental.subagent_depth`, then verify remaining capacity through actual native dispatch outcomes; bundled defaults alone do not prove capacity. Distinguish depth/capacity, permission, model-argument rejection, and missing-tool failures. Never bypass them through shell or another harness. Contract-permitted inline/parent fallback must preserve coverage and independence; separate same-model reviewers are not cross-model independence, and an unmet required different-model pass is incomplete coverage, not a completed review.

## Step 6 — residual handoff

Residuals are the findings left over: actionable findings **not** applied in step 5. They are not leftovers from an autofix inside `ce-code-review`. Use the Actionable Findings summary / artifact from step 4.

Two further triggers also require step 6, both outside the apply path: step 4 emitted any `settled_conflict`-stamped findings, or step 2's return carried proceeded-and-flagged `settled_decision_conflicts` entries. These are the findings where the work diverged from a settled decision, and this step is where they get written down somewhere that lasts.

A residual at this point is undecided, not accepted debt. Step 5 declined it because it needs judgment, and the pipeline does not merge unless the user granted it, so the human reviewing the PR supplies that judgment: fix it in this branch, dismiss it, or file it to carry past merge. The record therefore goes where that reviewer already looks, the PR body. The pipeline files no tickets for these; one ticket per finding, decided by nobody, is how a run of small nits floods a tracker.

**When a PR will exist (a remote is configured):** compose a `## Unapplied review findings` section, one checkbox bullet per item so a human ticks it when they close it:

- For each unapplied actionable finding: `- [ ] <severity> — <file:line> — <title>`, plus the reviewer's `suggested_fix` on the next line when present.
- For each `settled_conflict`-stamped finding from step 4: the same bullet plus the conflicting KTD the stamp names — included even though the finding is report-only.
- For each proceeded-and-flagged `settled_decision_conflicts` entry from step 2: a bullet with the KTD, the evidence, and how it was routed.

Close the section with the review run context (`run_id`, `artifact_path`). Hand the section to step 9 as PR-description context; `references/shipping.md` says where step 9 passes it into `ce-commit-push-pr`. Step 9 writes the body, so nothing here edits the PR directly, and nothing posts a PR comment for these.

**When no PR will exist (no remote):** load `references/tracker-defer.md` in **non-interactive mode** with the same items, collect `{ filed: [...], failed: [...], no_sink: [...] }`, and state every `failed` and `no_sink` item verbatim in the DONE report. The report is the only record those get.

## Step 7 — compound before shipping

Invoke `ce-compound` with `mode:non-interactive` when the run produced durable reasoning that the final code, tests, and plan or diagnosis do not carry, and losing it would plausibly cause recurrence or substantial rediscovery. The plan or `root_cause`, the review residuals, and the fixes applied in step 5 are the evidence for that judgment. `ce-compound` writes into the repository's tracked learnings store on the branch and asks nothing; `Documentation skipped` is a successful outcome, not a stop. Step 9 commits and pushes whatever it wrote with the rest of the change, so the learning is in the PR at the moment it opens and CI runs against a head that contains it. Do not run it after the babysit result: a push after "CI decided" leaves an unwatched head.
