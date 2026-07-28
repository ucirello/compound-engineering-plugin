# Apply Code Review Findings

Load after `ce-code-review` returns. Consume the existing JSON or Actionable Findings output; do not rerun review unless this is a cold caller with no result.

Stop on failed review. Record degraded coverage. Apply findings with a concrete, still-valid fix; push back when evidence is wrong; defer advisory, underspecified, or design-dependent findings. A worker confirms evidence at the cited location before editing.

Group eligible findings by file, severity first. Disjoint file groups may run concurrently only in isolated Jujutsu workspaces. Keep coupled files together; split large same-file batches into serial passes. Workers may edit and verify but may not describe, split, squash, rebase, bookmark, fetch, or push.

After each wave, inspect `jj status` and `jj diff`, verify assigned scope, run required checks, and integrate each result in dependency order. Use an inline shortcut only for one finding whose relevant region is already in context.

Before composing, editing, validating, or recommending the complete fix change's description, apply this exact rule:

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

The project's active runtime instructions and conventions are required input. Inspect descriptions with `jj log`; syntax observed there wins over generic guidance. Apply the linked Go guidance only when compatible with those instructions and that history. Use a neutral dynamic description with no fixed type, scope, template, example, or identity footer; then `jj describe` the verified complete fix change.

Report batches, findings applied/skipped with reasons, changed files, artifact path, verification, and remaining residuals. Route every unapplied actionable finding to the Residual Work Gate.
