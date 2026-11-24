# Choosing the model for a spawned subagent

This rule decides the model and reasoning effort for the ordinary reviewers and the lite reviewer. The cross-model pass uses its own fixed route under `references/cross-model-review.md`, with the same model-permission boundary. Read this before the first spawn. The orchestrator itself keeps the session model.

**Default tier.** The step that spawns the subagent names its default tier. The Codex compatibility mapping is `gpt-6.1-terra` at `high` effort instead of the per-step default; that mapping does not select a model for an OpenCode session.

An applicable user or project instruction can name the desired model by subagent tier, prompt-asset name, or dispatched set. Absent such an instruction, use the model configured for the role before the default tier. These rules determine intent, not permission.

**Configured model.** `review_subagents` in RocketClaw config is the model configured for this subagent's role. Read it under this rule:

<!-- ce-config-layers:start -->
**Resolve ordinary YAML keys from the two workspace files.**

- **Read** `<workspace-root>/.rocketclaw/config.local.yaml`, then `config.yaml`. Resolve the root with [`jj workspace root`](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace-root) from the absolute project directory and run subsequent JJ commands from the resolved absolute workspace root. Missing files are skipped; outside JJ there is no workspace config. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

The key maps a harness name (`codex`, `claude`, `grok`, `cursor`, `opencode`, `antigravity`) to an entry with an optional `model` and an optional `effort`. Only the entry for the current harness (`opencode` here) applies. A field the entry leaves out keeps the default tier's value; a non-string field is ignored.

**Native selection.** Use `opencode.models` to resolve a permitted override to an exact catalog ID and check advertised reasoning variants. If the host requires an explicit user model request, a tier or configuration does not satisfy that rule. Omit `model` and any unsupported or unauthorized effort parameter; use the inherited session model where it meets the reviewer contract. Disclose unapplied configured or requested model/effort in Coverage. Do not dispatch an inherited reviewer as satisfying a fixed route or different-model requirement, and do not count separate instances of the same model as cross-model independence.

**Rejected model argument.** If the actual error rejects an optional model or effort argument (not delegation), correct the invocation once by omitting the rejected override and inheriting, only if the ordinary reviewer can still do the job. Do not substitute another model or claim a required model ran; report the refusal and advertised options when available. A fixed model or effort requirement that inheritance cannot meet is incomplete. Capacity, nesting, and delegation errors follow `references/dispatch.md`, not this retry.
