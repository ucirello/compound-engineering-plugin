# Cross-Model POV Panel

This protocol obtains independent peer POVs, reconciles material disagreement, and returns one ce-pov decision. ce-pov remains the decision-maker: peers are cross-checks, never substitutes or votes. The panel is read-only and non-blocking; every branch ends in a panel POV, a solo POV with an availability note, or the ordinary POV's explicit blocked-on-missing-context result.

## 1. Resolve the subject, host, and participants

Resolve conversational shorthand before spending. If several plausible subjects would materially change the POV and context cannot distinguish them, return missing context to the caller.

A summons is an affirmative request to consult or reconcile peers, whether from the user or the calling workflow. `oracle` is shorthand, not a keyword gate. Declining a panel or recounting a past cross-check is not a summons. A caller's paraphrase does not cancel a summons that is still present elsewhere in the invocation. A warm invocation never proactively offers a panel.

Keep the **target** (the user-facing choice), **route** (the execution harness and actual provider/intermediaries), **requested model** (the named or configured model, preferred default, or Auto/inherited request), and **served model** (what runtime evidence says answered, otherwise `unverified`) separate. Attest the host's model family from the actual session's runtime metadata, not the OpenCode brand, a configured default, another installed CLI, or a model's own claim. A fresh same-model voice is separate reasoning, not cross-model independence. Mark independence verified only when the runtime attests both serving families and they differ. Explicitly requested peers with an unverified or same-family receipt can contribute observations, but cannot fill a required different-model slot. Automatic selection excludes candidates whose independence cannot be established; if a selected candidate's receipt fails to establish independence, report it as unmet, never as verified coverage.

Apply exactly one participation branch:

- **Named peers:** exact and uncapped. Named targets override discovery and the `oracle` cap. Announce and attempt each authorized, reachable target; report every unmet target rather than silently omitting it.
- **Bare `oracle`:** select up to two reachable, different-family candidates using conversation preference, local configuration, active project conventions, then `codex -> claude -> grok -> antigravity`. Announce them. `oracle` authorizes ordinary read-only consultation against the current project.
- **Explicit unnamed cross-check:** skip the correction-cost check and use the same count rule. Announce the selection.
- **No explicit cross-check:** only offer after forming a POV, and only when meaningful downstream work will build on the take before an error would show up, or it feeds a shared, public, security, or data commitment. Adoption Tier 1 is ineligible; Tier 2/3 are eligible. Do not offer on a warm invocation or when returning to a calling workflow. An offer is not authority to dispatch.

Zero reachable means solo plus an availability line when summoned. One or more selected peers means a concise progress line naming who will inspect the subject and that the work is read-only. Cursor default and Composer are not selected automatically unless configured as a preference.

**Prior-opinion subjects.** When the subject is ce-pov's prior POV or the user's stated view, that position ships as the subject artifact. Peers independently answer the underlying question and enter convergence. Withhold only the host's fresh meta-judgment formed after the summons. This is not skeptic mode.

## 2. Normalize scope and freeze repository identity

Normalize one workspace-relative read root and any ordered include and exclude patterns. The default is the whole project workspace. Give every peer the identical scope and the absolute project root; do not widen a narrower user or host scope. Point peers to evidence already in the shared working tree, and inline only conversational or otherwise unavailable material. Never send unrelated state or credentials.

Apply the narrowest actual OpenCode read-only permissions available, refuse peer requests to write or escalate, and tell each peer to search and read only the declared scope. Prompt-only patterns and a working directory are cooperative, not a confidentiality or write sandbox. Do not claim secrets in scope are inaccessible or use prompt-only restrictions to satisfy an authorization that requires enforced containment. The sole optional external research is a public subject-level query as directed by the peer brief, not a transfer of repository-derived material to another recipient.

