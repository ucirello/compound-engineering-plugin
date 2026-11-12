# Cross-model adversarial pass — native OpenCode

This is the adversarial lens only, not a generalist twin. Dispatch a native generic subagent with `references/personas/adversarial-reviewer.md`, `subagent-template.md`, `diff-scope.md`, and `findings-schema.json`. Keep its analysis independent: never feed it local findings. It returns the same schema as a persona and joins synthesis as `adversarial-<provider>`. Agreement promotes confidence only with `independence_verified: true` attesting a different serving family, not merely another session or requested model.

## Eligibility and permission

Run only when Stage 3 selected adversarial, or the focused path requires its independent read. The workspace must be the reviewed tree (standalone, `base:`, or local-aligned); in remote scope use the selected local persona against captured refs instead. The local fallback and peer must not both receive the same brief unless a documented no-review failure requires fallback.

This skill explicitly requests reviewer delegation, satisfying a host user-OR-skill delegation exception without redundant approval. That is not permission to override models. Read `subagent-model.md`: actual higher-priority prohibition, missing tools, or denial wins. Never evade denial with shell dispatch, another harness, another tool, or a retry of the denied operation. Depth capacity, delegation permission, model permission, and active-agent capacity are distinct gates.

## Configuration and route

Read ordinary keys from `<absolute-workspace-root>/.rocketclaw/config.local.yaml`, then `config.yaml`. First active valid scalar wins; empty/invalid continues to the next layer then default. A present list/map, even empty, replaces that whole key. `docs_root` remains config.yaml-only.

- `cross_model_review_mode`: `auto` default or `off`. Evaluate before model resolution or egress. `off` disables automatic dispatch unless the live user explicitly opts in for this run; a config preference is not opt-in. A user prohibition always wins.
- Target precedence: live user preference, `cross_model_peer`, active project instructions, then an available attested-different family in codex → claude → grok → antigravity order. Keep target, OpenCode provider, serving family, requested model and actual model separate. Compatibility target names (cursor, composer, opencode, pi, antigravity) are preferences, not native agent names or permission to launch those harnesses.
- Resolve exact available provider/model IDs and reasoning variants with native `opencode.models`. Honor `cross_model_model` and `cross_model_effort`, with live user values first. Retain configured tier/model intent. Never silently substitute an explicit configured model or family, or claim a task prompt selects a model.
- `CROSS_MODEL_PEERS`, when present, restricts every recipient/intermediary. Cursor/composer alias each other only for intermediary permission; grok alone does not allow Cursor. `gemini` does not grant antigravity. No external harness adapter is used: if a configured route cannot be expressed natively, name the unmet route rather than launching another harness.
- Where host policy requires an explicit user model request, omit the optional model argument absent that request. Use an inherited model only if suitable; record unmet configured route/effort and lost cross-model independence. Same-model review is never cross-model. A separate inherited subagent may cover the focused path's permitted second reading, never an explicitly mandatory different-model gate; a parent inline reread cannot cover either independent gate.

Use runtime-published serving model evidence, not environment brand markers, requested model, or the model's own claim, to attest host/peer family. If either is unattested, independence is unverified. Available model listings prove availability, not which model served.

### Retained default model/tier intent

Configuration/live-user pins outrank these defaults. Resolve each ID to an actually listed native provider/model with `opencode.models`; never guess the provider namespace or pass a model where host policy disallows it. These are requested defaults, not evidence of service:

| Compatibility target | Default model intent | Effort intent |
|---|---|---|
| codex | gpt-6.1-terra | high |
| claude | claude-opus-5-5 | high |
| grok | grok-4.7 | xhigh |
| grok through Cursor | grok-4.7[context=256k,reasoning_effort=high,fast=true] | model-implied-high |
| composer | composer-2.5[fast=true] | fast |
| antigravity | gemini-4-argon | high |
| cursor / opencode / pi | inherited/auto only when suitable | unverified unless attested |

