# Post-fix handoff (interactive)

Loaded at Phase 4 when Phase 3 actually applied a fix in interactive mode. Not used in `mode:pipeline` (see `pipeline-mode.md`) and not used when the user chose "Diagnosis only" — in both cases Phase 4 ends at the Debug Summary.

The goal of this tail is a **PR-ready** fix, not merely a locally green one — while never letting polish or review reach outside the bug's scope.

## Post-fix polish/review tail (before change finalization or PR)

**Contextual overrides first.** Check the user's original prompt, loaded memories, and the project's active instructions already in your context for explicit, clearly applicable preferences that conflict with automatic polish or review — "minimal hotfix only", "do not run review", "always ask before cleanup", "ship the smallest possible diff". Honor them and state what was skipped.

**Skip the tail only with a reason:** purely mechanical fixes (typo/import-only, formatting/lint-only, dependency-only, generated artifacts, docs-only, or roughly under 10 changed lines with no sensitive surface). Keep the Phase 3 tests and self-review regardless, and carry the skip reason into the summary.

**Scope rule for both passes below: never let either pass reach work the user did not offer up.** Phase 3 recorded the fix-owned files and which files already had changes; that is the scope. Never widen it to the bookmark stack because the stack looks safe. A stack diff equals the fix scope only when the working-copy change had no pre-existing edits, and bookmark creation is not evidence of a clean change.

**Simplify before review when useful.** Invoke `ce-simplify-code` when the fix diff is non-mechanical and large enough to benefit (default: >=30 changed lines), touches multiple implementation files, introduces a new helper or abstraction, or affects shared/risky surfaces (auth/authz, public contracts, persistence, concurrency, background jobs, external services). Always pass the fix-owned files that had no pre-existing edits before Phase 3 as an explicit scope — never the bookmark-stack diff. `ce-simplify-code` treats a named scope as authoritative and will not widen it, and it *modifies* what it is given, so a named scope is the guardrail. If a fix-owned file already had pre-existing user edits, skip it and record `Simplify: skipped for overlapping pre-existing edits`.

**Review the final fix scope.** Review every non-mechanical fix unless review tooling is unavailable. Run default `ce-code-review` **only when its diff scope is known to be this fix**: the pre-fix working-copy change had no edits and you can pass `base:<pre-fix-commit-id>`. On a change with pre-existing edits or a bookmark stack with unrelated revisions, use a review capability that accepts explicit fix-owned files; otherwise inspect `jj diff` for those files manually and record `Code review: targeted manual due to unrelated change-stack work`. If `ce-code-review` is unavailable on an otherwise fix-only scope, fall back to the harness's review tool or one explicit manual diff scan.

**Handle residual findings before shipping.** Do not auto-open a PR with unresolved P0/P1 findings, or with findings whose fix needs a product/design decision — ask whether to fix now, accept/defer durably, or stop. Accepted residuals must not live only in the session: if a PR will be opened, pass them as "Known Residuals" context to `ce-commit-push-pr`; on local-finalization or stop, file a ticket per finding in the tracker detected in Phase 1.4 with enough background to act on it independently, including the bookmark, change ID, and commit ID. When no tracker is reachable, name the accepted findings in the final summary and say plainly that nothing else recorded them.

**Re-verify after tail edits.** If simplification or review changed code, rerun the bug's regression test and any targeted checks the tail identified. Never finalize the change or open a PR with failing checks.

Then append this block below the Debug Summary, before the change/PR handoff:

```
## Post-Fix Quality
**Scope**: [fix-only change / base:<pre-fix-commit-id> / fix-owned files only / targeted manual due to unrelated change-stack work]
**Simplify**: [ran/skipped + reason]
**Review**: [ran/skipped/manual + outcome]
**Residuals**: [none / accepted Known Residuals for PR / filed as tracker tickets / stated in this summary only, no tracker reachable / blocked pending user decision]
**Re-verification**: [checks rerun after tail edits]
```

## Change / PR handoff detail

SKILL.md's Phase 4 **Routing** block owns the bare per-case actions — which skill fires, and when no PR is possible. It stays there because it must fire even if this file is never read. This section owns only the detail that shapes those actions.

**Opening a PR is the default; do not ask for permission.** What varies the route is what else sits in the publication bookmark's change stack, never whether the user would approve. A bookmark stack carrying only this fix ships as a PR whether or not this skill created it.

**Why a bookmark stack carrying unrelated work stops short of a push.** `ce-commit-push-pr` finalizes its file scope, pushes the bookmark, and opens a PR spanning every revision from the remote base through its target. A stack holding someone's in-progress work would publish what they never offered and hand it to `ce-babysit-pr`. The preview cannot make that safe because it does not wait for an answer.

**Why the separable case acts and the entangled case asks.** Finalizing only fix-owned files is recoverable through Jujutsu's operation log. Entanglement is different: when a fix-owned file already held the user's edits, every available file-level move includes or leaves both sets of edits, and no default is defensible. Most runs use a dedicated clean change and route directly to the PR.

**Contextual overrides come first.** An explicit, clearly applicable instruction — "always review before pushing", "open PRs as drafts", "don't open PRs from skills", "keep the change local" — outranks the default routing: skip the PR step, adjust it, or stop, whichever matches what the user said. A vague tonal cue is not an override.

**The preview is not a question.** State what gets described, which bookmark stack will be pushed, and whether a PR will be opened or updated, then proceed without waiting. It exists so the user can interrupt.

Pass the operational model/provider/harness and human attribution context to `ce-commit-push-pr` without adding creator branding.

**Link what already exists; never open a new record.** Reference the issue of record from Phase 0, plus any existing ticket Phase 1.4 found for this same bug — linking something that already exists is always fine, and on an auto-closing tracker it is how the fix closes it. What is forbidden is *creating* a record for this bug: do not open a ticket in a different system because the repo happens to use it, and do not ask the user whether you should; a Sentry issue, an alert, or a GitHub issue is as much the record as a Linear or Jira ticket, and a duplicate is noise the user then has to close. When Phase 0 found no issue of record — a pasted stack trace, a failing test — this run has none: ship the fix without one rather than opening a ticket to fill the slot. A new ticket is warranted only for a *different* problem you found along the way, per the residual rule above.

**Issue auto-close semantics.** When the issue of record's tracker supports automatic closure, include the required semantics in the location that tracker parses, whether PR description or change description. Do not prescribe a fixed message syntax. When the tracker has no auto-close mechanism, link the record in the PR description and state what the fix addresses.

## Learning-capture criteria (after a PR is open)

Most bugs are localized mechanical fixes where the only "lesson" is the bug itself, and compounding those clutters `<root>/solutions/` without adding value.

- **Skip silently** when the fix is mechanical with no generalizable insight. Default to this when in doubt.
- **Offer neutrally** when the lesson fits in one sentence — "X.foo() returns T | undefined when Y, not just T", or "the diagnostic path was non-obvious and worth recording." If you cannot articulate the lesson, skip rather than offer.
- **Lean into the offer** when the pattern appears in 3+ locations, or the root cause reveals a wrong assumption about a shared dependency, framework, or convention that other code is likely to repeat.

These are the criteria only; SKILL.md's Routing block owns what fires when the user accepts.
