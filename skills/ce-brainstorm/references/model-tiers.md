# Model Tiers

Read this when dispatching a sub-agent (the Phase 1.1 grounding scout, the Phase 2.6 claim verifier, or the opt-in Slack researcher). Sub-agent dispatch is tiered by task shape, never hardcoded to a model name:

- **Extraction tier** — the grounding scout: retrieval and quoting work. Use the platform's cheapest capable model when the current harness exposes a known override. "Capable" is part of the spec — escalate to the generation tier when the repo is large or the stack obscure.
- **Generation tier** — the claim verifier: evidence-driven mechanical verification. Use the platform's mid-tier model when the current harness exposes a known override. If model names are unknown, omit the override and inherit rather than guessing.
- **Ceiling tier** — the dialogue itself. Questions, approaches, synthesis, and the requirements-only unified plan run in the main conversation on the orchestrator's model; nothing is dispatched for them.

If the user's or project's active instructions or the live prompt name a model for this subagent, preserve that choice instead of the default tier above, subject to the host's separate model-selection permission. They can name it by tier, prompt-asset name, or the subagents being dispatched. Otherwise a configured role model takes precedence over the default tier. Resolve models through `opencode.models`; dispatch through native subagents. Apply the delegation, model-override and nesting-depth rules in `reasoning-elevation.md`: configuration alone does not authorize a forbidden model override.

**Degradation rule.** When the platform's subagent primitive does not support per-agent model selection, dispatch the scout and verifier on the inherited model and keep their read budgets and output caps — cost control then comes from structure, not tiering. When the platform has no subagent primitive at all, do the topic scan inline at Phase 1.1 — still writing the grounding dossier to the scratch path, because downstream consumers (the Phase 2.6 verifier, the ce-plan handoff) receive that path — and verify claims inline before the Phase 3 write, with the same budgets.

Classify an actual rejection separately as permission denial, model-argument rejection, missing tool or depth/capacity exhaustion. Correct a permitted pre-launch argument error at most once; never retry a denied operation or evade depth through another harness. Use the inline degradation above only where its contract permits; disclose unmet configured tier or required independence rather than claiming that coverage completed.
