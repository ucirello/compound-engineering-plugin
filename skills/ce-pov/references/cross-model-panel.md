# Cross-Model POV Panel

Obtain independent peer POVs, reconcile material disagreement, and return one
ce-pov decision. Peers are cross-checks, never substitutes or votes. The panel is
read-only and non-blocking: every branch returns a panel POV, a solo POV with
coverage disclosure, or the ordinary blocked-on-missing-context result.

## 1. Resolve subject, participation, and authority

Resolve conversational shorthand to the single unambiguous subject. Return
missing context to the caller when competing readings would change the result.
A summons is an affirmative request to consult or reconcile peers, including
`oracle`, named peers, or an unnamed cross-check in any invocation channel.
Declining consultation or recounting a past check is not a summons. A caller's
paraphrase does not cancel a summons still present in another readable channel.

- Named peers are exact and uncapped; explicit names override oracle discovery.
  Announce and attempt every named participant, reporting any that cannot run.
- Bare `oracle` selects up to two reachable, attestably different-model peers
  using conversation preferences, configuration, project conventions, then the
  configured default order. An unknown host family cannot establish independence.
- An explicit unnamed cross-check skips the correction-cost check and announces
  available independent participants. Zero available means solo plus disclosure.
- Without a summons, offer only after independently forming the POV when costly
  downstream work or a public, security, or data commitment warrants it. Adoption
  Tier 1 is ineligible; Tier 2/3 are eligible. Warm invocations and calling-workflow
  returns never make proactive offers.

This skill explicitly requests native reviewer subagents for an authorized panel.
Under a user-OR-loaded-skill delegation rule that request satisfies the exception;
do not demand another user approval. Loading a skill without a dispatch request
does not grant permission. An unconditional higher-priority prohibition, missing
tool, or actual denial remains binding and cannot be bypassed through shell or
another harness.

Delegation permission, model-selection permission, and nesting capacity are
separate. If a host requires an explicit user model request for an override,
omit the optional native `model` argument when none exists. Use inherited-model
reviewers only where they can satisfy the contract; preserve configured tiers and
routes as intent and disclose what cannot be satisfied. Same-model reviewers are
separate reviewers, not different-model corroboration. An unavailable required
different-model pass or exact route is incomplete coverage, never fully verified.
Check discovered project depth configuration and runtime parent depth; the package's
shipped default does not prove a consuming project's effective capacity. Identify
depth/capacity, permission, model-argument, and missing-tool failures from actual
errors. A parent coordinator may dispatch independent peers when permitted; inline
host reasoning cannot replace required independence. Never evade depth or denial.

## 2. Freeze scope, identity, and independent context

Normalize one repository-relative read root and ordered include/exclude patterns.
Pass the identical scope to every peer. Narrow user scope is binding and never
broadened. Peers inspect subject files directly; inline only conversation-only or
otherwise unavailable material. Prompt-only patterns and read-only instructions
are cooperative controls, not confidentiality boundaries or write sandboxes.
Use available native read-only controls and prohibit mutations or intentional
out-of-scope inspection; do not promise secrets in readable scope are inaccessible.

Capture the current JJ revision plus a digest of tracked modifications and
untracked content in scope. Revalidate before every reconcile and final fold-in.
On change, restart all voices on the new identity or return incomplete coverage;
never fold stale positions into the current project. Run JJ from the verified
absolute target workspace root, e.g. `(cd "$workspace_root" && jj log -r @)`.
Repository-scoped GitHub reads use
`(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`.
References: https://docs.jj-vcs.dev/latest/cli-reference/ and
https://docs.jj-vcs.dev/latest/git-command-table/ . No workspace creation or
mutation is required for this read-only panel.

Reuse the absolute Phase 1 scratch directory beneath local `.tmp/`. Create private
round directories under it, mode-600 payloads under `umask 077`, and keep all raw
output, errors, receipts, and results there. Never use global temporary fallbacks.

