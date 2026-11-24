# Pre-ship quality steps (LFG steps 3–7)

These are the quality steps that run after implementation and before shipping. On the defect route the implementation was `ce-debug`'s fix; `references/debug-return.md` names what each step below receives in place of the plan path. `ce-code-review` is review-only. LFG applies eligible fixes itself, then commits.

## The shipping precondition, in these steps

When the repo has no remote, the run finishes locally. That is a final state, not an error: never retry a push or hunt for a remote. Step 5 still makes every commit it calls for; only the pushes and the records that would live on the PR are dropped. With no PR to hold the unapplied findings, step 6 files them as tracker tickets and the DONE report states the rest. Never write them to a committed file nobody will read.

## Step 3 — simplify before review

Simplification runs before review so the code-review in step 4 covers the simplified code. It reviews code only. Code is source in a programming language that a compiler, interpreter, or shell runs, and the tests written in one. Prose is not code in any format, including markdown that agents read, such as skills, prompts, and agent instructions. Neither are documentation, plans, data, or configuration. A change with none of that code is docs-only for step 3's skip, however large it is.

When `ce-work`'s return carries `simplified_through: <sha>`, its own pass already covered everything up to that commit, so pass only the changes after it as the scope (`jj diff --from <sha> --to @`, run from the target workspace's absolute root after verifying the returned revision; this includes current working-copy changes). Otherwise let `ce-simplify-code` resolve the branch-diff scope itself. Either way it preserves behavior and runs the test suite, and the sub-10-line skip applies to that scope. Pass the `size-cutoff:` token step 3 names unchanged; `ce-simplify-code` measures the scope and picks single-pass or the full team. Pass the plan path from step 1 as context about structure the simplification must keep, not as the simplification scope; on the defect route pass the debug return's `root_cause` and `changed_files` instead, so the fix is not simplified away. On either route, pass each test `verification_evidence` names as proving the work (the regression or red-before-fix test, characterization coverage, or an existing test used unchanged) as its own `proof-test:<path>`, so the simplification leaves those tests untouched. Add a one-line constraint: KTDs labeled `session-settled:` describe structure the simplification must preserve, so deliberate duplication stays duplicated.

Do not commit in this step. `ce-simplify-code` leaves its changes in the working tree; step 4's review scopes the working tree (uncommitted changes included), and step 9's `ce-commit-push-pr` commits the remaining run-owned changes. Committing here could sweep unrelated edits into the simplification change.

## Step 4 — invoke `ce-code-review`

Load `ce-code-review` from the host catalog's listed path. A host skill named `review` is not this step; do not invent `skills/review/SKILL.md` under this plugin.

```
ce-code-review mode:agent plan:<plan-path-from-step-1>
```

Read the **Actionable Findings** summary and artifact path. Do not pass `mode:autofix`.

Pass the plan file path from step 1 so `ce-code-review` can verify requirements completeness. On a one-pass statement there is no plan: omit `plan:` and pass the statement as review context. On the defect route there is no plan: omit `plan:` and pass the `root_cause` summary as review context; the requirements check is additive by `ce-code-review`'s own contract and review still covers the diff. Also read any findings stamped `settled_conflict` (each names the conflicting KTD). Stamped findings that are matters of preference do not stop the pipeline (they are report-only), but they must reach step 6's record of unapplied findings.

`mode:agent` is report-only **by design**: it reports findings but never edits the tree, and LFG applies the eligible ones in step 5. When narrating progress to the user, frame this as "review found X -> applied X in step 5," not as "code review did not auto-fix." A report-only review followed by an LFG-applied fix is the intended contract, not a gap.

When the host permits delegation explicitly requested by the user **or** an applicable loaded skill, `ce-code-review`'s explicit reviewer dispatch instructions count: no second approval is needed. An unconditional prohibition or actual denial still applies. Use OpenCode-native dispatch; model override permission is separate, so omit the optional `model` argument when overrides are forbidden and use a suitable inherited model if it meets the review contract. A separate reviewer on the same model does not meet a different-model requirement. Verify effective OpenCode nesting depth and available capacity separately; classify dispatch failures from the actual error (depth/capacity, permission, model rejection, or missing tool). Do not retry a denial or use shell or another harness to bypass it. Use inline or parent-coordinator fallback only when the owning review contract permits it and its independence and coverage can still be met.

