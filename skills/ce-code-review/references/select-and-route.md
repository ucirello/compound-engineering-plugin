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
- `learnings-researcher` — `<root>/solutions/` has a plausible cheap path/title match (existence alone is insufficient), or local RocketClaw config declares packs (`declared_packs`). Declared packs need no pre-search; the persona matches their rules itself.

**Cross-cutting conditional (per diff):**

- `security-reviewer` — auth, public endpoints, user input, permissions (including feature-flag or entitlement gates controlling reachability)
- `performance-reviewer` — DB queries, data transforms, caching, async
- `api-contract-reviewer` — routes, serializers, type signatures, versioning
- `data-migration-reviewer` — migration files / schema dumps / backfills (see the `data-migration` spawn gate in Stage 3)
- `reliability-reviewer` — error handling, retries, timeouts, background jobs
- `adversarial-reviewer` lens — the Adversarial selection condition in `references/modes-and-output.md` applies. Satisfy this lens with the independent cross-model adversarial pass when a peer job on the approved route starts successfully. Dispatch the in-process `adversarial-reviewer` when the peer cannot start, or when the fold-in step later finds the peer never ran, or gives up after a retry on the same route fails on a rate limit and restores the local reviewer; do not run both reviews on the same brief.
- `previous-comments-reviewer` — PR with existing review comments (PR-only, comment-gated)

**Stack-specific conditional (per diff):** `frontend-races-reviewer` (async UI state, timers, listeners, or lifecycle cleanup that can race, in any browser UI framework).

**RocketClaw conditional (migration-specific):** `deployment-verification-agent` supplies deployment checklist/rollback when the migration gate applies and the change is risky.

## Review Scope

A full review always spawns correctness, adds applicable project standards and only generic/cross-cutting/stack-specific/RocketClaw conditionals justified by the diff. This full-spine reference never invents irrelevant domains. A Rails auth feature may add security/reliability/adversarial while skipping absent agent-native/learnings surfaces.

## Language-Aware Conditionals

Select stack-specific reviewers only when the diff touches runtime behavior they specialize in (async UI races), never mechanically from file extensions alone. The trigger is meaningful changed behavior in that stack's runtime domain. Structural quality (complexity deletion, 1k-line regressions, type-boundary leaks) belongs to the conditional `maintainability-reviewer`; do not spawn extra reviewers for language conventions, philosophy, or "strict bar" passes.

### Stage 3: Select reviewers

Read Stage 1 diff/file list and Stage 1b helper facts, then `persona-catalog.md`. Correctness is automatic; project standards follows Stage 3b. Select generic before domain reviewers: testing for changed test/harness surfaces or concrete runtime branches/state/API/control-flow/error handling without corresponding tests, never production-file presence or prose alone; maintainability for large/structural work; agent-native for agent-facing work; learnings for plausible cheap corpus matches or locally declared RocketClaw Packs. Judge each remaining conditional from actual behavior. Helper `signals`, `test_files_changed`, `agent_surface`, `has_learnings_corpus` prompt consideration, never automatic selection. `declared_packs` is a config fact, not a diff heuristic.

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

Complete this stage **before reading persona prompt assets, `references/dispatch-reviewers.md`, or entering Stage 4** (Dispatch reviewers). That reference's persona-file instructions are valid only once you have settled which single route covers the adversarial lens: the peer, or the in-process fallback. This stage makes that exclusive choice between a cross-model adversarial peer and the in-process `adversarial-reviewer`. Later stages use that choice and must not decide it again, except when the fold-in step finds the peer never ran, or restores the in-process reviewer after a retry on the same route fails on a rate limit.

Both routes share the run directory Stage 1b created; do not create another.

When adversarial was selected for a local reviewed tree, read `references/cross-model-review.md` in full. Verify host identity, resolve one native target/model with `opencode.models`, honor separate delegation/model permissions and announce recipients/code egress. Write the host-vetted constraints and untrusted semantic brief separately before launch; do not embed the full diff/file list. Launch the peer through native subagents, preserving exact-range endpoints, run directory, launch ID, requested model/effort, start time and deadline; record `--start peer` with `run-log.py`. The peer consumes native capacity, not a detached shell process.

- If native launch succeeds, reserve the adversarial lens for the peer and remove local `adversarial-reviewer` from the roster. A launch receipt is not completed coverage; recovery can restore the local lens only after stopping/collecting the peer.
- If no launch starts, follow `references/cross-model-recovery.md` before finalizing the roster. Distinguish actual depth exhaustion, active capacity, delegation denial, model-override denial/rejection and missing tools. Retry only supported native corrections within the same deadline. Keep local adversarial coverage when permitted, disclose required cross-model coverage lost, and never use a shell/other-harness bypass.
- In `pr-remote` / `branch-remote`, do not start the peer; keep the selected in-process adversarial reviewer because it can inspect the reviewed refs.

When native launch succeeds and task tracking is active, track its review outcome until terminal. Name it independent only when identity receipts verify different serving families. Never create a running task before launch or leave it running after fallback/failure.

Do not proceed until the final local roster is settled. This is a hard rule, not a preference: a started peer and the in-process adversarial reviewer must never both receive the same review brief.

Announce that final team before spawning, as a user-facing summary: name the always-on reviewers plainly, and for each conditional reviewer give the one-line reason it was added (the real concern, not the keyword that matched). Do **not** put local reviewer model-tier labels (`[session model]`/`[mid-tier]`) or the internal names of the scope modes in this announcement — those are internal. Still decide each local reviewer's tier here and keep it in working state for Stage 4. The cross-model line is separate; it uses the model/reasoning and route wording from its reference, which depends on what the peer's receipt attests. This is progress reporting, not a blocking confirmation.
