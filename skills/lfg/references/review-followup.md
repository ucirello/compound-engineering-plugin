# Review followup (LFG step 4–5)

`ce-code-review` is review-only. LFG applies eligible fixes itself, then finalizes a JJ change.

## Step 4 — invoke review

```
ce-code-review mode:agent plan:<plan-path-from-step-1>
```

Read the **Actionable Findings** summary and artifact path. Do not pass `mode:autofix`.

Capture parsed JSON (`status`, `actionable_findings`, `findings`, `artifact_path`, `run_id`) or the markdown Actionable Findings section. If `status` is `failed`, stop and surface `reason`.

## Step 5 — apply and persist review fixes

### What to apply

Apply a finding in the working-copy commit only when **all** of the following hold:

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
2. Apply eligible fixes in the working-copy commit in severity order (`#` stable from the review).
3. Run targeted tests when `requires_verification: true` on any applied finding.
4. If `jj status` shows review-driven changes, finalize only those files with `jj commit <review-driven-files> -m "$message"`. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and conventions already in context take precedence, followed by recent history inspected with the repository's preferred `git log` syntax. Apply Go guidance only where compatible, using its quality principles for clear imperative phrasing, concision, rationale when useful, and readable wrapping. Treat the applied review findings as composition context. Derive all wording and structure at runtime; do not impose a fixed message, prefix, type, scope, subject, body, template, or example. Push before step 6 **when a remote is configured** (per LFG's shipping precondition), using the writable remote resolved there. If the current stack has a feature bookmark, advance that bookmark to `@-` with `jj bookmark advance <bookmark> --to @-` and run `jj git push --bookmark <bookmark> --remote <remote>`; otherwise run `jj git push --change @- --remote <remote>` and record the generated tracked bookmark for the remaining shipping steps. If there is no remote at all, do not push — the local JJ commit suffices. If no eligible fixes were applied, note explicitly and skip the commit.

## Step 6 — residual handoff

Residuals are actionable findings **not** applied in step 5 — not leftovers from in-skill autofix. Use the Actionable Findings summary / artifact from step 4.
