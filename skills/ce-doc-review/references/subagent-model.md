# Choosing the model for a spawned subagent

This rule decides the model and reasoning effort for every subagent this skill spawns: reviewers, the lite reviewer, checks, leaves, and validators. Read it before the first spawn. The orchestrator itself keeps the session model.

**Separate gates.** This skill explicitly requests reviewers, including lite/check/validator paths, and therefore satisfies user-OR-skill delegation permission. An unconditional higher-priority prohibition, missing tool or actual denial still applies. Permission to delegate does not grant model-selection permission. If overrides require an explicit user model request, omit optional model/effort arguments despite configured tier intent and use a suitable inherited model. Disclose unmet fixed-route/cross-model requirements as incomplete; same-model reviewers are not cross-model independence. Never bypass a restriction using shell or another harness.

**Depth.** Verify effective runtime depth using supported OpenCode configuration inspection, not the bundled package default alone. Deep workflows need user-level `experimental.subagent_depth` at least 3; installation owns that prerequisite, not this run. Classify actual dispatch errors: nesting exhaustion, recoverable concurrent capacity, permission denial, missing tool and rejected model arguments are distinct. A nesting error is not queued backpressure. Use inline or parent-coordinator fallback only where the contract permits independence to be retained; report all unmet coverage.

**Default tier.** The spawning step names its tier intent. Discover native model IDs/variants with `opencode.models`; never guess or launch another harness. Preserve configured model/effort intent subject to the gates above.

If the user's or project's active instructions or the live prompt name a model for this subagent, that model supersedes default tier intent, subject to the separate selection-permission gate above. They can name it by tier, prompt-asset name, or the subagents being dispatched. Without such an instruction, a configured role model takes precedence over default tier intent, never over host policy.

**Configured model.** `review_subagents` in repository config is the model configured for this subagent's role. Read it under this rule:

<!-- ce-config-layers:start -->
**Resolve ordinary repository yaml keys from the two repo files.**

- **Read** `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml` (`<repo-root>` = `jj workspace root`, run from the target absolute workspace root). Missing files are skipped. Ignore status does not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- ce-config-layers:end -->

The key maps a harness name (`codex`, `claude`, `grok`, `cursor`, `opencode`, `antigravity`) to optional `model` and `effort`. Only the current `opencode` entry applies; retain other entries as configuration compatibility data, not active dispatch routes. Missing fields retain default tier intent; non-string fields are ignored. Pass effort only when supported and permitted; otherwise disclose unapplied effort in Coverage.

**Refused model.** For a genuine model/effort capability rejection, one no-override inherited-model retry is allowed only if delegation remains permitted and the inherited model satisfies the review contract. A required exact route/different-model pass remains incomplete otherwise. Do not retry a permission denial or depth failure. Report rejected intent and actual evidence in Coverage; concurrent capacity follows dispatch's bounded queue rules.