Capture parsed JSON (`status`, `actionable_findings`, `findings`, `artifact_path`, `run_id`) or the markdown Actionable Findings section, plus the review's coverage and dispatch diagnostics for its captured base/head. Do not substitute step 3's simplification scope for that range. If `status` is `failed`, stop and report `reason`. If any required pass remains incomplete, including a fixed or cross-model route, stop at step 4 as blocked, reporting completed and missing coverage and why; a partial findings list is not a complete review.

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
4. From the target workspace's absolute root, use `jj status` and `jj diff` to verify the applied fixes. Commit only the review-driven changes with `jj commit -m "<message composed from the standards below>" -- <review-owned-paths>`. If a path also contains unrelated work, select only the owned hunks with `jj commit --interactive` and verify the split; if they cannot be separated safely, stop rather than including unrelated work. If no eligible fixes were applied, say so and skip the commit and early push.
5. Push the verified committed head before step 6 when a remote is configured and publication is authorized. Use the intended bookmark's existing tracked remote if verified writable; otherwise choose a verified writable configured remote, preferring `origin` when it is the intended target. Resolve the exact commit and verify everything the push would publish is offered, especially on the defect route (`references/debug-return.md`). Verify an existing remote target is an ancestor of the publishing commit. Fast-forward only the verified publishing bookmark with `jj bookmark move "exact:<bookmark>" --to <verified-commit>` or create that bookmark with `jj bookmark create <bookmark> -r <verified-commit>` if absent. Inspect `jj git push --dry-run --remote "exact:<verified-remote>" --bookmark "exact:<bookmark>"` from the target workspace's absolute root; only then use the same scoped push without `--dry-run`. Do not publish the residual working copy, guess the target, or force-push. No remote or a defect-route publication hold leaves the fix local; ambiguous targets, conflicts, denial, or unknown push authority take the existing safe stop path.

### Commit-message standards for LFG-owned commits

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Before composing any LFG-owned message, read the full Go guide and, from the target workspace's absolute root, compare several complete subjects and bodies from the task's verified history head (for example, `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`). Identify the repository's prefixes, casing, tense, subject/body separation, wrapping, and issue references. Local syntax from project instructions and actual history always wins; apply compatible Go advice to clarity and structure. If no history exists, use explicit project/user instructions and compatible Go guidance without inventing precedent. Describe what the selected changes do and why; for the review-fix commit describe the findings applied.

Go Wiki source guidance (illustrative, not a repository template):

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

## Step 6 — residual handoff

Residuals are the findings left over: actionable findings **not** applied in step 5. They are not leftovers from an autofix inside `ce-code-review`. Use the Actionable Findings summary / artifact from step 4.

Two further triggers also require step 6, both outside the apply path: step 4 emitted any `settled_conflict`-stamped findings, or step 2's return carried proceeded-and-flagged `settled_decision_conflicts` entries. These are the findings where the work diverged from a settled decision, and this step is where they get written down somewhere that lasts.

A residual at this point is undecided, not accepted debt. Step 5 declined it because it needs judgment, and the pipeline does not merge unless the user granted it, so the human reviewing the PR supplies that judgment: fix it in this branch, dismiss it, or file it to carry past merge. The record therefore goes where that reviewer already looks, the PR body. The pipeline files no tickets for these; one ticket per finding, decided by nobody, is how a run of small nits floods a tracker.

**When a PR will exist (publication is available and authorized):** compose a `## Unapplied review findings` section, one checkbox bullet per item so a human ticks it when they close it:

- For each unapplied actionable finding: `- [ ] <severity> — <file:line> — <title>`, plus the reviewer's `suggested_fix` on the next line when present.
- For each `settled_conflict`-stamped finding from step 4: the same bullet plus the conflicting KTD the stamp names — included even though the finding is report-only.
- For each proceeded-and-flagged `settled_decision_conflicts` entry from step 2: a bullet with the KTD, the evidence, and how it was routed.

Close the section with the review run context (`run_id`, `artifact_path`). Hand the section to step 9 as PR-description context; `references/shipping.md` says where step 9 passes it into `ce-commit-push-pr`. Step 9 writes the body, so nothing here edits the PR directly, and nothing posts a PR comment for these.

**When no PR will exist (no remote or a defect-route publication hold):** load `references/tracker-defer.md` in **non-interactive mode** with the same items, collect `{ filed: [...], failed: [...], no_sink: [...] }`, and state every `failed` and `no_sink` item verbatim in the DONE report. The report is the only record those get. A publication hold does not authorize disclosing withheld work to a tracker; keep those items in the report.

## Step 7 — compound before shipping

Invoke `ce-compound` with `mode:non-interactive` when the run corrected a wrong belief about how something behaves: the plan's approach failed, a review finding exposed a real defect, a diagnosis disproved its first hypothesis, or an assumption or document turned out wrong. A naming, style, or preference fix does not count, and a run that went as first planned skips this step. Do not judge whether the lesson deserves a document: `ce-compound` decides whether it qualifies and what holds it (a test or lint rule, a coding standard, or a learning on the branch). It asks no questions. Pass the plan or `root_cause`, the review residuals, and the fixes applied in step 5 as its context. `Documentation skipped` is a successful outcome, not a stop. Step 9 commits and pushes whatever it wrote with the rest of the change, so the lesson is in the PR at the moment it opens and CI runs against a head that contains it. Pass any `Recommended form` other than `none` to step 9 as PR-description context, so a form that needs product code stays visible. Do not run it after the babysit result: a push after "CI decided" leaves an unwatched head.
