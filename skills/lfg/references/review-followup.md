# Pre-ship quality steps (LFG steps 3–7)

### Quoted Go source guidance (not a mandatory repository template)

The following verbatim excerpts are from https://go.dev/wiki/CommitMessage. Repository-local syntax ALWAYS wins; the Go illustration does not prescribe message syntax here. Keep the runtime full-guide/history comparison below.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,
>
> ```text
> net/http: handle foo when bar
>
> [longer description here in the body]
>
> Fixes #12345
> ```
>
> Notably, for the subject (the first line of description):
>
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).
>
> For the body (the rest of the description):
>
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - we **do not** use `Signed-off-by` lines. Don’t add them. Our Gerrit server & GitHub bots enforce CLA compliance instead.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.
> - when referencing CLs, prefer saying “CL nnn” or using a go.dev/cl/nnn shortlink over a direct Gerrit URL or git hash, since that’s more future-proof.
> - when moving code between repos, include the CL, repository name, and git hash that it was moved from/to, so it is easier to trace history/blame.

These are the quality steps that run after implementation and before shipping. On the defect route the implementation was `ce-debug`'s fix; `references/debug-return.md` names what each step below receives in place of the plan path. `ce-code-review` is review-only. LFG applies eligible fixes itself, then commits.

## The shipping precondition, in these steps

When the repo has no remote, the run finishes locally. That is a final state, not an error: never retry a push or hunt for a remote. Step 5 still makes every commit it calls for; only the pushes and the records that would live on the PR are dropped. With no PR to hold the unapplied findings, step 6 files them as tracker tickets and the DONE report states the rest. Never write them to a committed file nobody will read.

## Step 3 — simplify before review

Simplification runs before review so the code-review in step 4 covers the simplified code. Let `ce-simplify-code` resolve the branch-diff scope itself; it preserves behavior and runs the test suite. Pass the plan path from step 1 as context about structure the simplification must keep, not as the simplification scope (the branch diff remains the scope); on the defect route pass the debug return's `root_cause` and `changed_files` instead, so the fix is not simplified away. On either route, pass each test `verification_evidence` names as proving the work (the regression or red-before-fix test, characterization coverage, or an existing test used unchanged) as its own `proof-test:<path>`, so the simplification leaves those tests untouched. Add a one-line constraint: KTDs labeled `session-settled:` describe structure the simplification must preserve, so deliberate duplication stays duplicated.

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
4. Inspect `jj status` and `jj diff` from the absolute target workspace cwd. If eligible fixes were applied, capture only the review-driven paths/hunks in a separate JJ change; never include unrelated implementation or pre-existing edits. Follow the message standards below, then use `jj describe -m "<message composed from the standards above>"` on that verified change. Then push before step 6 **when a remote is configured** (per LFG's shipping precondition) and, on the defect route, only when everything published is offered work (`references/debug-return.md`). Verify the intended PR/source bookmark and its exact revision; advance only that bookmark to the completed change and run `jj git push --remote <verified-writable-remote> --bookmark <verified-bookmark>` (add `--allow-new` only for an authorized new bookmark). Choose the existing tracked remote, otherwise prefer writable `origin`, otherwise verify a configured writable remote from `jj git remote list`; do not rename bookmarks or publish other work. With no remote the local change suffices. If no eligible fixes were applied, say so explicitly and skip the commit.

### Commit-message standards (also applies to local-only shipping)

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards.

Read the full guide before composing. In the absolute target workspace cwd, verify the history head belongs to this task, then inspect several recent full subjects **and bodies**, for example `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\\n"'`. Repository-local syntax always wins: compare prefixes/packages, casing, tense, subject/body separation, wrapping, and issue references. With no history, follow explicit instructions and compatible Go guidance without inventing precedent. Do not impose a fixed template or conventional prefix. Resulting messages contain no Markdown, Co-authored-by, or Assisted-by trailers; compatible local rules win. Preserve the semantic explanation of the review fix.

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
