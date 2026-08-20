---
name: ce-work
description: Execute a plan or concrete work prompt end-to-end. Use when implementing from a plan document, a specification path, or a clear build request; use ce-debug for open-ended bugs. Standalone use owns the shipping tail; outer orchestrators pass `mode:return-to-caller [implementation_engine:<compact-json>] [implementation_run:<safe-id>] <plan path>` for implementation, recovery, and local verification only.
argument-hint: "[Plan path, work description, or recovery request with run id; blank uses latest] | [mode:return-to-caller [implementation_engine:<compact-json>] [implementation_run:<safe-id>] <plan path> for outer orchestrators]"
---

# Work Execution

## Setup

Run this once at invocation start, before subagent dispatch. Follow its directives unless they conflict with this skill's question policy. Run the fence as one unfiltered command. Its output begins with `=== skill context` and ends with `WORK_CONTEXT_END`; if exactly one boundary appears, rerun the fence once. If Node is unavailable, proceed unchanged.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
NODE="$(for c in node nodejs; do command -v "$c" >/dev/null 2>&1 && "$c" -e '' >/dev/null 2>&1 && { echo "$c"; break; }; done)";
if [ -n "$NODE" ]; then
  "$NODE" "$SKILL_DIR/scripts/context.mjs" || echo "context script failed; continue with the skill's normal behavior";
else
  echo "no Node runtime; continue with the skill's normal behavior";
