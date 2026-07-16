# Review followup (steps 4-5)

`ce-code-review` is review-only. The calling pipeline applies eligible fixes, then creates a JJ commit.

## Step 4 — invoke review

```
ce-code-review mode:agent plan:<plan-path-from-step-1>
```

Read the **Actionable Findings** summary and artifact path. Do not pass `mode:autofix`.

Capture parsed JSON (`status`, `actionable_findings`, `findings`, `artifact_path`, `run_id`) or the markdown Actionable Findings section. If `status` is `failed`, stop and surface `reason`.

## Step 5 — apply and persist review fixes

### What to apply

Apply a finding in the JJ working-copy change only when **all** of the following hold:

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
2. Apply eligible fixes in the JJ working-copy change in severity order (`#` stable from the review).
3. Run targeted tests when `requires_verification: true` on any applied finding.
4. Use `jj diff --name-only` and the review-driven fileset to determine whether eligible fixes changed files. If so, commit only those files with `jj commit <review-driven-fileset> -m <message>`. At this composition site, apply this guidance: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions take precedence over the syntax established by `git log`, and both take precedence over compatible Go guidance. Do not impose fixed message syntax or examples, and retain the semantic constraint that the message describes applying review findings without decorative markers or identity metadata. When a remote is configured per the calling pipeline's shipping precondition, create or move the shipping bookmark at `@-` as specified there and run `jj git push --remote <remote> --bookmark <shipping-bookmark>` before step 6. With no remote, the local JJ commit suffices. If no eligible fixes were applied, note that explicitly and skip the commit.

## Step 6 — residual handoff

Residuals are actionable findings **not** applied in step 5 — not leftovers from in-skill autofix. Use the Actionable Findings summary / artifact from step 4.
