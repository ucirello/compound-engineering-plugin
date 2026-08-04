# Execution Engines

`ce-work` can implement an implementation-ready unified plan with one of three engines. The engine decides how implementation runs; it never changes who owns the shipping tail.

Engine selection applies only to code execution. Knowledge-work and legacy plans keep the inline/subagent flow in `SKILL.md`.

## Step 1: Probe Provider Capability

An engine is usable only when the provider exposes a callable primitive for it. Do not assume one exists from its name.

| Engine | Usable when | Provider mapping |
|---|---|---|
| **Inline / subagent** | Always. The orchestrator runs units inline or dispatches through the provider's subagent primitive. | Claude Code `Agent` may use provider-managed Git worktree isolation; Codex may use a fork/upload worker; Cursor may use native isolated candidates or a shared task; Pi may use a shared subagent or an installed isolated-workspace extension. Integrate through the provider-specific JJ bridge in `SKILL.md`, not standalone Git. |
| **Goal-mode** | The provider exposes a callable goal tool, such as Codex `create_goal`, with a terminal-status operation. | A user-only `/goal` command is not callable; emit a copyable prompt or use inline/subagents when no tool exists. |
| **Dynamic-workflow** | The provider exposes a callable dynamic-workflow primitive that returns structured results and blockers without mid-run user decisions. | A user-prompt-only surface is not callable; emit a copyable prompt or use inline/subagents. |

Probe for the callable tool; do not infer capability from a command's existence. A callable goal activates the current session rather than starting a background worker. The working session, not this skill, records terminal goal status.

## Step 2: Pick by Plan Shape

| Plan shape | Engine | Why |
|---|---|---|
| Sequential or modest U-ID decomposition; units share files or depend on each other | **Inline / subagent** (default), or goal-mode when callable | The Definition of Done already supplies the completion condition. |
| Many independent U-IDs with disjoint ownership; codebase-wide sweep; large migration; adversarial cross-checking | **Dynamic-workflow** when callable; otherwise parallel subagents | The workflow coordinates branching and intermediate worker state. |
| Provider exposes no callable goal/workflow primitive | **Inline / subagent** | Preserve heading-scan, Definition-of-Done, and U-ID discipline without unavailable features. |

Recommend exactly one path. Present a non-default engine only when plan shape warrants it.

## Step 3: Run the Engine

### Inline / Subagent

Follow the dispatch strategy and provider bridge in `SKILL.md` Phase 1 Step 4, then the Phase 2 loop. Preserve provider-managed isolation only where operationally unavoidable. Git worktree refs enter JJ through parent-side `jj git import`; uploaded or applied results are snapshotted by JJ; returned JJ changes integrate directly. `ce-work` owns sequencing, verification, change ordering, and cleanup after recoverability.

### Goal-Mode and Dynamic-Workflow

With a callable goal tool, call it with the objective below minus the leading `/goal`. The current session works toward it; there is no separate worker or envelope to await. Use it only in standalone mode. Return-to-caller mode must run inline/subagents so control returns to the caller.

Without a callable tool:

- **Standalone interactive:** print the copyable prompt, then continue inline/subagents if the user does not paste it. Do not stall.
- **Return-to-caller:** do not emit a copyable prompt. Run inline/subagents or return a blocker.

The engine must not open a pull request, finalize the session, or bypass the owning workflow's gates.

Copyable goal-mode prompt, substituting only the literal plan path:

```text
/goal Implement <plan-path> to its Definition of Done.

Use the plan as authority. Scan headings, read the Goal Capsule, then work units in dependency order, reading each active unit and its cited requirements and decisions. Run the Verification Contract and satisfy each unit's test scenarios. Track progress outside the plan file.

Run applicable simplification, review, and verification gates. Follow the plan's pull-request/landing strategy when defined; active project instructions and user preferences override it. Surface genuine blockers instead of guessing.

Done when every non-deferrable unit has observed verification, required checks passed or are documented as inapplicable, applicable quality gates ran or were skipped with reason, dead-end code is absent from the JJ diff, and no progress status was written into the plan.
```

Copyable dynamic-workflow prompt:

```text
Execute <plan-path> as an end-to-end dynamic workflow. Use the Implementation Units and Definition of Done, parallelize only independent units, run simplification/review/verification in the workflow tail, and return changed files, completed units, verification, residual findings, and blockers.
```

Keep emitted prompts under 4,000 characters and substitute the literal plan path.

## Step 4: Resume the Correct Tail

After implementation, inspect `jj status`, `jj log`, and the stack diff.

| Mode | Tail |
|---|---|
| **Standalone** | Resume Phase 3-4 quality gates, review, JJ finalization, and handoff in `references/shipping-workflow.md`. |
| **Return-to-caller** | Return implementation and local-verification evidence with `standalone_shipping_skipped: true`; the caller owns simplify/review/pull-request/CI work. |

For long runs, coherent described JJ changes and optional progress artifacts under `<workspace-root>/.tmp/rocketclaw/ce-work/<run-id>/` provide visibility. Resolve `<workspace-root>` with `jj workspace root`, falling back to `pwd -P`. Never write progress into the plan body.

Whenever this workflow composes, edits, validates, or recommends a JJ description, active project instructions and description syntax inferred at runtime from `jj log` always win. Use `<description-composed-from-runtime-conventions>` as the neutral placeholder. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Preserve every semantic content requirement stated by this workflow while adapting syntax to runtime conventions. Apply compatible Go guidance only for quality, clarity, and structure; do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.
