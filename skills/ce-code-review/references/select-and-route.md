# Selecting reviewers and binding the adversarial route

Read this at Stage 3 (Select reviewers), together with `references/persona-catalog.md`. It defines the layers reviewers are selected in, the search for project standards paths, the check that shrinks the reviewer list for a small low-risk diff, and the decision between the cross-model peer and the in-process adversarial reviewer.

## Reviewers

Reviewer personas are selected in layers. The persona catalog in `references/persona-catalog.md` (read it at Stage 3) has the full selection criteria and the condition for spawning each reviewer. Each selected reviewer is a generic subagent seeded with a local prompt file from `references/personas/`; do not dispatch standalone agents by type/name.

**Core (always-on):** `correctness-reviewer`.

**Standards conditional:** `project-standards-reviewer` runs only when Stage 3b finds at least one applicable standards file (Stage 3b is the project-standards path search below). When the search succeeds but finds nothing, skip this persona and say so in Coverage, because this persona is not allowed to invent standards beyond those files.

**Generic conditional:**

- `testing-reviewer` — test files, test infrastructure, mocks, fixtures, or harness behavior changed; or the diff changes meaningful runtime behavior without corresponding test work. Behavioral triggers include new or changed branches, state mutation, API/control-flow behavior, and error handling. Production-file presence alone and non-behavioral edits do not select it.
- `maintainability-reviewer` — a large or structural diff: substantial refactor, new abstractions, file moves, coupling/type-boundary changes, or at least 200 executable changed lines.
- `agent-native-reviewer` — an agent-facing product surface changed: an agent tool surface (MCP tools, agent tool or function definitions, system-prompt construction), or a user-facing capability added or changed in a product that already has such a surface. Editing only the prose of skills, agent definitions, or instruction files does not select it.
- `learnings-researcher` — there is institutional knowledge to check the change against: `<root>/solutions/` exists and a cheap path/title search finds a plausible match for the changed modules or patterns (the existence of a corpus alone is not enough), or, in local scope, the workspace config declares Compound Packs (Stage 1b `declared_packs`). Declared packs need no pre-search; the persona matches their rules itself.

**Cross-cutting conditional (per diff):**

- `security-reviewer` — auth, public endpoints, user input, permissions (including feature-flag or entitlement gates controlling reachability)
- `performance-reviewer` — DB queries, data transforms, caching, async
- `api-contract-reviewer` — routes, serializers, type signatures, versioning
- `data-migration-reviewer` — migration files / schema dumps / backfills (see the `data-migration` spawn gate in Stage 3)
- `reliability-reviewer` — error handling, retries, timeouts, background jobs
- `adversarial-reviewer` lens — the Adversarial selection condition in `references/modes-and-output.md` applies. Reserve the lens for an approved native peer once it starts; only a usable result satisfies it. Use the native local `adversarial-reviewer` on the approved fallback paths. Never dispatch both on the same brief concurrently or count an inherited model as cross-model.
- `previous-comments-reviewer` — PR with existing review comments (PR-only, comment-gated)

**Stack-specific conditional (per diff):** `frontend-races-reviewer` (async UI state, timers, listeners, or lifecycle cleanup that can race, in any browser UI framework).

**Migration-specific conditional:** local prompt asset `deployment-verification-agent` — deployment checklist + rollback when the migration gate applies and the change is risky.

## Review Scope

A full review always selects correctness, adds project-standards when applicable files exist, then adds only the remaining conditionals justified by the diff. This file runs only on the full spine; it does not invent irrelevant domains. A Rails auth feature might add security, reliability, and adversarial while still skipping agent-native and learnings when those surfaces are absent.

## Language-Aware Conditionals

Select stack-specific reviewers only when the diff touches runtime behavior they specialize in (async UI races), never mechanically from file extensions alone. The trigger is meaningful changed behavior in that stack's runtime domain. Structural quality (complexity deletion, 1k-line regressions, type-boundary leaks) belongs to the conditional `maintainability-reviewer`; do not spawn extra reviewers for language conventions, philosophy, or "strict bar" passes.

### Stage 3: Select reviewers

Read the diff and file list from Stage 1 and the helper JSON from Stage 1b. Correctness is automatic; project-standards is decided by the Stage 3b (Discover project standards paths) result. Read `references/persona-catalog.md` from this skill's directory now; it defines the spawn condition for every other reviewer. Select generic reviewers before domain reviewers: testing for changed test/harness surfaces, or when meaningful runtime behavior changed without corresponding test work; maintainability only for large or structural work; agent-native only for agent-facing work; and learnings when a cheap search finds plausible matches in an existing `<root>/solutions/` corpus or, in local scope, the repo declares Compound Packs (Stage 1b `declared_packs`). For the behavioral testing trigger, require concrete diff evidence such as new or changed branches, state mutation, API/control-flow behavior, or error handling. Do not select testing from production-file presence alone or for non-behavioral edits. For each remaining conditional, decide whether the diff warrants it. Diff-derived helper signals (`signals`, `test_files_changed`, `agent_surface`, `has_learnings_corpus`) are prompts to consider a persona, never automatic selection. `declared_packs` is a config fact the learnings selection condition reads, not a diff signal.

