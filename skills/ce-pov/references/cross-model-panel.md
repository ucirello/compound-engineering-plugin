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
- **harness/intermediary route** — the native OpenCode route and any authorized intermediary that runs it;
- **requested model** — an explicit model or the route's declared default; and
- **served model** — the model the worker's receipt (its record of the route
  and model that actually answered) confirms, otherwise `unverified`.

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

Section 4 passes the attested host family and harness as separate payload fields.
Provider names such as `anthropic`, `openai`, or `xai` are recipients, not family
tokens; reject an invalid identity before dispatch.

`Cursor` and `Composer` are distinct targets:

- `cursor` preserves the configured
  default/Auto choice. No model was requested, so unless a receipt identifies it,
  report `Cursor default/Auto; serving model unverified` and
  `independence_verified: false`.
- `composer` requests the current compatible Composer model.
- `grok` requests the configured Grok model; a Cursor intermediary remains a
  different recipient requiring authorization, not an automatic fallback.

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

Pass that identical representation to every peer prompt and route adapter. The
default is the repository root. A narrower user- or host-supplied scope is
binding and is never broadened. Peers launched on the same host inspect existing
subject files and supporting evidence directly from this shared working tree;
point them to those files instead of copying their contents into the payload.
Pass material inline only when it exists solely in the conversation or is
otherwise unavailable in the workspace.

Treat include and exclude path patterns as cooperative unless the concrete
adapter turns them into filesystem controls. Never present prompt-only patterns,
a working directory, or a read-only flag as a confidentiality boundary, and
never promise that secrets inside the readable scope are inaccessible. Peers may
search and read within the declared scope but may not mutate the project or
intentionally inspect outside it.

Before initial dispatch, capture one **repository-scope identity**: the committed
revision plus a digest of dirty and untracked content inside the normalized
scope. Include it in every peer payload. Revalidate it before every reconcile
dispatch and before final fold-in. If it changed, never reconcile or fold stale
voices into the current project: disclose the change and either restart all
voices on the new identity or return an incomplete panel result.

In a JJ workspace, inspect `@` and its parent with `jj log`, and inspect the
scoped working-copy changes with `jj diff` and `jj status`; hash the scoped
file contents as well so untracked or ignored material peers read is covered.
Run all JJ commands from the target workspace's absolute root, not with `-R`
alone, and retain repository-relative file paths. In a non-JJ folder use the
same scoped content digest without inventing a committed revision. See
https://docs.jj-vcs.dev/latest/cli-reference/ and
https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace .

The caller passes this panel the resolved absolute `$SCRATCH_DIR` created in
SKILL.md Phase 1. Keep payloads, raw output, logs, and result artifacts there;
do not reconstruct the scratch root in this reference. Create each payload under
`umask 077`, then `chmod 600 "$PAYLOAD_PATH"` before dispatch; do not rely on
the ambient umask or a mode flag alone.

## 3. Resolve and announce one fixed route

Routing is adaptable only inside hard boundaries. The requested target plus
safety, authority, independence, read scope, and the rules on which external
recipients may receive project content are durable;
concrete model IDs, CLI flags, and availability are adapter defaults.

For each peer:

1. Probe current route and model capabilities without giving the process project
   content or repository access.
2. Try the declared preferred mapping first.
3. If that default is observed unavailable, obsolete, or incompatible, choose
   only the closest compatible equivalent in the same requested target, model
   family, and reasoning tier. Record the observed local fact and substitute.
   An explicit user model request cannot become another model.
4. Resolve one concrete target, model choice, harness route, provider, and every
   intermediary. Confirm every actual recipient is on the allowlist of permitted
   external recipients.
5. Announce the selected target and route in ordinary language before dispatch.

These compatibility target tokens identify model choices, not dispatch commands.
Resolve them through `opencode.models` and execute with native `subagents`:

| Target | Route token(s) |
|--------|----------------|
| `codex` | `codex` |
| `claude` | `claude` |
| `grok` | configured Grok model; a configured Cursor intermediary needs separate authorization |
| `cursor` | `cursor` |
| `composer` | `composer` |
| `opencode` | `opencode` |

Read the project's `.rocketclaw/config.yaml` and `config.local.yaml` model choices
and tiers before resolution; configured choices remain authoritative. Absent an
override, preserve the declared editorial defaults: `gpt-6.1-sol` high for
`codex`, `claude-opus-5-5` high for `claude`, `grok-4.7` xhigh for Grok,
`grok-4.7-xhigh` for the configured Cursor Grok choice, and `composer-2.5-fast`
for Composer (its ceiling). Cursor default/Auto and OpenCode auto remain unforced
choices. Query `opencode.models` for exact provider/model IDs and available
variants without project content. Do not invoke another harness's dispatcher.
If the native runtime cannot represent an exact requested target, default/Auto
choice, intermediary, or tier, report it unavailable instead of silently
substituting. Recipient allowlists still apply to the selected native provider.

Binary presence proves only that a route is a candidate. Pre-dispatch capability
evidence may refine the fixed route only when the current host context makes that
evidence authoritative. Do not preflight authentication there: the
provider-capable worker attempt owns authentication truth, and a valid artifact
is the usability proof. Classify a failed run from its structured diagnostics
rather than guessing from a generic terminal state.

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

