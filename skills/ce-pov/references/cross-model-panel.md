# Cross-Model POV Panel

This protocol obtains independent peer POVs, reconciles material disagreement,
and returns one ce-pov decision. ce-pov remains the decision-maker: peers are
cross-checks, never substitutes or votes. The panel is read-only and
non-blocking; every branch ends in a panel POV, a solo POV with an availability
note, or the ordinary POV's explicit blocked-on-missing-context result.

## 1. Resolve the subject, host, and participants

Resolve conversational shorthand before spending: "the approach," "these
options," and "the three options presented" mean the single unambiguous
subject identified by the active conversation. Return missing context to the caller when several possible subjects would
materially change the POV and context cannot distinguish them.

Keep four identities separate for the host and every peer:

- **target** — the user-facing choice (`codex`, `claude`, `grok`, `cursor`, or
  `composer`);
- **harness/intermediary route** — the actual OpenCode-native execution route and provider;
- **requested model** — an explicit model or the route's declared default; and
- **served model** — the model the runtime's receipt (native serving evidence
  reporting which model answered) names, otherwise `unverified`.

The requested model is a fact about the request and is always known; the served
model is a claim about the backend and is known only from a receipt. `unverified`
means no receipt exists, not that the model is unknown. In anything the user
reads, name a peer by its target and requested model. Add a serving caveat only
when a receipt disagrees with the request, or when the route requested no model
(Cursor default/Auto, OpenCode auto). A receipt-less route with a requested model
carries `model_actual: unverified` in the panel record and needs no caveat in
the chat note.

Attest the host from host-provided markers and serving evidence, never from
another installed CLI or home directory. Set `independence_verified: true` only
when the peer's served model family is attestably different from the host's.
Otherwise retain the useful cross-check but label independence unverified; do
not present it as different-model corroboration. If the host family is unknown,
automatic discovery excludes any candidate whose independence cannot be
verified rather than guessing.

Attest the host harness and its serving family as two separate tokens:

```bash
if [ "${CLAUDECODE:-}" = "1" ]; then XHOST_HARNESS=claude; XHOST_FAMILY=claude;
elif [ -n "${CODEX_SANDBOX:-}${CODEX_SANDBOX_NETWORK_DISABLED:-}${CODEX_SESSION_ID:-}${CODEX_THREAD_ID:-}${CODEX_CI:-}" ]; then XHOST_HARNESS=codex; XHOST_FAMILY=codex;
elif [ "${GROK_AGENT:-}" = "1" ] || [ -n "${GROK_SESSION_ID:-}" ]; then XHOST_HARNESS=grok; XHOST_FAMILY=grok;
elif [ -n "${CURSOR_AGENT:-}${CURSOR_CONVERSATION_ID:-}" ]; then XHOST_HARNESS=cursor; XHOST_FAMILY=unknown;
elif [ -n "${OPENCODE_TERMINAL:-}" ]; then XHOST_HARNESS=opencode; XHOST_FAMILY=unknown;
else XHOST_HARNESS=unknown; XHOST_FAMILY=unknown; fi
```

Both tokens come from the same peer-key vocabulary as the targets above, never
from a provider's corporate name: `<host-serving-family>` (`XHOST_FAMILY`) is
`codex`, `claude`, `grok`, `composer`, or `unknown`. `<host-harness>`
(`XHOST_HARNESS`) is `codex`, `claude`, `grok`, `cursor`, `opencode`, or `unknown`. The
snippet is evidence, not the verdict: it resolves the harnesses whose
environment markers it already names, and where it yields `unknown` on a harness
you can identify from your own runtime, attest what you know instead. A harness
the snippet does not name needs no new branch here.

Cursor is the one identity self-knowledge cannot complete, because the harness
does not determine the serving model: it keeps harness `cursor` and family
`unknown` unless an observable serving-family attestation lets you set
`XHOST_FAMILY` to `codex`, `claude`, `grok`, or `composer`.
Never infer serving family from the Cursor brand.

Record `XHOST_FAMILY` and `XHOST_HARNESS` separately in the dispatch record.
Provider IDs such as `anthropic`, `openai`, or `xai` belong in the provider
field, not in either family/harness slot.

`Cursor` and `Composer` are distinct targets:

- `cursor` means Cursor's configured default/Auto choice, not Composer. Preserve
  that compatibility intent; if native OpenCode cannot satisfy it, report the
  named route unavailable rather than launching Cursor. Unless a receipt identifies it,
  report `Cursor default/Auto; serving model unverified` and
  `independence_verified: false`.
