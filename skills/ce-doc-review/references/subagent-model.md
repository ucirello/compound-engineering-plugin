# Choosing the model for a native subagent

This rule covers every reviewer, lite reviewer, check, leaf, and validator. The orchestrator keeps its session model. Delegation explicitly requested by this skill is authorized under user-OR-skill delegation rules; this does not independently authorize model overrides or deeper nesting.

Resolve ordinary config keys from `.rocketclaw/config.local.yaml`, then `config.yaml` at the absolute workspace root obtained with `jj root`. First active valid value wins; empty scalars are unset, lists/maps replace the whole key. `docs_root` is config.yaml only. `review_subagents.opencode` supplies optional string `model` and `effort` fields. Live user/project model instructions override configured role choices, which override dispatch defaults. Preserve configured choices subject to host permission; do not silently substitute.

Use native `opencode.models` discovery to resolve model IDs and supported variants. A discovered model is not permission to override. When no override is required and the inherited model is suitable, omit model arguments. Pass configured effort only when supported; disclose any unapplied effort in Coverage.

Distinguish these outcomes:

- Active-worker capacity: queue, collect/release workers through supported lifecycle tools, then retry. Stop incomplete if capacity cannot recover.
- Nesting-depth limit: do not treat it as transient capacity, and never evade it through shell launches or another harness. Report unavailable independent coverage.
- Permission denial: obey it; no alternate transport or model to evade denial.
- Missing native delegation tool: disclose the missing tool. Inline or serial work is useful fallback but is not independent reviewer coverage.
- Model/effort argument rejected: report the exact rejected choice and advertised alternatives. A local persona may retry once with inherited model only when permitted and suitable; record the loss of requested model coverage. A cross-model reviewer may not count an inherited same-model retry as cross-model coverage. Explicitly pinned cross-model choices run exactly or are skipped.

Never claim full or independent review when required reviewers could not run. Preserve completed findings and report completed, failed, and undispatched reviewers separately.

## Preserved conditional harness configuration

The following conditional defaults and schema facts describe compatibility configuration, not authorization to execute a foreign harness. In this OpenCode run, only the `opencode` entry applies; native permission and failure rules above remain authoritative.

**Default tier.** The step that spawns the subagent names its default tier. In Codex (the host whose subagent tool is `spawn_agent`), the default tier for every subagent is instead `gpt-6.1-terra` with reasoning effort `high`, passed as the spawn's `model` and `reasoning_effort`. That replaces the step's tier, including a step that would otherwise run the subagent on the session model or a cheaper tier.

The key maps a harness name (`codex`, `claude`, `grok`, `cursor`, `opencode`, `antigravity`) to an entry with an optional `model` and an optional `effort`. Only the entry for the current harness applies, and it applies to every subagent this skill spawns. A field the entry leaves out keeps the default tier's value. A field that is not a string is ignored. Pass an effort only when the spawn tool takes one; otherwise say in Coverage that the configured effort was not applied.
