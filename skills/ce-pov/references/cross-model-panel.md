# Peer POV Panel

Obtain independent read-only peer judgments, reconcile material disagreement,
and return one ce-pov decision. Peers are cross-checks, not votes. A panel never
authorizes implementation or mutation.

## Participation and native routing

A summons is an affirmative user or calling-skill request for peers, a panel,
cross-check, or `oracle`, anywhere in the readable invocation. A decline or a
historical mention is not a summons. A warm invocation never proactively offers
a panel. Otherwise offer only where consequential downstream work relies on the
judgment (adoption Tier 2/3, not Tier 1).

This loaded skill's explicit requests for scouts and reviewers satisfy the
user-OR-loaded-skill delegation permission exception: do not ask for redundant
approval. Respect higher prohibitions and actual tool denials; never evade them
through another harness or shell. Delegation permission is not model-override
permission. If the host requires an explicit user model request, omit the
optional model argument without one. Use suitable inherited reviewers, keep
configured tiers as intent, and disclose requested routes that were not met.

Resolve model availability using native `opencode.models`, existing role/model
configuration, and the host's native subagent capability. Shell is for permitted
read-only evidence and native lifecycle operations, not another-harness
dispatchers or model elevation. Do not install or launch other agent CLIs.
Named peers/models are exact and uncapped; report unavailable named routes, never
silently substitute them. Bare oracle selects up to two reachable, attestably
different model families, honoring conversation preferences and configuration.
An explicit unnamed cross-check selects the available suitable reviewers.
If different-model routing is unavailable, distinct inherited reviewers remain
useful but are not cross-model corroboration; disclose the unmet route.

Record separately for each voice: target, native route/provider, requested model
(or inherited), served model from an actual receipt (otherwise `unverified`),
and independence. Attest the host from runtime serving evidence, never product
names, home directories, or a model's self-report. Only a verified different
served model family supports cross-model independence. Separate same-model
reviewers are distinct voices, not different-model independence.

Announce selected peers and read-only consultation before dispatch. Existing
consultation authority needs no second approval; unexpected recipients or
intermediaries need approval, as do genuine higher-level consultation gates.

## Scope and canonical payload

Freeze the absolute workspace root and ordered include/exclude patterns. All
peers receive the identical normalized scope; never broaden a narrower inherited
scope. Prompt restrictions are cooperative, not a confidentiality sandbox.
Require no writes and no intentional out-of-scope inspection. Do not promise
secrets inside the readable scope are inaccessible.

Capture repository identity using the exact committed JJ revision and a digest
of tracked dirty and untracked content within scope. Use native file reads and
JJ commands with cwd at the absolute workspace root, never direct Git or `jj -R`.
Revalidate before reconciliation and final fold-in; changes require restarting
all voices or reporting incomplete coverage, never folding stale results.
Repository-scoped `gh` reads require `GIT_DIR=$(jj git root)` in that workspace.

Use Phase 1's private workspace-local `.tmp` run directory for mode-600 payloads,
logs and results. Send the framed question, subject shape, scope, identity, mode,
subject file paths, and required conversation-only material. Peers inspect shared
files directly: do not copy readable files or add a curated architecture summary.
Use `references/agents/pov-peer.md` and `references/pov-schema.json` as the brief
and response contract.

Initial independent peers see neither ce-pov's new position nor another voice's
conclusion. Withhold host advocacy, risk rankings and evaluative labels; include
source-located facts and the user's goals and supporting evidence. Rejecting all
options or the framing is valid. Present host-authored options symmetrically.
If an already-formed opinion is itself the subject, send that opinion intact;
withhold only fresh meta-judgment after the summons. Skeptic mode deliberately
includes ce-pov's position and does not enter convergence. All selected peers
must receive the complete same payload: an oversized route is unavailable, not
an excuse for route-specific truncation.

## Native lifecycle and failure handling

