# Post-Fix Handoff (Interactive)

Loaded at Phase 4 when Phase 3 actually applied a fix in interactive mode. Not used in `mode:pipeline` (see `pipeline-mode.md`) and not used when the user chose "Diagnosis only" — in both cases Phase 4 ends at the Debug Summary.

The goal of this tail is a **PR-ready** fix, not merely a locally green one — while never letting polish or review reach outside the bug's scope.

## Post-fix polish/review tail (before describing the change or opening a PR)

**Contextual overrides first.** Check the user's original prompt, loaded memories, and the project's active instructions already in your context for explicit, clearly applicable preferences that conflict with automatic polish or review — "minimal hotfix only", "do not run review", "always ask before cleanup", "ship the smallest possible diff". Honor them and state what was skipped.

**Skip the tail only with a reason:** purely mechanical fixes (typo/import-only, formatting/lint-only, dependency-only, generated artifacts, docs-only, or roughly under 10 changed lines with no sensitive surface). Keep the Phase 3 tests and self-review regardless, and carry the skip reason into the summary.

**Scope rule for both passes below: never let either pass reach work the user did not offer up.** Phase 3 recorded the fix-owned files and which files already contained changes; that is the scope. Never widen it to a bookmark stack because it looks safe. Jujutsu has no current bookmark, and a bookmark's revset can include unrelated revisions even when `jj status` shows only this fix.

**Simplify before review when useful.** Invoke `ce-simplify-code` when the fix's `jj diff` is non-mechanical and large enough to benefit (default: >=30 changed lines), touches multiple implementation files, introduces a new helper or abstraction, or affects shared/risky surfaces (auth/authz, public contracts, persistence, concurrency, background jobs, external services). Always pass the fix-owned files that were unchanged before Phase 3 as an explicit scope, never a bookmark revset. `ce-simplify-code` modifies what it receives, so a named scope is the guardrail. If a fix-owned file already had user edits, skip it and record `Simplify: skipped for overlapping pre-existing edits` because file-level simplification could rewrite unrelated content.

**Review the final fix scope.** Review every non-mechanical fix unless review tooling is unavailable. Run `ce-code-review` only when its revision scope is known to be this fix: the pre-fix working-copy change was empty and you can pass `base:<pre-fix-commit-id>`. Review reads rather than writes, so a base-scoped interdiff is useful only where that commit ID provably bounds the fix. When `@` carried pre-existing content or the publication stack contains unrelated revisions, use a review capability that accepts explicit filesets; otherwise review `jj diff` for the fix-owned files manually and record `Code review: targeted manual due to unrelated change content`. If `ce-code-review` is unavailable on an otherwise fix-only scope, use the harness's review capability or one explicit manual scan and state that dedicated review was unavailable.

**Handle residual findings before shipping.** Do not auto-open a PR with unresolved P0/P1 findings, or with findings whose fix needs a product/design decision. Ask whether to fix now, accept/defer durably, or stop. Accepted residuals must not live only in the session: if a PR will be opened, pass them as "Known Residuals" context to `ce-commit-push-pr`; on a local-only or stop route, file one ticket per finding in the tracker detected in Phase 1.4, with the finding, impact, file:line, severity, review pointer, change ID, and current commit ID. When no tracker is reachable, name the accepted findings in the final summary and say plainly that nothing else recorded them.

**Re-verify after tail edits.** If simplification or review changed code, rerun the bug's regression test and any targeted checks the tail identified. Never describe or publish a red change.

Then append this block below the Debug Summary, before the description/PR handoff:

```
## Post-Fix Quality
**Scope**: [fix-only change / base:<pre-fix-commit-id> / fix-owned files only / targeted manual due to unrelated change content]
**Simplify**: [ran/skipped + reason]
**Review**: [ran/skipped/manual + outcome]
**Residuals**: [none / accepted Known Residuals for PR / filed as tracker tickets / stated in this summary only, no tracker reachable / blocked pending user decision]
**Re-verification**: [checks rerun after tail edits]
```

## Change / PR handoff detail

SKILL.md's Phase 4 **Routing** block owns the bare per-case actions — which skill fires, and when no PR is possible. It stays there because it must fire even if this file is never read. This section owns only the detail that shapes those actions.

**Opening a PR is the default; do not ask for permission.** What varies the route is what else sits in the revset to be published, never whether the user would approve. A bookmark stack containing only this fix ships as a PR whether the bookmark already exists or is created for publication.

**Why a bookmark stack carrying unrelated work stops short of publication.** `jj git push` publishes the target bookmark, and GitHub compares the revisions reachable from it against the PR base. Moving that bookmark to `@` can therefore publish ancestors the user never offered. The preview cannot authorize that scope because it does not wait for an answer. Shipping gets no exemption from the same scope rule used for simplify and review.

**Why the separable case acts and the entangled case asks.** Isolating fix-owned content in its own Jujutsu change is recoverable through the operation log, so it needs no round trip. Entanglement is different: when fix-owned lines overlap the user's edits and `jj split` cannot isolate them unambiguously, every available move changes publication scope. No default is defensible, so ask only in that state.

**Contextual overrides come first.** An explicit, clearly applicable instruction such as requiring review before publication, requiring draft PRs, forbidding skill-created PRs, or keeping changes local outranks the default routing. Skip, adjust, or stop accordingly. A vague tonal cue is not an override.

**The preview is not a question.** State the change ID, target bookmark, publication revset, and whether a PR will open or update, then proceed without waiting. It exists so the user can interrupt.

**Link what already exists; never open a new record.** Reference the issue of record from Phase 0, plus any existing ticket Phase 1.4 found for this same bug — linking something that already exists is always fine, and on an auto-closing tracker it is how the fix closes it. What is forbidden is *creating* a record for this bug: do not open a ticket in a different system because the repo happens to use it, and do not ask the user whether you should; a Sentry issue, an alert, or a GitHub issue is as much the record as a Linear or Jira ticket, and a duplicate is noise the user then has to close. When Phase 0 found no issue of record — a pasted stack trace, a failing test — this run has none: ship the fix without one rather than opening a ticket to fill the slot. A new ticket is warranted only for a *different* problem you found along the way, per the residual rule above.

**Issue auto-close syntax.** Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local active instructions and syntax observed at runtime always win. Apply compatible Go guidance only to message quality, clarity, and structure; do not impose fixed syntax, examples, or templates. Preserve dynamic tracker tokens and other placeholders required by the active provider. When the linked tracker supports auto-close, include its documented token in the location it requires, whether the PR body or Jujutsu change description. When it has no such syntax, link the record in the PR description and state what the fix addresses.

## Learning-capture criteria (after a PR is open)

Most bugs are localized mechanical fixes where the only "lesson" is the bug itself, and compounding those clutters `<root>/solutions/` without adding value.

- **Skip silently** when the fix is mechanical with no generalizable insight. Default to this when in doubt.
- **Offer neutrally** when the lesson fits in one sentence — "X.foo() returns T | undefined when Y, not just T", or "the diagnostic path was non-obvious and worth recording." If you cannot articulate the lesson, skip rather than offer.
- **Lean into the offer** when the pattern appears in 3+ locations, or the root cause reveals a wrong assumption about a shared dependency, framework, or convention that other code is likely to repeat.

These are the criteria only; SKILL.md's Routing block owns what fires when the user accepts.