- `composer` requests a compatible Composer model, not Cursor Auto.
- Native Grok and Grok through a Cursor intermediary remain different configured
  routes and recipients; compatibility intent does not authorize another harness's dispatch.

Apply exactly one participation branch:

`oracle` is shorthand for the panel behavior, not a keyword gate. An explicit
request to consult other models, gather independent peer opinions, pressure-test
with named peers, or reconcile their disagreement enters the same protocol even
when the request never says `oracle`. A request for ce-pov's take alone does not.

- **Named peers:** exact and uncapped. Announce and run every named target.
  Explicit names override
  `oracle` discovery and its cap. Never rewrite named `Cursor` to Composer or
  replace an explicitly named model with another model.
- **Bare `oracle`:** select up to two reachable, attestably different-model
  targets using conversation preference, local configuration, active project
  conventions, then the declared default order; announce the selection and run
  it. Invoking `oracle` authorizes this ordinary read-only consultation against
  the current project.
- **Explicit unnamed cross-check:** skip the correction-cost check and use the
  count rule below; announce the selected peers and run them.
- **No explicit cross-check:** after ce-pov independently forms its POV, offer
  only when meaningful downstream work will build on the take before an error
  would show up, or it feeds a shared, public, security, or data commitment.
  Adoption Tier 1 is ineligible; Tier 2/3 are eligible. A warm invocation (a
  mid-session second opinion) never offers.

For the count rule: zero reachable means solo plus one availability line. One
or more auto-selected peers means one concise progress line naming the selected
targets before dispatch.
Cursor-default counts automatically only when its serving family can be
attested as different from the host; it remains eligible when explicitly named
or configured as a preference.

**Prior-opinion subjects.** When the subject is an already-formed position —
ce-pov's own prior POV or the user's stated view — that position is the subject
artifact and ships in the payload; peers answer the underlying question with
their own verdict, and those `independent` voices enter convergence (unlike
`skeptic` mode, where the critique does not). Any fresh host meta-judgment formed
after the panel request (the summons) is withheld per Section 4's round-1 sequencing. A user-supplied
position is handled identically to a host-authored one — shipped as the subject,
never capitulated to.

## 2. Normalize scope and freeze repository identity

Normalize the allowed read scope once as:

- one repository-relative workspace root; and
- optional ordered include and exclude path patterns.

Pass that identical representation to every peer prompt and native dispatch. The
default is the repository root. A narrower user- or host-supplied scope is
binding and is never broadened. Peers launched on the same host inspect existing
subject files and supporting evidence directly from this shared working tree;
point them to those files instead of copying their contents into the payload.
Pass material inline only when it exists solely in the conversation or is
otherwise unavailable in the workspace.

Treat include and exclude path patterns as cooperative unless the concrete
runtime turns them into filesystem controls. Never present prompt-only patterns,
a working directory, or a read-only flag as a confidentiality boundary, and
never promise that secrets inside the readable scope are inaccessible. Peers may
search and read within the declared scope but may not mutate the project or
intentionally inspect outside it. Use available native read-only/tool restrictions
and deny peer write requests; do not claim a write sandbox without verified enforcement.

Before initial dispatch, capture one **repository-scope identity**: the committed
JJ revision plus a digest of tracked working-copy and untracked content inside the normalized
scope. Include it in every peer payload. Revalidate it before every reconcile
dispatch and before final fold-in. If it changed, never reconcile or fold stale
voices into the current project: disclose the change and either restart all
voices on the new identity or return an incomplete panel result.

Use `(cd "$workspace_root" && jj log -r @ --no-graph -T 'commit_id')` and
target-root `jj diff`/`jj status` plus bounded file reads to capture the identity;
digest all decision-relevant dirty and untracked scope content, not only names.
Exclude only this run's own verified scratch artifacts from the identity digest
so receipt writes do not invalidate it; never exclude subject evidence. In a
non-JJ project use a stable content digest of the allowed local scope instead.
JJ command references: https://docs.jj-vcs.dev/latest/cli-reference/ .

The caller passes this panel the resolved absolute `$SCRATCH_DIR` created in
SKILL.md Phase 1. Keep payloads, raw output, logs, and result artifacts there;
do not reconstruct the scratch root in this reference. Create each payload under
`umask 077`, then `chmod 600 "$PAYLOAD_PATH"` before dispatch; do not rely on
the ambient umask or a mode flag alone.

