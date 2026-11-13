# Cross-Model POV Panel

Obtain independent peer POVs, reconcile material disagreement, and return one
ce-pov decision. Peers are cross-checks, never votes or substitutes for the
host's judgment. The panel is read-only and non-blocking: unavailable peers
leave a solo POV with an availability note, not a false claim of verification.
The ordinary grounding floor still applies and may require a blocked result.

## 1. Resolve participation and permission

Resolve conversational shorthand to the unambiguous subject; return missing
context when several interpretations would materially change the POV.
An affirmative request for a panel, cross-check, other models, named peers, or
`oracle` enters this protocol, including requests from a calling workflow.
Declining consultation or recounting an earlier check is not a summons.
A caller's paraphrase in one channel cannot cancel a summons in another.

- **Named peers:** exact and uncapped. Announce every named target; never silently
  replace, omit, or reinterpret a named model. Cursor and Composer are distinct.
- **Bare oracle:** choose up to two reachable, attestably different-model peers
  using conversation preference, local configuration, project conventions, then
  `codex -> claude -> grok -> antigravity`. Cursor default and Composer run only
  when named or configured as a preference.
- **Explicit unnamed cross-check:** skip correction-cost gating and select
  available peers under the same count rule.
- **No explicit request:** first form the host POV. Offer only when meaningful
  downstream work would precede error detection, or the decision feeds a shared,
  public, security, or data commitment. Adoption Tier 1 and warm mid-session
  second opinions are ineligible; Tier 2/3 may qualify. Do not dispatch merely
  because an offer is eligible. A calling workflow receives no extra offer.

This skill explicitly requests native peer subagents. When the host allows
delegation if the user OR an applicable loaded skill requests it, this is the
skill-requested exception; no second user approval is needed. Respect an
unconditional higher-priority prohibition, absent tool, or actual denial.
Never use shell or another harness to evade those restrictions.

Delegation permission is not model-selection permission. Resolve models using
`opencode.models` and native `subagents`; use `shell` only for permitted local
mechanics, not another harness's dispatcher. Preserve model/tier choices in
`.rocketclaw/config.yaml` and `config.local.yaml` as desired behavior with
existing local override precedence. Project/user constraints remain binding.
If host policy requires an explicit user model request for an override, do not
pass optional `model` merely because configuration or this skill suggests one.
Use a suitable inherited-model reviewer where the contract permits it. Preserve
and disclose unmet tier/fixed-route intent. A same-model second reviewer is
useful but cannot satisfy a required different-model pass.

Verify effective nesting depth through supported runtime configuration and
capability evidence; do not assume permission implies remaining capacity.
Classify a failed launch from its actual error as depth/capacity, permission
denial, model-argument rejection, missing tool, or another failure. Never retry
a denied operation or bypass a nesting limit. Any unavailable required
cross-model pass leaves that coverage **incomplete**, even if a solo POV is sound.

## 2. Freeze scope and identity

Normalize one repository-relative read root and ordered include/exclude patterns,
defaulting to the repository root. Pass the identical scope to every peer;
never broaden a narrower supplied scope. Supply the absolute workspace root
separately as the command working directory. Peers inspect existing subject
files directly; inline only conversation-only or otherwise unavailable material.

Patterns and read-only instructions are cooperative unless the native tool
actually enforces them. Never promise a confidentiality sandbox. Peers must not
mutate the project, intentionally read outside scope, or send private identifiers,
source fragments, paths, credentials, or secrets in external research queries.
Confirm every actual provider/recipient is allowed before sending content.

Before dispatch capture the exact current JJ revision plus a digest of scoped
working-copy, untracked and ignored content relevant to the review. Use native
JJ facts and local file hashing, never Git. Run every JJ command from the
absolute target root, for example `(cd "$workspace_root" && jj log -r @ --no-graph -T 'commit_id')`.
Use https://docs.jj-vcs.dev/latest/cli-reference/ for JJ operations.
Revalidate identity before each reconciliation and final fold-in. On change,
restart all voices against the new identity or report an incomplete panel;
never fold stale results into the current project.

Use only the resolved absolute `$SCRATCH_DIR` from `references/grounding.md`,
under this project's `.tmp/`. Keep payloads, logs and artifacts there, including
failure paths. Create private directories with mode 700 and payloads with
`umask 077` and mode 600. Do not fall back to global temporary storage.

## 3. Resolve and announce one native route

Keep target, actual native route/provider, requested model, and served model
separate. Attest the host serving model from runtime evidence, not an installed
CLI, home directory, product brand, requested model, or a model's self-claim.
Record served model as `unverified` unless a native execution receipt attests it.
Set `independence_verified: true` only when evidence shows a different served
model family from the host. Unknown host family excludes automatic candidates
whose independence cannot be verified; an explicitly named peer may still run
with an independence caveat.

Discover current models without transmitting project content. The requested
target, model family, reasoning tier, recipient restrictions and scope are hard
boundaries. Preserve HIGH reasoning intent for panel peers (Composer's fast
ceiling is the accepted exception), subject to host permissions. A discovered
unavailable default may be replaced only with the closest compatible model in
the same target/family/tier; record the observed reason. Never substitute a
user-named model. An exact named harness route that native OpenCode cannot
satisfy is unavailable, not permission to launch its CLI.

Announce selected peers and that their inspection is read-only. Keep progress
plain and decision-relevant, not a dump of tier, identity, scratch or job details.
An explicit panel request authorizes normal read-only consultation unless an
active rule separately gates it. A new unexpected recipient/intermediary requires
disclosure and approval before a new attempt. A fixed-route worker never hops
providers automatically.

