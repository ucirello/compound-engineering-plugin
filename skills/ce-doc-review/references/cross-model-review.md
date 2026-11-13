# Cross-model judgment pass

Run this additive pass only when adversarial, product-lens or security-lens was activated. Run each activated lens plus exactly one `whole-doc` sweep in the same bounded parallel wave as ordinary reviewers, using one fixed target/model/route for the document. Feasibility, coherence and scope do not trigger it.

## Policy, model and disclosure

Resolve ordinary keys from `.rocketclaw/config.local.yaml`, then `config.yaml` at the absolute `jj workspace root`: first active nonempty valid scalar wins; invalid values continue then default; lists/maps replace whole keys including empty values. `docs_root` is config.yaml-only.

Evaluate `cross_model_review_mode` first (`auto` default, `off` disables automatic review unless this conversation explicitly requests it). Live prohibitions win. Resolve target from conversation, `cross_model_peer`, then an available different-provider route. Respect `CROSS_MODEL_PEERS` when set; unset means unfiltered, empty permits none. Preserve target intent (`codex`, `claude`, `grok`, `cursor`, `composer`, `opencode`, `antigravity`, `pi`) but execute through native OpenCode model discovery (`opencode.models`) and native subagents, never those harness CLIs or dispatch bridges. Unavailable required routes remain incomplete.

Conversation model/effort requests outrank `cross_model_model` and `cross_model_effort`. Explicit pins run exactly or remain unmet. Default tier intent is high, native Grok extra-high and Composer fast at its ceiling. Discover current IDs/variants rather than guess. An unavailable unpinned preferred ID permits one discovered same-family replacement before egress; Antigravity's editorial Argon preference permits Flash before egress, never for an explicit pin. No silent recipient changes.

Apply `subagent-model.md`'s distinct delegation, model-selection and depth gates throughout dispatch and recovery. Skill-requested reviewers satisfy a user-OR-skill rule. Forbidden model overrides must be omitted; suitable inherited models can perform ordinary reviews, not satisfy a required different-model pass. No permission/depth bypass through shell or another harness.

Attest host and served model/family from runtime receipts, not requested IDs, harness branding or model claims. Keep target, intermediary, serving family and actual model distinct. Before egress prominently disclose requested model and effort, native route, every recipient and that full document content is sent there. Call it independent only with attested different serving families; otherwise state independence unverified. Non-interactive runs retain the disclosure as evidence. Route/recipient changes require renewed resolution, sanction and disclosure.

## Dispatch and isolation

Each trio peer receives the same persona, template, schema, origin and document classification as its ordinary twin. Unified artifacts use the same reviewer-specific slice; legacy documents use the full document. The mandatory single whole-doc sweep receives the full document. Do not send accumulated peer claims or later-round decision primers: peers retain round-one framing and synthesis R29/R30 handles suppression.

Use private, owned, non-symlink run paths beneath the target workspace's `.tmp/rocketclaw/ce-doc-review/` (local `.tmp/` outside repositories), including diagnostics and error paths. Use empty per-peer scratch, embedded document content and enforced read-only least privilege without project context or MCP. If native capabilities cannot enforce this isolation, report the route incomplete rather than claiming prompt instructions are a sandbox.

Record handles, start times, requested route/model/effort, actual receipt, terminal outcome and diagnostics. `CROSS_MODEL_HARD_SECS` defaults to 1200 seconds; use one shared bounded budget and 480-second idle intent, disclosing unsupported enforcement. Queue temporary concurrency backpressure only while started jobs can free capacity. Classify actual nesting-depth errors separately from capacity, denial, missing tool or rejected model arguments; do not loop on depth failures.

## Collection, recovery and coverage

Await and classify every started reviewer before return, including failures. At the deadline use only supported native cancellation/release of run-owned jobs, then collect the terminal outcome. Preserve unresolved evidence and report lifecycle blockers.

Validate bounded owned regular-file JSON against `findings-schema.json`. Normalize reviewer to `<reviewer-name>-<provider>`, downgrade `safe_auto` to `gated_auto`, and retain `cross_model_target`, `cross_model_harness` (OpenCode), `cross_model_route`, `model_requested`, `model_actual`, `independence_verified`. Raw leftovers are not fold-in artifacts. Missing receipts never prove the requested model served.

Distinguish never-started policy/capability skips from started failed/timeout/lost-result jobs. Shared infrastructure failure loses whole-doc broad coverage and corroboration, not merely a lens covered by its ordinary twin. Permit one plausibly recoverable same-route infrastructure retry within the budget, holding recipient/model/isolation/read scope fixed; stop on repeated failure. One actual overload permits one same-route retry within that budget. Never retry denials/depth failures or repeatedly retry quota failures. Name observed authentication/capability errors without guessing the user's account is logged out from sandbox-shaped evidence.

A rejected explicit model stays unmet; an unpinned default permits at most one permitted, disclosed same-family discovered replacement. Same-model separate reviewers are not cross-model independence.

This pass is non-blocking for ordinary synthesis, but unmet cross-model requirements are incomplete, never fully verified. Name every owed lens and whole-doc sweep that did not fold in, including never-started legs, in structured non-interactive coverage. Only completed usable empty findings mean no additional issues. Merge via synthesis's one-fix test; promote agreement one anchor step only when `independence_verified: true`, otherwise retain attributed evidence without promotion. Collect outcomes without fixes/synthesis when the ordinary review stops incomplete.

Before cleaning consumed run-owned scratch, classify outcomes and preserve required evidence outside it. Never delete ambiguous/user-owned state; report unresolved cleanup instead.
