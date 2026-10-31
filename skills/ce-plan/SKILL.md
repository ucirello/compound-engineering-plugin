---
name: ce-plan
description: "Create structured plans for multi-step work, including software and non-software tasks. Use when asked to plan, break down implementation, plan from requirements, or deepen an existing plan; prefer ce-brainstorm for exploratory framing."
argument-hint: "[optional: feature description, requirements doc path, plan path to deepen, or any task to plan] [output:html]"
---

# Create Technical Plan

### Quoted Go source guidance (not a mandatory repository template)

The following verbatim excerpts are from https://go.dev/wiki/CommitMessage. Repository-local syntax ALWAYS wins; the Go illustration does not prescribe message syntax here. Keep the runtime full-guide/history comparison below.

> Commit messages, also known as CL (changelist) descriptions, should be formatted per https://go.dev/doc/contribute#commit_messages. For example,
>
> ```text
> net/http: handle foo when bar
>
> [longer description here in the body]
>
> Fixes #12345
> ```
>
> Notably, for the subject (the first line of description):
>
> - the name of the package affected by the change goes before the colon
> - the part after the colon uses the verb tense + phrase that completes the blank in, “this change modifies Go to **___**”
> - the verb after the colon is lowercase
> - there is no trailing period
> - it should be kept as short as possible (many git viewing tools prefer under ~72 characters, though Go isn’t super strict about this).
>
> For the body (the rest of the description):
>
> - the text should be wrapped to ~72 characters (to appease git viewing tools, mainly), unless you really need longer lines (e.g. for ASCII art, tables, or long links).
> - the Fixes line goes after the body with a blank newline separating the two. (It is acceptable but not required to use a trailing period, such as Fixes #12345.).
> - there is no Markdown in the commit message.
> - we **do not** use `Signed-off-by` lines. Don’t add them. Our Gerrit server & GitHub bots enforce CLA compliance instead.
> - similarly, we do not use Co-authored-by and Assisted-by lines. Don’t add them.
> - when referencing CLs, prefer saying “CL nnn” or using a go.dev/cl/nnn shortlink over a direct Gerrit URL or git hash, since that’s more future-proof.
> - when moving code between repos, include the CL, repository name, and git hash that it was moved from/to, so it is easier to trace history/blame.

**Outcome:** a plan for carrying out and checking the agreed work while preserving its outcome and constraints. Resolve technical choices from evidence; leave adequate instructions unchanged. `ce-brainstorm` defines **WHAT**, `ce-plan` plans **HOW**, and `ce-work` executes. A prior brainstorm is optional.

**An explicit invocation always produces a plan.** Never classify a direct invocation as "not a planning task" and route out. It may select any output contract below, and the smallest valid plan is a few sentences in chat.

**Research, decide, and write the plan — never implement.** Do not write production code, run tests, or learn from execution-time results. Directional pseudo-code and grammar sketches may communicate design; changing code to see what happens belongs in `ce-work`.

## Mandatory Completion Contract

A run is complete when its output contract's done condition is met. Every normal interactive branch that produces a plan artifact or checkpoint is incomplete until the user has been asked what to do next. A request that already authorizes the next action is that answer. For a Durable software implementation-plan run that continues past the resume check, that means the Phase 5.4 menu has been presented and the selected action has actually fired. For Direct, the change stated and the handoff offered; for a Chat brief, the brief and its one-line save-or-`ce-work` offer in chat. Neither presents the Phase 5.4 menu. Non-software plans and approach-level plans end with the handoff their reference workflow defines. A run that only answers a question may end after the answer unless its reference requires a save or share step.

Writing the file, checking confidence, and running or explicitly skipping `ce-doc-review` are intermediate milestones. In pipeline mode, the run is complete only when the plan, the confidence check, and the non-interactive document-review state have been returned to the caller, which decides what happens next.

## Interaction Method

Ask one question at a time through the host's blocking question tool already in the current tool list. Match by capability; never probe a user-facing tool to discover it. If none is listed or a real question call errors, render numbered choices in chat; never silently skip a required question. If no feature description was supplied, ask what to plan and wait.

## Output Contract

Decide which output contract applies at the start of scoping (Phase 0.6), before choosing depth and before the scoping synthesis. It applies only when no resume route (Phase 0.1) fired and the source check (Phase 0.2) found no upstream artifact. Ground it with bounded inline reads of what the request names, without dispatching a subagent. Select one:

- **Direct** — the work can be stated, done, and verified in one pass with no decision the user would weigh. State the change in a few sentences and offer the handoff to `ce-work` or the user; execution starts only with implementation authority, as `references/output-contracts.md` defines.
- **Chat brief** — bounded work with at most one decision the user would weigh and no risk surface. Deliver it in chat and stop.
- **Durable** — everything else. Continue the workflow below.

`references/output-contracts.md` defines Direct and Chat brief; read it when either is selected. When the tier is still uncertain after those reads, take the heavier one. If a read surfaces a decision the user would weigh, a risk surface, or multi-pass verification, move to the heavier tier before emitting anything. Durable regardless of size: a run with no synchronous user to act on chat this turn (pipeline, headless, goal- or scheduler-driven), a request whose wording asks for a plan, a plan file, or an output format, a request that continues an existing plan's item, and a risk surface — authentication, payments, migrations, external contracts.

## Workflow

Phases run in order unless a reference routes out or short-circuits. Read a phase's required reference in full when you enter that phase; a read made before that phase does not satisfy it, and a reference named for the final steps is read again at its step even when already in context. If a required reference cannot be read, stop before the action it governs and report the blocker and recovery path; never reconstruct the missing rules from memory. In pipeline mode, every required-reference failure returns `status: blocked`, `phase`, `blocker`, and `recovery_path`; include `artifact_path` and preserve the artifact when one exists. Report blocked even when an artifact exists.

### Phase 0: Output, Resume, and Scope

1. **Output first.** Read `references/output-mode.md` before interpreting any phase. It defines token parsing, output and confirmation precedence, renderer selection, artifact location, and when a repository may be resolved.
2. **Resume, deepen, approach, and domain.** Read `references/resume.md` before acting. It defines resuming an existing plan, enriching a requirements-only plan, deepening, approach-level planning, and the software/non-software split. Follow any terminal route it selects; otherwise continue.
3. **Source and scope.** Read `references/intake.md` before Phase 0.2 and follow it through Phase 0.7. It defines finding and preserving the upstream artifact, routing out to bootstrap work, blocking questions, depth, named resources, and the scoping synthesis; the Output Contract decision above happens inside it. Do not pass a decision point that has not resolved.

### Phases 1-4: Research and Compose

4. Read `references/research.md` before gathering context.
5. Read `references/structure.md` before resolving questions or structuring the plan.
6. Compose from `references/plan-sections.md` plus the format-rendering reference selected by `output-mode.md`.

### Phase 5: Review, Write, Deepen, and Hand Off

7. Read `references/final-review.md` before the pre-write review; it defines Phase 5.1 through 5.3.2. On an interactive run from a brainstorm, the user sees the Phase 5.1.5 scoping synthesis in chat before the write: a confirmation to wait on, or its one-line auto-proceed announcement.
8. **Model elevation.** Immediately before authoring, read `references/reasoning-elevation.md`, resolve the choice at this boundary, and follow it. Do not author until activation resolution has completed and any selected native dispatch or transparent fallback has settled.

## Native delegation and message standards

All explicit research, reviewer, deepening, and elevation dispatch in this skill uses OpenCode native subagents. Under user-OR-applicable-skill policy this skill authorizes those calls without second approval; unconditional prohibitions and tool denials win. Resolve configured tiers through `opencode.models`. Model override permission is separate from delegation permission: if an override requires an explicit user model request and none exists, omit the optional model argument, inherit a suitable model, and disclose unmet configured tier. Same-model work is not independent cross-model coverage. Inspect effective depth through supported config discovery and classify actual permission, model rejection, missing tool, depth, and capacity errors separately. Never evade restrictions via shell/another harness; use parent fallback only where the specific contract permits and mark missing required coverage incomplete. Apply `references/reasoning-elevation.md` setup guidance for deep delegation.

Whenever recommending, composing, or validating a commit/change message, use this strongest instruction: "Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `jj log`, compose commit messages adherent to the present standards." Read the full guide and compare several recent subjects AND bodies with `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\\n"'`, with cwd set to the absolute target workspace root and the head verified for this task. Repository-local syntax always wins: examine prefixes/packages, casing, tense, subject/body separation, wrapping, and issue references. Without history use explicit instructions and compatible Go guidance, never invented precedent. Resulting messages contain no Markdown or Co-authored-by/Assisted-by attribution; compatible local rules win. Do not prescribe a fixed message template.
9. In pipeline mode, evidence that invalidates a decision settled earlier in the session stops the write. Return the exact token `settled-decision-invalidated`, the decision, and the reason; do not resolve it silently.
10. Write the plan before presenting options, then complete the confidence path `final-review.md` defines.

**STOP. Read `references/plan-handoff.md` immediately before Phase 5.3.8 and 5.4** (document review and the handoff menu). Document review is mandatory for a Durable plan and the default is non-interactive (`mode:non-interactive`). In interactive software runs, ask exactly: "Plan ready at `<absolute path to plan>`. What would you like to do next?" Present its menu and wait. If the selection arrives after a user turn, reload `references/plan-handoff.md` before acting. Rendering the menu, receiving a selection, or announcing a route is not completion; execute the selected action.