## 4. Dispatch and collect natively

Prepare one complete canonical payload: framed question, subject shape, mode,
scope, repository identity, paths to available subject material, and required
conversation-only material labeled by provenance. Include the user's goal, its
strength and supporting evidence. State that rejecting every option or the
framing is valid. Do not substitute a host-curated architecture summary for
direct evidence reads. Use `references/agents/pov-peer.md` and
`references/pov-schema.json` as the brief and response contract.

Freeze the host's independent POV before peer dispatch. In the initial
`independent` round withhold all other voices' conclusions and fresh host
advocacy, risk rankings and evaluative option labels. Source-located facts and
user needs are evidence; host interpretations wait for reconciliation.
When ce-pov authored the subject, describe options symmetrically while leaving
the full subject available. If an already-formed position is itself the subject,
ship that position intact, including its premises; withhold only fresh
meta-judgment formed after the summons. In `skeptic` mode include the position
because critique is the task.

Send the same complete payload to all selected native subagents, concurrently
where supported, before awaiting them all. A route unable to accept the complete
payload is unavailable; never truncate per provider. Record native task IDs,
start times, fixed routes and terminal outcomes. Honor `CROSS_MODEL_HARD_SECS`
when configured, otherwise a 600-second peer cap; never shorten it to finish
sooner. Use supported native wait/status/cancel operations and await every
started peer. Do not leave detached workers behind. A larger configured cap
must also widen the host wait window, not be cut short by a stale supervisor cap.

Read only this run's owned results. Native completion alone is not a usable
answer: require schema-shaped JSON, a settled `position`, non-empty `reasoning`,
`final: true`, valid movement and route/model record. A settled Blocked answer
is usable. Initial responses require `movement: initial`; reconciliation requires
`moved` or `held` and an explanation. Retry a non-final result once on the same
route within the original deadline; then drop it as non-final.
Receipts are execution metadata, not the peer's self-reported model.

Record actual failure evidence, not guesses: permission, depth/capacity,
model rejection, timeout, quota, authentication, missing tool, malformed output.
Only describe account authentication failure when provider-capable dispatch is
established; sandbox-shaped errors alone do not prove the user is logged out.
A rejected configured default may receive one permitted same-family replacement
attempt from advertised native models; never replace a user-named model.

## 5. Reconcile material dissent

Only independent voices enter convergence. Material dissent changes the adoption
grade, selected approach, proceed/revise-first/reject action, or fatal-risk
judgment; wording and confidence differences alone are concurrence.
Default to the initial round plus at most two reconciliation exchanges.
A user pass limit overrides this: one pass means no reconciliation.

For each exchange revalidate scope identity; reconsider all positions; verify
only decision-changing disputed claims as verified, contradicted or unverifiable
with sources. Send every surviving peer the identical complete evidence delta,
full original subject and every surviving current position/reasoning (at most
five succinct attributed evidence bullets per voice). Re-resolve the permitted
fixed route and dispatch a fresh stateless native round. Drop failed peers rather
than implying an older response participated.

After initial material dissent, perform at least one reconciliation unless the
user limited the panel to one pass or remaining peers are unavailable. Report
the latter as incomplete reconciliation, not convergence.
Stop at `confident` (a reasoned host decision after weighing survivors),
`no-movement` (all survivors held and the host remains unconfident), or
`limit-reached` (finite authorized limit exhausted without confidence).
Convergence is not a vote. For the latter two, disclose stalemate. At a cap
recommend a specific bounded extension only with an unresolved decision question,
new evidence path and reason it might move a position; otherwise recommend
stopping. Further rounds require approval unless already authorized.

## 6. Disclose and degrade truthfully

Lead with the host POV in its subject shape, then a compact panel note:

- **Confident:** say whether voices aligned; explain a decision over dissent.
  Agreement does not remove correlated blind spots. Identify recommendations
  added after the panel as the host's, not the peers'.
- **Stalemate:** state each surviving position and movement, dropped voices'
  last state, and whether the gap is evidence or judgment. Give a justified
  recommendation or "Either is viable" with tradeoffs, plus bounded next steps.
- **Partial:** name survivors, dropped targets and observed failure states.
- **No survivor:** deliver the solo POV with "cross-model check unavailable or
  incomplete," attempted targets, or why none ran. Never omit the status after
  a summons. With no summons add no panel note.

Retain target, route, requested/served model and independence receipts in the
private record. The user-facing note names peer target/requested model, position,
movement and material caveats; it is not an author byline. Attribute no position
to a model that did not run. Missing required independence or fixed-route
coverage remains incomplete, even when an inherited-model review was useful.

A skeptic critique folds in once, with disclosure of whether it changed the
POV, and never enters convergence. A failed peer never blocks a properly grounded
solo POV. For recoverable native infrastructure errors, correct one ordinary
pre-launch argument or retry the same allowed route within the original deadline;
stop on repeated failure. No denial/depth bypass, changed recipient, widened
scope or leaked initial judgment is allowed. Inline evidence collection or
parent-coordinator assistance may preserve ordinary grounding where permitted,
but cannot masquerade as independent cross-model review.

The panel never mutates. Downstream handoff requires all four: original explicit
authorization of the named action, a non-stalemated result, inherited scope, and
a non-destructive otherwise-authorized action. Otherwise return the judgment;
calling workflows own continuation.

## 7. Cleanup

Stop/await native workers before cleanup. Remove only this run's owned consumed
payloads, round outputs, logs and results under its private scratch root on
success, failure, timeout or interruption. Never delete outside that root or
unrelated state. Peer reasoning and project context must not outlive their use.
