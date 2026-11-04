# Cross-Model POV Panel

Obtain independent peer POVs, reconcile material disagreement, and return one decision. The host remains the decision-maker: peers are cross-checks, not substitutes or votes. This is read-only and non-blocking: return a panel POV, a solo POV with an availability note, or the ordinary missing-context blocker.

## 1. Resolve the subject and participants

Resolve shorthand from the active conversation; return missing context when multiple referents materially change the judgment. An affirmative request for `oracle`, a panel, a cross-check, or named peers enters this protocol, including a request from a calling skill. Declining consultation or recounting a previous check is not a summons. A caller's paraphrase does not erase a summons still present elsewhere in readable invocation context.

- Named peers are exact and uncapped: announce and attempt every named target; never silently substitute or drop one.
- Bare `oracle` selects up to two reachable, attestably different-model peers using conversation preferences, configured routes, project conventions, then `codex -> claude -> grok -> antigravity`. Preserve configured model choices and reasoning tiers as intent.
- An explicit unnamed cross-check skips the correction-cost test and uses that same count rule. Zero reachable means solo plus an availability line.
- Without a summons, offer only after forming the independent POV, when downstream work precedes error detection or the decision feeds a shared, public, security, or data commitment. Adoption Tier 1 and warm mid-session second opinions never offer; Tier 2/3 may qualify. Do not dispatch merely because an offer is eligible. Calling workflows receive the result without new offers.

Keep target, requested model, concrete route/provider/intermediary, served model, and independence separate. Operational target names include `codex`, `claude`, `grok`, `cursor`, `composer`, `opencode`, and `antigravity`; they are not instructions to launch those harnesses. Cursor means its configured default/Auto choice; Composer is a distinct requested model, never an alias. Gemini/Antigravity intent must not silently become another family. Cursor default and Composer are automatic choices only when configured as a preference. A route that specifically requires an unavailable harness is unavailable, not permission to invoke its dispatcher.

Attest the host's serving model from runtime evidence, not an installed CLI, provider name, home directory, inherited environment marker, or model self-claim. Attribute the peer's served model only from native runtime receipts. Without a receipt record `model_actual: unverified`. Set `independence_verified: true` only with evidence that the served family differs from the host's. Same-model reviewers are separate voices, not cross-model corroboration. Unknown host family excludes unverified candidates from automatic different-model discovery. Name peers by target and requested model; add serving caveats when a receipt disagrees or the route had no requested model.

## 2. Permission, model selection, and depth

This skill explicitly requests native peer subagents for the panel branch. Where host policy permits delegation requested by the user OR an applicable loaded skill, these instructions satisfy that exception without a second approval. A skill that does not request delegation grants nothing. Respect unconditional higher-priority prohibitions, unavailable tools, and actual permission denials.

Delegation permission is not model-selection permission. Discover available exact model IDs with `opencode.models`; use native `subagents` for execution and `shell` only for local evidence and artifact handling. Do not launch another harness or restore deleted dispatch bridges. If the host requires an explicit user model request for overrides, omit the optional `model` argument unless that request exists. Suitable inherited-model reviewers may still run. Preserve configured choices and tiers as intent and disclose unmet requirements; a required different-model pass or fixed route that cannot run means coverage is incomplete, never fully verified.

Check effective OpenCode depth from discovered configuration and actual runtime capability, separately from permission; package-local depth does not prove consumer settings or remaining nesting capacity. Classify a failed launch from its actual error as permission denial, rejected model argument, missing tool, nesting-depth exhaustion, or capacity. Never evade a limit with shell/another harness or retry a denied operation. A parent-coordinator handoff is allowed only through the host's permitted mechanism with the same frozen evidence and independence contract. Inline host analysis can preserve the solo POV but cannot count as an independent peer.

## 3. Freeze scope, identity, and route

Normalize one repository-relative read root and ordered optional include/exclude patterns; default to the repository root and never broaden user scope. Pass identical scope to all peers. Peers inspect existing files directly; inline only conversation-only or otherwise unavailable material. Prompt scope, working directory, and read-only instructions are cooperative restrictions, not a confidentiality or filesystem sandbox. Do not claim secrets are inaccessible. Peers must not mutate the project or intentionally inspect outside scope.

