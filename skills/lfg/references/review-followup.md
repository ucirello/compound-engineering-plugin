# Review followup (LFG step 4–5)

`ce-code-review` is review-only. LFG applies eligible fixes itself, then records an isolated JJ change.

At every description, edit, and validation site in this reference, apply this exact rule: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active runtime instructions and current `jj log` syntax win over general guidance. Use `jj describe` locally and `jj git` for publication; never impose a fixed type, scope, prefix, message, template, or example.

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
2. When at least one fix is eligible, run `jj new` before editing so review-driven edits occupy their own working-copy change and prior implementation remains at `@-`.
3. Apply eligible fixes in the JJ working copy in severity order (`#` stable from the review).
4. Run targeted tests when `requires_verification: true` on any applied finding.
5. Use `jj status` and `jj diff --summary` to verify that only review-driven files changed. If the new change is non-empty, apply the reference-wide description policy and describe the isolated change with `jj describe`. Set LFG's retained shipping bookmark to `@` with `jj bookmark set <bookmark> -r @`, then run `jj new` so the described review change is `@-`. Before step 6, publish that exact bookmark with `jj git push --remote <remote> --bookmark <bookmark>` **when a remote is configured** (per LFG's shipping precondition), choosing the writable remote from `jj git remote list`: prefer `origin` when present, otherwise the first configured remote. If there is no remote, do not publish; the local described change suffices. If no eligible fixes were applied, note that explicitly and skip change creation, description, and publication.

## Step 6 — residual handoff

Residuals are actionable findings **not** applied in step 5 — not leftovers from in-skill autofix. Use the Actionable Findings summary / artifact from step 4.
