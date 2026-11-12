# Choosing the model for a spawned subagent

This rule decides the model and reasoning effort for every subagent this skill spawns: reviewers, the lite reviewer, checks, leaves, and validators. Read it before the first spawn. The orchestrator itself keeps the session model.

**Default tier.** The step that spawns the subagent names its default tier. In Codex (the host whose subagent tool is `spawn_agent`), the default tier for every subagent is instead `gpt-6.1-terra` with reasoning effort `high`, passed as the spawn's `model` and `reasoning_effort`. That replaces the step's tier, including a step that would otherwise run the subagent on the session model or a cheaper tier.

If the user's or project's active instructions or the live prompt name a model for this subagent, use that model instead of the default tier above. They can name it by the subagent's tier, by its prompt-asset name, or for the subagents being dispatched. Without such an instruction, a model configured for this subagent's role takes precedence over the default tier.

**Permission before selection.** Skill-explicit delegation is not an explicit user model request. If the host permits optional model arguments only on an explicit user request, omit the optional model/effort arguments unless that request exists; inherit the session model when suitable. Preserve the configured/default route as intent and disclose unapplied intent in Coverage. Same-model review is not cross-model review. Use `opencode.models` to discover exact supported provider/model IDs and variants before an authorized override; never guess an ID. Do not retry a permission denial under another model or harness.

**OpenCode nesting prerequisite (documentation only).** Before nested reviews, users must merge `experimental.subagent_depth` of at least `3` into their existing global `~/.config/opencode/opencode.json` or `.jsonc`. Locate the actual existing config with `opencode debug paths` or `opencode debug paths config`; do not create a competing file. Preserve a higher existing integer and all unrelated/sibling settings. Package/plugin config alone does not enable global nesting; higher-precedence configuration must not lower the value. Never modify host configuration during this skill. A real depth failure is distinct from a busy agent limit, denied delegation or unsupported model and does not authorize evasion.

**Configured model.** `review_subagents` in RocketClaw config is the model configured for this subagent's role. Read it under this rule:

<!-- ce-config-layers:start -->
**Resolve ordinary RocketClaw yaml keys from the two repo files.**

- **Read** `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml` (`<repo-root>` = `jj root`, with cwd set to the absolute target workspace root). Missing files are skipped. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

The key maps a harness name (`codex`, `claude`, `grok`, `cursor`, `opencode`, `antigravity`) to an entry with an optional `model` and an optional `effort`. Only the entry for the current harness applies, and it applies to every subagent this skill spawns. A field the entry leaves out keeps the default tier's value. A field that is not a string is ignored. Pass an effort only when the spawn tool takes one; otherwise say in Coverage that the configured effort was not applied.

**Refused model.** Only an actual unavailable model/effort error permits one inherited-model retry with no override, where that review contract permits fallback. Do not swap an explicit pin or claim that inherited same-model evidence fulfills independent cross-model coverage. Report the refused route and available models, preserving unmet intent. A permission, depth or tool denial never triggers this retry; active-agent limits follow dispatch backpressure handling instead.
