# Choosing the model for a spawned subagent

This rule decides the model and reasoning effort for every subagent this skill spawns: reviewers, the lite reviewer, checks, leaves, and validators. Read it before the first spawn. The orchestrator itself keeps the session model.

**Delegation, model permission, and depth are separate.** This skill explicitly requests native reviewer subagents. Under a user-OR-skill delegation rule that is sufficient; no second approval is needed. Respect unconditional higher-priority prohibitions and actual denials. Never bypass them through shell or another harness.

**Default tier.** Preserve the spawning step's tier as intent (including Codex's `gpt-6.1-terra` / `high` preference). Resolve permitted model names with `opencode.models`. If the host requires an explicit user model request before overriding a model, configuration or this skill alone does not authorize a `model` argument: omit it and use inherited reviewers where adequate. Disclose unmet tiers and required different-model coverage. Separate same-model reviewers are not cross-model evidence.

**Depth.** Verify effective OpenCode `experimental.subagent_depth` and available nesting capacity; permission does not imply capacity. Classify actual launch errors as depth/capacity, permission denial, model-argument rejection, or unavailable tool. Never evade limits or repeat denied calls. Use an allowed inline or parent-coordinator fallback only when its contract preserves required independence; otherwise report incomplete coverage.

Subject to host model-override permission, a user-requested model takes precedence, then the configured role choice, then the default tier. Project preferences remain intent, not permission to override host policy.

**Configured model.** `review_subagents` in RocketClaw config is the model configured for this subagent's role. Read it under this rule:

<!-- ce-config-layers:start -->
**Resolve ordinary RocketClaw yaml keys from the two repo files.**

- **Read** `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml` (`<repo-root>` = `jj workspace root`). Missing files are skipped. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

The key maps a harness name (`codex`, `claude`, `grok`, `cursor`, `opencode`, `antigravity`) to an entry with an optional `model` and an optional `effort`. Only the entry for the current harness applies, and it applies to every subagent this skill spawns. A field the entry leaves out keeps the default tier's value. A field that is not a string is ignored. Pass an effort only when the spawn tool takes one; otherwise say in Coverage that the configured effort was not applied.

**Refused model.** Only an actual unavailable-model error permits one inherited-model attempt, where policy and the review contract allow it. A policy denial is not model unavailability: do not retry it. Report requested and actual model, error category, and unmet independence or tier requirements in Coverage. Capacity handling belongs to the spawning step.
