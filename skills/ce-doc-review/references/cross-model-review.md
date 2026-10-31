# Native cross-model judgment review

When any conditional judgment lens is activated, dispatch its corroborating peer and one `whole-doc` broad reviewer through native OpenCode subagents in the same bounded wave. Each lens peer receives exactly its twin's slice; whole-doc receives the entire document once. Read `dispatch.md` for permissions, depth, capacity, model policy, payload and lifecycle. No external harness, shell dispatcher, escalation helper or permission bypass is allowed.

## Resolve once before dispatch

Read ordinary keys from `<absolute-workspace-root>/.rocketclaw/config.local.yaml`, then `config.yaml`; first valid active value wins. Keep config.example.yml as configuration documentation, not an override. Ignore commented values. `cross_model_review_mode: off` disables automatic peers unless the user explicitly requests this pass in conversation; a live prohibition always wins. Record that policy reason distinctly. `auto` is the default. Resolve `cross_model_peer`, `cross_model_model`, and `cross_model_effort` as routing/tier intent; user instructions take precedence. Preserve explicit model pins: never silently substitute a configured or user-requested model. `CROSS_MODEL_PEERS`, when set, restricts recipients; unset means no extra allowlist, not a permission grant.

Discover exact available model IDs and reasoning variants with `opencode.models`. Select one sanctioned target/model for the entire review, respecting model-override policy. If overrides are forbidden without a user model request, omit the optional model argument, use the suitable inherited model, and disclose the unmet configured tier/pin. Inherited same-model work does not fulfill cross-model coverage. Never route through another harness to satisfy a denied model operation.

Before content leaves, disclose the requested provider, model, reasoning level and full-document/slice egress recipients prominently in interactive mode. Do not infer serving identity from a request. Only attestably different serving families establish cross-model independence; unknown identities remain unverified. Preserve native receipts and record requested and actual identities separately.

## Dispatch and collect

Each peer reads the selected persona, subagent template and findings schema in full. Use `whole-doc-reviewer.md` for the sweep. Provide document type, origin, settled decisions and the same slice as the local twin; the broad sweep gets the full document. Pass resolved pack constraints. Peers are read-only and receive only the authorized review scope. Do not create an unapproved workspace: if native isolation cannot enforce that scope, report a safe blocker rather than relaxing it. All run artifacts belong under `<absolute-workspace-root>/.tmp/doc-review/<run-id>` (local `.tmp` for a document outside a repository).

Capture a receipt per owed lens and sweep: reviewer, native agent/session ID, requested model and effort, actual model if attested, independence_verified, slice, start/outcome, failure reason, and validated result path. Validate against findings-schema.json; force reviewer to `<lens>-<provider>` and downgrade peer `safe_auto` to `gated_auto`. Malformed/raw output is never fold-in evidence. Peers do not receive the prior-round decision primer; synthesis still suppresses previously settled findings.

Queue capacity rejections and retry only after a slot frees. Classify permission denial, actual nesting depth, missing tool, rejected model, authentication, quota, timeout and malformed output separately using actual errors. No speculative credential probes. Retry only the same authorized route for a genuinely recoverable infrastructure error within the bounded review deadline; stop on repeated failure or quota evidence. Never change an explicit recipient/model or widen scope as recovery. Denial/depth errors are not retry invitations.

Collect every started agent to a terminal outcome before synthesis/return and release only via supported lifecycle operations. Preserve receipts and unresolved evidence if collection fails. Never delete uncollected evidence or claim cleanup succeeded without verification.

## Coverage contract

This pass is additive: local persona findings may still be synthesized when a peer fails, but required independent coverage is **incomplete**, never fulfilled by same-model or inline work. Report each owed missing lens, the lost whole-document broad read, terminal state/reason and unmet tier or pin in Coverage (and structured non-interactive results). A policy-disabled pass is `not run — disabled by checkout config`, not a failure. Empty validated findings mean `no additional issues`, not missing coverage. Never claim complete cross-model coverage when any owed independent pass is absent or unverified. Promote agreement only with `independence_verified: true`, an in-process contributor, and the synthesis one-fix test; never stack peer promotions.
