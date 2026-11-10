# Cross-Model POV Panel

Obtain independent peer POVs through native OpenCode subagents, reconcile material disagreement, and return one decision. Peers are cross-checks, never votes or substitutes for the host's judgment. The panel stays read-only and non-blocking: finish with a supported panel POV, a solo POV with an availability note, or the ordinary blocked-on-missing-context result.

## 1. Resolve participation and permission

An affirmative request to consult other models, cross-check, reconcile peers, or run `oracle` enters this protocol, whether supplied by the user or a calling skill. A refusal or mention of past consultation is not a request. A caller's paraphrase does not cancel an affirmative request still present elsewhere in readable invocation context.

- **Named peers:** retain every exact requested peer/model, without the automatic cap. Never silently replace or drop one. A named unavailable model is reported as unavailable.
- **Bare oracle:** select up to two available, different-model peers using conversation preference, configuration, project conventions, then available capable models. Resolve concrete provider/model IDs with native `opencode.models`; do not infer availability from an installed CLI.
- **Explicit unnamed cross-check:** use available peers without the proactive-offer gate; zero available means a solo result with an availability line.
- **No request:** offer only after forming the host POV, when downstream work could conceal an error or the result feeds a shared, public, security, or data commitment. Adoption Tier 1 and warm invocations never get a proactive offer. An offer is not acceptance.

This skill explicitly requests native research and peer subagents. Under a user-OR-skill rule, skill-requested delegation is sufficient; do not invent a separate user-only delegation requirement. Host restrictions still apply. Delegation permission, external-recipient permission, and permission to override a model are separate checks. Honor configured model choices subject to host permission. If arbitrary model selection is disallowed or unsupported, use an inherited model only when useful and suitable, label it as same-model or independence-unverified coverage, and disclose any unmet cross-model or exact named-model requirement. It never counts as the requested different model.

Announce the selected reviewers and models in ordinary language before dispatch, saying they will inspect the subject read-only. Do not expose scratch mechanics or promise secrecy based on prompt scope. Ask only where active policy separately requires approval or a retry would add an unexpected external recipient/provider. Never bypass denial, capacity, or depth limits using shell launchers, another harness, or an external CLI.

## 2. Identity, scope, and independence

Keep requested peer, native subagent/session ID, requested provider/model, served model, and independence status separately. Requested identity is not proof of the served model. Use host runtime metadata and native response/session metadata as serving evidence, never a model's self-description or another installed product. If no serving receipt exists, record `model_actual: unverified`. Claim `independence_verified: true` only when attested served model families differ from the attested host family. Otherwise retain a useful cross-check with an honest caveat, not different-model corroboration. With an unknown host family, do not automatically select peers whose independence cannot be established.

Normalize one absolute JJ workspace root and optional ordered repository-relative include/exclude patterns. Respect narrower supplied scope; never broaden it. All repository commands run with cwd set to that absolute root, not a `-R` substitute. Use JJ only, never direct Git, including read-only history or fallback commands. Repository-scoped tracker calls require `export GIT_DIR=$(jj git root)` before `gh`, in that same workspace. A non-JJ project can use file evidence and a file-based scope identity without pretending JJ exists.

Peers read existing subject files directly in the shared working tree. Pass paths rather than copying readable content. Inline only conversation-only or otherwise unavailable material, labeled by provenance. Include/exclude prompts, cwd, and a read-only request are cooperative scope rules, not confidentiality or write sandboxes. Deny edits through available host permissions; disclose enforcement limitations rather than claiming secrets cannot be read.

Before dispatch, capture one repository-scope identity: current JJ revision (`jj log --no-graph -r @ -T 'commit_id'`), tracked/conflict status, and a content digest of relevant tracked, ignored, and untracked files in scope. Exclude this run's scratch output from identity, but not relevant source merely because it is ignored. An unchanged revision alone is insufficient. Revalidate before each reconciliation and final fold-in. If the source changed, restart all voices on the new identity or return an incomplete panel; never fold stale opinions into the new state.

Use the absolute `$SCRATCH_DIR` from Phase 1 under the project's local `.tmp/`. Keep private payloads, evidence receipts, logs, and results there only. Create private directories with mode 700 and payloads with mode 600; reject symlinked/unowned scratch roots. No global-temp or home-directory fallback.

## 3. Freeze the host position and prepare peers

First form and freeze the host's independent POV without emitting it. Prepare one canonical brief: framed question, subject shape, user goal and its strength, subject paths, conversational material unavailable on disk, normalized scope, repository identity, mode, and evidence requirements. Use the identical complete brief for all peers; never silently truncate for a model. A peer that cannot accept it is unavailable.

For `mode: independent`, withhold the host's frozen conclusion, every other peer conclusion, advocacy framing, risk ranking, and evaluative option labels. Include source-located facts, not the host's interpretations of their consequences. Permit rejection of every option or the framing. If the host authored the options in-session, present them symmetrically while keeping the full subject accessible.

When an already-formed host or user position is itself the subject, ship that position intact, including its premises and advocacy. Withhold only fresh host meta-judgment formed after the panel request. Peers still return their own independent verdict; this is not automatically skeptic mode. For explicit `mode: skeptic`, include the host position because critiquing it is the task, and exclude the resulting critique from convergence.

Use a native generic subagent whose role will not replace this brief. Ground each peer against the shared source, not a host-curated architecture summary. Return a settled position, non-empty reasoning, source-located evidence, `final: true`, and movement: `initial` for the first round, or `moved`/`held` with a reason for reconciliation. Follow `references/pov-schema.json` where applicable; preserve native serving receipts separately from peer prose.