Capture committed identity with `jj log -r @ --no-graph -T 'commit_id'`, plus a digest of tracked modifications and untracked content in scope. Use native `jj diff`/`jj file list` and bounded local file enumeration and byte hashing, including added, deleted, binary, and relevant ignored/untracked content; exclude only this run's scratch artifacts from the comparison. Do not substitute parent-relative history statistics. Run JJ with cwd set to the absolute target workspace root, never directly execute Git, and consult https://docs.jj-vcs.dev/latest/cli-reference/ . Revalidate before each reconcile dispatch and final fold-in. A changed identity requires restarting all voices on the new identity or reporting incomplete coverage, never stale fold-in. In non-repository projects use a scoped local-content digest.

Read configured model choices and tiers from the applicable `.rocketclaw/config.yaml` and `config.local.yaml` layers; preserve the separate SKILL.md rule that `docs_root` comes only from `config.yaml`. Resolve one permitted native route, model and recipient chain before sending content. Probe capabilities without project content. Explicit user models cannot be replaced. Only an observed unavailable default may be proposed as a closest compatible same-target, same-family, same-tier equivalent, subject to model-selection permission. Never automatically hop providers or intermediaries. Announce who will inspect the project and that it is read-only; do not recite internal scratch paths, hashes, tiers, or probes. A new unexpected recipient needs approval, as does any consultation separately gated by active policy. Otherwise the explicit panel request authorizes normal read-only consultation.

## 4. Dispatch, wait, collect, and recover

Use the absolute private scratch directory resolved in `references/grounding.md`. Keep payloads, outputs, receipts, and bounded logs there. Check containment, ownership and symlinks; create payloads under `umask 077` and `chmod 600` before dispatch. No OS-global temporary or detached bridge job storage.

Prepare one canonical payload with framed question, subject shape, scope, repository identity, mode, workspace file paths, required conversation-only material and the peer persona in `references/agents/pov-peer.md`. Allow rejecting all options or the framing. Give peers the user's goal, strength of preference and supplied evidence, but no host-curated architecture summary in place of sources. Verify the complete identical payload fits each selected route; never truncate per provider.

Freeze the host's own POV first without emitting it. In initial `independent` mode withhold that POV and all other judgments, advocacy, risk rankings and evaluative option labels. Source-located facts and decision-relevant needs may be included; host interpretations wait for reconciliation. Present host-authored options symmetrically. If a prior host/user position is itself the subject, include it intact as the artifact, withholding only fresh meta-judgment formed after the summons. In `skeptic` mode include the host position because critique is the task.

Start one native job per selected peer concurrently when supported, before waiting. Record native job/session IDs, fixed target/route, requested model and start/deadline. Use the runtime's supported wait/result/cancel lifecycle, not invented tool names or bridge scripts. Default peer window is 600 seconds; preserve a valid larger configured `CROSS_MODEL_HARD_SECS` and never shorten it to finish sooner. Wait through healthy running jobs using supported bounded waits. Collect completed results while others run. On deadline cancel only this run's still-running jobs, await terminal status and retain observed diagnostics; never orphan a peer. No retry may exceed the original aggregate deadline.

Require the shape in `references/pov-schema.json`: settled `position`, non-empty `reasoning`, valid `movement`, `final: true`, and route/model receipt fields. `done` is not proof of a usable artifact. A settled `Blocked — …` is usable; a non-final placeholder is not. Initial results require `movement: initial`; reconciliation requires `moved` or `held` and an explanation. Retry a non-final answer once on the same permitted route within the remaining window, requiring finality; then drop that voice with its reason. Do not infer finality from prose or infer served model from the request.

