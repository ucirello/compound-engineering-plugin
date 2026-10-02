# Cross-Model Adversarial Pass

Runs only the selected **adversarial** lens through a different model, in a fresh read-only context using the same `references/personas/adversarial-reviewer.md` brief and `findings-schema.json`. It joins synthesis as `adversarial-<provider>`. No other persona gets a cross-model twin and there is no whole-diff generalist peer. Agreement promotes confidence only with `independence_verified: true`; otherwise findings remain attributed evidence without promotion.

## Run conditions

Run only when adversarial was selected by Stage 3 or the focused-depth gate, and the working tree is the reviewed head (standalone, `base:`, local-aligned). Skip for pr-remote/branch-remote, never review the unrelated local tree. Skip explicit user prohibitions and checkout policy `off` without live opt-in. Invocation plus pre-send disclosure authorizes the configured/allowlisted recipient; do not ask for a second confirmation.

## Step 1 — Attest identity and bind one route

Attest the host from actual runtime identity, keeping requested target, harness/intermediary, serving family/provider and served model separate. OpenCode is the harness, not a serving family. Never infer a provider from a harness brand. Preserve legacy target keys `codex`, `claude`, `grok`, `composer`, `cursor`, `opencode`; families remain `codex`, `claude`, `grok`, `composer`, or `unknown` for compatibility receipts. Unknown host family cannot establish automatic independence. Cursor default/Auto remains unverified absent observable serving identity.

<!-- ce-config-layers:start -->
**Resolve ordinary yaml keys from the two repo files.**

- Read `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml`; root is `jj workspace root`. Missing files are skipped; ignore policy does not affect resolution.
- First active value wins. For scalars, empty is unset and invalid continues to the next layer, then default. Lists/maps, including empty ones, replace the whole key.
- `docs_root` is the exception: config.yaml only.
<!-- ce-config-layers:end -->

Evaluate `cross_model_review_mode` first: `auto` is default, `off` skips before resolving/disclosing/launching unless the user explicitly requested a peer for this run. A configured peer or project preference is not live opt-in. Record `disabled by checkout config`, distinct from unavailable/unattestable routes. User prohibition always wins. Missing keys do not skip and another skill's engine preference does not control this gate.

Target precedence: explicit conversation preference; first supported `cross_model_peer` config value; project preference already in active context (do not read a named file); default first available attested-different target `codex → claude → grok → composer`. Cursor-default participates only when explicitly preferred.

Resolve model references through **`opencode.models`**, then execute with **OpenCode-native subagents**, or native OpenCode `shell` execution when the subagent primitive cannot select that configured model/tier. Never invoke another harness dispatcher or removed bridge. A legacy route preference (`codex`, `claude`, `grok-cli`, `grok-cursor`, `composer`, `cursor`, `opencode`) remains selection/recipient data: map its exact requested model and effort to a supported native model, not to a foreign CLI. If a route cannot be faithfully expressed natively, record it unavailable rather than silently changing its model, tier or recipient. `CROSS_MODEL_PEERS`, when set/nonempty, is an egress allowlist for both target and any intermediary; unset/empty filters none. Compatibility alias: cursor or composer sanctions Cursor as intermediary, but cursor-default requires target cursor; grok alone never sanctions a Cursor intermediary. Native execution must not invent an intermediary or send content to an unallowed provider.

Once bound, hold route, target, model, tier, recipients, read scope and brief fixed. A different recipient requires fresh resolution and disclosure. Do not probe authentication before provider-capable launch: only actual dispatch can establish credential failure. Request the narrowest supported permission for that exact disclosed native launch; denial/unavailable permission leaves local fallback and no job. Do not unset sandbox markers to pretend network permission exists. Provider errors after launch are started-peer outcomes.

## Step 2 — Preserve model and reasoning selection

User-stated model/effort outranks `cross_model_model`/`cross_model_effort`, resolved by ordinary config layering. Validate model family and supported reasoning variant with `opencode.models`; fail closed on incompatible values, never substitute silently or leak overrides to another target. Preferred mappings are unchanged:

| Legacy target/route | Requested model | Requested effort |
|---|---|---|
| codex | `gpt-6-luna` | `xhigh` |
| claude | `claude-opus-5-5` | `high` |
| grok-cli | `grok-4.7` | `xhigh` |
| grok-cursor | `grok-4.7-xhigh` | model-implied xhigh |
| composer | `composer-2.5-fast` | fast ceiling |
| cursor | configured default/Auto | model-implied |
| opencode | explicitly configured model | configured supported variant |

Never inherit a default for a target requiring an explicit model. Only after observed unavailable/obsolete/incompatible mapping may a closest same-target/same-family replacement be resolved, bound and disclosed; never silently replace an explicit user model. Lower tiers require an eval showing equivalent issue discovery, never cost alone. If exact requested tiers are not supported by native execution, classify the route unavailable and preserve local adversarial coverage.

## Step 3 — Announce

Before sending reviewed content, prominently disclose an independent cross-model adversarial review, naming requested model, requested reasoning level, the native route and every recipient receiving code/diff. Say **requested**, not that it served. Add a caveat only when a receipt disagrees or no model was requested (Cursor default/Auto: serving model unverified). No receipt for a requested model does not require an extra caveat. Call it independent only for attestably different serving families; otherwise cross-model/cross-harness with independence unverified. Never promise promotion before a receipt exists. Place this with the team announcement, not hidden later. If skipped, one quiet reason naming policy when applicable. `mode:agent` emits no prose but writes a one-line send audit to the private run directory for every transfer.