## 3. Resolve and announce one fixed route

Routing is adaptable only inside hard boundaries. The requested target plus
safety, authority, independence, read scope, and the rules on which external
recipients may receive project content are durable;
concrete model IDs and availability are resolved through `opencode.models`.

For each peer:

1. Read the applicable `.rocketclaw/config.yaml` and `config.local.yaml` model
   choices, tiers, preferred routes, and recipient policy as authoritative intent.
   Query `opencode.models` without sending project content to resolve exact available IDs.
2. Try the declared preferred mapping first.
3. If that default is observed unavailable, obsolete, or incompatible, choose
   only the closest compatible equivalent in the same requested target, model
   family, and reasoning tier. Record the observed local fact and substitute.
   An explicit user model request cannot become another model.
4. Resolve one concrete target, model choice, OpenCode-native route, provider, and every
   intermediary. Confirm every actual recipient is on the allowlist of permitted
   external recipients.
5. Announce the selected target and route in ordinary language before dispatch.

Preserve configured reasoning tiers. Without a configured override, peer review
uses high reasoning (native Grok uses xhigh); resolve current concrete IDs through
`opencode.models` rather than pinning obsolete adapter defaults. If the native
runtime cannot apply the required tier, disclose that unmet requirement instead
of treating an unsupported option as active.

Execute through OpenCode-native subagents, not another harness CLI or dispatcher.
Legacy configured route tokens (`codex`, `claude`, `grok-cli`, `grok-cursor`,
`cursor`, `composer`, `opencode`) preserve recipient/model intent; they are not
commands to invoke. A native mapping must satisfy that intent and recipient policy.
If a fixed intermediary/default cannot be reproduced, report it unavailable.

**Delegation, model choice, and nesting are separate gates.** This protocol
explicitly requests peer delegation. Under a host rule permitting subagents when
the user OR an applicable loaded skill asks, these instructions satisfy the skill
exception; do not require another user request. An unconditional higher-priority
prohibition, missing tool, or actual permission denial still applies. A skill that
does not request delegation does not grant it merely by being loaded.

Model configuration and tiers are intent, not authority to override host policy.
If the host requires an explicit user model request before an override, omit the
native subagent's optional `model` argument unless that request exists. Use a
suitable inherited model for otherwise permitted reviewers, disclosing any unmet
configured tier or route. These are separate reviewers, not cross-model proof.
If a required different-model pass or named fixed route cannot run, mark that
coverage incomplete, never fully verified or silently substituted.

Verify effective depth from runtime-discovered configuration and the current
nesting level; shipped `experimental.subagent_depth` is a project default, not a
guarantee that a consuming project adopted it or that capacity remains. Classify
dispatch failures by the actual error: depth/capacity, permission, model-argument
rejection, or missing tool. A permitted parent-coordinator handoff can preserve
the fixed route and payload; inline work cannot satisfy an independent peer pass.
Never retry a denied operation or evade a nesting limit through shell/another harness.

Catalog availability is only candidate evidence. Provider-capable native dispatch
owns authentication truth; a valid artifact proves usable completion. Classify a
failure from its actual structured diagnostics, not a generic terminal state.

The dispatched worker runs only the fixed route. It must return failure to the
host rather than automatically hopping to another provider or intermediary. If
a retry would add an unexpected recipient or intermediary, resolve it at the
host, explain the change, and ask before starting a new fixed-route job. An
active user, project, or organization instruction that separately gates external
consultation also requires approval. Otherwise the explicit peer, cross-check,
or `oracle` invocation is the authority to proceed. A named peer that cannot run
within these rules is reported, never silently replaced or dropped.

The pre-dispatch update should say who will inspect the subject and that the
review is read-only. Do not recite scope mechanics, promise that repository
secrets are inaccessible, or describe probe results, CLI versions, model tiers,
commit hashes, repository identity, route health, job lifecycle, or scratch
paths. Mention a cooperative scope restriction only when it materially changes
the user's choice. Refer to the codebase as "this project" or "the repository"
unless the user supplied a recognizable name.

## 4. Dispatch, wait, reap, and collect

Prepare one complete canonical payload containing the framed question, subject
shape, normalized read scope, repository-scope identity, mode, paths to subject
material already in the workspace, and required conversational material that is
not available there. Let peers inspect and ground against the shared working
tree. Do not duplicate readable files or add a host-curated architecture summary
merely to brief the peer.

