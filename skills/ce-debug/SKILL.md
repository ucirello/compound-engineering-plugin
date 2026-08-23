---
name: ce-debug
description: "Diagnosis loop for bugs and failing behavior. Use when asked to debug or fix failing behavior."
argument-hint: "[issue reference, error message, test path, or description of broken behavior]"
---

# Debug and Fix

Find the root cause of a failure, then, when the user chooses to, fix it with test-first discipline.

**Done when:** the causal chain from trigger to symptom is stated without gaps and with file:line evidence, and either a verified fix has been handed off as a PR or described change, the user chose another stop, or a diagnosis-only summary was delivered. After 2-3 exhausted hypotheses or 3 failed fixes, diagnose why instead of repeating attempts. One hypothesis and one change at a time.

`<bug_description>` is whatever invoked this skill: a failure description, `mode:` token, or issue reference, supplied by the user or a caller. It is blank when absent.

## Setup

Run this once before subagent dispatch and follow its directives except where this skill's interaction rules override them. Run it as its own unfiltered command. Its output begins with `=== skill context` and ends with `ROCKETCLAW_CONTEXT_END`; if only one appears, rerun once verbatim. If Node is unavailable, proceed unchanged.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
NODE="$(for c in node nodejs; do command -v "$c" >/dev/null 2>&1 && "$c" -e '' >/dev/null 2>&1 && { echo "$c"; break; }; done)";
if [ -n "$NODE" ]; then
"$NODE" "$SKILL_DIR/scripts/context.mjs" || echo "context script failed; continue with the skill's normal behavior";
else
echo "no Node runtime; continue with the skill's normal behavior";
fi
```

## Mode

Interactive mode investigates, runs the Phase 2 choice, then Phase 4 handoff.

For `mode:pipeline`, strip the token, **read `references/pipeline-mode.md`**, ask nothing, fix convergent bugs, defer divergent ones, and return exactly one documented status.

## Blocking Questions

Use the host's blocking question interface. Fall back to numbered options in chat only when none exists or the call errors. Never silently skip a question or end a phase without its answer.

## Paths

Reusable learnings live under `<workspace-root>/.context/solutions/`, with `<workspace-root>` from `jj workspace root`. Resolve that path only when a durable artifact is first needed; a scratch-only or no-workspace run skips it. Configuration lives under `<workspace-root>/.rocketclaw/`.

Put every invocation-owned scratch file or directory under `<workspace-root>/.tmp/rocketclaw/debug/`. If no Jujutsu workspace is available, use `./.tmp/rocketclaw/debug/`. Never use host-wide temporary storage.

## Execution Flow

Five phases in order: **0 Triage -> 1 Investigate -> 2 Root Cause -> 3 Fix -> 4 Handoff.** Beyond Phase 0's trivial fast path, do not skip phases or invent complexity tiers.

**Read `references/investigate.md` now for Phases 0-2.** It owns issue fetching, reproduction, workspace sanity and working-copy isolation, backward tracing, prior-work search, hypothesis grounding, and escalation.

Whatever issue the user supplied remains the issue of record. Input that is only a stack trace, test path, or description means no issue of record; ship without inventing one. Prior-work search never creates a new home for the bug.

The trivial fast path still runs Phase 2's fix-choice gate before editing.

Choose regression coverage from existing tests that own the confirmed defect. Read `references/fix.md` before recommending or editing tests. A test whose intended expectation the proposed change reverses is divergent, not wrong.

### Phase 2 Gate

Do not proceed until the full causal chain is explained. Only the user can authorize a best-available hypothesis when investigation is stuck.

Present a user-visible findings block before asking: causal chain with file:line evidence, proposed fix and files, regression-test plan and why existing tests missed it, and relevant prior work. Then ask for **Fix it now**, **Diagnosis only**, or **Rethink the design** only when the cause is a responsibility/interface or requirements problem.

In `mode:pipeline`, ask nothing: apply a convergent fix and defer a divergent product/design decision as `needs-human`.

### Phase 3: Fix

If diagnosis-only was selected, skip to the summary. If design rethinking was selected, invoke `ce-brainstorm` and end.

**Read `references/fix.md` before editing.** Two preconditions remain here because Phase 4 cannot reconstruct them:

- Check `jj status`. If a file that must change carries pre-existing user work, confirm before editing.
- Record `@`'s change ID and commit ID, whether it has changes, and all pre-existing changed files. Track fix-owned files as work proceeds. If `@` is `trunk()` or immutable, create a dedicated child with `jj new @`; create a bookmark only when publication requires one.

### Phase 4: Handoff

In `mode:pipeline`, skip the interactive handoff. Describe and push the convergent fix per `references/pipeline-mode.md`, emit its structured return, and defer divergent items there.

Always begin with:

```text
## Debug Summary
**Problem**: [What was broken]
**Root Cause**: [Full causal chain, with file:line references]
**Recommended Tests**: [Specific tests and assertions]
**Fix**: [What changed, or diagnosis only]
**Prevention**: [Coverage and defense-in-depth]
**Confidence**: [High/Medium/Low]
```

If Phase 3 was skipped, stop after the summary.

If Phase 3 ran, read `references/post-fix-handoff.md` before routing. It owns the quality tail, fix-only scoping, residuals, report block, and learning criteria.

Land only fix-owned files. If one already carried user edits, ask before finalization whether to include the whole file, leave it in the working-copy change, or stop. Only inclusion continues.

Exactly one route runs:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe imperative mood, casing, punctuation, line wrapping, subject/body shape, or any fixed syntax.

- **Ships** when the pre-fix working copy had no edits, the bookmark's entire change stack contains only offered work, and `origin` is PR-capable. Preview the described scope, bookmark stack, and create/update action, then invoke `ce-commit-push-pr`; do not finalize first.
- **Stays local** otherwise. Invoke `ce-commit` for fix-owned files and push nothing. State why it stayed local.
- **Not a Jujutsu workspace** stops without finalization.

Honor an explicit local-only or stop-after-fix instruction. After a PR opens, apply the learning criteria; if accepted, invoke `ce-compound`, include its learning in a described change on the same bookmark, and push it. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe imperative mood, casing, punctuation, line wrapping, subject/body shape, or any fixed syntax.