**Adversarial selection is consequence-based.** Apply the condition already read in `references/modes-and-output.md`, including its explicit-request override. Instruction prose, configuration, and executable code receive the same assessment of the behavior they govern. For a verification mechanism, identify the material failure its false success could conceal; ordinary per-feature assertions remain the testing reviewer's job. Include the affected boundary and consequence in the conditional reviewer's selection reason.

**`previous-comments` is PR-only AND comment-gated.** Only select this persona when both conditions hold:

1. Stage 1 gathered PR metadata (PR number or URL was provided as an argument, or `gh pr view` returned metadata for the current branch).
2. `hasPriorComments` from Stage 1 is true (the PR has at least one review submission or issue comment).

Skip it for standalone branch reviews with no associated PR, and skip it for PRs with no prior feedback yet -- there is nothing for the persona to verify, and a spawned subagent that returns empty findings still costs the full subagent startup overhead (persona spec, diff, schema, plus its own gh calls).

Stack-specific personas are additive when runtime behavior warrants them. A UI change that adds polling or an async state update may warrant `frontend-races`; a TypeScript boundary change may warrant `api-contract` only when the diff changes an externally consumed contract, not merely because it exports a symbol.

**`data-migration` spawn gate.** Select `data-migration-reviewer` only when the diff includes at least one migration or schema artifact: `db/migrate/*`, `db/schema.rb`, `db/structure.sql`, Alembic/Flyway/Liquibase migration paths, or explicit backfill/data-transform scripts (rake tasks, one-off data migration classes). **Do not spawn** for model-only changes, query-only refactors, serializers/controllers that reference columns without a migration or schema dump in the diff, or migration tests alone.

For `deployment-verification-agent`, use the same migration-artifact condition when the change is risky (destructive DDL, backfills, NOT NULL without default, column renames/drops).

### Stage 3b: Decide the project-standards dispatch

Stage 1c already paired each criteria file governing this change with the changed files it governs. Decide from that mapping whether the `project-standards` persona runs. When the instruction-file fallback supplied the criteria for any changed file, name it as the fallback in Coverage. **When uncertain, run the persona rather than skip it** — an error is never an empty result:

- One or more applicable paths: select `project-standards` and pass the mapping inside a `<standards-paths>` block in its Stage 4 context. The persona applies the precedence Stage 1c resolved rather than re-deriving it, and reads the files itself, targeting only relevant sections.
- Empty successful search: do not dispatch `project-standards`; record `project standards: not run (no applicable standards files)` in Coverage.
- Search failure or uncertain scope: dispatch `project-standards` with the uncertainty stated.

### Stage 3c: Depth already decided

The Review depth gate in `references/modes-and-output.md` already chose lite, focused, or full, before this file was read. This stage does not size the run and does not shrink the roster. You are on the full spine. Continue to Stage 3d.

### Stage 3d: Bind the adversarial route and final roster

Before Stage 4, choose which route receives the adversarial brief. Both routes reuse the Stage 1 run directory.

For a selected local scope, follow `references/cross-model-review.md`: resolve and disclose the sanctioned route, stage constraints and brief separately, and request the native peer under the separate delegation, model and depth rules. Store the launch identity (or synchronous terminal outcome) and its request, start time, and stage-log event. A started peer takes the local adversarial reviewer out of the roster; only the owning bounded recovery can restore the local reviewer. Complete any pre-launch recoverable retry before finalizing the roster. If no peer can start, keep the local reviewer when permitted and name the peer's actual skip or failure reason. In remote scope, use only the local native adversarial reviewer.

If task tracking is active, show the peer task only after launch and record its terminal outcome when collected. A receipt reserves the lens, not proof of completed review. Do not proceed until the local roster is settled.

Announce that final team before spawning, as a user-facing summary: name the always-on reviewers plainly, and for each conditional reviewer give the one-line reason it was added (the real concern, not the keyword that matched). Do **not** put local reviewer model-tier labels (`[session model]`/`[mid-tier]`) or the internal names of the scope modes in this announcement — those are internal. Still decide each local reviewer's tier here and keep it in working state for Stage 4. The cross-model line is separate; it uses the model/reasoning and route wording from its reference, which depends on what the peer's receipt attests. This is progress reporting, not a blocking confirmation.