## 4. Dispatch, wait, recover, and collect

Use only the available native subagent mechanism. Discover available models with `opencode.models` and pass a model argument only when that tool actually supports it and policy permits it. Configuration remains authoritative within those permissions; do not silently downgrade a named model. Start independent peers before waiting when host capacity permits. Record each native session/task ID, selected model, start state, and result location. Wait through the native lifecycle, honor the host's cancellation and timeout behavior, and collect completed results without attributing pending work as complete. Do not shorten deadlines merely to finish sooner.

Classify observed outcomes distinctly:

- **Malformed argument before launch:** verify no agent started, correct once using the actual tool schema, then retry the same authorized request.
- **Model-argument rejection:** selection is unsupported or rejected, not evidence of a delegation ban or depth exhaustion. If suitable and permitted, retry once with inheritance; report lost exact-model or cross-model coverage. Never substitute a model the user explicitly named without permission.
- **Actual depth-limit error:** report that limit, stop deeper dispatch, and retain only available coverage. Do not label a generic failure as depth exhaustion.
- **Capacity:** leave pending work queued or use native waiting; do not spin up another route to evade the cap.
- **Explicit denial:** respect it, report the permission limitation, and do not retry through shell or another harness.
- **Missing native tool:** report unavailable native delegation; inline bounded evidence can support a solo POV, but is not a peer.
- **Started job timeout, quota, authentication, or provider failure:** report the observed terminal reason, not a guessed account diagnosis. A failure before provider access does not prove the user's credentials expired.

A native infrastructure failure may get one bounded same-request retry if recoverable, after checking whether an agent already started. Keep recipient, model, scope, payload, and independence rules unchanged. Never duplicate a running agent. No manual external-harness recovery is allowed. New recipients need the applicable permission/disclosure first.

Accept only a settled answer with non-empty reasoning and the required movement. `final: true` can include a settled `Blocked — …` answer; an unfinished placeholder is not a voice. Ask a non-final peer once to settle within its existing budget, then mark unavailable if it remains non-final. A successful task status alone does not prove usable content. Attribute actual models only from native serving metadata. Record incomplete/missing receipts honestly.

## 5. Reconcile material dissent

Only independent voices enter convergence. Material dissent means different adoption grades, selected approaches, document actions (`proceed`, `revise-first`, `reject`), or fatal-risk judgments, not differences in wording or emphasis.

Default: one independent initial round plus at most two reconciliation exchanges. A user-supplied finite limit wins; one pass means no reconciliation. After initial material dissent, run at least one exchange unless that user limit prevents it.

For each exchange:

1. Revalidate source identity; restart or return incomplete on change.
2. Reconsider all surviving positions and evidence.
3. Verify disputed decision-relevant project claims in scope; classify them as verified, contradicted, or unverifiable with source locations.
4. Send every survivor the same complete original subject and evidence delta, plus each surviving voice's current position and reasoning, capped at five succinct source-attributed bullets per voice.
5. Use fresh native peer contexts under the same permission, model, scope, and receipt rules. Drop failed peers for later rounds; do not portray an older opinion as participation in a newer round.

Stop at the first matching state:

- `confident`: the host has a reasoned position after weighing every survivor, including dissent.
- `no-movement`: every survivor held and the host remains unconfident.
- `limit-reached`: the finite limit completed and the host remains unconfident.

Confidence is not a vote. The latter two states are stalemates, not inferred agreement. At the cap, recommend a specific bounded extension only if a named unresolved question and new evidence path could move a position; otherwise recommend stopping. Further rounds require approval unless authorized in advance. Never run an open-ended loop.

## 6. Decide, disclose, and clean up

Lead with the host POV in the active subject shape, then a compact panel note:

- **Confident:** say whether voices aligned; if deciding over dissent, name the disagreement and why the selected conclusion prevails. Concurrence does not eliminate correlated blind spots. Recommendations added after the panel belong to the host, not peer consensus.
- **Stalemate:** give the host's current position, each survivor's position and movement, every dropped voice's last state, and whether the gap is evidence or judgment. Recommend only when supported; otherwise explain viable tradeoffs. At a cap, state the bounded extension recommendation or why stopping is best.
- **Partial:** name survivors and dropped requests with observed failure states, unmet named-model/cross-model coverage, and limits on independence.
- **None:** deliver the solo POV with “cross-model check unavailable or incomplete,” saying which peers were attempted or why none ran.

Every affirmative panel request gets this status disclosure even if dispatch never began. No request means no panel note. Never attribute a position to a model that did not run, equate inline research with independent coverage, or call a same-model panel cross-model verification. Keep requested/served identities and receipts in the private panel record; the default user note stays decision-relevant, with serving caveats when independence or a mismatch matters.

A skeptic critique is folded in once, with whether it changed the host POV; it never enters convergence. Missing peers never block a sufficiently grounded solo result, but missing project/external grounding still follows the ordinary blocker rules.

The panel never mutates the project. Downstream handoff requires all four: the original prompt explicitly authorized that named action, the result is not stalemated, the action stays in inherited scope, and it is non-destructive and otherwise authorized. A calling workflow retains continuation ownership.

After collecting or cancelling all owned native tasks, clean only this run's owned scratch payloads, logs, outputs, and results on success, failure, timeout, or interruption. Verify exact paths remain beneath the owned private run root before deletion; never remove shared/project files or another run's data. Do not claim cleanup succeeded without evidence. Retain only the minimal non-sensitive coverage/receipt summary needed for honest reporting.