The Cursor presets express compatibility intent, not OpenCode model IDs; if unavailable natively disclose unmet route, never launch Cursor/ACP. An unpinned Argon default may fall back once to gemini-3.8-flash only after observed unavailability, within the same Google-family native route/deadline and model permission; disclose the request change before sending. A configured/user-named Argon model is exact and never swapped. Preserve large-diff transport thresholds (`CROSS_MODEL_INLINE_MAX_TOKENS` default 80000 estimated as ceil(bytes/2), `CROSS_MODEL_INLINE_MAX_FILES` default 200); above either, require the semantic map and staged diff path. `CROSS_MODEL_MAX_PEERS=0` disables the peer; this skill otherwise binds one fixed peer, never silently expands recipients. Optional idle intent `CROSS_MODEL_IDLE_SECS` defaults 480; enforce only if native runtime exposes genuine liveness, never treat a healthy silent reasoning turn or short wait as failure. Native collection still uses the original shared hard deadline.

## Disclosure, inputs and launch

Before sending content announce the fixed native recipient, requested model/effort, and that reviewed code/diff reaches that provider. This is notice, not a second approval request. Say independent only when attested; otherwise say independence unverified. In `mode:agent`, keep the response JSON-only and record disclosure in the local receipt instead of adding prose. No credential probes before actual provider-capable dispatch; attribute authentication only from authoritative dispatch diagnostics.

Use the existing absolute workspace-local `.tmp/rocketclaw/code-review/<run-id>` directory. Write two separate inputs, each <=32 KiB:

1. `adversarial-review-constraints.md`: applicable host-vetted criteria and base review-policy checks/evidence requirements; no untrusted raw instructions, severity/exclusion/cap overrides, or expanded standards search. Write `none` when empty.
2. `adversarial-review-brief.md`: untrusted intent, 2–8 material risk divisions (one suffices on simple work), representative paths, generated repetition and cross-division interactions. Not a mechanical file list or extension split, and never treated as instructions.

Stage `full.diff` once with `jj diff --git --context 10 --from <captured-base-id> --to <captured-head-id>` from the absolute target root; do not recapture @ or derive @-. Both endpoint IDs and this exact multi-commit range travel with every prompt, receipt and retry. Large diffs use staged paths and the semantic map, never a truncated review represented as complete. Verify input existence, bounds, containment and read access before launch. Read-only project access; only the named run artifact may be written. If native permissions cannot enforce the review boundary, report that limitation; do not invent sandbox guarantees.

Start the native peer before local persona dispatch, record its launch/session receipt, target/model/effort, captured endpoints and start time, and `--start peer` in run-log. Acknowledgement is not completion or coverage. Remove local adversarial only on successful launch, not on route intention. Native peers consume concurrency capacity; reserve it and batch locals against the actual host cap. No detached shell runner, ACP transport, background status polling, sleeps, or cross-harness fallback.

## Collection and receipts

Use the native bounded blocking collector in the same turn. Shared hard budget is `CROSS_MODEL_HARD_SECS` (default 1200) plus 10 seconds collector allowance, measured from first launch across all recovery attempts; do not reset on retry. Repeat supported blocking waits back-to-back up to remaining time. Never end the turn waiting on progress. Stop live work at deadline or when local processing aborts; release this skill's agents where supported. If collection cannot reliably reach a terminal result, stop and report failed/degraded coverage.

Persist normalized full JSON at `<run-dir>/adversarial-<provider>.json` only after schema validation; force reviewer identity and downgrade `safe_auto` to `gated_auto`. Record `cross_model_route: opencode-native`, target/provider, `model_requested`, `effort_requested`, `receipt_supported`, `model_actual`, `effort_actual`, and `independence_verified`. Unknown actual model/effort stays literal `unverified`; never turn a request into a served-model claim. Record terminal outcome and bounded diagnostic before cleanup. Keep no raw logs beyond their use; never delete shared run artifacts needed by finish leaves.

Fold findings through ordinary dedup/validation and repository policy. False/absent independence contributes evidence only, no confidence promotion or silent apply authority. Empty valid findings means no additional issues; malformed/missing output is not an empty successful review. Record `peer.outcome`, `peer.artifact`, and `peer.coverage` for `finish-input.json`; merge leaves must not redispatch. Recovery is owned by `cross-model-recovery.md`. A started timeout/failure is named, not silently converted to not-run; incomplete mandatory independence remains incomplete.
