# Cross-Model POV Panel

Obtain independent peer POVs, reconcile material disagreement, and return one
ce-pov decision. Peers are cross-checks, never substitutes or votes. The panel is
read-only and non-blocking: finish with a panel POV, a solo POV with an explicit
availability note, or the ordinary blocked-on-missing-context result.

## 1. Resolve the subject, host, and participants

Resolve shorthand from the active conversation when one subject fits; return
missing context when competing meanings materially change the decision.
Keep four identities separate: user-facing target, actual native route/provider
and intermediaries, requested model, and receipt-supported served model
(`unverified` without runtime evidence). Never infer the served model from a
request, model self-description, installed CLI, or home directory. Attest the
host family from runtime serving evidence. Set `independence_verified: true`
only when the peer's served family is attestably different from the host's.
Same-model reviewers remain useful separate reviewers, not cross-model proof.
Exclude automatically selected peers whose independence cannot be verified.

Apply exactly one participation branch:

- **Named peers:** announce and attempt every named target, uncapped; never
  replace a named model or silently drop an unavailable target.
- **Bare `oracle`:** select up to two reachable, attestably different-model
  peers using conversation preference, local configuration, active project
  conventions, then the default order `codex -> claude -> grok -> antigravity`.
- **Explicit unnamed cross-check:** skip correction-cost screening and announce
  the selected available peers; zero reachable means solo plus availability.
- **No explicit cross-check:** form the POV independently, then offer only for
  Tier 2/3 decisions where meaningful downstream work precedes error discovery
  or a shared, public, security, or data commitment depends on the result.
  Tier 1 and warm mid-session second opinions never receive proactive offers.

`oracle` is not a keyword gate: any affirmative request to consult or reconcile
peers enters this protocol. A refusal or historical mention is not a summons.
A calling skill's explicit request counts, including when another invocation
channel paraphrases it away. No summons means no unsolicited panel-status note.
Cursor default/Auto and Composer are distinct preferences, never automatic
selections. Preserve named/configured route intent: Cursor means its configured
default, Composer means a Composer model, Grok through Cursor includes that
intermediary, and Antigravity denotes a Gemini route. These are compatibility
identities, not instructions to launch another harness. If a fixed harness route
cannot be fulfilled natively, report it unavailable rather than mislabeling a
native model as that route.

For a prior-opinion subject, ship the existing host or user position intact as
the subject; peers still return independent verdicts. Withhold only fresh host
meta-judgment formed after the panel request, not the original position's own
premises. Skeptic mode instead explicitly critiques the supplied host position.

## 2. Permission, model selection, depth, and fixed routing

This skill explicitly requests native reviewer subagents for an authorized
panel. Under a user-OR-applicable-skill delegation rule, that satisfies the
skill-requested exception: do not refuse because the user did not separately
ask for subagents or demand another approval. Mere skill loading without an
applicable dispatch request is not permission. Respect unconditional
higher-priority prohibitions, actual denials, missing tools, recipient policies,
and tool limits; do not bypass them via shell or another harness.

Read applicable `.rocketclaw/config.yaml` and `config.local.yaml` model/route
preferences with their established precedence. Keep configured choices and tiers
authoritative intent. Use `opencode.models` to resolve available concrete native
models and native subagents to execute, with shell only for bounded local
evidence and artifact processing, never an alternate harness dispatcher.
Permission to delegate does not grant permission to override a model. If the
host requires an explicit user model request, omit the optional `model` argument
unless that request exists. Use inherited-model peers when suitable, recording
unmet tier/route intent; a required different-model pass or fixed route that
cannot run leaves cross-model coverage incomplete even if a solo POV is sound.
Peers prefer one model at high reasoning; Composer's fast ceiling remains an
accepted configured exception. Never silently upgrade or alter authorized tiers.

Verify effective nesting capacity separately from permission using effective
OpenCode configuration and its sources (for example `opencode debug config`).
The installed package's depth default is not proof of the consuming session's
effective depth. At launch, classify the actual error: permission denial,
model-argument rejection, missing tool, depth limit, capacity, authentication,
quota, timeout, or another observed route failure. Do not relabel nesting errors
as policy denials or retry denied operations. A parent-coordinator handoff is
allowed only within its permissions and the same review contract, not to evade
a depth limit. Inline work cannot replace required independent voices.