Prepare one complete canonical payload: framed question, subject shape, normalized
scope, frozen identity, mode, subject paths, required conversation-only material,
and `references/agents/pov-peer.md` plus `references/pov-schema.json`.
Every route receives the same complete payload; never truncate per provider.
An oversized route is unavailable under partial-panel degradation.

For initial `independent` rounds, withhold the host's frozen POV and every other
voice's conclusion. Include source-located facts and the user's goal, including
its intensity, but withhold fresh host advocacy, risk rankings, evaluative labels,
and interpretations until reconciliation. Rejecting all options or the framing is
valid. Present host-authored options symmetrically while keeping the subject file
available. A prior host or user opinion explicitly submitted for judgment is the
subject: its premises and advocacy ship intact, but fresh host meta-judgment stays
withheld. These peers form independent verdicts and enter convergence. In `skeptic`
mode include the host POV because critique is the task; skeptics do not converge.

## 3. Resolve and announce fixed native routes

Keep target, actual route/intermediary, requested model, and served model separate.
Targets such as `codex`, `claude`, `grok`, `cursor`, and `composer` retain their
requested meaning. Cursor default/Auto is not Composer, and Grok via Cursor is
not a direct Grok route. Do not silently rewrite a named target or intermediary.
Configuration (`.rocketclaw/config.yaml`, applicable local configuration and
example defaults) remains authoritative for model choices, reasoning tiers, and
route intent. Use `opencode.models` to resolve exact available provider/model IDs
before any permitted native model selection. Model availability is not proof of
authentication or successful execution.

Use OpenCode-native subagents; do not invoke another harness's dispatcher or the
removed bridge scripts. Shell may prepare private payloads, perform bounded
read-only probes, collect evidence and clean owned scratch, not evade delegation
or model policy. Probe capabilities without project content first. Try the
configured preferred mapping; when an unpinned default is demonstrably unavailable
or obsolete, only a permitted same-target, same-family, same-tier equivalent may
replace it, with the observed reason recorded. Explicit user models are exact.
An exact harness/default route unavailable natively is incomplete, not permission
to simulate it with a similarly branded model.

Resolve provider and every actual intermediary against permitted recipients.
Announce who will inspect this project and that the review is read-only before
dispatch. Do not dump diagnostics, hashes, job lifecycle or scratch paths. A summons
authorizes ordinary read-only consultation, subject to actual host permissions.
Ask only for a new unexpected recipient/intermediary or separately required
approval. Workers never hop providers or intermediaries themselves.

Attest host family from runtime serving evidence, not installed CLIs or home
directories. Keep requested and served model distinct. Record served model only
from trustworthy native session/provider receipts, never the request or peer's
self-identification; absent evidence remains `unverified`. Set
`independence_verified: true` only when host and peer served families are attestably
different. Receipt-less or same-family peers remain useful checks but never prove
cross-model independence. Cursor default/Auto requires an actual receipt to count
automatically as a different-model peer. Do not attribute a position to a model
that did not run.

## 4. Dispatch, bound, collect, and recover

Start all permitted peer calls concurrently before awaiting completion, using
fresh native subagents and `background: false` when supported. Record native call
or session IDs, target, requested/served models, actual route, start/terminal state,
and independence evidence. If concurrency is unavailable, disclose the limitation.
Use a 600-second worker budget by default, honoring an authorized configured
`CROSS_MODEL_HARD_SECS` increase; the aggregate deadline is that budget plus ten
seconds from the last start. Use native bounded waits/cancellation where available,
never unbounded polling. Do not cancel healthy work with a shorter hardcoded cap.
At deadline cancel owned nonterminal jobs through the native lifecycle, collect
final states, and disclose inability to stop a job rather than deleting live state.

