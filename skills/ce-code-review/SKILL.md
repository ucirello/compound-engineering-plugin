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

- **Read** `docs_root` from `<workspace-root>/.rocketclaw/config.yaml` only (`<workspace-root>` = absolute `jj workspace root`). Do not read `config.local.yaml` for this key. Unset -> `<root>` is `docs`.
- **Validate** a set value: a workspace-relative directory whose real, symlink-resolved path stays inside the workspace and is neither its root nor under `.jj/` or `.git/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Execution spine

Follow these steps in order; the references supply the detail but never change the order. Read each reference when you enter the step whose own work it governs; a read made before that step does not satisfy it, and a reference you only hand to a leaf is not one you read.

1. Read `references/modes-and-output.md` first. It settles arguments, conflicts, the quick-review short-circuit, the Review depth gate, and what this invocation returns.
2. **Stage 1.** Read `references/scope.md` and resolve the reviewed diff, the scope mode, and the deterministic scope signals. Then apply that Review depth gate before Stage 2. Lite ends the run without the later spine references; lite and focused each run from this context by `references/depth-paths.md`.
3. **Stage 2.** Read `references/intent-and-plan.md`, write the intent summary every reviewer receives, and discover the plan Stage 6 verifies requirements against.
4. **Stage 3.** Read `references/persona-catalog.md` and `references/select-and-route.md`, then select the reviewers the change's risks call for, find the applicable standards files, and decide how the adversarial review will run.
5. **Stage 3d.** When adversarial is selected for a local reviewed tree, start the sanctioned native cross-model subagent per `references/cross-model-review.md` before local persona dispatch. Invoking this skill authorizes a sanctioned route after the required disclosure; honor checkout opt-outs, user prohibitions and actual host permissions. A started peer reserves the lens; only the reference's failure/recovery rules can restore its local fallback.
6. **Stage 4.** Read `references/dispatch-reviewers.md`. Dispatch the selected native reviewers as a concurrent batch sized to the host cap and collected within the stated bound in this turn. A valid return is consumed; a terminal error or malformed return is a failed reviewer. A launch acknowledgement is not a result. On collection failure stop outstanding work, including any peer, under the owning reference. Do not detach review into a polled job.
7. **Stages 5 and 6.** Once every reviewer result is in, write the finish input `references/finish-input.md` defines and stay in that reference: it owns the validator launch and the run-artifact list. Dispatch in sequence the two leaf subagents it names, each seeded with its own finish reference, which the leaves read from disk and you do not open: a merge leaf (`references/finish-merge.md`) that folds in the peer's findings once and merges from the run dir, then, after you launch and collect the validator it selected, a report leaf (`references/finish-report.md`) that renders the report. Neither leaf launches a subagent; you launch every one. Emit the report leaf's return verbatim as this skill's response. Never synthesize directly from raw reviewer artifacts, and never merge or render in the dispatch context.

## Operating principles

- **Report-only by default; never push.** A bare `ce-code-review` invocation produces findings and does not apply them. Entering the apply stage requires `apply:local`, or an explicit user request in the invoking prompt to apply or fix this review's findings; a deprecated `mode:autofix` token is neither. `mode:agent` never mutates the tree, even when nested inside a workflow that later applies findings. Never push, open PRs, or file tickets in any mode.
- **No blocking prompts.** Never use `AskUserQuestion`, `request_user_input`, `ask_user`, or other blocking question tools. Infer intent, plan, and scope from explicit tokens, JJ state, PR metadata, and conversation. Note uncertainty in Coverage or the verdict — do not stop to ask.
- **A spawned worker or peer starts a new context and does not continue the parent conversation.**
- **Explicit mutations only.** Never switch revisions or edit a different working copy to carry out a review (including `jj edit`, `jj new`, and PR checkout). A PR, URL, or bookmark selects **review scope**, not mutation. The caller reviews local working-copy changes from the workspace that holds them.
- **Native delegation.** This skill explicitly requests its named reviewers, peer, checks and finish leaves. Before the first launch use `references/subagent-model.md` to distinguish delegation permission, model-override permission and effective nesting depth. No other harness or shell launch is a fallback for blocked native delegation.
- **Report outcomes, not machinery.** What you show the user is about the review: what is being examined, which coverage is included and the one-line reason for each conditional lens, the independent cross-model pass, and the findings. Name what the user would recognize, such as a PR number, a reviewer's concern, or a peer model. This skill's internal labels, dispatch bookkeeping, and setup narration stay out of user-facing text. Never claim more about the peer than its receipt attests. This governs *what* you surface and suppress, not the wording; use your own voice.
