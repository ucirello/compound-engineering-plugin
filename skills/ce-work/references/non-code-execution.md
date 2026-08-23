# Non-Code Execution (Knowledge-Work Carve-Out)

Load from input triage when a plan carries `execution: knowledge-work`. The plan is a production plan for a non-code deliverable such as a synthesized document, study artifact, or research write-up. Execute it to produce the deliverable. The normal code lifecycle does not apply.

## What This Skips

- No feature-change, bookmark, or extra-workspace setup.
- No task list derived from implementation units and no code-worker dispatch keyed on `Files:`.
- No Test Discovery, test-scenario completeness, or system-wide code test check.
- No incremental code descriptions and no code shipping workflow, PR, or CI tail.

## Execute The Production Plan

1. **Read the plan fully.** Honor its source, synthesis, output-shape, and user-confirmed decisions.
2. **Read every named source.** Treat user-named resources as authoritative; report an inaccessible source rather than substituting memory.
3. **Synthesize and produce the deliverable** in the confirmed shape without inventing scope.
4. **Save and report.** Write to the user-named durable location or a sensible tracked documentation path under the resolved artifact root, and report the absolute path. Offer to place it into a dynamically described Jujutsu change; do not force that action.

## Stay Scoped

If production legitimately requires code, configuration, or a data-transform script, route that bounded sub-step through the normal code path so its evidence, review, and change-quality safeguards apply. The deliverable itself remains non-code.