Before dispatch, capture the **repository-scope identity**: the current committed parent revision(s) of the workspace plus a stable digest of dirty and untracked files in scope, including relevant path, type, mode, and content changes. Resolve the parent IDs with [native JJ](https://docs.jj-vcs.dev/latest/cli-reference/#jj-log) from the absolute workspace root, e.g. `(cd "$workspace_root" && jj --ignore-working-copy log --no-graph -r '@-' -T 'commit_id ++ "\n"')`. Inspect the actual scoped working tree locally; include scoped dirty and untracked files even if JJ has not snapshotted them. Do not hash files outside the permitted scope through symlinks. Exclude repository metadata and this run's own scratch. Outside JJ bind the identity to the absolute local project root and a deterministic digest of its scoped evidence. If identity cannot be measured reliably, report panel coverage incomplete rather than merging results of unknown scope. Include the identity in every prompt. Revalidate before each reconciliation dispatch and final fold-in; on a change either restart all voices on the new identity or return an incomplete panel result.

Keep payloads, raw output, logs, and result artifacts under the private absolute scratch directory created in `references/grounding.md`. Scope native prompts to the subject and evidence, not other peers' artifacts. If writing payloads, use `umask 077` and mode 600.

## 3. Resolve and announce one fixed native route

Preserve named targets, configured preferences and model/effort pins as intent. Use the user's request, active instructions, and applicable settings from the workspace's `.rocketclaw/config.yaml` and its `config.local.yaml` overrides rather than asking the user to restate configured intent. Resolve one actual OpenCode route and its recipients before giving it project material. Use `opencode.models` for exact `provider/model` IDs and available variants; a listing is capability evidence, not permission or proof of authentication or the model served. A bare family label may map to its native OpenCode provider/model; a fixed intermediary, harness-specific default or user-pinned model must match what the native route actually supports.

| Target intent | Preferred model and tier unless pinned |
|---|---|
| `codex` | `gpt-6.1-sol`, high |
| `claude` | `claude-opus-5-5`, high |
| `grok` | `grok-4.7`, xhigh; Grok through Cursor is distinct and requests `grok-4.7[context=256k,reasoning_effort=high,fast=true]` |
| `antigravity` / Gemini | `gemini-4-argon`, high; editorial fallback `gemini-3.8-flash` when Argon is unavailable, only through the same sanctioned recipient(s) |
| `cursor` | Cursor's configured default/Auto, not Composer |
| `composer` | `composer-2.5[fast=true]` |
| `opencode` | OpenCode's default/Auto unless pinned |
| `pi` | Pi's configured default unless pinned |

Resolve Gemini only when the host's serving family differs. A fixed Cursor default, Cursor intermediary, Pi, Antigravity harness or other legacy route not exposed as an exact native capability is unavailable; do not silently reinterpret it as a different recipient or start that CLI. A generic request for a Gemini peer does not require the Antigravity harness. For an observed unavailable editorial model, substitute at most once with the closest compatible native model in the same target, family, tier, and allowed recipient chain. Do not substitute an exact user or configuration pin. If only a non-pinned editorial effort is rejected and the same model's default is permitted by the request, one same-model default-effort retry is allowed; disclose the change. An unsupported fixed model, tier, or route remains unmet.

Confirm every actual provider and intermediary is sanctioned by the user's request, project/organization policy, and `CROSS_MODEL_PEERS` when set. Preserve the existing allowlist target vocabulary (including `antigravity` for Gemini); if a sanctioned Grok-through-Cursor route is exposed natively, its allowlist requires `grok` and either `cursor` or `composer` for the intermediary. Never infer allowlist approval for a newly introduced intermediary from target-name similarity. A named peer, explicit cross-check, or `oracle` supplies normal consultation authority; ask only where an active instruction requires separate approval or an unexpected recipient or intermediary would receive the material. If that cannot be approved, skip the affected voice. Announce selected targets and actual routes in plain language before dispatch; keep operational details out of the progress line.

## 4. Dispatch, collect, and verify coverage

Apply the separate delegation, model-selection, and remaining depth gates in `references/grounding.md`. In particular, this skill explicitly requests native peer subagents when a panel is authorized; a user-or-skill host rule is satisfied without a second approval, but a hard prohibition or actual denial is not. Where host policy requires a user model request before passing `model`, omit it unless that requirement is met. Use the inherited model for a permitted reviewer only if it meets that slot's requirements; a same-model skeptic or supplemental cross-check is useful where the request allows it, but cannot replace a required different-model voice. Keep configured routes and tiers as intent and report unmet different-model, fixed route, and fixed tier coverage explicitly. Never bypass a denial or nesting limit with shell or another harness. The shell can inspect config, count data, and manage local evidence, not launch peers.

Prepare one complete canonical payload with the framed question, subject shape, normalized scope, scope identity, mode, paths to subject evidence and required conversation-only material. Keep the same complete payload for each route and do not truncate it to fit. Honor `CROSS_MODEL_MAX_PAYLOAD_CHARS` as the payload byte ceiling (200,000 by default) as well as route context limits; report routes that cannot accept it. Brief native subagents with `references/agents/pov-peer.md` and `references/pov-schema.json`. Use fresh isolated conversation context; do not use a dispatch mode that inherits the parent's verdict or previous peers' reasoning.

In an initial `independent` round, exclude ce-pov's position and every other voice's conclusion. Supply the complete proposal, document, or option set under judgment. Include source-located facts and the user's decision-relevant goals, their priority and stated evidence; label conversation-only material. Withhold host interpretations, risk rankings, candidate-risk enumerations, evaluative option labels, and recommended consequences. Present host-authored options symmetrically and make clear that rejecting every option or the framing is valid. For an already-formed position supplied as the subject, preserve that position's premises, labels, and advocacy while withholding new host meta-judgment. In `skeptic` mode, deliberately include the position being critiqued. Reconcile prompts follow Section 5.

Dispatch all eligible native subagents together when the host supports it, one per target and round. Track each native task/session ID with its allowed scope, target, requested model/tier, actual route, and deadline. Use the native completion notifications and available wait/cancel controls; do not start duplicate waits or retry a still-running voice. Keep the round bounded by the peer window (600 seconds by default; honor a valid user-set `CROSS_MODEL_HARD_SECS`) plus at most ten seconds to settle. Within that window use any available liveness information (the default idle budget is 180 seconds, overridable via `CROSS_MODEL_IDLE_SECS`); absence of progress notifications on a host that exposes none is not proof of a stall. Cancel or stop waiting on timed-out work and do not accept late results. If the native tool cannot enforce the timeout or cancel, do not claim the child was terminated; disclose that limitation and leave its coverage incomplete. Do not start new recovery work after the deadline.

Only fold in results from the recorded task and round. A completion notice is not a usable result. Accept one schema-valid JSON result for the requested mode with a non-empty `position` and `reasoning`, appropriate `movement`, and `final: true`. Initial responses require `movement: initial`; reconcile responses require `moved` or `held` plus what changed or why evidence was insufficient. A settled `Blocked — …` counts; a non-final response does not. On a valid but non-final reply, retry once on the same route, model, scope, and independence conditions with a final-answer instruction, only if enough of the original window remains (default minimum 60 seconds, `CROSS_MODEL_RETRY_MIN_SECS` if set). If the retry cannot run or also yields no settled result, drop the voice and record why.

Build the receipt as coordinator: normalize the voice to the target, record target, actual harness and route (including actual provider/intermediary), requested model, served model and serving family, and `independence_verified` separately. Use runtime-provided model metadata, never peer self-report or the requested model as proof. If no receipt identifies the served model, preserve `model_actual: unverified`. If the evidence contradicts or cannot attest a required fixed route or model, leave that coverage incomplete. Keep one accepted `pov-<target>.json` per target per round if recording results on disk; never substitute a raw log or an earlier round's artifact.

Classify failures from actual tool diagnostics: missing tool, permission denial, depth, transient capacity, pre-launch model/variant rejection, provider quota/authentication, timeout, or invalid output. Distinguish provider rejection from shared dispatch failure; only attribute an account authentication failure once provider access or a provider response is established. For a recoverable native pre-launch failure, confirm no task started, correct the actual error without changing scope, permissions, or participants, and retry only while the failure is new and the original window allows it. Stop on a repeated failure. Model refusal follows Section 3's bounded substitution rules; never retry a denied operation. Otherwise report the voice unavailable and continue with the survivors.

## 5. Detect dissent, verify claims, and reconcile

Only `mode: independent` voices enter convergence. Material dissent means a different adoption grade, a different selected approach, or document bottom lines that imply different reader actions (`proceed`, `revise-first`, or `reject`) or disagree on whether a risk is fatal. Wording, emphasis, confidence, or supporting detail with the same decision is concurrence.

The default limit is the independent initial round plus at most two reconcile exchanges. A user-supplied pass or round limit overrides it: "one pass" or "one round" means no reconcile exchange, while a larger explicit limit replaces the default cap. Never reinterpret a smaller user limit as a suggestion.

For each reconcile exchange:

1. Revalidate repository-scope identity. Restart or return incomplete on change.
2. Have ce-pov reconsider every current position and its evidence.
3. Identify only disputed project claims that could change the decision. Verify them against the allowed scope and classify each as `verified`, `contradicted`, or `unverifiable`, with source locations when available.
4. Build one common evidence delta. Send the identical complete delta to every surviving peer—never route-specific truncation—along with the full original subject and every surviving voice's current position and reasoning, capped at five succinct source-attributed evidence bullets per voice.
5. Re-resolve every fixed route under Section 3, then dispatch a fresh stateless round. The same recipients need no question; an unexpected new recipient or intermediary does. A failed peer is dropped for later rounds; do not reuse its older position as if it participated.

When initial independent voices materially dissent, run at least one reconcile exchange before any stop unless the user limited the run to one pass. If dispatch gates make that exchange impossible, disclose incomplete reconciliation; deciding over a dissenter who never saw the counter-evidence is not convergence.

After fold-in, stop on the first matching enum:

- **`confident`** — ce-pov has a reasoned POV after weighing every survivor;
- **`no-movement`** — every surviving peer returned `held` and ce-pov is still not confident; or
- **`limit-reached`** — the effective user-authorized finite limit completed after initial dissent and ce-pov is still not confident.

Convergence is ce-pov's reasoned confidence, not a vote. A three-way split still ends in a confident decision or stalemate. At a cap, suggest a specific bounded extension only if you can name the unresolved decision-relevant question, what evidence or framing it would add, and why it could move a position. Otherwise recommend stopping. Further rounds need user approval unless already authorized by the user's larger limit.

## 6. Decide and disclose

Lead with ce-pov's POV in the active subject shape, followed by a compact panel note:

- **Confident:** state whether voices aligned. Concurrence raises confidence but does not eliminate correlated-model blind spots. If ce-pov decided over dissent, name the disagreement and why its result prevailed. Claim peer agreement only for what peers judged; name any recommendation added after the panel as your own.
- **Stalemate:** state ce-pov's current position, each surviving peer's position and movement, every dropped voice's last state, and whether the disagreement is an evidence gap or judgment difference. Recommend when there is a real basis; otherwise say "Either is viable" with the material tradeoffs. At a cap, state which bounded extension could help and why, or recommend stopping.
- **Partial:** name surviving and dropped targets and observed failure states. Explicitly mark requested different-model, exact model/route, or reconciliation coverage that was not satisfied as incomplete, even when an inherited or unverified voice produced a useful answer and even when the POV itself is confident.
- **No survivor:** deliver the solo POV with "cross-model check unavailable or incomplete." When summoned, always state who ran or that none ran and why. With no summons and no panel, omit the panel note.

Retain target, route, requested model, served model, and independence receipts in the panel record until fold-in. Name peers in chat by target and requested model, their position and movement, and the relevant serving/independence caveat when a receipt disagrees, no model was requested, or independence affects credibility. `unverified` is not a serving-model attribution. Never attribute a position to a model that did not run.

The panel never mutates the project. After delivery, hand off only when the original prompt explicitly authorized the downstream action, the decision is non-stalemated and resolves what that action needs, the action stays in inherited scope, and it is non-destructive and otherwise authorized. Otherwise return the judgment without starting downstream work. A calling workflow retains ownership of continuation.

## 7. Skeptic mode and degradation

When asked to challenge ce-pov rather than form an independent POV, set `mode: skeptic`. Fold a valid attributed critique into ce-pov once, but do not put that voice into convergence. Disclose whether it changed the POV. A failed skeptic degrades like any unavailable peer.

A peer never blocks a POV. Mid-round failure drops only that voice; an oversized canonical payload drops routes that cannot accept it. If native dispatch is unavailable, return a solo POV or the ordinary grounding blocker; a parent coordinator may dispatch the exact permitted missing voices if the caller owns that fallback and can preserve the frozen initial context, scope, recipients, and deadline. Inline reasoning cannot replace a required independent voice.

## 8. Cleanup

Remove consumed panel payloads, raw logs, results, and round directories under this run's verified private scratch root on success, failure, timeout, or interruption, after stopping any worker that can still use them. Never delete outside the current run root or alter native session storage outside this run. If the host cannot confirm a worker is stopped, report the outstanding work and any retained scratch instead of claiming cleanup succeeded.
