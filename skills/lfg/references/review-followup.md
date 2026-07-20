# Review followup (LFG step 4–5)

`ce-code-review` is review-only. LFG applies eligible fixes itself, then records them as a described JJ change.

## Step 4 — invoke review

```
ce-code-review mode:agent plan:<plan-path-from-step-1>
```

Read the **Actionable Findings** summary and artifact path. Do not pass `mode:autofix`.

Capture parsed JSON (`status`, `actionable_findings`, `findings`, `artifact_path`, `run_id`) or the markdown Actionable Findings section. If `status` is `failed`, stop and surface `reason`.

## Step 5 — apply and persist review fixes

### What to apply

Apply a finding in the JJ working copy only when **all** of the following hold:

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
2. Apply eligible fixes in the JJ working copy in severity order (`#` stable from the review).
3. Run targeted tests when `requires_verification: true` on any applied finding.
4. If `jj status` shows review-driven changes, put only those paths in a dedicated change: use `jj split <review-driven-files>` when the working-copy change also contains unrelated edits, otherwise use the current change. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local instructions and syntax observed in `git log` take precedence; use Go guidance only when compatible. Apply the locally derived description with `jj describe -r <review-fix-change-revset> -m <locally-derived-description>`. Before step 6, set the shipping bookmark to that change with `jj bookmark set <bookmark> -r <review-fix-change-revset>` and, **when a remote is configured** per LFG's shipping precondition, push with `jj git push --remote <remote> --bookmark <bookmark>`; add `--allow-new` only when the selected bookmark is new. If there is no remote, the locally described change suffices. If no eligible fixes were applied, note that explicitly and do not create or describe a change.

## Step 6 — residual handoff

Residuals are actionable findings **not** applied in step 5 — not leftovers from in-skill autofix. Use the Actionable Findings summary / artifact from step 4.
