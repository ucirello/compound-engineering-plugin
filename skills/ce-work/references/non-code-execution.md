# Non-Code Execution (Knowledge-Work Carve-Out)

Loaded from Phase 0 Input Triage when the plan carries `execution: knowledge-work`. The plan is a **production plan** for a non-code deliverable (a synthesized document, a study artifact, a research write-up) — typically produced by `ce-plan`'s approach-altitude flow. Execute it to produce the deliverable. This is a minority-case branch; the normal code lifecycle does not apply and is not invoked here.

## What this skips

Do **not** run any of the code-shipping machinery — it does not fit knowledge work:

- No Jujutsu change/workspace setup (Phase 1 Step 2).
- No task-list-from-implementation-units, no execution-strategy/subagent dispatch keyed on `Files:`.
- No Test Discovery, no test-scenario completeness, no system-wide test check.
- No incremental code changes, and none of `references/shipping-workflow.md` (no PR, no CI).

## Execute the production plan

1. **Read the plan fully.** It is a decision artifact describing *how* the deliverable gets made: which sources to read, how to mine each, how they combine, the shape of the deliverable, and any forks the user already confirmed. Honor those decisions.
2. **Read the sources the plan names** — the actual inputs (PDFs, transcripts, docs, links). Treat user-named resources as authoritative; read them rather than working from memory. If a named source is missing, say so plainly rather than substituting.
3. **Synthesize and produce the deliverable** following the plan's intended shape and the confirmed forks. This is the work the approach-plan deliberately deferred.
4. **Save and report.** Write the deliverable to a durable, tracked location — default to a sensible `docs/` subpath (or a path the user named at the checkpoint) — and report its absolute path. Whether to describe and retain it as a Jujutsu change is the user's call; offer, do not force.

## Stay scoped to non-code deliverables

The carve-out is for knowledge-work output. If producing the deliverable legitimately requires emitting code, route that sub-step through the normal code path so Test Discovery, review, and change hygiene apply. The deliverable itself stays non-code.