fi
```

## Outcome

- **Result:** A fully implemented, locally verified Jujutsu change set from a plan, specification, or concrete work prompt.
- **Next consumer:** Standalone use hands the verified changes to the shipping workflow. Return-to-Caller Mode returns a structured implementation and verification envelope to its invoking workflow.
- **Done:** Every in-scope task is complete, required verification evidence is recorded, relevant checks pass, and the run reaches its owned shipping handoff, complete return envelope, or explicit blocker.
- **Intent:** Finish the requested feature without renegotiating the plan or transferring canonical composition authority. Workers receive bounded units; the host inspects actual changes and owns authoritative verification and canonical changes.

## Input And Artifact Roots

The **input document** is the invocation input visible in the prompt or conversation. It may be a plan/specification path, a leading `mode:` token and path, a bare work prompt, or blank. Invocation origin does not affect resolution.

Plans live under `<root>/plans/`. Resolve the Jujutsu workspace root with `jj workspace root` only when first composing a repository path. Read `docs_root` from `<workspace-root>/.workflow/config.yaml`; unset means `docs`. A configured value must resolve to a workspace-relative directory inside the workspace, excluding the workspace root, `.jj/`, and `.tmp/`. Use the resolved `<root>` exclusively.

Ordinary checkout configuration resolves `.workflow/config.local.yaml` before `.workflow/config.yaml`; the first active scalar wins, while a present list/map replaces the lower layer. `docs_root` remains team-file-only. Missing files are absent configuration. Preserve `ce-*` skill routing names and provider names.

All transient state belongs under the current Jujutsu workspace root's `.tmp/`. The controller uses `.tmp/work-runs/<run-id>/`; one-off packet and prompt sources use `.tmp/work-inputs/<run-id>/`. Outside a Jujutsu repository, use `<cwd>/.tmp/`. Never default to an OS-global temporary directory or environment-selected temporary root. Atomic publications must reserve a temporary file in the destination directory and replace it in that same directory.

## Workspace Availability

Repository writes require a writable Jujutsu workspace. Confirm `jj workspace root` succeeds and the workspace can be edited. A harness-provided remote work surface is acceptable when it exposes such a workspace. Otherwise report that no writable Jujutsu workspace is available and perform no repository writes.

Bundled references and scripts resolve from this skill's loaded directory. If a required bundled file cannot be resolved, stop before the governed action rather than approximating it.

## Phase 0: Input Triage

**Recovery comes first.** When the request asks to resume, inspect, reap, or clean an existing external run and supplies a safe run id (`^[A-Za-z0-9._-]{1,128}$` with at least one non-period character), load `references/cross-model-execution.md`, operate on that run, and return observed state or a blocker. Do not dispatch, reselect a route, discover another plan, or enter a shipping tail. Ask for a missing run id rather than guessing.

Otherwise parse `mode:return-to-caller` (including legacy caller-owned aliases), then optional `implementation_engine:<compact-json>` and `implementation_run:<safe-id>` carriers in that order, then the plan path. The engine object contains exactly `mode`, `target`, `model`, and `source` as defined in `references/execution-engines.md`. Reject malformed, duplicate, or pathless control data. A run carrier activates exact recovery and forbids route selection, redispatch, reimplementation, repeated completed verification, and a second caller tail.

Before non-recovery code execution, load `references/execution-engines.md` and resolve the implementation engine. With a caller binding, pre-controller discovery remains read-only: inspect metadata, source, configuration, bookmark state, workspace status, and command availability, but do not run commands that can create artifacts before the controller captures its starting change.

Resolve a session-carried plan before blank/bare classification when continuation language and conversation identify exactly one current plan. Ask when several are plausible.

For a path input, classify metadata before body reads:

- `artifact_contract: unified-plan/v1`, `artifact_readiness: implementation-ready`, and `execution: code` proceeds.
- `artifact_readiness: requirements-only` routes to `ce-plan` enrichment.
- `execution: knowledge-work` loads `references/non-code-execution.md`.
- Unknown readiness/execution values block automatic code execution.
- Legacy code plans proceed through the normal lifecycle.

For blank input, inspect `<root>/plans/*.{md,html}` metadata and select only the newest implementation-ready or legacy code plan. A same-basename implementation-ready sibling supersedes a stale requirements-only representation. Otherwise ask for a path or planning enrichment.

For a bare prompt, discover likely files, tests, and local patterns. Trivial work may skip task-list ceremony but not workspace setup or engine resolution. Small/medium work gets a task list. Large or unclear work is clarified or offered `ce-brainstorm`/`ce-plan`; external workers never invent missing scope.

## Phase 1: Prepare

### Read And Bound

For long unified plans, map headings and read metadata, Goal Capsule, Verification Contract, Definition of Done, unit headings, the active unit, and only its cited requirements/decisions. Read legacy plans fully. Treat plan decisions, scope boundaries, execution notes, deferred implementation questions, patterns, and verification as authority. Ask only questions that materially change implementation. Never write progress into the plan.

### Establish Jujutsu State

Before the first edit, preserve work the user did not offer and establish a dedicated feature change:

1. Run `jj status` and inspect `jj diff --summary` to record existing workspace changes.
2. Inspect local/remote bookmarks with `jj bookmark list --all-remotes` and identify the project's default publishing bookmark from active project conventions and remote state. Jujutsu has no active bookmark; do not infer one from `@`.
3. Use Jujutsu's configured remote-fetch capability only when current remote state is required. Use the remote bookmark as parent only when the working-copy ancestry contains no local changes beyond it; otherwise preserve current ancestry.
4. If `@` already contains unrelated work, create a new child with `jj new @`. If `@` is empty and already a dedicated child, continue there. Do not move a bookmark merely to begin work.
5. Record pre-work paths and unpublished changes. Do not rewrite, abandon, describe, publish, or compose them into this run.

When a task must modify a path already changed before the run, ask once in interactive mode whether that existing work may be included in the resulting change or must remain excluded. In Return-to-Caller Mode, block that path without asking.

### Task And Engine Setup

Create outcome-led tasks from implementation units, dependencies, files, execution notes, and verification. Use the harness task capability when available; do not simulate one in chat.

Resolve the engine before any implementation write. Cross-model selection loads `references/cross-model-execution.md`; a successful controller `init` locks the unit to that route until the controller authorizes fallback. Native inline/subagent execution remains the default only after higher-authority routing is absent or exhausted.

Parallelize only units whose dependencies, declared and semantic surfaces, generated/configuration resources, runtime resources, and expected composition cost establish independence. Every concurrent worker requires an isolated workspace. Uncertainty selects serial execution; cap waves at 3-5 workers and stop waves on broad edits, semantic overlap, or repeated collision.

Native workspace isolation belongs to the harness. Do not create Jujutsu workspaces for ordinary native subagents unless the harness explicitly assigns that lifecycle to the caller. The external controller alone creates sibling Jujutsu workspaces under `.tmp/work-runs`.

Every worker receives one bounded unit and inherited authority, the relevant plan excerpts and decisions, expected paths, evidence strategy, and verification. It reports changed paths and observed evidence. Workers do not describe/finalize changes, move bookmarks, publish, open PRs, or integrate another workspace. The orchestrator inspects the actual Jujutsu delta and owns composition.

After each serial unit, inspect `jj diff --summary` and `jj diff`, verify scope, run authoritative checks, record evidence, and finalize the logical change before beginning the next. For isolated parallel results, integrate one in dependency order, revalidate remaining results against the advancing canonical change graph, and retire each worker after its accepted result.

## Phase 2: Execute

Read `references/implementation-loop.md` before the first task and follow it for evidence selection, implementation, verification, and completion stops.

### Incremental Changes

Finalize a Jujutsu change when it is a complete, valuable logical unit with passing relevant checks, before context switches, or before risky experimentation. Keep partial/scaffolding-only work in the current change until its logical unit is complete. Plan units guide boundaries but current implementation evidence decides them.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; do not impose a fixed syntax. Use neutral placeholders in commands:

```bash
jj describe -m "<description derived from local instructions and history>"
jj new
```

Before `jj describe`, prove the current change contains only the logical unit with `jj diff --summary` and `jj diff`. If unrelated pre-work shares `@`, finish only the owned files with `jj commit -m "<description derived from local instructions and history>" <owned-files>`; the unrelated remainder stays in the new working-copy change, so do not run the generic `jj describe` / `jj new` pair afterward. An isolated workspace is also acceptable. Never finalize or rewrite user-owned content.

Resolve conflicts in the change graph before continuing. Use `jj status`, `jj diff`, and Jujutsu conflict materialization; use `jj rebase`, `jj squash`, `jj restore`, or `jj resolve` according to the graph and local intent. Do not translate another VCS's staging workflow into Jujutsu.

At natural phase boundaries, inspect changed files for simplification and invoke `ce-simplify-code` when the substantive code delta meets the repository's normal threshold. Preserve plan structure pins. Continue test discovery, focused checks, applicable UI/Figma verification, and task/evidence tracking throughout.

## Phase 3-4: Quality And Shipping

When implementation completes, load `references/shipping-workflow.md`. Standalone shipping requires either a completed `ce-code-review` receipt or one documented skip/fallback phrase from that reference. Review is read-only; load `references/review-findings-followup.md` to apply eligible fixes, then resolve or durably record residual findings.

## Return-to-Caller Mode

Return implementation and local verification only:

- `status`, `plan_path`, `changed_files`, `u_ids_attempted`, `u_ids_completed`
- `verification_results` and per-unit `verification_evidence`
- engine binding, requested/actual route and model, receipt status, fallback reason
- `run_id`, source kind/digest, unit receipts, plan checkpoint change, blockers, recovery path
- `standalone_shipping_skipped: true`

The caller owns final simplify/review/publish/CI gates. Return exactly once.

## Failure Direction

Stop with preserved evidence when scope, route identity, workspace ownership, Jujutsu graph state, exact restoration, authoritative verification, or review completion cannot be proven. Never abandon or rewrite unknown changes, guess a bookmark target, publish an unoffered change, or silently fall back across an authority boundary.
