# Input Triage

Read this before classifying the invocation, discovering a plan, or deciding whether normal implementation may begin. It covers resolving the source, parsing the mode token and its optional carriers, recognizing a recovery request, classifying plan readiness, discovering the latest plan, and deciding how a bare prompt enters. Return to the main `SKILL.md` flow: the resolved source, the execution class, which side runs the shipping steps (this skill standalone, or the caller), and any typed engine or recovery binding. Do not perform implementation writes here.

## Input Document

The **input document** for this run is the input this skill was invoked with — present in the current prompt or conversation, whether the user provided it directly or a calling skill passed it (e.g. `lfg` in `mode:pipeline`, which passes a plan path). It may be a plan or spec path, a `mode:` token followed by a path, or a bare work prompt. This reference calls it `<input_document>`; if nothing was provided, treat `<input_document>` as blank.

Invocation origin is not observable or relevant: apply the same source-resolution rules whether the user invoked `ce-work` explicitly or the host selected it automatically.

## Artifact Root

This skill discovers plans under `<root>/plans/`. Resolve `<root>` when you first compose a `<root>/` path (per the block below), never before you need it. A write to `<root>/...` and a read of `<root>/solutions/` both count as composing a `<root>/` path, so either one triggers resolution; only a run that touches no `<root>/` path at all -- a scratch-only or no-repo flow -- skips it; pass the resolved path to any subagent, not the config.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.rocketclaw/config.yaml` only (`<repo-root>` is the absolute `jj workspace root` obtained from the candidate directory). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the repo and is neither the repo root nor under `.git/` or `.jj/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Recovery and Control Grammar

**Recovery activation comes first.** Recognize semantic requests to resume/inspect/reap/clean an existing implementation run before normal classification. Validate its supplied id with `^[A-Za-z0-9._-]{1,128}$` and at least one non-period character. Read `cross-model-execution.md` and reconcile the native run record using that authoritative id. No fresh dispatch, route selection, latest-plan discovery, reimplementation or shipping tail. Completed recovery is read-only: report stored unit/source-wide receipts without rerunning test/build/format/install/generation. Missing id requires clarification, never a guessed run.

**Otherwise, parse a leading mode token.** If `<input_document>` begins with `mode:return-to-caller` (or the legacy aliases `mode:caller-owned-tail` / `caller:lfg`), strip that token before anything else and enter **Return-to-Caller Mode**: implement and locally verify only, then return the structured summary defined in `references/return-to-caller.md` instead of running the standalone shipping tail (final simplify, review, PR, CI). Before the plan path, accept up to two optional carriers (extra tokens that carry a binding or a run id) in this fixed order: first one compact JSON object prefixed exactly `implementation_engine:`, then one run id prefixed exactly `implementation_run:`. Fully validate and normalize both before any workspace action. The engine object must contain exactly four fields: `mode` is `prefer` or `require`; `target` is `codex`, `claude`, `grok`, `cursor`, `composer`, or `opencode`; `model` is a string pin or `null`; and `source` is a non-empty caller-visible provenance string. The run carrier is accepted only for return-to-caller recovery and must satisfy the safe-id contract above. Reject malformed JSON, missing/extra fields, invalid field types or values, an unsafe run id, an out-of-order carrier, or a duplicate carrier. The entire remaining string is the plan path. A mode token or carrier with no following path is an error; report it instead of treating control data as a bare prompt. Without either optional carrier, the original `mode:return-to-caller <plan-path>` form is unchanged and standing configuration remains eligible.

When `implementation_run:<safe-id>` is present, recovery wins: read `references/cross-model-execution.md`, reconcile that exact native run record, and return the normal Return-to-Caller summary. Preserve supplied engine binding. No different route, redispatch, reimplementation, completed-check rerun or caller shipping tail.

With a valid engine binding, discovery before the durable ready record is read-only: metadata, source, config, bookmarks, status and tool availability. No baseline/test/build/format/install/generation can create ignored/untracked artifacts before the canonical inventory. A necessary non-read probe requires artifact suppression and proof of unchanged canonical tracked tree and inventory; otherwise return a route blocker.

**Resolve a session-carried plan before blank or bare-prompt classification.** When the current request is continuation language such as "proceed" and the conversation identifies exactly one current plan for this work — a plan/spec path or an in-conversation brief from `ce-plan` — that was authored, selected, or accepted, treat it as `<input_document>`. A brief enters as a bare prompt with `source_kind: prompt`. If multiple session plans are plausible, ask which one; do not choose by recency. Do not replace a concrete new work request with an unrelated earlier plan. This rule depends only on visible conversation state, never on whether invocation was explicit or automatic.

## Source Classification

Determine how to proceed based on what was provided in `<input_document>` after any mode token is stripped.

**Plan document** (input is a file path to an existing plan or specification): resolve the canonical document before classification. Follow an explicit supersession notice to its canonical path only when the linked document's contents establish that it represents the same requested work; otherwise stop for clarification. Then inspect its contents, using a section map for long documents. Metadata describes the artifact; an old readiness label is not execution authority.

- A non-code deliverable, including `execution: knowledge-work`, follows `references/non-code-execution.md` instead of the code workflow.
- A Product Contract without enough implementation direction needs `ce-plan` enrichment. An approach-only or answer-seeking document is not an implementation plan.
- Proceed only when the intended code work, scope, and verification are sufficiently defined and no launch-blocking question remains. For unified plans, inspect the Product Contract, Planning Contract, Implementation Units, Verification Contract, and Definition of Done. Judge legacy plans and saved briefs by the same sufficiency condition without requiring unified headings.
- Verify material existing prerequisites for the active work against the repository before implementation. If the plan depends on something that is unavailable or contradicts current code, resolve it within the agreed scope or return the blocker; do not invent a substitute that changes the contract. Explicitly planned additions need not exist yet. Deferred implementation details remain the executor's work.

Then continue using the reader strategy in `references/work-intake.md`. Do not require a metadata repair before working from an otherwise sufficient plan.

**Blank invocation latest-plan discovery:** when `<input_document>` is blank, glob `<root>/plans/*.md` and `<root>/plans/*.html` and inspect the newest candidate's contents using the same canonical resolution and classification. If same-basename format siblings have no clear canonical path, ask which to use. Do not silently skip a newer incomplete or non-code artifact to execute an older plan; ask for an explicit path or `ce-plan` enrichment.

**Bare prompt** (input is a description of work, not a file path): read `references/work-intake.md` and follow its scan-and-route steps. Trivial work (1-2 files, no behavioral change) must skip only the task list, then pass the mandatory engine-before-write gate in `SKILL.md` (resolve the engine before the first write) before implementing directly, with no unit execution loop. Do not treat an unclear prompt as permission to hand work to an external worker. If discovery cannot state a concrete goal, bounded scope, and authoritative verification, clarify or route to `ce-plan` before sending any work to a cross-model worker.
