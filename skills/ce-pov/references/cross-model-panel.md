# Cross-Model POV Panel

Obtain independent peer POVs, reconcile material disagreement, and return one
decision. The agent running this skill remains the decision-maker; peers are
cross-checks, not votes. The panel is read-only and non-blocking. Every branch
ends in a panel POV, a solo POV with an availability note, or the ordinary
explicit blocked-on-missing-context result.

## 1. Participation and identities

Resolve conversational shorthand to the single unambiguous subject before
spending. Return missing context when competing meanings materially change the
question. A summons is an affirmative user or calling-skill request for a panel,
cross-check, named peers, or `oracle`, anywhere in readable invocation context.
Declining consultation or recounting a past consultation is not a summons. A
caller paraphrase never cancels a summons still present in another channel.

- **Named peers:** run every exact named target, without the automatic count cap.
  Never replace an explicitly named model or rewrite Cursor to Composer.
- **Bare oracle:** select up to two reachable, attestably different-model peers,
  using conversation preference, authoritative local configuration, project
  conventions, then the compatibility preference `codex -> claude -> grok ->
  antigravity`. This is a model preference, not permission to launch those CLIs.
- **Explicit unnamed cross-check:** select reachable suitable peers and announce
  them; skip the correction-cost test.
- **No summons:** only offer after independently forming a POV when downstream
  work would build on it before an error surfaces, or it informs a shared,
  public, security, or data commitment. Adoption Tier 1 and warm invocations do
  not offer. No dispatch until the offer is accepted.

Zero reachable peers means solo plus an availability line after a summons.
Cursor default and Composer are selected only when named or configured. Cursor
means its configured default/Auto, Composer a Composer model; neither is an
alias for the other. Grok through Cursor is a distinct intermediary. A Gemini
peer requested as Antigravity retains that target; Pi serves its configured
model and is not automatically independent. Native OpenCode cannot satisfy a
literal harness-specific request by pretending to run that harness: report the
unmet route, and obtain approval for an unexpected recipient/intermediary.

Keep target, actual route/harness/intermediaries, requested model, served model,
and independence separate. Attest the host from runtime serving evidence, not
installed binaries, inherited environment markers, provider names, home paths,
or a model's self-claim. A requested model is not a serving receipt. Set served
model to `unverified` without a receipt. Set independence true only when actual
served model family is attestably different from the host's served family;
same-model separate agents are independent contexts, not cross-model evidence.
Unknown host family excludes unverified candidates from automatic cross-model
selection, but a requested useful cross-check can run with the caveat.

## 2. Permission, model routing, and setup

This skill explicitly delegates scout and peer reviews. That satisfies a host
user-OR-skill delegation exception; do not ask for redundant approval. Actual
higher-priority prohibitions and tool denials still apply. Delegation permission,
model-selection permission, and nesting capacity are separate checks.

Discover models through `opencode.models`; retain configured role/tier/provider
choices as authoritative intent. If the host requires an explicit user request
to choose a model, configuration or this skill alone does not grant it: omit the
optional model argument and inherit when suitable. Disclose unmet configured
routing and independence. Do not claim that inherited same-model review fulfills
a required cross-model route. With model permission, use the exact supported
provider/model reference from discovery. A named model is never substituted.
Only an unpinned default observed unavailable may receive one closest compatible
same-family, same-reasoning-tier replacement within the same authorized recipient;
record the original failure and replacement. Binary presence is not capability
or authentication proof.

Document this prerequisite to users; never modify host configuration: locate the
existing global `~/.config/opencode/opencode.json` or `.jsonc` through `opencode
debug paths` (or `opencode debug paths config`). Merge
`experimental.subagent_depth` as an integer at least 3 into that existing file,
preserving a higher integer, sibling settings, and unrelated configuration. Do
not create a competing JSON/JSONC file. Package/plugin configuration alone does
not enable global nesting, and higher-precedence configuration must not lower
the effective depth.

Announce selected peers and the read-only consultation before dispatch. Do not
recite internal payloads, model diagnostics, hashes, scratch paths, or scope
mechanics unless they affect the user's decision. Named consultation authorizes
normal read-only use; separately gated external consultation still needs its
required approval. Never evade denial by retrying the denied operation or
launching another harness.

