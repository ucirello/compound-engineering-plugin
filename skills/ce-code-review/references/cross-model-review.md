# Native cross-model adversarial review

This skill explicitly requests delegation. Where host policy permits delegation requested by the user **or a loaded skill**, that exception is satisfied here: do not ask the user again. An unconditional prohibition or denied tool still wins. Permission, model-selection permission, and actual nesting capacity are three different checks.

## Resolve once, before disclosure

Read `.rocketclaw/config.local.yaml`, then `config.yaml`, for `cross_model_review_mode`, `cross_model_peer`, `cross_model_model`, and `cross_model_effort`. First active valid scalar wins; empty/invalid continues to next layer/default. Present lists/maps replace the whole key, even empty. `docs_root` remains config.yaml-only. Evaluate mode first: `auto` default, `off` skips before disclosure/dispatch unless the user explicitly requests cross-model review for this run. A configured peer/project preference is not that live opt-in. User prohibition always wins; record `disabled by checkout config` distinctly. Preference precedence is conversation > configured peer > active project-instruction preference > first available attested-different target in codex→claude→grok→antigravity order. Cursor/Composer require an explicit preference. Preserve target/model/effort as intent, including legacy mappings: codex→OpenAI, claude→Anthropic, grok→xAI, antigravity→Gemini, composer→Composer, cursor→its attested serving model, opencode→explicit provider/model. These are selection hints, never commands to launch other harnesses.

Retain the editorial defaults as **intent**, resolved to actual native provider IDs using `opencode.models` without silent substitutions:

| Legacy target | Model intent | Effort intent |
| --- | --- | --- |
| codex | `gpt-6-luna` | `xhigh` |
| claude | `claude-opus-5-5` | `high` |
| grok | `grok-4.7` | `xhigh` |
| grok through Cursor | `grok-4.7[context=256k,reasoning_effort=high,fast=true]` | model-implied high |
| composer | `composer-2.5[fast=true]` | fast |
| antigravity | `gemini-4-argon`, with `gemini-3.8-flash` availability fallback only before sending and after disclosure | high |
| cursor / opencode auto | no attested model until runtime receipt | unverified |

Legacy intermediary flags are not native model IDs: if the same capabilities cannot be resolved natively, record unmet intent. Validate configured effort against the chosen model's offered variants and reject incompatible family/model/effort rather than substituting. All selections below remain subject to host override policy.

Use `opencode.models` to resolve the requested model and its supported reasoning variants. Default preference is an available attested-different family, preserving configured high/extra-high review tier. Never infer serving family from a product name or a requested model. Only runtime identity is evidence.

Model overrides require host permission for an explicit user model request. A skill/configured tier does not override that restriction. When overrides are forbidden, omit the model field and inherit a suitable model; record configured intent and unmet cross-model independence. Do not reject otherwise-authorized delegation just because model selection was rejected. A same-model reviewer is not cross-model coverage.

Honor `CROSS_MODEL_PEERS` as recipient restrictions. Announce target, provider/model, effort, and any intermediary before sending reviewed content. The skill invocation and this disclosure authorize the normal pass unless policy says otherwise; no repeated approval prompt. Unknown or same family cannot earn cross-model agreement promotion.

## Dispatch and receipt

Use the available native subagent primitive (or native OpenCode CLI through shell only when the host explicitly supports that route and it does not evade policy). Never call another harness, detached bridge, or forbidden nesting workaround. Send the adversarial persona, exact captured `DIFF_A` and `DIFF_B` IDs, absolute workspace root, root-relative changed paths, semantic review map, review policy, and schema. Stage a large exact JJ patch under the workspace's absolute `.tmp/` and pass its path; do not truncate the review silently. All repository inspection runs with that workspace as absolute cwd. Native shell commands must be read-only for reviewers.

Start the peer before finalizing the local roster. A launch receipt is not a completed review. Record native launch/session ID, requested and actual identity/effort when attested, exact endpoints, artifact path, start/deadline, terminal status, and failure reason under `<run-dir>/peer-receipt.json`. Collect with native bounded waits/result delivery; no sleeps, status-file polling, detached processes, or artificial waiting turns. Budget is `CROSS_MODEL_HARD_SECS` (default 1200 seconds) from successful launch; retries share the same deadline. An artifact is usable only after schema validation and identity reconciliation. Stop/release this run's live agents where supported before returning. Never invent a cleanup capability.

Write valid findings to `<run-dir>/adversarial-<target>.json`. Peer and local adversarial reviewer must not both run the same brief. A valid independent peer replaces the local adversarial reviewer; other reviewers receive neither its findings nor one another's output. Required cross-model independence unavailable means coverage **incomplete**, even when a same-model fallback covers the adversarial lens. See `cross-model-recovery.md` for truthful recovery classifications.