Before sending project content, resolve one fixed target/model/provider route
and all actual recipients, checking the external-recipient allowlist. Announce
who will inspect this project and that the review is read-only. Do not dump
tiers, hashes, scratch paths, or route probes in progress notes. Probe native
capabilities without project content; availability is proven by a usable result,
not binary presence. A non-user-named default observed unavailable may receive
one closest compatible same-target/family/tier substitute, recording the evidence.
Never substitute a user-named model. A retry adding a recipient/intermediary
requires disclosure and approval; other separately gated consultation does too.
Otherwise an explicit panel request authorizes normal read-only consultation.

## 3. Scope, identity, and payload

Normalize one repository-relative read root and ordered include/exclude patterns
for every peer. Never broaden user/host scope. Peers inspect shared subject files
directly; inline only material unavailable on disk. Scope patterns and read-only
prompts are cooperative, not a confidentiality boundary or write sandbox. Deny
write requests and use available read-only tool restrictions; do not promise
secrets inside readable scope are inaccessible.

Capture one repository-scope identity before dispatch: exact committed revision
plus a digest of dirty and untracked content within scope. Use native JJ facts
from the absolute target workspace root, such as `jj log -r @ --no-graph -T
'commit_id'`, and local file enumeration/hashing that covers additions,
deletions, binary content, modes, and symlinks. Do not invoke Git. For non-JJ
projects use a local content identity and disclose that no revision exists.
Revalidate before every reconcile round and final fold-in. On change, restart
all voices on the new identity or report incomplete; never fold stale voices.
See https://docs.jj-vcs.dev/latest/cli-reference/.

Use the caller's absolute Phase 1 `$SCRATCH_DIR`, under the project's local
`.tmp/rocketclaw/`, for payloads, logs, receipts, and round artifacts. Verify
ownership/containment and reject symlinks; create private directories and payloads
under `umask 077`, explicitly `chmod 600` payloads. No global temporary fallback.

Prepare one complete canonical payload: framed question, subject shape, scope,
identity, mode, subject paths, and necessary conversation-only material labeled
as such. Include the user's goal, its strength, and their evidence. Explicitly
permit rejection of all options or the framing. For independent round 1 omit
the host's frozen verdict, other voices, host risk rankings, advocacy, evaluative
labels, and conclusions. Source-located facts are evidence; interpretations wait
for reconciliation. Present host-authored options symmetrically. Prior-opinion
subjects retain their original position intact; skeptic payloads include it.
The identical complete payload must fit every route: never truncate per peer;
an oversized route is unavailable under partial-panel degradation.

## 4. Native dispatch, collection, and bounded recovery

Seed native generic subagents with `references/agents/pov-peer.md` and require
`references/pov-schema.json`. Start all selected peers before waiting when native
concurrency permits; record native task IDs, target, route, requested model,
start/deadline, scope identity, output path, and terminal state in private scratch.
Use native lifecycle operations to await every started peer, collect outputs,
and cancel timed-out work. Never leave detached workers running. Default peer
hard budget is 600 seconds; preserve a valid configured `CROSS_MODEL_HARD_SECS`
increase, never shorten it merely to finish faster. Allow bounded collection
grace without extending the peer's work indefinitely. If native tools cannot
enforce the lifecycle, disclose the limitation and mark affected coverage
unavailable rather than pretending a detached supervisor exists.

Read only owned/contained results. A completed task alone is not usable evidence.
Require a schema-shaped settled `position`, nonempty `reasoning`, valid movement,
`final: true`, and separate route/model receipt facts. `Blocked` with `final:
true` is a usable settled answer; a non-final placeholder is not. Retry a
non-final response once on the same permitted route within its original budget
with an explicit final-answer requirement, then drop that voice. Initial results
require `movement: initial`; reconcile results require `moved` or `held` and why.
Receipt-less served models remain `unverified`; never invent runtime receipts.