## 3. Scope and fixed native route

Normalize once to the absolute target workspace root plus one repository-relative
read root and optional ordered include/exclude patterns. Pass the identical
representation to every peer. Narrow scope is binding and never broadened.
Peers inspect subject files directly; do not duplicate readable files or add a
host-curated architecture summary. Inline only material unavailable in files.
Patterns and read-only prompts are cooperative, not a confidentiality boundary
or write sandbox. Require no edits, mutating commands, or intentional reads
outside scope; do not promise secrets are inaccessible.

Capture one repository-scope identity before dispatch: the exact current
revision plus a digest of tracked dirty and untracked content within scope.
Use JJ and native file reads, never the Git executable. Run JJ with cwd equal
to the absolute target workspace root. Repository-scoped `gh` additionally needs
`GIT_DIR=$(jj git root)` in that root. Revalidate identity before every reconcile
dispatch and final fold-in. Changed identity means restart all voices against
the new identity or return incomplete; never fold stale voices into new content.

Resolve each fixed route to a native OpenCode subagent, authorized provider/model,
and disclosed intermediaries. Probe capability without project content first;
authentication truth comes from a provider-capable attempt or response, not a
generic terminal error. Keep the route fixed throughout an attempt. A new
recipient or intermediary needs approval. An unavailable exact named route is
reported, never silently replaced.

Use the Phase 1 absolute private scratch directory beneath the target workspace's
`.tmp/rocketclaw`. Create payloads with umask 077 and mode 600; outputs and logs
stay under that run root, never OS temporary paths or an external scratch root.

## 4. Dispatch, wait, collect, and recover

Prepare one complete canonical payload: framed question, subject shape, normalized
scope, scope identity, mode, subject paths, required conversation-only material,
and `references/agents/pov-peer.md` plus `references/pov-schema.json`. Rejecting all
options or the framing is valid. Include the user's goal, its importance, and
their supporting evidence without turning those claims into verified facts.

For initial independent peers withhold the host's frozen position and other
voices' conclusions, advocacy, risk rankings, and interpretations. Source-located
facts and user needs are allowed. Present host-authored options symmetrically,
while leaving the full subject artifact accessible. If an already-formed host
or user position is itself the subject, ship it intact; withhold only fresh
meta-judgment formed after the summons. Skeptic mode instead includes the host
position. Reconcile rounds deliberately include already-formed views.

The identical complete payload must fit every route. Do not truncate per peer;
drop an incapable route with the partial-panel disclosure. Discover the host's
available native agents and use a generic one whose role/tools do not override
the brief. Start all selected peers before waiting where capacity allows, queue
capacity-limited work, and retain native session/job IDs. Do not use dispatch
scripts, detached supervisors, another harness, or shell CLI review launchers.

Preserve a 600-second default per-peer hard budget, honoring a valid larger
`CROSS_MODEL_HARD_SECS` user setting. Never shorten it to finish sooner. Use
native wait/result lifecycle, allowing a 10-second collection grace after the
last launch's hard deadline without extending a peer's execution budget. Honor
the native tool's bounded wait slices and finish consuming any still-running
wait before starting another. Collect completed results while others run, and
stop timed-out work through the native mechanism. No overlapping duplicate
launches or busy polling. A platform's missing cancellation capability must be
reported; never claim a worker was stopped without evidence.

Validate returned JSON against the schema: non-empty settled `position` and
`reasoning`, evidence, correct mode/movement, and `final: true`. A settled
Blocked answer counts. Initial movement must be `initial`; reconcile movement
must be `moved` or `held`, explaining the change or why evidence did not move it.
A shaped response with `final` other than true is a placeholder, not a voice.
Retry it once on the same permitted route with a final-answer requirement inside
the original hard budget; a second placeholder is dropped as non-final.

Store an orchestrator receipt alongside each validated result: target, actual
native route, requested and served model, runtime session ID, independence, and
observed lifecycle/failure. Never infer served identity from the request or peer
self-description. Keep absent serving evidence `unverified`.

