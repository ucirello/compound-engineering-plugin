# Cross-Model Judgment Pass

Run the activated conditional judgment lenses (`adversarial-document-reviewer`, `product-lens-reviewer`, `security-lens-reviewer`) through one separately selected OpenCode-native model route. The pass is additive and non-blocking, but missing required cross-model coverage is **incomplete**, never fully verified. Each lens retains its normal in-process reviewer. When the pass runs, also run exactly one `whole-doc` sweep of the full document: it has no in-process twin and its loss must be named explicitly.

## Resolve policy and the fixed route before dispatch

Read ordinary keys from `<repo-root>/.rocketclaw/config.local.yaml`, then `config.yaml`, where the absolute root comes from `jj workspace root`. First active valid scalar wins; empty is unset, invalid continues to the next layer and default. A present list/map replaces the whole key. `docs_root` remains config.yaml-only. With no repository, do not invent configuration.

Evaluate `cross_model_review_mode` first (`auto` default, `off` supported). `off` skips automatic dispatch unless the user explicitly requests this cross-model pass in conversation; a configured peer or project preference is not that opt-in. Record **disabled by checkout config** distinctly from unavailable tools or unverified independence. A live user prohibition wins.

Resolve target preference: live user request, `cross_model_peer`, active project instructions already in context, then first available attested-different target in `codex → claude → grok → antigravity`. Preserve target identities and intent: codex is the GPT family; claude is Claude; grok is Grok; antigravity requests Gemini; cursor requests default/Auto; composer requests Composer. OpenCode is the execution harness, not evidence of serving family. Do not invoke another harness's CLI, ACP adapter, or dispatcher to implement these routes. A fixed intermediary that cannot be represented natively is unavailable, not permission to silently change recipients.

Use `opencode.models` to resolve an exact available provider/model ID and supported reasoning variant. Record the runtime-published host model/family separately from requested peer target, serving provider/family, requested model, and actual served model. Never infer a family from a harness brand, environment marker, requested ID, or model self-claim. An unattestable host cannot satisfy automatic different-family selection.

Keep the former route preferences as selection intent, subordinate to user/config and actual capabilities:

| Target | Preferred model | Reasoning intent |
|---|---|---|
| codex | `gpt-6-luna` | extra-high |
| claude | `claude-opus-5-5` | high |
| grok | `grok-4.7` | extra-high; a specifically requested Cursor route used high/fast |
| composer | `composer-2.5[fast=true]` | fast |
| antigravity | `gemini-4-argon` | high; only if not explicitly pinned, unavailable Argon permits `gemini-3.8-flash` before egress |
| cursor / opencode | configured default | unverified unless runtime attests it |

Read `cross_model_model` and `cross_model_effort` using the ordinary layers; live user values outrank them. A pinned model must match the selected target family, and effort must be actually supported. Never silently swap a pinned value. If an unpinned preferred model is observed unavailable, resolve the closest same-target/same-family replacement from `opencode.models` and disclose it before sending. Otherwise report the exact missing capability.

`CROSS_MODEL_PEERS` is an optional egress restriction: unset/empty means unfiltered. When set, every target and intermediary recipient must be sanctioned. Preserve aliases: either cursor or composer admits the Cursor intermediary, but default Cursor requires cursor; grok alone does not admit Cursor; only antigravity admits that target, not gemini. Never add recipients silently.

## Permission, model selection, and depth

This skill explicitly requests peer reviewer delegation. Apply `references/dispatch.md`: a user-or-skill host rule permits these reviewers without a second approval, but an unconditional prohibition or actual denial remains binding. Model override permission is separate. If an explicit user request is required and absent, omit the optional native `model` argument; use inherited-model reviewers only where they satisfy the contract. They do not satisfy a required different-model pass merely by being separate contexts. Name the cross-model requirement incomplete when it cannot be met. Check effective nesting depth independently; classify actual errors as capacity, depth, permission, missing tool, or model-argument rejection. Never evade a restriction through shell or another harness.

## Disclosure and native dispatch

Interactive: place a prominent standalone cross-model disclosure with the team announcement, naming the requested model, reasoning, native route, and every recipient receiving document content. Name models as **requested**, not as proven served. Call the review independent only with attested different host/peer serving families. If actual receipt disagrees, disclose the mismatch; if no model was requested, say serving model unverified. In non-interactive mode, write the same egress audit to the run record without a user-facing announcement. The skill invocation sanctions permitted dispatch under this contract; it does not override host permissions or egress policy.

