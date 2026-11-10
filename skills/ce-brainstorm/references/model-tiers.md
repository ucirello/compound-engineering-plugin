# Subagent model tiers

This skill authorizes native delegation for the grounding scout, claim verifier, and opt-in Slack researcher, subject to host policy. Delegation permission and model-override permission are separate.

- **Extraction tier:** retrieval and quoting for the scout; favor the cheapest capable permitted model, escalating for large or obscure repositories.
- **Generation tier:** evidence-driven claim verification; favor a capable mid-tier model.
- **Ceiling tier:** dialogue, synthesis, and writing remain in the main conversation unless the separately resolved reasoning-elevation preference applies.

Explicit active user instructions win, then configured role-specific model choices, then these defaults. Config choices remain authoritative subject to host permission. Discover exact available models through `opencode.models`, never guess aliases or override arguments. Inherit the current model when suitable. If a requested model cannot be selected, disclose the unmet request and any missing independent or cross-model coverage; never claim full coverage silently.

Use the native subagent primitive only. If unavailable, perform the bounded scan inline, still writing the grounding dossier for downstream consumers, and verify claims inline before Phase 3. A denied dispatch is not missing tooling; obey the denial. Correct a pre-launch argument rejection once using the supported schema. Queue capacity-limited work; depth exhaustion requires returning work to the parent or inline execution, not another nested launch. Never bypass any of these conditions through shell, another harness, or provider CLI. A started agent's failure is recorded and disclosed, not blindly duplicated. Preserve all original read budgets and output caps on inherited or inline execution.
