# Review followup (LFG step 4–5)

`ce-code-review` is review-only. The pipeline applies eligible fixes itself, then persists them as a described change.

## Step 4 — invoke review

```
ce-code-review mode:agent plan:<plan-path-from-step-1>
```

Read the **Actionable Findings** summary and artifact path. Do not pass `mode:autofix`.

Capture parsed JSON (`status`, `actionable_findings`, `findings`, `artifact_path`, `run_id`) or the markdown Actionable Findings section. If `status` is `failed`, stop and surface `reason`.

## Step 5 — apply and persist review fixes

### What to apply

Apply a finding in the workspace only when **all** of the following hold:

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
2. Apply eligible fixes in the workspace in severity order (`#` stable from the review).
3. Run targeted tests when `requires_verification: true` on any applied finding.
4. If `jj status` shows review-driven changes, isolate only the exact review-driven paths into their own change with `jj split` and record the resulting composed revision. The project's active local instructions and repository history always win. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Set the resulting change description without imposing fixed message syntax. Push that exact revision before step 6 **when a remote is configured** (per the shipping precondition). Resolve one writable remote from the delivery bookmark's tracked remote or repository identity; do not choose a remote by list order. When a delivery bookmark exists, move it explicitly with `jj bookmark set --allow-backwards <delivery-bookmark> -r <composed-revision>` and run `jj git push --remote <remote> --bookmark <delivery-bookmark>`. Otherwise run `jj git push --remote <remote> --change <composed-revision>` so only the composed revision receives a generated tracked bookmark. If no remote can be resolved, do not push — the locally described change suffices. If no eligible fixes were applied, note explicitly and do not split or describe a change.

## Step 6 — residual handoff

Residuals are actionable findings **not** applied in step 5 — not leftovers from in-skill autofix. Use the Actionable Findings summary / artifact from step 4.
