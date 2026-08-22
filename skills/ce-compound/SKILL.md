---
name: ce-compound
description: Document a recently solved problem as a durable repo learning. Use when capturing a learning after work.
argument-hint: "[optional: brief context] [mode:non-interactive] [depth:lightweight|full]"
---

# /ce-compound

**Outcome:** one solved problem is written as a durable learning under `.context/solutions/`, grounded against the current tree, discoverable by the next agent.

**Done:** the doc is written or updated, its frontmatter and claims validated, vocabulary capture recorded even when nothing qualified, and the mode's completion report emitted.

**One learning per run.** A session that produced several gets several sequential runs, never one batched run - `references/research.md` carries what batching breaks.

## Setup

Run this once at the start of this invocation, before any subagent dispatch, and follow the directives it prints except where this skill's interaction rules override them. Run the fence exactly as written as its own command; do not pipe, filter, truncate, or batch it. Its output opens with `=== skill context` and ends with `ROCKETCLAW_CONTEXT_END`; if only one appears, rerun the fence verbatim once. Otherwise do not rerun it in this invocation. If no Node runtime is available, proceed unchanged.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
NODE="$(for c in node nodejs; do command -v "$c" >/dev/null 2>&1 && "$c" -e '' >/dev/null 2>&1 && { echo "$c"; break; }; done)";
if [ -n "$NODE" ]; then
"$NODE" "$SKILL_DIR/scripts/context.mjs" || echo "context script failed; continue with the skill's normal behavior";
else
echo "no Node runtime; continue with the skill's normal behavior";
fi
```

## Preconditions

Document a problem that is solved, verified working, and non-trivial. These are advisory: judge them from the session rather than asking about them. When the session plainly holds no such problem, write nothing and report why.

`ce-compound` is not a `.context/CONCEPTS.md` bootstrap tool - it seeds the learning's own area as a side effect, never the whole workspace. Send a standalone request to create or bootstrap that file to `ce-compound-refresh`, then exit.

## Mode Detection

```bash
/ce-compound [brief context]
/ce-compound mode:non-interactive depth:lightweight [context]
/ce-compound mode:non-interactive depth:full [context]
```

Enter non-interactive mode when the arguments contain `mode:non-interactive` or deprecated `mode:headless`, or when the invocation makes unattended intent unmistakable. Bare "automatically" or "auto-run" does not suppress prompts. Strip `mode:` and `depth:` flags before treating the remainder as context. Once detected, non-interactive mode applies for the entire run.

Depth is a non-interactive-only selector, with at most one token. `depth:lightweight` routes to Lightweight Mode. `depth:full` or no token enters Full Mode, including its automatic session-history probe. Unknown, duplicate, or interactive-only depth tokens produce the non-interactive failure report and end with `Documentation skipped`.

**Non-interactive mode asks nothing.** Every exit ends with `Documentation complete`, or `Documentation skipped` plus the reason when no doc was written. Interactive mode asks only for Discoverability Check consent and, when several stale docs are involved, which refresh to run.

## Workspace Paths

Resolve `<jj-root>` with `jj root` when first needed. Durable configuration lives under `<jj-root>/.rocketclaw/`; durable learning artifacts live under `<jj-root>/.context/`. The learning path is `.context/solutions/<category>/<filename>.md`, and vocabulary lives at `.context/CONCEPTS.md`.

All invocation-owned scratch stays under `<jj-root>/.tmp/rocketclaw/ce-compound/<run-id>/`. If no Jujutsu workspace is available, use `./.tmp/rocketclaw/ce-compound/<run-id>/`. Never use host-wide temporary storage.

## Change Descriptions

Whenever this workflow composes or recommends a Jujutsu change description, inspect local descriptions first with `jj log -r ::@`; broaden to `jj log -r 'all()'` only when local ancestry does not reveal a standard. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe imperative mood, casing, punctuation, line wrapping, subject/body shape, or any fixed syntax.

## Write Boundary

**Only the orchestrator writes product files.** Phase 1 subagents write to per-run scratch only and never touch `.context/`, project instruction files, or another tracked path.

The orchestrator writes one learning under `.context/solutions/`, plus two maintenance side effects owned by their steps: `.context/CONCEPTS.md` during vocabulary capture and, only in interactive Full mode after consent, a small discoverability line in a project instruction file. An instruction file is edited only, never created. Other learning-doc edits belong to `ce-compound-refresh`.

## Choosing the Path

**Read `references/modes.md` before step 1.** Interactive runs choose their own depth. Default to **Full**; choose **Lightweight** only under real context pressure or when the fix is too trivial for cross-referencing to add value. Non-interactive runs use Mode Detection's depth.

Lightweight mode skips session history. Non-interactive Full runs the same automatic probe because it asks nothing.

## Full Mode

Run these in order. Each reference is required at the named step.

1. **Research** - read `references/research.md`.
2. **Session history** - read `references/session-history.md`, starting it after the parallel block so they overlap. Its result is the final Phase 1 input; continue directly to assembly.
3. **Assembly and write** - wait for every Phase 1 input, then read `references/assembly.md`.
4. **Refresh check and discoverability** - read `references/refresh-and-discoverability.md`.
5. **Optional enhancement** - read `references/enhancement.md`. Interactive only.
6. **Report** - read `references/report.md`, emit the required report, and end the turn.

**Lightweight Mode** replaces those steps with `references/lightweight.md`, which owns its completion output.