Create an owner-private run directory under `<absolute-workspace-root>/.tmp/rocketclaw/ce-doc-review/<run-id>` (or local `.tmp/rocketclaw/ce-doc-review/<run-id>` outside a repo). Reject symlinks and unexpected ownership; use restrictive permissions. Keep all slices, logs, receipts, and error-path data here, never in OS-global temporary storage.

Dispatch generic native `subagents` in the same bounded wave as the normal reviewers. Give each only its persona, schema, embedded document/slice, document type, and origin; the peer intentionally has round-1 framing, not the accumulated decision primer. Unified trio peers get exactly their twin's slice; legacy peers get the full document. `whole-doc` gets the full document once. Use the same resolved fixed model/route for every leg. Request read-only, least-privilege tool restrictions, an empty per-peer scratch context with no project hooks/MCP context, and no edits or further delegation. Verify what the native tool actually enforces; do not claim tool-less or filesystem isolation from a prompt alone. If required isolation cannot be provided, report the limitation and do not weaken the scope silently.

Use shell only for local evidence and validation, not cross-harness model launch or permission workarounds. Keep task IDs, start times, exact scope, selected route/model/effort, egress disclosure, and terminal outcomes in the run record. `CROSS_MODEL_HARD_SECS` is one shared hard budget (default 1200 seconds), with 480 seconds idle limit where observable; derive the collection deadline once as budget plus 10 seconds. Use supported native timeout/wait/cancel operations, never invent tools. Collect every started task before synthesis/return, including failure and cancellation outcomes. Release only agents this review owns after collection. If cancellation or collection cannot be confirmed, retain evidence and report unresolved work.

## Receipts, bounded recovery, and fold-in

Validate bounded result files are regular, non-symlink, owned files inside the private run directory before reading. Validate the `findings-schema.json` shape. Normalize reviewer to `<reviewer-name>-<target>` and downgrade peer `safe_auto` to `gated_auto`. Save `<reviewer-name>-<target>.json` only for usable validated results. Record `cross_model_target`, `cross_model_harness` (OpenCode), `cross_model_route`, `model_requested`, `model_actual`, and `independence_verified`. Actual-model claims need a runtime serving receipt; without it use `unverified`, not the requested value. Set independence true only from attested different serving families. Same-model/unknown results are attributed evidence, never agreement-promotion proof.

- Never-started policy/capability skip: name the reason, retain normal lens coverage, and mark cross-model coverage incomplete when owed. Not-activated lenses owe no peer.
- Dispatch-infrastructure crash: not a clean skip. Retry the same fixed native route only for a new plausibly recoverable failure within the shared deadline, retaining model, scope, isolation, and recipients. Stop when the failure repeats or the deadline expires. Explicitly report loss of the whole-doc broad read and corroboration.
- Permission denial or nesting limit: do not retry or bypass. Use an allowed independent parent-coordinator fallback only under the same contract; otherwise report incomplete.
- Provider overload: at most one same-route retry after a confirmed overload within the shared deadline. Quota/usage failure: no automatic route switching or repeated retries. Read bounded failure logs before classifying or cleanup.
- Authentication: attribute an account problem only from provider-capable dispatch/response evidence. A sandbox/network error alone is not proof the user is logged out; report the observed execution limitation.
- Refused unpinned default model: at most one same-family restart per affected lens after discovering an available compatible model, with disclosure. Never swap a configured/user-pinned model. New route or recipient always requires fresh resolution, sanction, and disclosure.
- Started timeout/failure/no usable output: report lens and terminal state. Do not fold raw or untrusted leftovers. Empty findings means no additional issues, not failed review.

Preserve all completed outcomes even when the main review stops incomplete without synthesis. When synthesis proceeds, peer corroboration promotes agreement only for `independence_verified: true` and the synthesis one-fix test, never a title/string match. Later-round suppression still applies. Classify and read back needed evidence before cleanup; delete only consumed owned scratch artifacts with existing authorization, never unresolved work. Keep evidence and report any cleanup blocker rather than claiming success.
