# Model Tiers

Read this when dispatching a sub-agent (the Phase 1.1 grounding scout, the Phase 2.6 claim verifier, or the opt-in Slack researcher). Sub-agent dispatch is tiered by task shape:

- **Extraction tier** — the grounding scout: retrieval and quoting work. Use the least expensive capable dispatch setting when one is available. Escalate when the repo is large or the stack obscure.
- **Generation tier** — the claim verifier: evidence-driven mechanical verification. Use the standard reasoning dispatch setting when one is available; otherwise inherit rather than guessing.
- **Main-conversation tier** — questions, approaches, synthesis, and the requirements-only unified plan remain in the main conversation and are not dispatched.

**Degradation rule.** When dispatch settings cannot be selected, inherit the current setting and keep the read budgets and output caps. When no subagent primitive exists, do the topic scan inline at Phase 1.1, still writing the grounding dossier to the scratch path because downstream consumers receive that path, and verify claims inline before the Phase 3 write with the same budgets.