Start independent native subagents before waiting where capacity permits. Keep
native task/session IDs, bounded status and terminal receipts. Default per-peer
deadline is 600 seconds, unless the user configured a larger finite budget;
preserve it through retries and allow a short terminal-collection grace period.
Never shorten it merely to finish sooner. Stop/cancel only owned live tasks on
deadline or interruption; collect completed results as they arrive.

Classify actual launch errors separately: malformed arguments before launch may
be corrected once; capacity may be queued within the deadline; effective nesting
depth exhaustion is not a permission denial. A policy/tool denial is not a depth
error. Do not claim a peer ran when no task launched. For recoverable native
infrastructure errors, retry the same authorized route while errors are new and
plausibly recoverable and the aggregate deadline remains; stop on repeated
failure or deadline. Never bypass denial or change recipients/model/scope.
An allowed inline grounding fallback is not an independent reviewer. Report
mandatory independent or different-model coverage as incomplete when unmet.

Accept only schema-shaped results with a settled position, nonempty reasoning,
valid mode/movement and `final: true`. A settled Blocked verdict is usable.
Retry a non-final placeholder once on the same route within the original budget;
if repeated or out of time, drop it and record non-final position. Initial
movement is `initial`; reconciliation requires `moved` or `held` with reasons.
Record route/model receipts separately; never infer served model from requested
model. Report observed timeout, quota, authentication or other diagnostics, not
guessed causes. Authentication-looking text without provider-capable execution
proof does not establish that the user's account is logged out.

## Reconciliation

Only independent voices enter convergence. Material dissent is a different
adoption grade, selected approach, document reader action, or fatal-risk judgment;
wording and emphasis differences alone are concurrence. Default limit is the
initial round plus two reconciliation exchanges. Honor a user's finite limit;
one pass means no reconciliation.

For each exchange, revalidate identity, reconsider every surviving position,
verify disputed decision-relevant project claims as verified/contradicted/
unverifiable with sources, then send every survivor the identical complete
evidence delta, full original subject, and every survivor's current reasoning
(up to five succinct attributed evidence bullets per voice). Re-resolve native
routes and use fresh stateless reviewers. Failed peers are dropped; their older
positions do not count as participation in later rounds. Initial material
dissent requires at least one exchange unless the user allowed only one pass.

Stop on `confident` (reasoned confidence, not a vote), `no-movement` (all
survivors held and ce-pov remains unconfident), or `limit-reached`. The latter two
are stalemates, not settled consensus. At a cap recommend a specific bounded
extension only with an unresolved question, new evidence/framing and a reason it
could move a position; otherwise recommend stopping. Further rounds require
approval unless already authorized within a larger finite cap.

## Delivery and cleanup

Lead with the POV, then a compact panel note:

- Confident: state alignment or explain the dissent and why the decision won.
  Claim agreement only on what peers judged; label later additions as your own.
- Stalemate: give current positions/movement, dropped voices' last states, and
  whether the gap is evidence or judgment. Say "Either is viable" when warranted;
  at a cap include the bounded-extension recommendation or reason to stop.
- Partial: name surviving/dropped targets and observed failures. Distinguish
  useful inherited-model voices from unmet cross-model coverage.
- No survivor: deliver the solo POV with "cross-model check unavailable or
  incomplete," naming attempts or why none ran. Never ship a bare solo verdict
  after a summons. Without a summons no panel note is required.

Keep detailed receipts in the panel record, not default chat diagnostics. Never
attribute an opinion to a model that did not run. A skeptic folds in once with
disclosure of whether the critique changed the POV, without entering convergence.
Clean only owned run-local payloads/logs/results after consumption, including on
failure, timeout and interruption; stop live tasks first and never delete outside
the verified private run root. A calling workflow retains continuation ownership.
Standalone handoff requires explicit original authorization, a non-stalemated
result, inherited scope and a non-destructive otherwise-authorized action.
