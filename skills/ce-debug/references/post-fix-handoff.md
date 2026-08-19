# Post-Fix Handoff

Loaded at Phase 4 when Phase 3 actually applied a fix in interactive mode. Not used in `mode:pipeline` (see `pipeline-mode.md`) and not used when the user chose "Diagnosis only" — in both cases Phase 4 ends at the Debug Summary.

The goal of this tail is a **PR-ready** fix, not merely a locally green one — while never letting polish or review reach outside the bug's scope.

## Post-fix polish/review tail (before finalization or PR)

**Contextual overrides first.** Check the user's original prompt, loaded memories, and the project's active instructions already in your context for explicit, clearly applicable preferences that conflict with automatic polish or review — "minimal hotfix only", "do not run review", "always ask before cleanup", "ship the smallest possible diff". Honor them and state what was skipped.

**Skip the tail only with a reason:** purely mechanical fixes (typo/import-only, formatting/lint-only, dependency-only, generated artifacts, docs-only, or roughly under 10 changed lines with no sensitive surface). Keep the Phase 3 tests and self-review regardless, and carry the skip reason into the summary.

**Scope rule for both passes below: never let either pass reach work the user did not offer up.** Phase 3 recorded the fix-owned files and which files already had working-copy changes; that is the scope. Never widen it to bookmark ancestry because it looks safe: ancestry equals the fix scope only when the working copy and unpublished ancestry were clean, and otherwise it silently includes the user's work. Bookmark creation is not evidence of isolation.

**Simplify before review when useful.** Invoke `ce-simplify-code` when the fix diff is non-mechanical and large enough to benefit (default: >=30 changed lines), touches multiple implementation files, introduces a new helper or abstraction, or affects shared/risky surfaces (auth/authz, public contracts, persistence, concurrency, background jobs, external services). Always pass the fix-owned files that were clean before Phase 3 as an explicit scope; never substitute bookmark ancestry. `ce-simplify-code` treats a named scope as authoritative and will not widen it, and it *modifies* what it is given, so a named scope is the guardrail. If a fix-owned file already had pre-existing user edits, skip it and record `Simplify: skipped for overlapping pre-existing edits` — file-level simplification could rewrite unrelated hunks the user did not authorize.

**Review the final fix scope.** Review every non-mechanical fix unless review tooling is unavailable. Run default `ce-code-review` **only when its diff scope is known to be this fix**: the pre-fix working copy was clean and you can pass `base:<pre-fix-commit-id>`. Review reads rather than writes, so a base-scoped diff is worth preferring where it is provably the fix. With pre-existing working-copy changes or unrelated unpublished revisions, standalone review would reach outside the bug scope; instead use a lightweight review capability that accepts explicit file scope, or review the fix-owned files manually and record `Code review: targeted manual due to unrelated work`.

**Handle residual findings before shipping.** Do not auto-open a PR with unresolved P0/P1 findings, or with findings whose fix needs a product/design decision — ask whether to fix now, accept/defer durably, or stop. Accepted residuals must not live only in the session: if a PR will be opened, pass them as "Known Residuals" context to `ce-commit-push-pr`; on local-finalize or stop, file a ticket per finding in the tracker detected in Phase 1.4 with enough background to action it standalone (the finding, why it matters, file:line, severity, a pointer to the review run, and the bookmark/commit ID). When composing or editing that durable change description, local repository conventions and visible history take precedence; apply compatible Go guidance only where they do not decide the wording. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. When no tracker is reachable, name the accepted findings in the final summary and say plainly that nothing else recorded them.

**Re-verify after tail edits.** If simplification or review changed code, rerun the bug's regression test and any targeted checks the tail identified. Never proceed to finalization or PR with a red working copy.

Then append this block below the Debug Summary, before the finalization/PR handoff:

