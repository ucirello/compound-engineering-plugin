# Choosing the model for a spawned subagent

This rule decides the model and reasoning effort for every subagent this skill spawns: reviewers, the lite reviewer, checks, leaves, and validators. Read it before the first spawn. The orchestrator itself keeps the session model.

**Default tier.** The step names the desired capability tier, not a model ID or permission grant. Use native `opencode.models` to resolve current provider/model IDs and supported reasoning variants when an override is needed and permitted. Inherit the session model when it is suitable or the host exposes no permitted override. Do not apply another product's conditional defaults in OpenCode or shell out to select a model.

If the user's or project's active instructions or the live prompt name a model for this subagent, use that model instead of the default tier above. They can name it by the subagent's tier, by its prompt-asset name, or for the subagents being dispatched. Without such an instruction, a model configured for this subagent's role takes precedence over the default tier.

**Configured model.** `review_subagents` in RocketClaw config supplies the role's model. Read it under this rule:

<!-- ce-config-layers:start -->
**Resolve ordinary RocketClaw YAML keys from the two repo files.**

- **Read** `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml` (`<repo-root>` = absolute `jj root`, with commands run in that root). Missing files are skipped. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

The key maps a harness name to an entry with optional `model` and `effort`. Only `review_subagents.opencode` applies here, to every ordinary subagent this skill spawns; preserve other entries without applying their product-specific semantics. Non-string fields are ignored; an omitted field keeps its default. Live user/project instructions outrank configured role choices, which outrank tier defaults. Configured models stay authoritative subject to host permission: discover availability, do not silently replace them with a cheaper/newer choice. Pass effort only if native dispatch supports it and the exact model advertises that variant; otherwise disclose it was not applied.

**Permission distinctions.** This skill requests delegation, which is allowed when user OR skill authorization is sufficient under the host; user/host prohibitions still win. That is separate from permission to override models. If overrides are denied, ordinary suitable reviewers may inherit; disclose the configured model/effort not applied. Never evade denial through shell, another harness or nested delegation. Inheritance does not satisfy a required different-family cross-model pass.

**Refused model argument.** When native dispatch rejects a requested model/effort as unsupported or unavailable, retry an ordinary local subagent once without overrides. Disclose the rejected choice and offered models when reported. No silent substitution. Configured cross-model peer choices use `cross-model-recovery.md`, never an inherited same-family pass mislabeled cross-model.

**Do not conflate failures.** Capacity backpressure queues work until native slots release. Nesting-depth exhaustion is an actual depth error, not capacity or denial: no deeper retry or shell workaround. Missing native tools/collector means explicit degraded coverage. A successful launch followed by failure is a failed reviewer; a denied launch is not a completed pass. In every degraded case record persona/validator/model coverage lost and do not claim full review. Parent analysis is not independent, cannot populate `independent_reviewers`, promote confidence, or satisfy cross-model validator shortcuts.

## Preserved conditional harness configuration

The following conditional defaults and schema facts describe compatibility configuration, not authorization to execute a foreign harness. In this OpenCode run, only the `opencode` entry applies; native permission and failure rules above remain authoritative.

**Default tier.** The step that spawns the subagent names its default tier. In Codex (the host whose subagent tool is `spawn_agent`), the default tier for every subagent is instead `gpt-6.1-terra` with reasoning effort `high`, passed as the spawn's `model` and `reasoning_effort`. That replaces the step's tier, including a step that would otherwise run the subagent on the session model or a cheaper tier.

The key maps a harness name (`codex`, `claude`, `grok`, `cursor`, `opencode`, `antigravity`) to an entry with an optional `model` and an optional `effort`. Only the entry for the current harness applies, and it applies to every subagent this skill spawns. A field the entry leaves out keeps the default tier's value. A field that is not a string is ignored. Pass an effort only when the spawn tool takes one; otherwise say in Coverage that the configured effort was not applied.
