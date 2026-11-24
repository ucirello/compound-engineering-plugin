---
name: ce-doc-review
description: Review requirements, plans, or specs with role-specific lenses. Use when the user wants to improve an existing planning document.
argument-hint: "[mode:non-interactive] [path/to/document.{md,html}]"
---

# Document Review

Help the author finish a sound document they can use to carry out the agreed work. Find problems that would change that work's outcome or materially hinder execution, and resolve them within the authority already given. Judge the document by whether it guides correct work, not by how much detail it contains. Serious consequences warrant attention even when the defect is small. An adequate document needs no changes.

Reviewer personas supply evidence; the judgment is yours. Check their claims against the whole document, project facts, and settled decisions. Correct proven errors that prevent an existing decision from being carried out, within the edit authority and reviewer requirements the synthesis reference states. Return only worthwhile improvements still needing permission, consequential choices or essential information only the user can supply, and useful observations.

**Done when:** every selected reviewer has returned or is named as failed in Coverage, retained findings have a verified consequence for the agreed work, and every authorized correction assigned to Apply has been made and checked. Report that final state through the interactive approval or decision process, or return it as structured text in non-interactive mode.

## Interactive mode rules

**Read `references/modes.md` before anything else.** It defines how the mode is detected, the non-interactive argument contract, and the question-tool rules: match the host's blocking question tool already in the current tool list (never call a user-facing question tool to discover it), pre-load it at the top of the interactive flow if it is listed but unloaded, and fall back to a numbered list only when the harness genuinely lacks one.

Either way, a question that calls for a user decision calls the tool or falls back loudly. Narrating it as plain text is a bug.

## Artifact Root

Resolve `<root>` **only** in the no-path interactive branch, which discovers the most recent plan under `<root>/plans/`. Every other run reads the document at the path it was handed. An absolute-path or non-interactive review can use a readable file outside any repository without depending on a repository root or project configuration.

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.yaml` only (`<workspace-root>` = `jj workspace root`; see the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace)). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before. If the current directory is standalone, use its local `docs` directory.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither the workspace root nor under `.jj/` or `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Phase 1: Get and Analyze Document

**Read `references/document-intake.md` now.** It covers how the document is obtained in each mode, what to do and say when no document is found, and the classification signals.

Two of its rules apply to every later step.

**Verify before any dispatch.** Every resolved path must be readable on disk. If one is not, dispatch **no** personas: reviewers read from the filesystem, so they cannot reach a path that exists only in another revision (issue #925).

**Classify by content, not readiness labels or file path.** A unified artifact with only a Product Contract is **`unified-requirements`**; missing implementation sections are expected. Any implementation planning makes it **`unified-plan`**, including incomplete or blocked planning that needs review. Other artifacts use the legacy `requirements` / `plan` split.

HTML unified artifacts take the same routes. Every fix lands in the document's native format; never insert markdown into HTML. That reference covers ID-bearing items. Pass the classification to each persona in the `{document_type}` slot.

## Phase 2: Announce and Dispatch Personas

Skip dispatch only when the completed-review reuse condition in `references/document-intake.md` passes; continue with that evidence at Phase 3.

**Read `references/persona-selection.md`** for each conditional persona's activation signals and the announcement format. Two of those signals over-activate on plausible evidence: the sensitive-data bound on `security-lens-reviewer`, and the challenge-surface bar on `adversarial-document-reviewer`. Then read **`references/dispatch.md`** for payload variables, slicing, model tiering, and reviewer-failure handling. For a plan, **`references/depth.md`** then decides lite or full review and owns the lite pass.

The team is `coherence-reviewer` and `feasibility-reviewer` always, plus each activated conditional persona. Announce the team briefly before any dispatch, and stay quiet while reviewers run.

This skill explicitly requests generic OpenCode subagents for the selected reviewers. Dispatch with **bounded parallelism** when the actual host policy allows it. Follow `references/dispatch.md` to distinguish delegation permission, model permission and nesting depth, and give each reviewer its `references/personas/<reviewer-name>.md`. Never dispatch a standalone persona as an agent type.

An active-slot capacity rejection is backpressure, not reviewer failure: wait for a slot before retrying. If capacity cannot recover and selected reviewers remain undispatched, collect any started reviews, then stop as incomplete without synthesis, fixes, or a success handoff. For a delegation, depth, tool, or required-model blocker, use only the fallback permitted by `references/dispatch.md` and `references/depth.md`. In all incomplete cases preserve collected outcomes and report which reviewers completed, failed, or could not run, and why.

### Cross-Model Judgment Pass

Run this pass if any of the **conditional judgment trio** was activated: `adversarial-document-reviewer`, `product-lens-reviewer`, `security-lens-reviewer`. This skill explicitly requests the eligible peer subagents as well. Follow `references/cross-model-review.md` for provider attestation, native OpenCode model discovery and dispatch, disclosure before egress, and receipt and coverage handling.

The pass is additive and non-blocking: a failure or timeout leaves the ordinary review running but makes cross-model coverage incomplete and is named in Coverage. The checkout's `cross_model_review_mode` setting is checked first and can skip the pass with a named reason. Filter recipients only when `CROSS_MODEL_PEERS` is set and nonempty — no filter does not imply overriding host or user permission. Never silently change an explicit model or recipient.

## Phases 3-5: Synthesis, Presentation, and Next Action

Settle and account for every dispatched agent before synthesis, including any cross-model `<reviewer-name>-<provider>.json` returns, within the bounds in the dispatch references. Then read `references/synthesis-and-presentation.md`. It defines synthesis, how each finding is routed by confidence and fix class, fix application, the non-interactive result format, and the handoff to the routing question. When promoting cross-model agreement, only an artifact with `independence_verified: true` counts as independent cross-model corroboration.

**Interactive mode only.** Read `references/walkthrough.md` for the routing question, the per-finding walk-through, and the completion report. Read `references/bulk-preview.md` for the preview behind the walk-through's auto-resolve. Load neither before review evidence is complete, whether newly collected or validly reused, and a non-interactive run never loads them at all — it stops at the structured review result.

---

Read or pass only the persona prompts the current review selected, each to its own reviewer. The template and schema the dispatch payload fills:

@./references/subagent-template.md

@./references/findings-schema.json