Read only artifacts belonging to this run and validate their resolved containment before reading. Populate the schema's optional route/model fields in the panel record from native runtime evidence, not peer self-attestation; absent served-model evidence remains `unverified` and independence remains false. Record terminal status and observed cause per peer: timeout, non-final output, quota, authentication, unavailable model, permission, depth, missing tool or capacity. Attribute account authentication failure only with provider-capable launch or provider-response evidence, not merely authentication-shaped text from a restricted context; never guess logout or recommend credential refresh without that evidence.

A recoverable native infrastructure or malformed-argument failure before launch may be corrected once on the same route, scope, payload and model within the window, after verifying no duplicate job launched. A refused default model may have one permitted same-family substitute attempt using advertised availability; an explicitly named model is never swapped. Do not retry a denied operation, bypass depth restrictions, add a recipient without approval, broaden scope or leak withheld positions. Repeated failures end that voice. Distinguish infrastructure failure from a provider that ran and returned unusable output; report exact observed evidence, not invented causes. Preserve useful coverage from survivors, but do not call missing required coverage complete.

## 5. Detect dissent and reconcile

Only independent voices enter convergence; skeptic critique is folded into the host POV once with disclosure of whether it changed the judgment. Material dissent is a different adoption grade, selected approach, document action (`proceed`, `revise-first`, `reject`), or fatal-risk judgment, not stylistic differences.

Default to one independent round and at most two reconciliation exchanges. An explicit user limit overrides this: one pass means no reconciliation. For each exchange:

1. Revalidate identity, then reconsider every current position and its evidence.
2. Verify only disputed project claims that can change the decision; mark each verified, contradicted, or unverifiable with sources.
3. Send every surviving peer the same complete evidence delta, original subject, and every survivor's position/reasoning, capped at five succinct source-attributed evidence bullets per voice. Never route-specific truncation.
4. Re-resolve the same permitted fixed routes and dispatch fresh stateless native jobs. Same recipients need no new approval; unexpected recipients do. Drop failed voices rather than treating older positions as participation.

After initial material dissent, run at least one reconciliation unless the user limited the run to one pass. Deciding over a dissenter who never saw counter-evidence is not convergence. Stop at the first matching state:

- `confident`: the host has a reasoned POV after weighing every survivor;
- `no-movement`: every survivor held and the host remains unconfident;
- `limit-reached`: the finite authorized limit ended without confidence.

Confidence is reasoned judgment, not a vote. The latter two states disclose stalemate. At a cap recommend a specific bounded extension only with a named unresolved question, new evidence/framing and reason it could move a position; otherwise recommend stopping. Further rounds require approval unless authorized in advance, never an open-ended loop.

## 6. Decide and disclose

Lead with the POV in its active subject shape, then a compact panel note:

- Confident: say whether voices aligned; explain any decision over dissent. Agreement does not eliminate correlated blind spots. Distinguish recommendations added by the host after the panel.
- Stalemate: state current and surviving positions/movement, dropped voices' last states, evidence gaps versus judgment differences, and a supported recommendation or viable tradeoffs. At the cap include the bounded extension recommendation or why to stop.
- Partial: name survivors and dropped targets with observed failures, and explicitly state any unmet different-model, fixed-route or independence requirement as incomplete coverage.
- No survivor: deliver the solo POV with “cross-model check unavailable or incomplete,” stating which peers were attempted or why none ran.

Every summons gets a panel-status line even when dispatch never started; a solo POV without a summons gets none. Never attribute a position to a model that did not run. Retain route, requested/served model and independence receipts in the private panel record; keep the chat decision-relevant and disclose independence uncertainty where it affects credibility. Do not add author/byline or generated-by branding.

The panel never mutates the project. A downstream handoff requires all four: original explicit authorization for the named action, a non-stalemated result, inherited scope, and a non-destructive otherwise permitted action. Calling workflows retain ownership of continuation.

## 7. Cleanup

Stop or cancel and await this run's workers first. Remove consumed payloads, raw logs, results and round directories only beneath the verified private run root on success, failure, timeout or interruption. Never delete outside it or unrelated state. Peer reasoning and project context must not outlive their use. Retain a requested write-up or necessary failure evidence only as required by the caller's delivery/recovery contract, reporting its private path; do not delete the deliverable before it is consumed.
