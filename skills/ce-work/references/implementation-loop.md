# Implementation Loop

For each ready task:

1. Mark it active and read only its referenced plan/code context.
2. Detect already-satisfied work from current files and verification; verify rather than reimplement.
3. Inspect local patterns and existing tests.
4. Choose evidence before behavior changes: existing failure, strengthened test, new focused failure, characterization, or deliberate no-test replacement verification.
5. Observe the intended failure/baseline when the evidence strategy requires it, then implement within scope.
6. Add/update/remove tests to match behavior and trace callbacks, middleware, persistence failure, parallel interfaces, and cross-layer error handling when applicable.
7. Run focused and system-relevant checks, record observed evidence, inspect `jj diff --summary` and `jj diff`, then mark complete.
8. Finalize a logical Jujutsu change according to the main skill's incremental-change gate.

Cross-model execution retains host ownership of ordering, evidence, actual-scope inspection, verification, composition, and final change description. Process completion is only authoring evidence. A preserved or restoration-blocked unit stops the loop.

Parallel waves pause after each canonical composition. Recompute readiness against accepted Jujutsu changes, revalidate semantic independence, and keep dependents queued. A clean content composition is not semantic proof. Repeated collision or broad edits disables later waves.

Use proof-first or characterization-first for behavior-bearing work when a practical seam exists. Skip that order for non-behavioral/generated/manual-only surfaces only with recorded replacement verification. Prefer strengthening the existing correct test home over duplicate coverage.
