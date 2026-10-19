# Cross-Model POV Panel

The panel obtains independent peer POVs, reconciles material disagreement, and returns one ce-pov decision. ce-pov remains the decision-maker: peers are cross-checks, never substitutes or votes. The panel is read-only and non-blocking; every branch ends in a panel POV, a solo POV with an availability note, or the ordinary blocked-on-missing-context result.

## 1. Resolve subject and participation

Resolve conversational shorthand from the active conversation; return missing context when competing subjects would materially change the result. A summons is an affirmative request to consult or reconcile other models: named peers, a panel, a cross-check, or `oracle`, including calling-skill arguments. Declining or merely mentioning consultation is not a request. A caller's paraphrase does not cancel a summons still present in another readable channel.

- **Named peers:** exact and uncapped. Announce every named target and run each permitted, available participant. Never silently replace an explicitly requested model. `Cursor` means its configured default/Auto choice; `Composer` is a distinct model choice, not an alias. Preserve these compatibility meanings without invoking either harness's dispatcher.
- **Bare oracle:** select up to two reachable, attestably different-model peers using conversation preference, local configuration, active project conventions, then the preference order `codex -> claude -> grok -> antigravity` (Gemini). Cursor default and Composer run only when named or configured as preferences.
- **Explicit unnamed cross-check:** skip the correction-cost check and announce available selected peers.
- **No request:** form the solo POV first. Offer consultation only for Tier 2/3 when meaningful downstream work or shared, public, security, or data commitments make correction costly. Never offer for Tier 1 or a warm mid-session second opinion.

Zero reachable peers means solo plus an availability line when consultation was requested. A POV without a summons carries no panel note.

## 2. Permission, native routing, and independence

Use OpenCode-native `opencode.models` and subagents, with shell only for permitted local evidence reads and artifact handling. Do not launch another harness, ACP adapter, dispatcher, or removed helper. Configuration files remain the source of desired models, tiers, and routes; native execution must preserve that intent or report the unavailable requirement. Historical target names describe requested compatibility, not permission to substitute another recipient.

Check three independent gates before each initial or reconciliation dispatch:

1. **Delegation permission:** this skill explicitly requests peer reviewers when a panel is selected. A host rule allowing user OR loaded-skill requests is satisfied without asking again. A loaded skill that never requests delegation would not suffice. Respect unconditional higher-priority prohibitions, missing tools, and actual permission denials. Never bypass them through shell or another harness.
2. **Model-selection permission:** discover exact available model IDs with `opencode.models` only as allowed. A configured tier or skill request does not authorize a model override when the host requires an explicit user model request. In that case omit the native subagent's optional `model` argument and use suitable inherited-model reviewers. Preserve the intended route and tier in the record, and disclose unmet requirements. An explicit model request cannot silently become another model.
3. **Depth and capacity:** inspect effective runtime configuration and current nesting evidence before launch. The package-project `experimental.subagent_depth` default is not proof of a consumer's effective limit or remaining capacity. If unknown, record uncertainty. Classify actual launch errors as depth/capacity, permission, rejected model argument, or missing tool; do not infer permission denial from a nesting-limit error. Never evade depth limits or retry a denied operation. An allowed parent coordinator may perform the native dispatch with the same payload and constraints; inline solo analysis cannot replace an independent peer.

Track target, actual native route/provider and intermediaries, requested model, served model, and `independence_verified` separately. Attest the host and peer serving models only from runtime receipts, not the model's own claim, installed CLIs, product names, or inherited environment markers. Missing receipt means `model_actual: unverified`. Set independence true only when the served family is attestably different from the host's. Same-model reviewers are separate reviewers, not different-model corroboration. If a required cross-model pass or fixed route is unavailable, report coverage **incomplete**, never fully verified.

Resolve a fixed native route before sending project content. Confirm all actual external recipients are permitted. Announce selected peers and read-only review in ordinary language; do not promise that prompt scope hides secrets. A named peer unavailable under these rules is reported, not silently replaced or dropped. A retry adding an unexpected provider or intermediary needs disclosure and approval; routine authorized consultation and reconciliation with the same recipients do not. Active external-consultation approval rules still apply.

## 3. Scope, identity, and payload

Normalize one repository-relative read root plus optional ordered include/exclude patterns and pass the identical scope to every peer. Never broaden it. Peers inspect shared subject files directly; inline only material absent from the workspace. Read-only instructions and patterns are cooperative, not a confidentiality boundary or write sandbox. Peers must not mutate the project or intentionally inspect outside scope.

