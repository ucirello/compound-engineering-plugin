---
name: ce-simplify-code
description: "Simplify settled, recently changed code for clarity, reuse, quality, and efficiency while preserving behavior. Use after implementation and before review; use ce-debug for bugs."
argument-hint: "[blank to simplify current task changes, or describe what to simplify]"
---

Simplify recently changed code for clarity, reuse, quality, and efficiency while preserving exact behavior. Prioritize readable, explicit code over compact code — fewer lines is not the goal.


## Step 1: Identify scope

Resolve the simplification scope in this order:

1. **User-named scope** is authoritative; do not widen it.
2. **Otherwise, in JJ**, resolve the current task's change or bookmark and its verified base, and inspect their difference with `(cd "$workspace_root" && jj diff --from "<verified-base>" --to "<verified-task-tip>")`. An empty `@` above the task tip does not erase that scope. Without a usable base, inspect the working-copy change with `(cd "$workspace_root" && jj diff)`.
3. **Outside JJ or without a diff**, use files the user named or that were edited earlier in the conversation.

Run every JJ command from the target workspace's absolute root (`workspace_root`); returned file paths must remain repository-relative. Use native JJ operations as documented in https://docs.jj-vcs.dev/latest/git-command-table/ and https://docs.jj-vcs.dev/latest/cli-reference/ rather than a Git workspace bridge. Any temporary review files belong under that workspace's local `.tmp/` (or local `.tmp/` outside a JJ repository).

If none of the above produces a non-empty scope, stop and ask the user what to simplify rather than guessing. Use the host's blocking question tool already in the current tool list (match by capability, not by a host-specific name). Presence in the current tool list is proof the tool exists; never call a user-facing question tool to discover whether it exists. If a matching tool is listed but unloaded, use the host's tool-discovery primitive to load that capability — do not search for another host's tool name. Fall back to numbered options on the host's user-visible chat surface only when no such tool is in the list or a real question call errors. Never silently skip the question.

**Preflight.** If the scope has no substantive human-authored code — only documentation, generated or vendored files, dependencies or lockfiles, or mechanical churn — report that there is nothing to simplify and stop without reviewers. For mixed scopes, retain only the code. This check is about the kind of change, never its size: explicit small scopes still run, and any size or cost threshold is the caller's to set.

When the platform's task-tracking capability is available, show the review, apply, and verification outcomes without creating one task per reviewer. Otherwise continue without simulating a task list in chat.

## Step 2: Launch 3 review agents in parallel

Dispatch three generic subagents — code-reuse, code-quality, and efficiency reviewers — via OpenCode's native subagent capability where permitted and available; otherwise run the reviews inline or serially and disclose the substitution. This skill explicitly requests these reviewers: under a host rule allowing user-OR-loaded-skill delegation, no second user request or approval is needed. Respect an unconditional higher-priority prohibition, actual denial, or missing tool; never bypass it with shell dispatch or another harness. For each reviewer, read its prompt asset from this skill's directory and pass the **full file content** as the subagent's prompt, together with the resolved scope (the full diff or file set) so it has complete context:

- `references/personas/code-reuse-reviewer.md`
- `references/personas/code-quality-reviewer.md`
- `references/personas/efficiency-reviewer.md`

Do not paraphrase these rubrics from memory. Read each file and pass it verbatim, or the reviewer loses the rules that keep the pass behavior-preserving.

**Bounded dispatch.** Discover runtime configuration sources for the target project through OpenCode's configuration discovery, inspect their precedence and `experimental.subagent_depth`, and compare the effective limit with the current nesting level before dispatch. The package's shipped depth default is not automatically adopted by a consuming project; permission alone does not prove capacity. Queue the three reviewers and launch only as many as the harness accepts at once. Classify actual errors separately: concurrency/active-agent capacity, nesting depth, permission denial, model-argument rejection, or missing tool. For transient active-agent capacity, leave the reviewer queued and retry after a slot is demonstrably released. Do not retry denied operations or evade nesting limits through another harness. When a dispatch cannot recover through active work, supported release, or an allowed corrected invocation, run that pass inline using the same prompt asset and disclose the substitution and loss of reviewer independence; a parent-coordinator handoff is also allowed when available. Preserve all three rubrics and report any missing coverage rather than claiming completion.

**Agent lifecycle.** Collect terminal outcomes, including failures, before cleanup. Close or release review-owned agents when the harness provides caller-owned cleanup, before refilling slots, advancing stages, or returning. Do not message completed agents with no remaining work. Do not infer released capacity from completion or interruption, or invent cleanup operations.

**Model selection.** Preserve the balanced mid-tier intent and any configured model choices and tiers. Discover exact available references with `opencode.models` when a model override is permitted. Delegation permission does not grant model-selection permission: if the host requires an explicit user model request for overrides, a configured tier or this skill alone does not authorize the optional `model` argument. Omit it and use suitable inherited-model reviewers, disclosing unmet tier or fixed-route intent. Compatibility tier mappings remain Sonnet class in Claude Code and an explicit model/custom-agent selector in Codex; task wording alone never selects a model. Separate same-model reviewers are not cross-model independence. If a caller requires a different-model pass or fixed route that cannot be satisfied, mark that coverage incomplete rather than fully verified.

**Permission mode.** Omit the `mode` parameter on the dispatch call so the user's configured permission settings apply.

## Step 3: Fix issues

Proceed only after all three review outcomes are complete, whether returned by subagents or produced inline. Apply worthwhile findings directly; record false positives and low-value findings as skipped without asking the user.

Inspect beyond the resolved scope when needed to evaluate a finding, but edit only that scope and the import/export lines it needs. For a user-named file or directory scope, those import/export lines must also be inside it; skip any fix that would edit outside the mutation boundary.

Each fix must preserve outputs, errors, side effects, and ordering. If that cannot be established, skip it.

An interface or data shape that existed only in an earlier iteration of the current unshipped scope is not protected behavior once you verify it has no deployed, persisted, public, external, dependent-branch, or in-repo caller outside the resolved scope. Remove that compatibility path only when every required caller update fits the existing mutation boundary; otherwise preserve it.

**Never simplify away a safety check.** Preserve trust-boundary validation, data-loss protection, security checks, and accessibility affordances. Skip any finding that would thin or remove one.

**Honor caller-passed structure pins.** A plan path passed with the structure-pin constraint is context, not scope. Preserve its `session-settled:` Key Technical Decisions, including deliberate duplication or separation.

## Step 4: Verify behavior is preserved

Run project-wide typecheck and lint. Run tests matched to blast radius: scoped tests for local changes, broader tests for shared or wide-reach changes, and the full suite when the runner cannot scope tests.

Report failures with the check name and relevant output. Fix simplification-caused failures or revert the responsible change; never relax assertions, weaken types, or skip tests.

If no test suite, lint, or typecheck is configured, state that explicitly in the summary; do not silently skip verification.

## Step 5: Summarize

Summarize what was already sound and what improved. Report applied counts by reuse, quality, and efficiency; skipped count; and check outcomes. If nothing changed, say so. Do not use net lines removed as the success metric.
