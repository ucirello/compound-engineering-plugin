# Apply Code Review Findings

Consume the completed `ce-code-review` output already in hand. Invoke review only for a cold caller with no receipt. Failed review blocks shipping; degraded review records lost coverage.

Apply actionable findings with concrete fixes when evidence still matches. Defer advisory findings, missing fixes, and changes requiring product/design authority. Fix subagents own file inspection and application; the orchestrator filters structured fields, batches by file, dispatches disjoint batches in parallel where workspace isolation permits, inspects actual Jujutsu deltas, runs checks, and finalizes accepted fixes.

Workers must not describe/finalize changes or move bookmarks. They report applied/skipped finding IDs, reasons, and paths. The orchestrator verifies one batch at a time against its assigned findings.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; do not impose a fixed syntax. Use a neutral `jj describe -m "<description derived from active project instructions and runtime jj log>"` placeholder. Start the next fix unit with `jj new` only after the accepted current change is described.

Report batches, findings applied/skipped with reasons, review artifact, checks, and resulting change IDs. Any unapplied actionable finding enters the Residual Work Gate; rerun review only after a materially changed delta.
