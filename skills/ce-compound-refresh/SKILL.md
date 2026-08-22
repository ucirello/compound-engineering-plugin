---
name: ce-compound-refresh
description: Refresh the repo's captured learnings against the current codebase. Use when auditing stale, overlapping, superseded, or drifted learnings; avoid general refactor, debugging, or code review unless the learnings store is explicit.
argument-hint: "[optional: scope hint - directory, filename, module, or keyword] [mode:non-interactive]"
---

# Learning Refresh

**Outcome:** every learning in scope under `.context/solutions/` is checked against the current codebase and receives an evidence-backed maintenance outcome.

**Done:** supported edits are applied, vocabulary and discoverability are reconciled, the full per-doc report is printed, and changed files are described and routed according to the selected mode.

## Setup

Run this once at the start, before subagent dispatch, and follow its directives except where this skill's interaction rules override them. Run it as its own unfiltered command. Its output begins with `=== skill context` and ends with `ROCKETCLAW_CONTEXT_END`; if only one appears, rerun once verbatim. If Node is unavailable, proceed unchanged.

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

**Read `references/modes.md` now.** It owns argument parsing, unattended actions, stale-marking fallback, question interfaces, and `.context/CONCEPTS.md` bootstrap routing.

In both modes, a failed write is **recommended** and the run continues. Never silently skip a required question.

## Repository Paths

Resolve `<jj-root>` with `jj root`; if it fails, stop because version-control and artifact boundaries cannot be established. Pass concrete resolved paths, not configuration, to subagents. Every subagent spawn omits the `mode` parameter so user permission settings apply.

Repository-local configuration is under `<jj-root>/.rocketclaw/`; this skill reads only `<jj-root>/.rocketclaw/config.yaml` when configuration is needed. Durable artifacts map directly to `<jj-root>/.context/`.

All scratch output stays under `<jj-root>/.tmp/rocketclaw/refresh/`. During preflight only, if `jj root` is unavailable, use `<current-working-directory>/.tmp/rocketclaw/refresh/` long enough to report the blocker. Never use host-wide temporary storage.

Correct a rejected pre-launch argument once, queue capacity-limited work until a slot frees, and substitute the orchestrator for another launch failure with the same inputs. Report any substitution.

## Scope

Candidates are `.md` files under `.context/solutions/`, excluding `README.md` and `_archived/`. A hint that matches nothing never widens scope. **Read `references/scope.md`** for narrowing, misses, empty-store behavior, triage, and README cleanup.

## Investigate

**Read `references/investigate.md`** for staleness dimensions, auto-memory rules, subagent roles, and category-shape notes.

Check each learning against current code, then the set for overlap, supersession, and contradiction. A contradiction outranks individual staleness. Compare only guidance a knowledge-track learning names; never search the guidance layer for one.

Every investigation subagent prompt carries the reference's three **Subagent prompt** clauses verbatim.

## Classify

Every doc gets exactly one outcome: **Keep**, **Update**, **Consolidate**, **Replace**, or **Delete**. There is no `_archived/`; Jujutsu history is the archive.

**Read `references/classify.md` before assigning outcomes.** It owns outcome meanings, evidence boundaries, auto-delete, relocation, split, retrieval value, pattern docs, and interactive decisions.

When code and doc disagree, the doc changes and code does not. When a learning contradicts guidance, report it; never edit a skill, runbook, or instruction file in this workflow.

## Execute

Read `references/per-action-flows.md` and follow the matching flow once per doc.

## Vocabulary Capture

After per-doc actions, reconcile flagged terms with `.context/CONCEPTS.md`. **Read `references/concepts-vocabulary.md` unconditionally.** Apply edits silently in every mode. The report records the scan even when no term qualifies.

## Report

**Print the full report as markdown.** It is the deliverable and, in non-interactive mode, the only one. Keep it self-contained and unabridged, split into **Applied** and **Recommended**. **Read `references/report.md`** for the summary and per-file requirements.

## Describe And Publish

Skip if nothing changed. Otherwise **read `references/commit.md`** for Jujutsu description, bookmark, publication, and failure behavior. Keep only this refresh's files in its described change.

## Discoverability Check

After the report, check whether the project's instructions lead agents to `.context/solutions/` before documented work. **Read `references/discoverability.md`** for the semantic bar, smallest addition, `.context/CONCEPTS.md` variant, mode-specific consent, and late-edit publication.

## Relationship To `ce-compound`

`ce-compound` captures a newly solved problem. This skill maintains the store as code evolves. Replace only on evidence; otherwise stale-mark and point to `ce-compound`. Consolidate proactively because redundant docs drift.