Completion alone is not a usable artifact. Read only verified run-owned results
and bounded diagnostic logs. Require the supplied schema, settled `position`,
nonempty `reasoning`, valid movement and external-check fields, and `final: true`.
A settled Blocked answer is valid; a placeholder is not. Initial movement is
`initial`; reconcile movement is `moved` or `held` with what changed or why not.
Retry a non-final response once on the same fixed route within the same deadline
with a final-answer requirement; otherwise drop it as a non-final position.
Record the route/model receipt tuple alongside the artifact without inventing
missing serving evidence.

Classify actual outcomes: not launched, quota, authentication, timeout, malformed
or non-final output, permission denial, model rejection, depth/capacity, or missing
tool. Never invent a cause. Authentication-shaped text proves an account problem
only with provider-capable execution or a provider response; otherwise it describes
execution context and does not justify claiming logout or recommending login.

For a recoverable native infrastructure error before launch, attempt the same
resolved route with fixed model, read scope, and independence rules. Correct a
bad pre-launch argument once when allowed. Continue recovery only for a new
plausibly recoverable error within the aggregate deadline; stop when one repeats.
Never retry denial, evade depth, silently change targets, widen scope, or leak a
withheld position. A route returning no usable artifact is dropped. Preserve
survivors; no survivors yields the solo POV with an availability note.

## 5. Verify dissent and reconcile

Only independent voices enter convergence. Material dissent is a different
adoption grade, selected approach, or document bottom line implying proceed,
revise-first, reject, or a fatal-risk disagreement. Wording or emphasis with the
same decision is concurrence. Default: initial round plus at most two reconcile
exchanges. An explicit user limit overrides it; one pass means no reconciliation.

For each exchange revalidate identity, reconsider every position, verify only
decision-changing disputed project claims as verified/contradicted/unverifiable
with sources, and build one common evidence delta. Send every survivor the same
complete delta, original subject, and every survivor's current position/reasoning
with at most five succinct source-attributed evidence bullets per voice. Dispatch
a fresh stateless round on revalidated fixed routes. Existing recipients need no
new approval; unexpected ones do. Drop failed voices, never treating their old
position as participation in a later round.

Stop at reasoned host confidence, no movement while still not confident, or the
authorized finite limit while still not confident. Confidence is not a vote; a
three-way split may end with a reasoned decision or stalemate. At a cap recommend
a specific bounded extension only when an unresolved question, new evidence path,
and potential position change justify it; otherwise recommend stopping. Further
rounds require approval unless already authorized, always establishing a finite cap.

## 6. Deliver, disclose, and clean up

Lead with the active subject-shape POV and a compact panel note:

- Confident: concurrence or the dissent and why the host's decision prevailed;
  concurrence does not remove correlated-model blind spots.
- Stalemate: current host and surviving peer positions/movement, dropped voices'
  last state, evidence gap versus judgment difference, and bounded-extension or
  stop recommendation. Say "Either is viable" when that is the supported result.
- Partial: surviving/dropped targets, observed failures and unmet exact-route or
  different-model requirements. Useful same-model reviews do not complete oracle
  cross-model coverage.
- No survivor or no dispatch after a summons: solo POV plus "cross-model check
  unavailable or incomplete", attempted peers or that none ran, and observed reason.

Keep receipts in the panel record; default chat names target/requested model,
position/movement, failures, and material serving/independence caveats without a
diagnostic dump. With no summons keep the solo result unchanged and no panel note.
A valid skeptic critique is folded in once, disclosed as changed/unchanged, and
excluded from convergence. Never claim an unavailable optional oracle completed;
return accurate coverage to callers such as `ce-bakeoff`.

The panel never mutates. Handoff requires all four: original explicit downstream
authorization, non-stalemated result, inherited scope, and non-destructive otherwise
authorized action. Otherwise return the judgment; a calling workflow owns continuation.
After all workers stop and required disclosure/receipts have been consumed, remove
only verified run-owned payloads, round outputs, raw logs and results beneath the
private scratch root on success, failure, timeout or interruption. Never delete
outside that root or remove live-job state; report cleanup blockers. Peer reasoning
and project context must not outlive their use.
