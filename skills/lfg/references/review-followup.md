# Review followup (RocketClaw steps 4–5)

`ce-code-review` is review-only. RocketClaw applies eligible fixes itself, then persists them with Jujutsu.

## Step 4 — invoke review

```
ce-code-review mode:agent plan:<plan-path-from-step-1>
```

Read the **Actionable Findings** summary and artifact path. Do not pass `mode:autofix`.

Capture parsed JSON (`status`, `actionable_findings`, `findings`, `artifact_path`, `run_id`) or the markdown Actionable Findings section. If `status` is `failed`, stop and surface `reason`.

## Step 5 — apply and persist review fixes

### What to apply

Apply a finding in the working copy only when **all** of the following hold:

1. **`suggested_fix` is present** — concrete change shape from the review source.
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
2. When no eligible fixes remain, note that explicitly and skip persistence. Otherwise, before editing, run `jj status` and finalize the complete delivery change that step 4 reviewed. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Derive its Jujutsu description from the complete reviewed change, the project's active instructions, and recent repository descriptions inspected with syntax supported by the installed `jj log`; those sources win, and the preceding Go guidance applies only where compatible. Set that description with `jj describe`, then run `jj commit` with no file paths so all pre-existing implementation and simplification edits become the reviewed parent revision. Stop if the new working copy is not clean before review edits begin; never classify pre-existing hunks by filename.
3. Apply eligible fixes in the clean working copy in severity order (`#` stable from the review).
4. Run targeted tests when `requires_verification: true` on any applied finding.
5. Persist the resulting review-fix working copy before step 6. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Compose the Jujutsu description from the project's active instructions and recent repository descriptions inspected with syntax supported by the installed `jj log`; those sources win, and the preceding Go guidance applies only where compatible. Derive a neutral description from the fixes actually applied and repository history; do not use a fixed message, impose a fixed style, or add promotional or attribution material. Set that description with `jj describe`, then run `jj commit` with no file paths. If `jj status` contains edits that cannot be attributed unambiguously to the applied fixes or their required verification, stop instead of committing them as review fixes.
6. Apply `SKILL.md`'s unresolved-conflict publication gate, then inspect the exact local delivery bookmark: create it at `@-` when absent or move it to `@-` when present. Never call move on an absent bookmark. When the shipping precondition established a remote's write authority, apply the gate again immediately before `jj git push --bookmark <delivery-bookmark> --remote <remote>`. If no remote exists, the local Jujutsu commits suffice.

## Step 6 — residual handoff

Residuals are actionable findings **not** applied in step 5 — not leftovers from in-skill autofix. Use the Actionable Findings summary / artifact from step 4.
