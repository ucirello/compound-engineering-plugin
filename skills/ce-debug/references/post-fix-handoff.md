# RocketClaw ce-debug — post-fix handoff (interactive)

Loaded at Phase 4 when Phase 3 actually applied a fix in interactive mode. Not used in `mode:pipeline` (see `pipeline-mode.md`) and not used when the user chose "Diagnosis only" — in both cases Phase 4 ends at the Debug Summary.

The goal of this tail is a **PR-ready** fix, not merely a locally green one — while never letting polish or review reach outside the bug's scope.

## Post-fix polish/review tail (before commit or PR)

**Contextual overrides first.** Check the user's original prompt, loaded memories, and the project's active instructions already in your context for explicit, clearly applicable preferences that conflict with automatic polish or review — "minimal hotfix only", "do not run review", "always ask before cleanup", "ship the smallest possible diff". Honor them and state what was skipped.

**Skip the tail only with a reason:** purely mechanical fixes (typo/import-only, formatting/lint-only, dependency-only, generated artifacts, docs-only, or roughly under 10 changed lines with no sensitive surface). Keep the Phase 3 tests and self-review regardless, and carry the skip reason into the summary.

**Scope rule for both passes below: never let either pass reach work the user did not offer up.** Phase 3 recorded the fix-owned files and which files already had changes; that is the scope. Never widen it to a bookmark stack because the workspace looks safe — a stack diff equals the fix scope only when the working-copy change was clean anyway, so it buys nothing there and silently swallows the user's in-progress work when it is not. Bookmark creation does not isolate or move working-copy changes.

**Simplify before review when useful.** Invoke `$rocketclaw:ce-simplify-code` when the fix diff is non-mechanical and large enough to benefit (default: >=30 changed lines), touches multiple implementation files, introduces a new helper or abstraction, or affects shared/risky surfaces (auth/authz, public contracts, persistence, concurrency, background jobs, external services). Always pass the fix-owned files that were clean before Phase 3 as an explicit scope — never the bookmark-stack diff. `$rocketclaw:ce-simplify-code` treats a named scope as authoritative and will not widen it, and it *modifies* what it is given, so a named scope is the guardrail. If a fix-owned file already had pre-existing user edits, skip it and record `Simplify: skipped for overlapping pre-existing edits` — file-level simplification could rewrite unrelated hunks the user did not authorize.

**Review the final fix scope.** Review every non-mechanical fix unless review tooling is unavailable. Run default `$rocketclaw:ce-code-review` **only when its diff scope is known to be this fix**: the pre-fix working-copy change was clean and you can pass `base:<pre-fix-change-id>`. Review reads rather than writes, so a base-scoped diff is worth preferring where it is provably the fix; it is the one place the scope may come from a revision rather than the file list. With pre-existing working-copy changes or unrelated described revisions in the bookmark stack, standalone review would reach outside the bug scope — instead use RocketClaw's lightweight review capability if it accepts an explicit file scope, else review the fix-owned files manually and record `Code review: targeted manual due to unrelated workspace work`. If `$rocketclaw:ce-code-review` is unavailable on an otherwise fix-only scope, fall back to RocketClaw's lightweight review capability, else one explicit manual diff scan, and state that dedicated review was unavailable.

**Handle residual findings before shipping.** Do not auto-open a PR with unresolved P0/P1 findings, or with findings whose fix needs a product/design decision — ask whether to fix now, accept/defer durably, or stop. Accepted residuals must not live only in the session: if a PR will be opened, pass them as "Known Residuals" context to `$rocketclaw:ce-commit-push-pr`; on commit-only or stop, file a ticket per finding in the tracker detected in Phase 1.4 — pick the sink and file it, do not ask which sink to use — with enough background to action it standalone (the finding, why it matters, file:line, severity, a pointer to the review run, and the bookmark/change ID so it points at the code even without a PR). When no tracker is reachable, name the accepted findings in the final summary and say plainly that nothing else recorded them.

**Re-verify after tail edits.** If simplification or review changed code, rerun the bug's regression test and any targeted checks the tail identified. Never proceed to commit or PR with a failing working-copy change.

**Advance a skill-created bookmark before handoff.** If Phase 3 created a bookmark, move it to the completed fix revision after all fix, simplification, and review edits with `jj bookmark set <skill-created-bookmark> -r @`, then verify that exact target with `jj bookmark list -r @`. JJ bookmarks do not automatically follow every rewritten working-copy revision. Do not move a pre-existing bookmark without the user's authorization, and require the recording skill to advance the skill-created bookmark again if its commit creates a new completed revision.

Then append this block below the Debug Summary, before the commit/PR handoff:

