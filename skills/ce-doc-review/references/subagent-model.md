# Choosing the model for a spawned subagent

This rule decides the model and reasoning effort for every subagent this skill spawns: reviewers, the lite reviewer, checks, leaves, and validators. Read it before the first spawn. The orchestrator itself keeps the session model.

**Default tier.** Use the role-specific tier in `dispatch.md`. The historical Codex default (`gpt-6.1-terra`, `high`) remains compatibility context, not an OpenCode override.

The live user's or project's active model instructions take precedence over a configured role model, then the role defaults. They can name it by tier, prompt-asset name, or dispatch scope. These are preferences or route requirements, not permission grants.

**Configured model.** Read `review_subagents` under this rule:

<!-- ce-config-layers:start -->
**Resolve ordinary YAML keys from the two workspace files.**

- **Read** `<workspace-root>/.rocketclaw/config.local.yaml`, then `config.yaml` (`<workspace-root>` = `jj workspace root`). Missing files are skipped. Ignore rules do not change resolution. Outside a JJ workspace, use the skill defaults unless the active user or project instructions say otherwise.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

The map retains harness keys (`codex`, `claude`, `grok`, `cursor`, `opencode`, `antigravity`) with optional string fields `model` and `effort`. Only `opencode` applies to native reviewer dispatch; absent or non-string fields keep the default. `config.example.yml` describes the supported shape and is not a runtime config layer.

**Delegation permission is not model-selection permission.** Only when permitted, use `opencode.models` (chat) to resolve the intended tier or exact `provider/model` and any supported variant. Pass only options the native tool documents. If the host requires an explicit user model request and there is none, omit `model` and any disallowed effort override, even when configuration or project instructions name a tier. Use the inherited model when suitable; disclose unapplied configured model/effort or tier limitations in Coverage. If an exact route or independent cross-model requirement cannot be met, report that coverage incomplete; same-model contexts can count as separate local reviewers, not as cross-model corroboration.

**Refused model.** If the actual dispatch error rejects an unavailable model or effort (not a permission denial), an ordinary reviewer whose brief does not require the exact model may retry once without overrides, using the inherited model if suitable. Report which request was rejected and any relevant advertised alternatives. Do not retry a denial, depth rejection, or missing tool with different arguments. Cross-model model rejection uses only the bounded rule in `cross-model-review.md`; an explicit pin cannot be substituted.