For an initial `independent` round, exclude ce-pov's position and every other
voice's conclusion. The proposal, document, or approach set being judged is the
subject and remains fully available; independence means withholding prior
judgments about it, not withholding the artifact. The host's own argument —
candidate-risk enumerations, decisive premises stated as fact, advocacy framing,
and evaluative option labels — is reconcile-round material, not round-1 material;
the independent round carries only the framed question, the subject, the read
scope, and the evidence. Define round-1 evidence by provenance: source-located
facts and the user's decision-relevant need are round-1 material, while host
interpretations, risk rankings, and recommended consequences are not (for
example, "the file at PATH contains X" is round-1 evidence, while "X is the risky
option" waits for reconcile). Label inlined conversation-only material as such,
and carry the user's stated goal — including its intensity — when it bears on the
decision. State in the payload that rejecting every supplied option, or the
framing itself, is a valid position. When ce-pov authored the subject in-session,
present the options symmetrically in the payload's own words even though the full
subject document remains attached. When the subject is itself an already-formed
position (Section 1), the list of material to withhold above applies only to fresh
host framing generated in response to the panel request: the position's own
premises, labels, and advocacy ship intact as the subject artifact, and only host
meta-judgment formed about it after the panel request waits for reconcile — peers still return their own
independent verdict. For `skeptic` mode, include
ce-pov's position because critiquing it is the task. Reconciliation payloads
follow Section 5 and deliberately include already-formed positions.

Verify that the same complete payload fits every selected route; never truncate
it per provider. A route that cannot accept it is unavailable under the ordinary
partial-panel degradation rule.

Use native subagents with the resolved permitted model (or omit `model` for
inherited execution), seeded with `references/agents/pov-peer.md`, the canonical
payload, and the exact result path for host publication. Peers return JSON without
writing files; the host atomically publishes it to that verified path. Pass the actual absolute workspace root
separately from a narrower read root. Pre-create the private round directory under
the Phase 1 local `.tmp/` scratch root, never outside it. Start all ready peers
concurrently before waiting, recording every returned task/session ID. Named
peers each receive their exact target; selected panels each receive one selected peer.

Native task ownership and lifecycle replace detached runner jobs. Use shell only
for permitted local file preparation, evidence reads, and receipt handling, never
to bypass native delegation policy. A denied or unavailable permission creates
no peer task; record it and continue with survivors. Started-task network,
authentication, or provider failures follow terminal/recovery rules below.
Do not unset sandbox markers to claim connectivity or broaden permissions by
default; request only an actual required grant through the host's supported flow.
Retain the distinction between launch context and enforceable peer restrictions.

Each peer returns `<run-dir>/pov-<target>.json`, with Grok routes using `grok`.
Record the exact path and native ID, not a guessed filename. Use a 600-second
peer hard budget by default, respecting a valid `CROSS_MODEL_HARD_SECS` override;
any supported supervisor timeout must be at least `max(1230, budget + 30)` seconds
and must not inherit a stale shorter cap. Use one aggregate deadline
of that budget plus 10 seconds, measured after the final start. Wait through
native supported bounded slices of at most 30 seconds without crossing the
deadline; one short slice is not completion. At deadline cancel run-owned active
tasks through the supported lifecycle and collect terminal status in a final
bounded wait. If the runtime cannot provide this lifecycle, disclose the
capability blocker; never invent timeout/cancellation flags or claim a task stopped.

Classify each task from actual terminal evidence; completion alone does not prove
a usable artifact. Read result/log files only after verifying exact run ownership,
containment, no symlink redirection, and expected private permissions. Preserve
atomic result publication with a temporary file in the same local run directory.
Accept only schema-shaped artifacts whose `position` is a settled
answer to the framed question, with non-empty `reasoning`, a valid `movement`,
and the route/model receipt tuple. Settledness is the peer's own declaration
through the schema's required `final` flag, never a reading of its prose: a
settled `Blocked — …` verdict marked `final: true` is a usable answer, while
any shaped artifact whose `final` is not true is a placeholder. The host
retries a non-final artifact once on the same route with a final-answer
requirement, inside the same hard window, and if it recurs or no window
remains drops the voice with `peer skip evidence: non-final position`. Should
a non-final artifact still reach you, treat it as no usable artifact, not as a
peer voice. Initial responses require `movement: initial`; reconcile
responses require `moved` or `held` plus what changed or why the new evidence
was insufficient.

Attribute a served model only from a receipt, never from the request. Record
target, actual harness/intermediary route, requested model, served model, and
`independence_verified` separately. A served model of `unverified` stays
`unverified` in the record; it does not become "unknown model" in the note,
because the requested model is known.

Capture native receipts for route, target, actual harness (`opencode`), requested
model, served model, and verified independence using `references/pov-schema.json`.
The host namespaces `voice` as `peer-<provider>` and adds the verified receipt
tuple to the validated peer JSON; peer assertions cannot manufacture receipts.
A catalog entry or requested model is not a served-model receipt. Missing receipt
means `model_actual: unverified`; never infer actual serving from peer prose.
Distinguish a shared native capability failure from a route-specific provider/model
failure; replacements still follow Section 3's recipient and model-permission rules.
Only positive runtime evidence proves no provider egress occurred; do not claim
that merely because no usable artifact arrived.

If a task yields no usable artifact, retain bounded `peer skip evidence`
from its actual diagnostics to state an observed quota, authentication, or route failure; never
invent a cause. Attribute an account authentication failure only after
provider-capable dispatch is positively established by the launch context or
provider response; then report the observed failure and login or
credential-refresh remediation. Without that proof, authentication-shaped peer
text describes only the peer's execution context: a sandboxed host can produce
the same signal as a genuine logout, so never report it as the user's account
being logged out or prompt a login command.

## 5. Detect dissent, verify claims, and reconcile

Only `mode: independent` voices enter convergence. Material dissent means a
different adoption grade, a different selected approach, or document bottom
lines that imply different reader actions (`proceed`, `revise-first`, or
`reject`) or disagree on whether a risk is fatal. Wording, emphasis, confidence,
or supporting detail with the same decision is concurrence.

The default limit is the independent initial round plus at most two reconcile
exchanges. A user-supplied pass or round limit overrides it: "one pass" or "one
round" means no reconcile exchange, while a larger explicit limit replaces the
default cap. Never reinterpret a smaller user limit as a suggestion.

For each reconcile exchange:

1. Revalidate repository-scope identity. Restart or return incomplete on change.
2. Have ce-pov reconsider every current position and its evidence.
3. Identify only disputed project claims that could change the decision. Verify
   them against the allowed scope and classify each as `verified`,
   `contradicted`, or `unverifiable`, with source locations when available.
4. Build one common evidence delta. Send the identical complete delta to every
   surviving peer—never route-specific truncation—along with the full original
   subject and every surviving voice's current position and reasoning, capped at
   five succinct source-attributed evidence bullets per voice.
5. Re-resolve every fixed route under Section 3, then dispatch a fresh stateless
   round. The same recipients need no question; an unexpected new recipient or
   intermediary does. A failed peer is dropped for later rounds; do not reuse its
   older position as if it participated.

After fold-in, stop on the first matching enum:

- **`confident`** — ce-pov has a reasoned POV after weighing every survivor;
- **`no-movement`** — every surviving peer returned `held` and ce-pov is still
  not confident; or
- **`limit-reached`** — the effective user-authorized finite limit completed
  after initial dissent and ce-pov is still not confident.

Convergence is ce-pov's reasoned confidence, not a vote. A three-way split still
ends in a confident decision or the stalemate disclosure. Route `confident` to
the **Confident** disclosure below. Route `no-movement` and `limit-reached` to
the **Stalemate** disclosure; those stops mean bounded reconciliation ended
without confident convergence, never that ce-pov should infer a settled result.

The cap stops automatic dispatch; it is a checkpoint, not proof that another
round would be useless. At the checkpoint, decide whether a bounded extension is
likely to change the result. Recommend a specific number of additional exchanges
only when ce-pov can name the unresolved decision-relevant question, the new
evidence or framing the extension would introduce, and why it could move a
position. Otherwise recommend stopping. Further rounds require user approval
unless the user supplied the larger limit in advance; each approval establishes
a new finite cap, never an open-ended loop.

## 6. Decide and disclose

Lead with ce-pov's POV in the active subject shape, followed by a compact panel
note:

- **Confident:** state whether voices aligned. Concurrence raises confidence but
  does not eliminate correlated-model blind spots. If ce-pov decided over
  dissent, name the disagreement and why its result prevailed.
- **Stalemate:** state ce-pov's current position, each surviving peer's position
  and movement, every dropped voice's last state, and whether the disagreement
  is an evidence gap or judgment difference. Recommend when there is a real
  basis; otherwise say "Either is viable" with the material tradeoffs. At a cap,
  add **Further rounds:** recommend a specific bounded extension with its new
  evidence path, or recommend stopping because no additional exchange is likely
  to change the result.
- **Partial:** name surviving and dropped targets and the observed failure state
  (for example quota, authentication, timeout, or a non-final placeholder
  position that survived the bounded retry).
  Missing required cross-model independence or a fixed route remains incomplete,
  even when same-model reviewers delivered useful checks; say so explicitly.
- **No survivor:** deliver the solo POV with "cross-model check unavailable or
  incomplete." When a summons was present but the panel branch never entered
  (no reachable peers, or the branch was never entered), still state that panel status —
  which peers were attempted, or that none ran and the observed reason — rather
  than shipping a bare solo verdict.

Retain target, route, requested model, served model, and independence receipts in
the panel record, but keep the default chat note decision-relevant: name the
peer by target and requested model, its position and movement, any observed
failure, and a serving or independence caveat only where a receipt disagreed, no
model was requested, or independence affects credibility. Do not dump route or model diagnostics unless they
materially change the conclusion or the user asks. Never attribute a position to
a model that did not run.

The panel itself never mutates. After delivery, apply SKILL.md Phase 4's
four-part conjunction: the original prompt explicitly authorized the named
downstream action, the result is non-stalemated, the action stays in inherited
scope, and it is non-destructive and otherwise authorized. All four must pass
for handoff; otherwise return the judgment without starting downstream work. A calling workflow retains ownership of continuation.

## 7. Skeptic mode and degradation

When asked to challenge ce-pov rather than form an independent POV, set
`mode: skeptic`. Fold a valid attributed critique into ce-pov once, but do not
put that voice into convergence. Disclose whether it changed the POV. A failed
skeptic degrades like any unavailable peer.

A peer never blocks a POV. Mid-round failure drops only that voice; an
oversized canonical payload drops routes that cannot accept the identical
payload; no surviving peer yields the solo POV plus the availability note.

Distinguish a route-level failure from a dispatch-infrastructure failure. A
route that runs and returns no usable artifact is dropped as above. But if the
native dispatch infrastructure fails unexpectedly before a task starts, do not
drop that peer on the first recoverable error. Correct a pre-launch argument once
or use a permitted parent-coordinator handoff, holding the selected target and
model, the normalized read scope, and the round's independence rules fixed.
Keep recovery bounded by the panel's aggregate deadline; stop and fall to the
solo POV once a failure repeats or the deadline is spent. A recovery may not
substitute a different target, widen read scope, or include a withheld
position — those make the recovered peer's result untrustworthy, not merely
unavailable. A permission denial, missing tool, prohibited model override, or
nesting limit is not a recoverable bridge error: report it accurately, do not
retry or route through another harness. Required unavailable different-model or
fixed-route coverage remains incomplete, even if inherited-model reviewers ran.

## 8. Cleanup

Stop or cancel and verify termination of run-owned peers first. Remove every consumed task artifact directory, round output directory, payload, raw log,
and result beneath this run's private scratch root on success, failure, timeout,
interruption, and reap. Never delete outside the current run root. Peer reasoning
and project context must not outlive their use.

## Participation, announcement, and disclosure (relocated from the body)

A summons (a panel request) is an **affirmative** request to consult or reconcile peers, detected by reasoning over the invocation context — the user's wording or a calling skill's args. Wording that declines consultation ("solo POV, do not cross-check") or merely recounts a past cross-check names the same terms without asking for one, and is not a summons: peers are not dispatched and no project context leaves the run. For an affirmative request, a caller's paraphrase in one channel never cancels a summons still present in another; only a summons erased from every readable channel upstream is unrecoverable here.
Invoking a named peer, an explicit cross-check, or `oracle` authorizes the panel protocol's normal read-only consultation against this project. Announce the selected peers before dispatch; ask only when a retry adds an unexpected recipient or intermediary, or an active instruction requires separate approval. Peers inspect the shared working tree directly and are told not to edit it. The panel protocol preserves an unbiased initial round, bounds evidence-based reconciliation while honoring user-supplied pass limits, and attributes only receipt-supported independence.
Any POV delivered after a summons states which peers ran, or that none did and the observed reason; if no panel runs after a summons, keep the verdict content unchanged but add that panel-status line rather than shipping a bare solo verdict. A POV with no summons keeps the solo result unchanged with no panel note.
Keep the host's own frozen position out of an independent peer's initial context; expose it only when the requested task is to critique that position or when a later reconciliation round compares already-formed views.