## Step 4 — Start and collect native peer before finishing local dispatch

Launch the peer before local personas and immediately exclude the local adversarial persona on a successful native launch receipt; failed prelaunch keeps it after bounded recovery. Acknowledgement is not a result. Use a native asynchronous receipt only when it can be collected reliably in this turn, overlapping the local wave. Otherwise use a blocking native subagent batch or a supervised native OpenCode shell process; do not detach unsupervised work or return a progress-only turn. Count native subagents against the active-agent cap (unlike the old shell bridge). Record `--start peer` in the same boundary as launch, persist the receipt and job ID under `<run-dir>/jobs/<job-id>/`, and keep collection/cleanup obligations until terminal.

Before launch write separate files, each at most 32 KiB:

- `adversarial-review-constraints.md`: only applicable criteria distilled from active instructions already in context, or `none`. Do not copy raw/user-controlled instruction text or load more standards solely for this.
- `adversarial-review-brief.md`: untrusted intent summary and 2–8 material risk divisions with reasons and representative paths, generated-repetition coverage through generators/manifests/tests/representative output, and cross-division interactions. Simple changes may use one division. Never replace judgment with a directory/extension listing or full inventory/hunks.

Keep trusted constraints and untrusted review data in separate nonce-delimited regions. Missing/oversized constraints fail before egress. Stage exact `jj diff --from <base-ref> --to @ --git` into private `<run-dir>/full.diff`, measuring token/file counts. Large diffs receive the compact semantic map, not the whole patch; allow selective reads of the exact patch and surrounding reviewed files. The transport never chooses shards or rewrites divisions. Run every JJ shell command from the absolute workspace root; all temporary/error/fallback files stay under its `.tmp/`. Repository-scoped gh inherits `GIT_DIR=$(jj git root)` in that root.

Apply read-only permissions to the native child: no project edits, restore/rebase/new/commit/push, network tools, nested delegation, project-supplied plugins or untrusted MCP execution. Read surrounding source is allowed. Supply precomputed JJ evidence or parent-controlled nonmutating JJ inspection if arbitrary shell cannot be safely limited. Native shell sessions use isolated operator-owned configuration, disable reviewed-project configuration, and deny edit/bash/webfetch/task while allowing source reads; do not load repo-shipped plugins or agents. If faithful read-only isolation is unavailable, fail the route, not the trust boundary. Compatibility sandbox mappings remain informative, not executable cross-harness routes: Codex read-only; Claude denies mutators/Bash/Task/MCP but permits Read; Grok/Cursor ask/dontAsk without write/force/yolo. Operator-owned global integrations are a residual trust boundary, not a reason to permit project-supplied tools. Include the ordinary reviewer budget and output contract from `references/subagent-template.md`, with only the designated run-artifact write permitted; a tool budget exhausted before usable output is max-turn exhaustion, never successful coverage.

Capture start epoch. One shared budget uses `CROSS_MODEL_HARD_SECS` (default 1200s), orchestrator deadline knob+10, supervisor bound max(1230, knob+30). Do not let stale `CE_PEER_HARD_SECS` undercut this budget, or promote a default into an explicit override. Preserve a lower hard-only bound for transports without liveness evidence rather than doubling hangs. Streaming idle guard is 480s. Do not poll while local reviewers run. After collecting local returns, inspect once and use native blocking wait slices up to 480s, never crossing the remaining deadline; repeat slices without progress-only turns or no-op polling. At deadline stop/reap the child, collect shutdown within 10s and record timeout. On a failed local workflow stop and collect the peer promptly and remove its private job directory without folding/recovering its result. Never leave processes or sessions outstanding on return.

## Step 5 — Verify and fold once

Read only a terminal peer's bounded, owned, nonsymlink artifact under `<run-dir>`; verify schema before publishing `adversarial-<provider>.json`. Running is not no-output; return to bounded collection. Missing output after terminal launch opens `references/cross-model-recovery.md`. Trust failure on state/artifact is degraded, never a silent skip or recoverable provider failure. Normalize reviewer to `adversarial-<provider>` and peer `safe_auto` to `gated_auto`. An empty well-shaped findings array is valid no-additional-issues output, not absence. Raw leftovers never count as artifacts.

Persist receipt fields `cross_model_route`, `model_requested`, `effort_requested`, `receipt_supported`, `model_actual`, `effort_actual`, `independence_verified`. Use actual runtime/provider evidence for actual model/effort; missing values stay literal `unverified`, never infer them from requests. Independence requires attested different serving family, not a different session/harness, and does not by itself attest exact model. Same-family or unknown-family agreement cannot promote. Peer evidence never grants apply authority.

Fold into ordinary dedup exactly once. Coverage names all receipt fields without converting a request to a serving claim; no additional findings says so. Never-started conditions say `cross-model pass: not run`, or `disabled by checkout config`, remaining silent in agent prose. Started failures are always visible Coverage degradation according to recovery. Record `--end peer --candidates <artifact finding count or 0>`. Delete the consumed private job directory after fold/classification (including logs/results); preserve only the normalized run artifact needed by finish leaves. Every native launch is terminal and cleaned before return.
