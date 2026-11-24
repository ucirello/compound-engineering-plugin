# OpenCode subagent permissions and model selection

Apply this before every native OpenCode subagent launch in this skill, including
reviewers, leaves, judges, peers, and validators. The orchestrator keeps its model.

**Dispatch and model overrides are separate permissions.** This loaded skill
explicitly requests its described subagents and satisfies a user-or-skill
delegation gate. Respect unconditional denial, a missing tool, and higher-priority
limits. Do not use a shell, subprocess, plugin, CLI, or another agent to bypass
them. An explicit model/effort override requires its own permission; an
instruction or config value does not override a denial.

Resolve ordinary YAML keys from `<workspace-root>/.rocketclaw/config.local.yaml`
then `config.yaml`; use the shipped `config.example.yml` (or `.yaml` if so
named) as the key/schema guide, not an active override. Missing files are skipped; use the first active valid scalar
(empty means unset) or present list/map (including empty, replacing the whole
key). `docs_root` remains `config.yaml` only. Use the `opencode` entry of
`review_subagents` (optional string `model` and `effort`); other harness entries
(`codex`, `claude`, `grok`, `cursor`, `antigravity`) are not OpenCode routes.
User or active project instructions for the role override this config, which
overrides the stage default (session, balanced mid-tier, or cheapest capable).
Find exact provider/model IDs and offered variants with `opencode.models`.
Pass only options the native dispatch tool actually supports.

When an override is disallowed or unavailable, inherit the session model if
that fulfills a non-fixed role. For a non-fixed role whose model/effort was
rejected on launch, retry once without the override when suitable; report the
rejected value and whether inheritance was used. Do not upgrade silently or
claim an unsupported effort. A fixed/cross-model route not actually fulfilled
is incomplete; follow only its explicit recovery/fallback rules.

Distinguish actual OpenCode nesting-depth exhaustion, dispatch denial, override
denial, missing tool, model/effort rejection, and active-agent capacity. Batch
capacity contention can be retried when a slot opens; it is not depth.
For a depth failure report the failing stage and, as a repair for a later run,
point to the user's existing OpenCode V2 JSON/JSONC found via
`opencode debug paths` or `opencode debug paths config`: merge
`experimental.subagent_depth` to at least 3 (preserve other keys and any higher
value; default user file `~/.config/opencode/opencode.json`; avoid competing
files and higher-precedence lower overrides). Package config alone does not
enable consumer nesting. Do not edit config, restart, retry denied dispatch, or
raise claimed coverage to disguise the failed step.