For no usable artifact, report bounded actual diagnostic evidence. Distinguish
pre-dispatch infrastructure failures from a started peer's failure. A genuinely
invalid argument may be corrected once before launch. For another recoverable
native infrastructure error, retry only the same permitted route while each
failure is new and plausibly recoverable and the deadline remains; stop on a
repeat. Never retry permission denials, evade nesting limits, broaden scope,
substitute recipients, or reveal withheld initial judgments during recovery.
Authentication-shaped text without provider-capable execution evidence is not
proof the user's account is logged out; do not invent login remediation.

## 5. Dissent and reconciliation

Only independent voices enter convergence. Material dissent is a different
adoption grade, selected approach, proceed/revise-first/reject bottom line, or
fatal-risk judgment, not mere wording, emphasis, confidence, or supporting detail.
Default to the initial independent round plus at most two reconcile exchanges.
Honor explicit user limits: one pass means no reconciliation; larger limits
replace the default. Never reinterpret a smaller limit as a suggestion.

For each exchange, revalidate identity, reconsider every current position, and
verify only disputed project claims that could change the decision. Mark them
verified, contradicted, or unverifiable with sources. Send one identical complete
evidence delta to every survivor, with the full original subject and every
survivor's position/reasoning (at most five succinct source-attributed evidence
bullets per voice). Re-resolve permitted fixed routes and dispatch fresh stateless
peers. Failed peers drop from later rounds; never reuse an old position as if
it participated. Same recipients need no new approval; unexpected ones do.
After initial material dissent, run at least one exchange unless the user
limited the run to one pass. Deciding over an unheard dissenter is not convergence.

Stop at the first matching enum: `confident` when ce-pov has a reasoned position
after weighing survivors; `no-movement` when every peer held and ce-pov remains
unconfident; `limit-reached` when the authorized finite limit ends without
confidence. Convergence is reasoned judgment, not voting. The latter two mean
stalemate, not a settled answer. At a cap, recommend a specific bounded extension
only with an unresolved decision-relevant question, new evidence/framing, and
why it could move a position; otherwise recommend stopping. Further rounds need
approval unless already authorized, and always have a finite cap.

## 6. Decide, disclose, and return

Lead with ce-pov's subject-shaped POV, then a compact note:

- **Confident:** say whether voices aligned; concurrence does not eliminate
  correlated blind spots. If deciding over dissent, name it and why. Distinguish
  recommendations added after the panel from actual peer agreement.
- **Stalemate:** give the current POV, survivors' positions/movement, dropped
  voices' last states, and whether the gap is evidence or judgment. Recommend
  only with a real basis; otherwise explain material tradeoffs. Include the
  bounded further-round recommendation or why to stop.
- **Partial:** name survivors/dropped targets and observed failures, including
  unavailable required cross-model or fixed-route coverage. Never call it fully
  verified.
- **No survivor:** deliver the solo POV plus “cross-model check unavailable or
  incomplete,” naming attempted peers or saying none ran and why. A summons
  always receives this status even if dispatch never entered.

Keep target, actual route, requested/served model, independence, and failure
receipts in the record. Name peers by target and requested model in the default
note; add serving/independence caveats where receipts differ, no model was
requested, or independence affects credibility. Never attribute a view to a
model that did not run. Skeptic voices fold in once with a note about whether
they changed the POV; they never enter convergence. Failed skeptics degrade
like other peers. No peer failure blocks the solo POV.

The panel never mutates. Downstream handoff requires all four: original prompt
explicitly authorized that named action, non-stalemated result, inherited scope,
and non-destructive otherwise authorized action. Otherwise return judgment only;
the calling workflow owns continuation.

## 7. Cleanup

Stop/await all native workers first. Remove consumed payloads, round outputs,
raw logs, receipts, and result artifacts only within this run's verified private
scratch root on success, failure, timeout, or interruption. Preserve only any
explicitly required decision record without raw project context. Never delete
outside the owned run root; peer reasoning and project context must not outlive
their use. This protocol creates no workspaces and grants no workspace-removal
authority.
