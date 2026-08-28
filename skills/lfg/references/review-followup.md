# Pre-ship quality tail (LFG steps 3–6)

`ce-code-review` is review-only. LFG applies eligible fixes and finishes them as focused Jujutsu changes.

## The shipping precondition, in these steps

A missing remote is a terminal local-only state, not an error. Steps 5 and 6 still finish their local changes; pushes and PR-side records drop. With no PR, state residuals in the DONE report rather than creating a tracked report file.

## Step 3 — simplify before review

Simplification runs before review so step 4 covers the simplified code. Let `ce-simplify-code` resolve the active Jujutsu stack diff. Pass the plan path as structure-pin context, with the constraint that `session-settled:` KTDs remain structure pins.

Do not describe or advance the working-copy change in this step. Step 4 reviews the full active diff, and step 5 separates review fixes before step 8 finalizes anything remaining.

## Step 4 — invoke `ce-code-review`

Load `ce-code-review` from the host catalog's listed path. A host skill named `review` is not this step; do not invent `skills/review/SKILL.md` under this plugin.

```
ce-code-review mode:agent plan:<plan-path-from-step-1>
```

Read the **Actionable Findings** summary and artifact path. Do not pass `mode:autofix`.

Pass the plan file path from step 1 so `ce-code-review` can verify requirements completeness. Also read any findings stamped `settled_conflict` (each names the conflicting KTD). Stamped preference-grade findings proceed (they are report-only) but must flow into step 6's residual record.

`mode:agent` is report-only **by design** — it surfaces findings but never edits the tree; LFG applies the eligible ones in step 5. When narrating progress to the user, frame this as "review found X -> applied X in step 5," not as "code review did not auto-fix." A report-only review followed by an LFG-applied fix is the intended contract, not a gap.

Capture parsed JSON (`status`, `actionable_findings`, `findings`, `artifact_path`, `run_id`) or the markdown Actionable Findings section. If `status` is `failed`, stop and surface `reason`.

## Step 5 — apply and persist review fixes

### What to apply

Apply a finding in the working copy only when **all** of the following hold:

1. **`suggested_fix` is present** — concrete change shape from the reviewer.
2. **`confidence` is `100`, or `75` with cross-persona agreement noted in the report** — do not apply anchor-50 findings.
3. **The fix is mechanical** — one coherent change, no contract/permission/security posture change, no new public API shape, no behavior change that needs product sign-off.
4. **Evidence still matches the code** at the cited `file:line` before editing.

Do not treat `autofix_class` as permission to auto-apply.

### What not to apply

- `autofix_class: manual` without a clear mechanical `suggested_fix`
- `autofix_class: advisory` — report-only
- `gated_auto` findings that change behavior, contracts, auth, or permissions
- Anything that needs a design conversation

### Execution

1. Filter `actionable_findings` (or markdown Actionable Findings) with the bar above.
2. Apply eligible fixes in the working copy in severity order (`#` stable from the review).
3. Run targeted tests when `requires_verification: true` on any applied finding.
4. If `jj diff -r @ --name-only` shows review-driven changes, separate only that fileset with `jj split` when it is mixed with other work, describe the completed review change, and start a new empty change with `jj new`. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Local conventions and visible history win. When a remote and stable bookmark are already configured, push that bookmark with `jj git push --remote <remote> --bookmark <bookmark>` before step 6. Do not invent a bookmark merely for this intermediate push; the final shipping step owns bookmark creation. If no eligible fixes were applied, note that and leave the revision structure unchanged.

## Step 6 — residual handoff

Residuals are actionable findings **not** applied in step 5 — not leftovers from in-skill autofix. Use the Actionable Findings summary / artifact from step 4.

Two further triggers also require step 6, both outside the apply path: step 4 emitted any `settled_conflict`-stamped findings, or step 2's return carried proceeded-and-flagged `settled_decision_conflicts` entries. They are the divergent class and must be made durable here.

1. Load `references/tracker-defer.md` in **non-interactive mode**. Pass the residual actionable findings from step 4/5 (or the run artifact when the summary was truncated).
2. Collect the structured return: `{ filed: [...], failed: [...], no_sink: [...] }`.
3. Compose a `## Residual Review Findings` markdown section from the structured return (this goes into the run-report PR comment, **not** the PR body):
   - For each item in `filed`: a bullet with severity, file:line, title, and a link to the tracker ticket URL.
   - For each item in `failed`: a bullet with severity, file:line, title, and the failure reason (e.g., `Defer failed: gh returned 401 — tracker unavailable`).
   - For each item in `no_sink`: a bullet with severity, file:line, and title inlined verbatim, since the comment is the only record these get.
   - For each `settled_conflict`-stamped finding from step 4: a bullet with severity, file:line, title, and the conflicting KTD the stamp names — included even though the finding is report-only.
   - For each proceeded-and-flagged `settled_decision_conflicts` entry from step 2: a bullet with the KTD, the evidence, and how it was routed.
4. Never write the `## Residual Review Findings` section into the PR description: it duplicates GitHub's own tracking and goes stale as items resolve. Review residuals have no GitHub thread of their own, so they are made durable by the tracker tickets filed above plus **one run-report comment on the PR** carrying the composed section (ticket links included) and the source run context — the same surface `ce-babysit-pr` already uses for unfixable CI. Post it with `GIT_DIR="$(jj git root)" gh pr comment`; a point-in-time comment does not go stale as items resolve, the way a body section or a committed file does.

When no PR exists because no remote is configured, the run output is the record: state residuals in the DONE report rather than creating a tracked file nobody will read.
