# Implementation Loop

For each task in dependency order:

1. Mark it active and read only its cited authority and local patterns.
2. Inspect `jj status`, `jj diff`, and the relevant revset. If the requested behavior already exists, verify it rather than reimplementing.
3. Find existing tests that import, reference, or mirror the affected code.
4. Choose existing-failure, proof-first, characterization-first, or a deliberate no-test exception before production edits.
5. For proof-first work, observe the expected failure before implementation. For characterization, capture the baseline first.
6. Implement only the current behavior slice and follow existing conventions.
7. Check happy, edge, failure, and cross-layer scenarios that apply.
8. Trace callbacks, middleware, persisted state, retries, alternate interfaces, and error classes two levels outward when relevant.
9. Run focused verification, then broader checks required by the plan.
10. Record behavior signal, tests inspected/changed/used, red or characterization evidence, commands/results, and any exception.
11. Inspect the complete Jujutsu diff. Split unrelated work with `jj split`; do not hide collisions in one change.
12. Mark the task complete only after its complete logical change is verified and described.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active runtime instructions and conventions are required input. Inspect descriptions with `jj log`; syntax observed there wins over generic guidance. Apply the linked Go guidance only when compatible with those instructions and that history. Descriptions are neutral and dynamic; no fixed type, scope, template, example, or identity footer is permitted.

For an external unit, controller terminal state is only authoring evidence. Completion requires canonical squash, verification, description, fresh working-copy change, workspace cleanup, and receipt. Restoration-blocked work stops all dependents.

For a wave, pause after every canonical result, inspect actual scope, recompute independence against the advancing revision, and rebase/retry or serialize stale work. A conflict-free squash is not semantic proof.
