---
name: ce-code-review
description: "Review a named diff or PR for bugs, regressions, tests, and standards. Use when asked to review code or when a shipping skill needs a review receipt. Use when asked to apply this review's findings locally. Use ce-resolve-pr-feedback for feedback already left on a PR."
argument-hint: "[mode:agent] [apply:local] [blank to review current branch, or provide PR link]"
---

# Code Review

Help the caller deliver a correct change within the agreed scope. Find defects and improvements whose consequences justify action; judge the code against its intended behavior and project requirements, not a preferred rewrite. Serious defects remain important even when the diff is small. An adequate change needs no findings.

**Done when:** required review and validation are complete, retained findings are supported by the source, and the caller has a clear result with any remaining coverage limits. Apply only when the invocation authorizes it, under the rules below.

## Artifact Root

<!-- ce-docs-root:start -->
**Resolve the artifact root `<root>` before composing any artifact path.**

- **Read** `docs_root` from `<repo-root>/.rocketclaw/config.yaml` only (`<repo-root>` = `jj workspace root`). Do not read it from `config.local.yaml`. Unset -> `<root>` is `docs`, exactly as before.
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the repo and is neither the repo root nor under `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Execution spine

Follow these steps in order; the references supply the detail but never change the order. Read each reference when you enter the step whose own work it governs; a read made before that step does not satisfy it, and a reference you only hand to a leaf is not one you read.

1. Read `references/modes-and-output.md` first. It settles arguments, conflicts, the quick-review short-circuit, the Review depth gate, and what this invocation returns.
2. **Stage 1.** Read `references/scope.md` and resolve the reviewed diff, the scope mode, and the deterministic scope signals. Then apply that Review depth gate before Stage 2. Lite ends the run without the later spine references; lite and focused each run from this context by `references/depth-paths.md`.
3. **Stage 2.** Read `references/intent-and-plan.md`, write the intent summary every reviewer receives, and discover the plan Stage 6 verifies requirements against.
4. **Stage 3.** Read `references/persona-catalog.md` and `references/select-and-route.md`, then select the reviewers the change's risks call for, find the applicable standards files, and decide how the adversarial review will run.
5. **Stage 3d.** When adversarial is selected for a local reviewed tree, start and persist the sanctioned cross-model job that `references/cross-model-review.md` defines, **before any local persona dispatch**. Invoking this skill is itself the authorization for its configured or allowlisted peer route, once you have made the required disclosure of the recipient and of the code that leaves the machine. Do not ask the user to confirm a second time, and do not skip the peer because the user did not repeat that authorization. An explicit user prohibition on external review overrides it, as does a checkout that sets `cross_model_review_mode: off` with no live opt-in; both are resolved before you bind a route. A started peer replaces the local adversarial persona at this stage, and only a real failure to scope, allowlist, reach, authenticate, or start it leaves the local fallback in the roster; a later stage may still restore the local reviewer under the conditions that reference states.
6. **Stage 4.** Read `references/dispatch-reviewers.md`. Dispatch the selected local reviewers as a concurrent native batch collected in this turn, sized to actual capacity. Consume only terminal compact results; tool errors/malformed output are failed reviewer outcomes, launch acknowledgements and progress are not results. Use bounded native collection for asynchronous IDs, cancelling/awaiting unresolved jobs at deadline and preserving their diagnostics. If reliable collection is unavailable, stop launched work, follow peer lifecycle cleanup before the failure result, and never end the turn merely to wait. The native cross-model peer may overlap this batch; no detached shell/harness dispatcher or polled status-file loop.
7. **Stages 5 and 6.** Once every reviewer result is in, write the finish input `references/finish-input.md` defines and stay in that reference: it owns the validator launch and the run-artifact list. Dispatch in sequence the two leaf subagents it names, each seeded with `references/finish-review.md`, which the leaves read from disk and you do not open: a merge leaf that folds in the peer's findings once and merges from the run dir, then, after you launch and collect the validator it selected, a report leaf that renders the report. Neither leaf launches a subagent; you launch every one. Emit the report leaf's return verbatim as this skill's response. Never synthesize directly from raw reviewer artifacts, and never merge or render in the dispatch context. In the multi-agent path, emit only this skill's report: do not also invoke a harness-native findings or reporting tool, which belongs to the quick-review short-circuit alone.

## Operating principles

- **Report-only by default; never push.** A bare `ce-code-review` invocation produces findings and does not apply them. Entering the apply stage requires `apply:local`, or an explicit user request in the invoking prompt to apply or fix this review's findings; a deprecated `mode:autofix` token is neither. `mode:agent` never mutates the tree, even when nested inside a workflow that later applies findings. Never push, open PRs, or file tickets in any mode.
- **No blocking prompts.** Never use `AskUserQuestion`, `request_user_input`, `ask_user`, or other blocking question tools. Infer intent, plan, and scope from explicit tokens, JJ state, PR metadata, and conversation. Note uncertainty in Coverage or the verdict — do not stop to ask.
- **A spawned worker or peer starts a new context and does not continue the parent conversation.**
- **Explicit mutations only.** Never run `gh pr checkout`, `jj edit`, or similar workspace-switch commands during scope selection. Passing a PR number, URL, or bookmark name selects **review scope**, not permission to mutate the working tree. Uncommitted work can only be reviewed from the workspace that holds it; pass `base:` or no target there.

This skill explicitly requests its reviewer subagents. Under a host rule permitting user-OR-loaded-skill requests, that satisfies delegation permission without asking again; unconditional higher prohibitions and actual denials remain binding. Model override and nesting depth are separate gates: omit optional `model` without the user request a host requires, use suitable inherited-model reviewers, and disclose unmet configured tiers/routes. Same-model reviewers are not cross-model proof. Inspect effective depth and classify actual capacity/permission/model/tool errors; never evade a denial or depth limit with shell/another harness. Required independence or fixed-route coverage left unavailable remains incomplete, never fully verified. See `references/cross-model-review.md` and `references/dispatch-reviewers.md`.

Use latest native JJ only, never the Git executable even for read-only history or transport. Run repository commands with cwd the absolute `jj workspace root`; repository-scoped `gh` inherits `GIT_DIR=$(jj git root)` captured there. All scratch belongs under that workspace's `.tmp/`. Native reference: https://docs.jj-vcs.dev/latest/cli-reference/ .
- **Report outcomes, not machinery.** What you show the user is about the review: what is being examined, which coverage is included and the one-line reason for each conditional lens, the independent cross-model pass, and the findings. Name what the user would recognize, such as a PR number, a reviewer's concern, or a peer model. This skill's internal labels, dispatch bookkeeping, and setup narration stay out of user-facing text. Never claim more about the peer than its receipt attests. This governs *what* you surface and suppress, not the wording; use your own voice.
