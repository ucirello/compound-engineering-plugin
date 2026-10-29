# Stage 3d: Native cross-model adversarial review

Use OpenCode-native model discovery (`opencode.models`) and native subagents; never launch a CLI harness, adapter, detached peer runner, or another harness through shell. Configuration remains authoritative: read `.rocketclaw/config.yaml` and `config.local.yaml`, retaining configured peer allowlists, mode, explicit target, model and effort intent. Local overrides take precedence. An explicit prohibition on external review wins; `cross_model_review_mode: off` requires a live opt-in. Do not silently discard a configured route or lower its tier.

Preserve editorial model/tier intent when no configured override exists; discover exact available native IDs rather than inventing provider prefixes:

| Configured target/route intent | Requested model | Reasoning intent |
| --- | --- | --- |
| codex | `gpt-6-luna` | xhigh |
| claude | `claude-opus-5-5` | high |
| grok / grok-cli | `grok-4.7` | xhigh |
| grok-cursor | `grok-4.7[context=256k,reasoning_effort=high,fast=true]` | model-implied high/fast |
| composer | `composer-2.5[fast=true]` | fast |
| antigravity | `gemini-4-argon` | high |
| cursor / opencode default | inherited/auto | unverified |

The existing Antigravity account-entitlement fallback intent is `gemini-3.8-flash` before any content is sent, only when the configured route permits that fallback and host model-selection permission allows it; disclose it. Native unavailability is otherwise incomplete coverage, never permission to dispatch the old CLI/intermediary. Default/Auto is not evidence of distinct-model independence. Overrides `cross_model_model` and `cross_model_effort` retain precedence within the same permitted target/family; invalid or unavailable required overrides fail closed rather than silently changing models. The Codex Luna/xhigh choice retains its benchmarked cost/detection intent; do not lower tiers merely for cost.

Interpret delegation, model selection and nesting independently. This skill explicitly requests reviewer delegation: under a user-OR-loaded-skill delegation rule that is sufficient, without a second approval. A higher-priority unconditional prohibition, missing native tool or actual permission denial remains binding. Permission to delegate is not permission to override a model. If the host requires an explicit user model request for the optional `model` argument, omit that argument unless authorized. Suitable inherited-model reviewers may cover ordinary lenses. They are distinct reviewers, not proof of different-model independence. A required fixed-route or cross-model pass that cannot be satisfied is **incomplete coverage**, never fully verified.

Check effective nesting capacity independently (configuration depth at least 3 is the installation prerequisite, not proof that this call has a free level). Classify the actual native error as depth/capacity, permission, model-argument rejection or unavailable tool. Never evade a denial/depth limit through shell or another harness.

Before dispatch, disclose the one selected recipient, actual provider/model when known, reasoning tier, and that reviewed code leaves the machine. Existing invocation authorization covers configured/allowlisted review, subject to actual host permissions. Resolve a concrete available model using `opencode.models` only when model selection is permitted. Never infer the served model from a harness name, environment marker or model's own claim. Bind one route, target, exact captured base/head, persona brief and read-only trust boundary. Do not switch recipients automatically after a failure.

Stage the exact captured JJ range in a private workspace-local `.tmp/rocketclaw/ce-code-review/<run-id>/` file. Large diffs remain files, not whole prompts: provide the compact semantic review map (changed systems, invariants, cross-cutting contracts, deletion/rename risks) and the exact file path; the reviewer reads relevant sections selectively. This is transport sizing, not permission to omit changed surfaces. Remote scope reads the captured head with `jj file show -r <head> <path>`, never unrelated checkout paths. All JJ calls use the target absolute workspace root as cwd. No direct Git executable is allowed.

Dispatch the adversarial native subagent before finalizing the local roster, and collect it in the same bounded native batch as other reviewers. A successfully launched peer replaces the duplicate local adversarial persona. Pass `references/personas/adversarial-reviewer.md`, `references/subagent-template.md`, findings schema, exact endpoints, run directory, semantic map and diff artifact. Do not feed it another reviewer's findings. Persist launch identity and requested versus actual model/provider/tier in the receipt; do not fabricate identities unavailable from runtime evidence.

Use the native blocking collector and its actual terminal result, not a progress acknowledgement. Bound the peer by `CROSS_MODEL_HARD_SECS` (default 1200 seconds), preserve the native launch's identity and stop/release it through supported lifecycle tools before returning on timeout. No detached jobs, shell polling, scheduled wakeups or bypasses. Validate compact JSON against the findings schema and persist `<run-dir>/adversarial-<target>.json` only after valid normalization. Record the final artifact and any failure exactly once for Stage 5 fold-in. Independence is attested only when actual serving models/families satisfy the required distinct-model contract; same-model agreement cannot receive cross-model promotion.

Read `cross-model-recovery.md` for bounded failure handling. If the host cannot run required independent review, continue only where the workflow explicitly permits degraded coverage, naming the missing pass; never manufacture a completed shipping gate.
