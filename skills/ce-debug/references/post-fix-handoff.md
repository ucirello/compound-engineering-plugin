# ce-debug - post-fix handoff (interactive)

Loaded at Phase 4 after an interactive fix. It is not used in `mode:pipeline` or after "Diagnosis only."

The goal is a PR-ready fix whose polish, review, recording, and publication never include work the user did not offer.

## Post-fix quality

Honor explicit project or user instructions that narrow automatic polish or review. Skip dedicated simplify/review only when the fix is mechanical enough that those passes cannot materially improve it; retain Phase 3 tests and self-review and report the skip reason.

Phase 3's fix-owned files and pre-existing changes define the writable scope. Pass only previously clean fix-owned files to `ce-simplify-code`; skip overlapping files rather than risk rewriting unrelated edits. Review every non-mechanical fix. Use `ce-code-review` only when a JJ revision scope is provably fix-only; otherwise use an available explicitly file-scoped review or manually review the fix-owned files. Report any reduced review coverage.

Resolve actionable findings before shipping. Do not publish unresolved high-severity findings or findings requiring a product decision. Accepted residuals must be durable: pass them as Known Residuals when opening a PR, otherwise file them in the project's tracker; if no tracker is reachable, record them under `<root>/residual-review-findings/` and mention that path in the summary.

Preserve the accepted-residual meaning without fixed syntax examples. Do not add creator, model, provider, tool, runtime, or product attribution to any output.

If simplification or review changed code, rerun the regression test and targeted checks before handoff.

Append this block below the Debug Summary:

```
## Post-Fix Quality
**Scope**: [fix-only JJ revision or fix-owned files]
**Simplify**: [ran/skipped and reason]
**Review**: [ran/skipped/manual and outcome]
**Residuals**: [durable disposition or blocking decision]
**Re-verification**: [checks rerun after tail edits]
```

## Recording and publication

The routing in `SKILL.md` owns which recording skill runs. This reference supplies the safety conditions:

- Opening or updating a PR is the default only when the complete published JJ change stack contains no unoffered work and `gh` can open the PR against the configured GitHub remote.
- When fix-owned files contain inseparable pre-existing edits, ask before recording them because no safe default preserves both ownership and a complete fix.
- An explicit user instruction to keep the work local, stop, or alter PR behavior wins.
- Preview the scope, bookmark, and PR action before publication; the preview is not a question.

Preserve the diagnosis, fix, residual, and issue-linking semantics in the recording handoff without fixed syntax examples. Do not add creator, model, provider, tool, runtime, or product attribution to any output.

Link the issue of record and any existing duplicate or prior-fix discussion. Use the tracker's runtime auto-close syntax and required placement when supported; otherwise link the record and state what the fix addresses. Never create a duplicate issue merely to fill an absent record.

## Learning capture

Offer learning capture only when the diagnosis produced a reusable insight beyond the localized bug. Lean into the offer when the pattern is repeated or exposes a wrong shared assumption; otherwise skip when no concise generalizable lesson exists. `SKILL.md` owns the action after acceptance.
