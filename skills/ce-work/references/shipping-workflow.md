# Review And Delivery Workflow

Load after implementation and local unit verification complete.

## Quality Gates

1. Run the project's required test, build, formatting, generation, and lint checks.
2. Inspect `jj status` and `jj diff`. Resolve conflicts and remove accidental artifacts.
3. Invoke `ce-simplify-code` for a substantial non-mechanical diff; otherwise perform a focused reuse/dead-code pass.
4. Invoke `ce-code-review mode:agent`, adding plan/base/depth context when known. Skip only a purely mechanical diff, with a recorded reason.
5. Load `references/review-findings-followup.md` and apply eligible fixes. Rerun verification after edits.
6. Process unresolved actionable findings through the Residual Work Gate.

If review cannot run, use an available native review interactively. In headless use, record unavailability and perform an explicit manual diff scan. Never silently deliver a non-mechanical change without review.

## Residual Work Gate

Interactive use asks whether to apply now, file through the project tracker, accept and record, or stop. Headless use applies eligible fixes, then records residuals without prompting.

Preferred durable sinks are the PR Known Residuals section, a tracker ticket via `references/tracker-defer.md`, then `docs/residual-review-findings/<bookmark-or-change-id>.md`. Do not proceed until every accepted residual has a named sink. A settlement-invalidating conflict always blocks.

## Final Validation

- Every task and supplied requirement is accounted for.
- Behavior changes have tests or an explicit replacement-verification rationale.
- Required checks pass without unexpected warnings.
- Existing patterns and settled decisions remain intact.
- Deferred implementation questions are resolved.
- UI/design validation is recorded when applicable.
- The active Jujutsu change contains only intended work and no conflicts.

Add `Post-Deploy Monitoring & Validation` to the PR description with logs/searches, metrics, healthy and failure signals, rollback trigger, window, and owner. If runtime impact is absent, state that and why.

## Change Descriptions

Before composing, editing, validating, or recommending any complete Jujutsu change description, apply this exact rule:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active runtime instructions and conventions are required input. Inspect descriptions with `jj log`; syntax observed there wins over generic guidance. Apply the linked Go guidance only when compatible with those instructions and that history. Never impose a fixed type, scope, template, example, or identity footer. Use `jj split` for independent changes, `jj squash` for a verified subordinate change, and `jj describe` for each complete unit.

## Deliver

Invoke `ce-commit-push-pr` with neutral actor context to inspect repository conventions, finalize logical Jujutsu changes, publish with `jj git push`, and create/update the PR with `gh`. Pass plan decisions, verification evidence, observable behavior, design links, monitoring, and residuals.

If the user wants no PR, invoke `ce-commit` with neutral actor context. Notify the user with completed scope, verification, PR link when present, residuals, and recovery information.

Before delivery verify that descriptions match repository history, bookmarks are intentional, remote publication uses `jj git push`, and no unrelated change is included.