Use native `subagents` with the exact model/variant resolved by `opencode.models`;
use `shell` only for bounded local inspection, result persistence, and cleanup,
never to launch another harness. Pass the absolute repository root separately
from the narrower read root, the host attestations, identical canonical payload,
and `references/agents/pov-peer.md` and `references/pov-schema.json` contracts.
Create private round output directories under the Phase 1 local `.tmp/` scratch.
Launch one fresh stateless peer per named or selected target concurrently; start
all peers before waiting and await every result. Keep the host's frozen position
out of independent round 1 as specified above.

Maintain a coverage ledger for every selected peer: target, requested provider,
model and variant, actual route, launch ID, start time, terminal state, result
path, observed failure and serving receipt. Each peer returns its structured
result to the host, which persists it to `<run-dir>/pov-<target>.json` privately;
task completion alone is not proof of a usable artifact. Do not expose mutation
tools to peers where runtime controls permit; otherwise label read-only scope as
cooperative rather than enforced. A denied permission grant creates no job and
drops only that voice. Do not unset sandbox markers to claim network access;
seek only authorized native permissions for the disclosed recipient. Lifecycle
inspection needs no extra provider permission.

Use `CROSS_MODEL_HARD_SECS` as the worker hard budget (600s default) and honor a
configured increase. Bound streaming output inactivity where observable; lack
of observable streaming is not proof of a hung peer. The aggregate deadline is
the epoch after final launch plus the effective hard budget plus 10s. Wait in
at most 30s slices within that deadline, not one short slice followed by an early
drop. At the deadline cancel all nonterminal peers, await cancellation in a final
at most 10s slice, and record any cancellation limitation. Native supervision
must not undercut the effective worker budget; when configurable, retain the
supervisor floor `max(1230, effective hard budget + 30)`. Do not let a stale
`CE_PEER_HARD_SECS` override shorten it. If the runtime cannot provide bounded
execution and cancellation, mark that route unavailable before launch rather
than create an uncontrolled detached job.

Read only results belonging to this run: reject symlinks, foreign-owned paths,
or paths outside the private run directory, including error and fallback logs.
If the structured return is missing but this peer's captured native output
contains a complete schema-shaped JSON object, recover and validate that object
without inventing missing fields. Namespace `voice` to the resolved target and
record `cross_model_route`, `cross_model_target`, `cross_model_harness`,
`serving_family`, `model_requested`, `model_actual`, and `independence_verified`
in the persisted result. Only runtime/provider serving evidence is a model
receipt; a peer's self-description or the requested model is not such evidence.
Keep `model_actual: unverified` and independence false when receipts are absent;
record a model mismatch without relabeling the requested target.
Classify every launched peer from its observed terminal state. Accept only
schema-shaped artifacts whose `position` is a settled
answer to the framed question, with non-empty `reasoning`, a valid `movement`,
and the route/model receipt tuple. Settledness is the peer's own declaration
through the schema's required `final` flag, never a reading of its prose: a
settled `Blocked — …` verdict marked `final: true` is a usable answer, while
any shaped artifact whose `final` is not true is a placeholder. The worker
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
because the requested model is known. If a job yields no usable artifact, use bounded `peer skip evidence`
from its log to state an observed quota, authentication, or route failure; never
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
native dispatch infrastructure fails unexpectedly — a crash, a rejected argument
before any job starts, an unavailable tool route — do not drop that peer on the first
error. Correct the invocation and attempt the same native resolved route, holding the selected target and
model, the normalized read scope, and the round's independence rules fixed.
Keep attempting only while each failure is a new, plausibly recoverable one and
the panel's aggregate deadline has not passed; stop and fall to the solo POV
once a failure repeats or the deadline is spent. A hand recovery may not
substitute a different target, widen read scope, or include a withheld
position — those make the recovered peer's result untrustworthy, not merely
unavailable.

## 8. Cleanup

Remove every consumed job directory, round output directory, payload, raw log,
and result beneath this run's private scratch root on success, failure, timeout,
interruption, and reap. Never delete outside the current run root. Peer reasoning
and project context must not outlive their use.

## Participation, announcement, and disclosure (relocated from the body)

A summons (a panel request) is an **affirmative** request to consult or reconcile peers, detected by reasoning over the invocation context — the user's wording or a calling skill's args. Wording that declines consultation ("solo POV, do not cross-check") or merely recounts a past cross-check names the same terms without asking for one, and is not a summons: peers are not dispatched and no project context leaves the run. For an affirmative request, a caller's paraphrase in one channel never cancels a summons still present in another; only a summons erased from every readable channel upstream is unrecoverable here.
Invoking a named peer, an explicit cross-check, or `oracle` authorizes the panel protocol's normal read-only consultation against this project. Announce the selected peers before dispatch; ask only when a retry adds an unexpected recipient or intermediary, or an active instruction requires separate approval. Peers inspect the shared working tree directly and cannot edit it. The panel protocol preserves an unbiased initial round, bounds evidence-based reconciliation while honoring user-supplied pass limits, and attributes only receipt-supported independence.
Any POV delivered after a summons states which peers ran, or that none did and the observed reason; if no panel runs after a summons, keep the verdict content unchanged but add that panel-status line rather than shipping a bare solo verdict. A POV with no summons keeps the solo result unchanged with no panel note.
Keep the host's own frozen position out of an independent peer's initial context; expose it only when the requested task is to critique that position or when a later reconciliation round compares already-formed views.