Freeze repository-scope identity before dispatch: current JJ revision plus a digest of current changed and untracked content within scope, including relevant ignored material that peers can read. Use JJ status/diff/file reads from the verified absolute workspace root, for example `(cd "$workspace_root" && jj status)` and `(cd "$workspace_root" && jj log -r @ --no-graph)`. Return workspace-relative file paths. See https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/cli-reference/. Repository-scoped GitHub reads require `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Outside JJ, identify and digest the local subject files instead. Revalidate before every reconciliation and final fold-in; changed identity requires restarting all voices or returning an incomplete panel, never folding stale opinions into current state.

Use the resolved absolute Phase 1 scratch directory beneath the project's ignored `.tmp/rocketclaw/`; payloads, raw output, logs, and results stay there even on error. Create private directories with mode 700 and payloads under `umask 077`, then verify mode 600. Never fall back to OS temporary storage.

Prepare a complete canonical payload: framed question, subject shape, normalized scope, repository identity, mode, subject-file paths, required conversation-only material labeled as such, and the peer contract in `agents/pov-peer.md` / `pov-schema.json`. Fill persona placeholders explicitly: a fresh peer does not inherit the conversation. Rejecting every supplied option or the framing itself is valid.

For initial `independent` rounds withhold the host's position, other voices' conclusions, host advocacy, risk rankings, and evaluative option labels. Source-located facts and the user's decision-relevant need, including intensity, remain available. Present host-authored options symmetrically. When an already-formed host or user position is itself the subject, ship that position intact; withhold only fresh meta-judgment formed after the summons. In `skeptic` mode include the host position because critique is the task. All routes receive the same complete payload; an oversized payload makes a route unavailable rather than authorizing truncation.

## 4. Dispatch and collect

Launch one native reviewer per exact selected participant, concurrently when supported, before waiting; record every returned task/session handle. Preserve the fixed route, permissions, scope, and independence requirements throughout. Use native lifecycle/result tools, await every started reviewer, and do not invent detached jobs or helper commands. Preserve configured time budgets: absent an override, allow a 600-second peer budget and an aggregate 610-second collection window. A larger configured peer budget widens the aggregate window to that budget plus ten seconds; do not prematurely cancel healthy reviewers. At deadline stop outstanding work through supported native lifecycle controls, collect terminal results, and report timeout. If cancellation is unavailable, report outstanding handles and do not delete files still used by them.

Require schema-shaped results with nonempty settled `position` and `reasoning`, `final: true`, valid `movement`, and route/model receipt information. A settled `Blocked — …` result is usable; `final: false` is not. Initial movement is `initial`; reconciliation movement is `moved` or `held` with what changed or why evidence was insufficient. Retry a non-final result once on the same permitted route inside the same deadline, then drop it as non-final. A terminal task alone does not prove valid review coverage.

Classify failures from actual native errors. A rejected unauthorized model argument may be omitted for a suitable inherited-model reviewer; disclose lost different-model coverage. Correct other non-permission malformed arguments once before launch. Do not retry denial or depth exhaustion. Temporary capacity can be queued within budget. A parent dispatch fallback must preserve independence and be permitted; otherwise return the solo POV with incomplete panel coverage. Never hand-launch a different harness as recovery.

Use bounded diagnostics to report observed quota, authentication, transport, timeout, missing-tool, depth, or permission failures; do not invent a cause. Attribute account authentication failure only when provider-capable execution or a provider response establishes it, not merely authentication-shaped text from a restricted context. Never attribute a position to a model that did not run.

## 5. Reconcile material dissent

Only independent voices enter convergence; a skeptic critique folds in once, with disclosure of whether it changed the POV. Material dissent means different adoption grades, different selected approaches, document conclusions implying different reader actions (`proceed`, `revise-first`, `reject`), or disagreement on fatal risk. Wording, emphasis, and confidence differences alone are concurrence.

Default to the initial round plus at most two reconciliation exchanges. An explicit user pass limit wins: one pass means no reconciliation. Before each exchange:

1. Revalidate repository identity; restart or return incomplete on change.
2. Reconsider every surviving position and evidence.
3. Verify disputed decision-relevant project claims within scope; label each verified, contradicted, or unverifiable with source locations.
4. Send every survivor one identical complete evidence delta, original subject, and all surviving positions/reasoning, with at most five succinct source-attributed evidence bullets per voice.
5. Recheck native route, permission, model, and depth gates; dispatch fresh stateless reviewers. Drop failed voices from later rounds rather than treating stale positions as current participation.

Stop at `confident` when ce-pov has a reasoned conclusion, `no-movement` when all survivors hold and confidence is still absent, or `limit-reached` when the finite authorized cap ends without confidence. Convergence is reasoned judgment, never voting. The latter two outcomes are stalemate, not proof of consensus. At the cap recommend a specific bounded extension only if a named unresolved question and new evidence/framing could move the result; otherwise recommend stopping. Additional rounds require approval unless authorized in advance; never use an open-ended loop.

## 6. Decide, disclose, and clean up

Lead with the POV, then a compact panel note:

- **Confident:** state alignment or explain why the host decided over dissent. Concurrence does not eliminate correlated-model blind spots.
- **Stalemate:** give current host and survivor positions, movement, dropped voices' last states, whether the gap is evidence or judgment, material tradeoffs, and a bounded further-round recommendation or reason to stop.
- **Partial:** name surviving/dropped targets and observed failures; disclose unverified independence and any required different-model or fixed-route coverage still incomplete.
- **No survivor:** deliver solo with “cross-model check unavailable or incomplete,” naming attempted peers or why none ran. Never ship a bare solo verdict after a summons.

Keep route/requested/served-model receipts in the private record; user-facing notes name peers by target and requested model, with caveats when a receipt disagrees, no model was requested, or independence matters. No visible model/harness authorship attribution is added to artifacts.

The panel never mutates. Downstream continuation requires all four: the original prompt explicitly authorized that named action, the result is non-stalemated, inherited scope is preserved, and the action is non-destructive and otherwise authorized. Otherwise return judgment only; a calling workflow owns continuation.

On success, failure, timeout, or interruption, stop and await started reviewers before removing consumed payloads, logs, results, and round directories owned by this run beneath its private scratch root. Never delete outside it, remove unrelated content, or delete files still referenced by active workers. Retain and report remaining state if lifecycle controls cannot safely stop a reviewer. Project context and peer reasoning must not outlive their authorized use.
