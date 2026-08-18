# Review followup (LFG step 4–5)

`ce-code-review` is review-only. LFG applies eligible fixes itself, then describes and ships the resulting Jujutsu change.

## Step 4 — invoke review

```
ce-code-review mode:agent plan:<plan-path-from-step-1>
```

Read the **Actionable Findings** summary and artifact path. Do not pass `mode:autofix`.

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
4. If `jj status` shows review-driven changes, isolate only those edits in the review-fix revision with Jujutsu's revision-editing operations, using `jj split` or `jj squash` as the current revision graph requires, and compose its description from the project's active instructions and current history. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime project instructions and the history visible through `jj log` win; use a neutral description derived from the applied findings, with no fixed syntax, message, or template. Finalize it with `jj describe`, start a new empty change with `jj new`, and push before step 6 **when a remote is configured** (per LFG's shipping precondition). Resolve the relevant bookmark and writable remote dynamically from `jj bookmark list` and `jj git remote list`, creating or advancing the bookmark to the described revision when needed, then use `jj git push --bookmark <bookmark> --remote <remote>`. Preserve any required GitHub interoperability through `gh`. If there is no remote, do not push; the locally described revision suffices. If no eligible fixes were applied, note explicitly and skip describing or pushing a review-fix revision.

## Step 6 — residual handoff

Residuals are actionable findings **not** applied in step 5 — not leftovers from in-skill autofix. Use the Actionable Findings summary / artifact from step 4.
