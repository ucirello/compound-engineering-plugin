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
- **Validate** a set value: a repo-relative directory whose real, symlink-resolved path stays inside the repo and is neither the repo root nor under `.git/` or `.jj/`. Otherwise stop with an error naming `docs_root` and the value -- never fall back to `docs`.
- **Use** `<root>` as the sole artifact location: create it if absent, compose each path as `<root>/<subdir>` with this skill's own subdirectory, and never also read `docs`.
<!-- ce-docs-root:end -->

## Execution spine

Follow these steps in order; the references supply the detail but never change the order. Read each reference when you enter the step whose own work it governs; a read made before that step does not satisfy it, and a reference you only hand to a leaf is not one you read.

1. Read `references/modes-and-output.md` first. It settles arguments, conflicts, the quick-review short-circuit, the Review depth gate, and what this invocation returns.
2. **Stage 1.** Read `references/scope.md` and resolve the reviewed diff, the scope mode, and the deterministic scope signals. Then apply that Review depth gate before Stage 2. Lite ends the run without the later spine references; lite and focused each run from this context by `references/depth-paths.md`.
3. **Stage 2.** Read `references/intent-and-plan.md`, write the intent summary every reviewer receives, and discover the plan Stage 6 verifies requirements against.
4. **Stage 3.** Read `references/persona-catalog.md` and `references/select-and-route.md`, then select the reviewers the change's risks call for, find the applicable standards files, and decide how the adversarial review will run.
5. **Stage 3d.** Read `references/subagent-model.md` and, when adversarial is selected locally, `references/cross-model-review.md`; resolve the native peer before local dispatch. This skill explicitly requests reviewers, satisfying a user-OR-skill rule without redundant approval, but never overriding an unconditional prohibition. Model selection and nesting depth are separate: omit forbidden model arguments and use a suitable inherited reviewer; accurately classify actual depth/denial/model/capacity/tool errors. Required unavailable cross-model independence or a fixed route is incomplete, not fully verified. Honor egress restrictions, explicit opt-outs and `cross_model_review_mode: off` without live opt-in. Disclose the allowed recipient/code transfer without another confirmation; collect terminal evidence before claiming coverage. Avoid duplicate peer/local adversarial reads and apply bounded native recovery only as the references permit.
6. **Stage 4.** Read `references/dispatch-reviewers.md`. Dispatch the selected native reviewers concurrently within the host's cap and collect every launch's terminal result within this turn using bounded native collection. Launch acknowledgements and progress are not results. Record malformed returns and tool failures; stop/release uncollectable owned work, including peers, before returning failure. No detached CLI dispatch, polling or scheduled wakeups. Native peer collection may overlap this batch.
7. **Stages 5 and 6.** After collection write `references/finish-input.md`'s disk handoff. Normally dispatch its merge leaf, collect the independent validator batch it selects, then dispatch the report leaf; leaves launch no subagents and the report returns verbatim. Apply the same permission/model/depth gates to each launch. When permitted parent merge/report fallback is necessary, read the owned finish reference and use the same handoff/mechanical contracts, never inventing independent review or validation. Unavailable required validators remain degraded gates and required cross-model coverage remains incomplete.

## Operating principles

- **Report-only by default; never push.** A bare `ce-code-review` invocation produces findings and does not apply them. Entering the apply stage requires `apply:local`, or an explicit user request in the invoking prompt to apply or fix this review's findings; a deprecated `mode:autofix` token is neither. `mode:agent` never mutates the tree, even when nested inside a workflow that later applies findings. Never push, open PRs, or file tickets in any mode.
- **No blocking prompts.** Never use `AskUserQuestion`, `request_user_input`, `ask_user`, or other blocking question tools. Infer intent, plan, and scope from explicit tokens, git state, PR metadata, and conversation. Note uncertainty in Coverage or the verdict — do not stop to ask.
- **A spawned worker or peer starts a new context and does not continue the parent conversation.**
- **Explicit mutations only.** Never run `gh pr checkout`, `git checkout`, `git switch`, or similar branch-switch commands. Passing a PR number, URL, or branch name selects **review scope**, not permission to mutate the working tree. Uncommitted work can only be reviewed from the checkout that holds it, so to review it on a feature branch, stay on that branch (or check it out yourself) and pass `base:` or no target.
- **Report outcomes, not machinery.** What you show the user is about the review: what is being examined, which coverage is included and the one-line reason for each conditional lens, the independent cross-model pass, and the findings. Name what the user would recognize, such as a PR number, a reviewer's concern, or a peer model. This skill's internal labels, dispatch bookkeeping, and setup narration stay out of user-facing text. Never claim more about the peer than its receipt attests. This governs *what* you surface and suppress, not the wording; use your own voice.
