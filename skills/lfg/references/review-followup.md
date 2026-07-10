# Review followup (LFG step 4–5)

`ce-code-review` is review-only. LFG applies eligible fixes itself, then commits the selected fileset as a JJ change.

## Step 4 — invoke review

```
ce-code-review mode:agent plan:<plan-path-from-step-1>
```

Read the **Actionable Findings** summary and artifact path. Do not pass `mode:autofix`.

Capture parsed JSON (`status`, `actionable_findings`, `findings`, `artifact_path`, `run_id`) or the markdown Actionable Findings section. If `status` is `failed`, stop and surface `reason`.

## Step 5 — apply and persist review fixes

### What to apply

Apply a finding in the current JJ working-copy change only when **all** of the following hold:

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
2. Apply eligible fixes in the current working-copy change in severity order (`#` stable from the review).
3. Run targeted tests when `requires_verification: true` on any applied finding.
4. If `jj status` shows review-driven changes, inspect the exact fileset with `jj diff --summary`, commit only those files with `jj commit <files> -m "fix(review): apply review findings"`, run `jj bookmark set "$FEATURE_BOOKMARK" -r @-`, and push before step 6 **when a remote is configured** (per LFG's shipping precondition) using `jj git push --bookmark "$FEATURE_BOOKMARK" --remote "$SHIPPING_REMOTE"`. JJ has no staging area, and `jj commit <files>` moves unselected edits into the new working-copy change. If there is no remote at all, do not push — the local committed change suffices. If no eligible fixes were applied, note explicitly and skip `jj commit`.

## Step 6 — residual handoff

Residuals are actionable findings **not** applied in step 5 — not leftovers from in-skill autofix. Use the Actionable Findings summary / artifact from step 4.