```
## Post-Fix Quality
**Scope**: [fix-only bookmark / base:<pre-fix-change-id> / fix-owned files only / targeted manual due to unrelated workspace work]
**Simplify**: [ran/skipped + reason]
**Review**: [ran/skipped/manual + outcome]
**Residuals**: [none / accepted Known Residuals for PR / filed as tracker tickets / stated in this summary only, no tracker reachable / blocked pending user decision]
**Re-verification**: [checks rerun after tail edits]
```

## Commit / PR handoff detail

SKILL.md's Phase 4 **Routing** block owns the bare per-case actions — which skill fires, and when no PR is possible. It stays there because it must fire even if this file is never read. This section owns only the detail that shapes those actions.

**Opening a PR is the default; do not ask for permission.** What varies the route is what else sits in the bookmark stack, never whether the user would approve. A bookmark stack carrying only this fix ships as a PR whether or not this skill created it.

**Why a bookmark carrying unrelated work stops short of a push.** `$rocketclaw:ce-commit-push-pr` commits its explicit fileset, pushes the bookmark's whole change stack, and opens a PR spanning every revision in it — so a bookmark containing someone's unoffered work publishes what they never offered up and hands that PR to `$rocketclaw:ce-babysit-pr`. The preview cannot catch this, because it does not wait for an answer. This is the same scope rule the polish tail above already applies to simplify and review; shipping gets no exemption from it.

**Why the separable case acts and the entangled case asks.** A path-limited JJ commit of only fix-owned files is safe and reversible, so the user who wanted exactly that pays no round trip, and the user who wanted the PR says one word — the routing offers it rather than asking permission for it. Entanglement is different in kind: when a fix-owned file already held the user's edits, every available move loses something real, and no default is defensible. Restricting the question to that state is what keeps it from becoming the reflexive prompt this routing exists to remove. Most runs reach neither state — a fresh bookmark or clean working-copy change routes straight to the PR.

**Contextual overrides come first.** An explicit, clearly applicable instruction — "always review before pushing", "open PRs as drafts", "don't open PRs from skills", "commit only" — outranks the default routing: skip the PR step, adjust it, or stop, whichever matches what the user said. A vague tonal cue is not an override.

**The preview is not a question.** State what gets committed, on what bookmark, and that a PR will be opened, then proceed without waiting. It exists so the user can interrupt. When the preview composes or recommends the JJ description, use `<description-composed-from-runtime-conventions>` as the neutral placeholder. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The mandated sentence's history wording is not an operational command; inspect history with `jj log`. Local instructions and runtime `jj log` history win over compatible Go guidance. Preserve the site's semantic requirements, and do not impose a fixed prefix, type, scope, message, subject, body, layout, template, or example.

**Link what already exists; never open a new record.** Reference the issue of record from Phase 0, plus any existing ticket Phase 1.4 found for this same bug — linking something that already exists is always fine, and on an auto-closing tracker it is how the fix closes it. What is forbidden is *creating* a record for this bug: do not open a ticket in a different system because the repo happens to use it, and do not ask the user whether you should; a Sentry issue, an alert, or a GitHub issue is as much the record as a Linear or Jira ticket, and a duplicate is noise the user then has to close. When Phase 0 found no issue of record — a pasted stack trace, a failing test — this run has none: ship the fix without one rather than opening a ticket to fill the slot. A new ticket is warranted only for a *different* problem you found along the way, per the residual rule above.

**Issue auto-close syntax.** When the issue you are linking lives in a tracker with auto-close support, discover and use that tracker's runtime syntax in the location it requires so the fix flows back to the issue and closes on merge. When that location is the JJ description, use `<description-composed-from-runtime-conventions>` as the neutral placeholder. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The mandated sentence's history wording is not an operational command; inspect history with `jj log`. Local instructions and runtime `jj log` history win over compatible Go guidance. Preserve the issue-linking requirement without imposing a fixed closing phrase, prefix, type, scope, message, layout, template, or example. When the tracker has no auto-close syntax, link the record in the PR description and state what the fix addresses.

## Learning-capture criteria (after a PR is open)

Most bugs are localized mechanical fixes where the only "lesson" is the bug itself, and compounding those clutters `<root>/solutions/` without adding value.

- **Skip silently** when the fix is mechanical with no generalizable insight. Default to this when in doubt.
- **Offer neutrally** when the lesson fits in one sentence — "X.foo() returns T | undefined when Y, not just T", or "the diagnostic path was non-obvious and worth recording." If you cannot articulate the lesson, skip rather than offer.
- **Lean into the offer** when the pattern appears in 3+ locations, or the root cause reveals a wrong assumption about a shared dependency, framework, or convention that other code is likely to repeat.

These are the criteria only; SKILL.md's Routing block owns what fires when the user accepts.