```
## Post-Fix Quality
**Scope**: [fix-only bookmark / base:<pre-fix-commit-id> / fix-owned files only / targeted manual due to unrelated work]
**Simplify**: [ran/skipped + reason]
**Review**: [ran/skipped/manual + outcome]
**Residuals**: [none / accepted Known Residuals for PR / filed as tracker tickets / stated in this summary only, no tracker reachable / blocked pending user decision]
**Re-verification**: [checks rerun after tail edits]
```

## Finalization / PR handoff detail

For every commit message or jj change description composed, edited, validated, or recommended in this handoff, local repository conventions and visible history take precedence; apply compatible Go guidance only where they do not decide the wording. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

SKILL.md's Phase 4 **Routing** block owns the bare per-case actions — which skill fires, and when no PR is possible. It stays there because it must fire even if this file is never read. This section owns only the detail that shapes those actions.

**Opening a PR is the default; do not ask for permission.** What varies the route is what else sits in the bookmark's unpublished ancestry, never whether the user would approve. A bookmark carrying only this fix ships as a PR whether or not this skill created it.

**Why bookmark ancestry carrying unrelated work stops short of a push.** `ce-commit-push-pr` finalizes the changed files it finds, pushes the bookmark, and opens a PR spanning its unpublished ancestry. If that ancestry contains someone's in-progress work, shipping publishes what they never offered up. The preview cannot cure the scope problem because it does not wait for an answer.

**Why the separable case acts and the entangled case asks.** Finalizing only fix-owned files is safe and recoverable. Entanglement is different: when a fix-owned file already held the user's edits, every available move loses something real, and no default is defensible. Restrict the question to that state.

**Contextual overrides come first.** An explicit, clearly applicable instruction — "always review before pushing", "open PRs as drafts", "don't open PRs from skills", "commit only" — outranks the default routing: skip the PR step, adjust it, or stop, whichever matches what the user said. A vague tonal cue is not an override.

**The preview is not a question.** State what gets finalized, on what bookmark, and that a PR will be opened, then proceed without waiting. It exists so the user can interrupt.

**Link what already exists; never open a new record.** Reference the issue of record from Phase 0, plus any existing ticket Phase 1.4 found for this same bug — linking something that already exists is always fine, and on an auto-closing tracker it is how the fix closes it. What is forbidden is *creating* a record for this bug: do not open a ticket in a different system because the repo happens to use it, and do not ask the user whether you should; a Sentry issue, an alert, or a GitHub issue is as much the record as a Linear or Jira ticket, and a duplicate is noise the user then has to close. When Phase 0 found no issue of record — a pasted stack trace, a failing test — this run has none: ship the fix without one rather than opening a ticket to fill the slot. A new ticket is warranted only for a *different* problem you found along the way, per the residual rule above.

**Issue auto-close syntax.** When the issue you are linking lives in a tracker with auto-close support, include that tracker's required syntax in the commit message or PR description location it parses, so the fix closes the issue on merge. Do not impose a fixed wording beyond the tracker's required token. Local repository conventions and visible history take precedence for the surrounding commit message or change description; apply compatible Go guidance only where they do not decide the wording. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. When the tracker has no auto-close syntax, link the record in the PR description and state what the fix addresses.

## Learning-capture criteria (after a PR is open)

Most bugs are localized mechanical fixes where the only "lesson" is the bug itself, and compounding those clutters `<root>/solutions/` without adding value.

- **Skip silently** when the fix is mechanical with no generalizable insight. Default to this when in doubt.
- **Offer neutrally** when the lesson fits in one sentence — "X.foo() returns T | undefined when Y, not just T", or "the diagnostic path was non-obvious and worth recording." If you cannot articulate the lesson, skip rather than offer.
- **Lean into the offer** when the pattern appears in 3+ locations, or the root cause reveals a wrong assumption about a shared dependency, framework, or convention that other code is likely to repeat.

These are the criteria only; SKILL.md's Routing block owns what fires when the user accepts.