Classify actual errors separately: depth/capacity, delegation permission, model
permission/unavailability, missing tools, quota, authentication, timeout, malformed
or non-final result. Check whether a launch happened before correcting one bad
argument once. Do not retry a denied operation. One genuinely transient native
infrastructure recovery is allowed on the identical route, scope, payload, and
independence rules inside the original deadline; repeating failure stops recovery.
Do not include a withheld position or widen scope while recovering.

A failed peer is dropped, not replaced by parent reasoning represented as an
independent voice. This non-blocking panel permits a solo/parent POV with the
availability note, but mandatory independent or cross-model coverage stays
incomplete. If all routes share a missing capability, do not try another harness
to evade it. Report account authentication failure and login remediation only
when provider-capable launch context or provider response establishes it;
otherwise describe only the observed execution-context error.

## 5. Dissent and bounded reconciliation

Only independent-mode voices enter convergence. Different adoption grades,
selected approaches, or document bottom lines implying proceed/revise-first/
reject or fatal-risk disagreement are material dissent. Wording, emphasis, or
confidence differences with the same decision are concurrence.

Default: one initial round and at most two reconcile exchanges. Honor user
limits exactly: one pass means no reconciliation; a larger explicit finite cap
replaces the default. After initial material dissent, run at least one exchange
before stopping unless the user limited the run to one pass.

For each exchange:
1. Revalidate repository identity; restart or return incomplete on change.
2. Reconsider every current position and its evidence.
3. Verify disputed decision-relevant project claims within scope as `verified`,
   `contradicted`, or `unverifiable`, citing source locations.
4. Send every survivor the same complete evidence delta, full original subject,
   and every survivor's current position/reasoning, capped at five succinct
   source-attributed evidence bullets per voice. No route-specific truncation.
5. Revalidate fixed native routes and dispatch fresh stateless contexts. Same
   recipients need no new approval. Drop failed voices from later rounds and
   never reuse their old positions as current participation.

After fold-in stop at the first applicable enum: `confident` (reasoned confidence
after weighing all survivors), `no-movement` (all survivors held and the host
remains unconfident), or `limit-reached` (authorized finite cap exhausted without
confidence). The latter two are stalemate, not settled agreement. Convergence is
reasoning, not a vote; deciding over a dissenter who never saw counter-evidence
is not reasoned convergence. At a cap, recommend a specific bounded extension
only with an unresolved decision-relevant question, new evidence/framing, and
why it could move a position; otherwise recommend stopping. Further rounds need
approval unless authorized in advance, always with a new finite cap.

## 6. Decide, disclose, and clean up

Lead with the subject-shaped POV, then a compact panel note:
- **Confident:** whether voices aligned; concurrence does not erase correlated
  blind spots. Name overruled dissent and why. Recommendations added after the
  panel are not attributed to peers.
- **Stalemate:** host position, every survivor's position/movement, every dropped
  voice's last state, and evidence gap versus judgment difference. Recommend
  when supported; otherwise say “Either is viable” with tradeoffs. At the cap
  include the bounded-extension recommendation or why stopping is best.
- **Partial:** surviving/dropped targets and observed failure states.
- **No survivor:** solo POV with “cross-model check unavailable or incomplete.”
  After any summons, including when no branch ran, state who ran or that none
  did and the observed reason. With no summons, no panel note.

Keep full route/model/independence receipts internally. Default chat names the
target and requested model, position/movement, failures, and serving or
independence caveats when material or unverified. Do not dump diagnostics or
attribute a position to a model that did not run. No output creator/model/harness
bylines; decision-relevant review receipts are disclosures, not attribution.

Skeptic mode critiques the supplied host position once; it never joins convergence.
Disclose whether the critique changed the host POV. Failed skeptics degrade like
other unavailable peers. A peer never blocks delivery of the properly caveated
solo POV, but missing mandatory independence remains incomplete.

The panel never mutates. Continuation requires all four: original explicit
authorization for that downstream action, a non-stalemated result, inherited
scope, and a non-destructive otherwise-authorized action. A calling workflow
retains continuation ownership.

After collection, timeout, interruption, or failure, stop native workers first
and remove consumed payloads, raw logs, results, and round/job directories only
inside this run's verified private scratch root. Never delete outside it or
claim cleanup succeeded when it failed. Peer reasoning and project context must
not outlive their use; preserve only necessary non-sensitive lifecycle receipts.
