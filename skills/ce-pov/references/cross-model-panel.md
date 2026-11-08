# Cross-Model POV Panel

Obtain independent peer POVs, reconcile material disagreement, and return one
ce-pov decision. Peers are cross-checks, never votes or substitutes for the host.
The panel is read-only and non-blocking; missing coverage never becomes proof.

## 1. Resolve the subject, host, and participants

Resolve conversational shorthand to the single unambiguous subject. Return
missing context when competing subjects would materially change the decision.
Keep target, actual route/provider/intermediary, requested model, and served model
separate. Use runtime serving evidence, not an installed CLI, requested model,
model self-report, or product name, to attest the host and peer model families.
Record `independence_verified: true` only for an attestably different served
family. Otherwise retain a useful separate review but never call it cross-model
corroboration. A missing receipt means served model `unverified`.

A summons is an affirmative panel, cross-check, named-peer, or `oracle` request
anywhere in the invocation context. A refusal or historical mention is not one;
a caller's paraphrase cannot cancel a request still present in another channel.
Apply one participation branch:

- **Named peers:** run every exact requested target, with no automatic cap.
  Never silently replace an explicit model or map Cursor default/Auto to Composer.
- **Bare oracle:** choose up to two reachable, attestably different-model peers,
  using conversation preference, local configuration, active conventions, then
  `codex -> claude -> grok -> antigravity` as selection intent.
- **Unnamed explicit cross-check:** use available independent peers under those
  preferences; zero reachable means solo plus an availability line.
- **No summons:** offer only where meaningful downstream work precedes error
  detection or a shared/public/security/data commitment depends on the take.
  Adoption Tier 1 and warm invocations never receive proactive offers.

Configured targets and tiers remain intent, not authority to invoke another
harness. Cursor, Composer, Grok-through-Cursor, and Antigravity are distinct
recipient/route choices, not aliases for an arbitrary provider model. If a fixed
route cannot be honored natively, disclose it as unavailable rather than silently
substituting. A prior formed position being judged ships intact as the subject;
withhold only fresh host meta-judgment about it.

## 2. Scope, identity, and private scratch

Normalize one repository-relative read root and ordered include/exclude patterns.
Pass identical scope to every peer. The default is the repository root; never
broaden a narrower scope. Peers inspect subject files directly; inline only
conversation-only material. Prompt restrictions and a working directory are
cooperative, not filesystem isolation or a promise that secrets are inaccessible.
Require no edits or mutating commands, and use real read-only controls where
available without claiming a sandbox they do not provide.

From the target workspace's absolute root, capture the exact JJ revision and a
digest of tracked, dirty, ignored and untracked readable content inside scope,
including paths, bytes, types and executable modes. Use native JJ facts and local
file processing, never direct Git. Revalidate before every reconciliation and
final fold-in. If identity changes, restart every voice or return incomplete;
never fold stale judgments into changed content. See
https://docs.jj-vcs.dev/latest/cli-reference/ for native JJ operations.

Use only the Phase 1 absolute local `.tmp/` scratch directory. Payloads, raw
output, logs and results stay there. Create directories under umask 077 and
payloads with mode 600; verify ownership and reject symlinks. Repository-scoped
GitHub commands run as `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`.

## 3. Native routing and permission gates

This skill explicitly requests native reviewer subagents. Under a user-OR-loaded-
skill delegation rule, these instructions satisfy the skill exception; no second
user approval is needed. An unconditional higher-priority prohibition, missing
tool or actual permission denial still controls. Never bypass it via shell,
another harness, or repeated denied calls.

Discover models through `opencode.models` without sending project content.
Resolve configured choices/tiers against the catalog and allowed recipients.
Delegation permission is not model-override permission: when a host requires an
explicit user model request, omit the optional subagent `model` argument unless
that request exists. Use inherited-model reviewers where adequate, retaining
configured tier intent and disclosing unmet requirements. Same-model reviewers
are separate voices but do not satisfy a required different-model pass.

Verify effective nesting capacity separately through the supported OpenCode
configuration interface; permission does not imply remaining depth. Classify
actual failures as permission denial, model-argument rejection, missing tool,
depth/capacity, authentication, quota, timeout, or other observed failure. Do not
guess from a generic failure. Never evade depth limits with another harness.

Bind a concrete permitted native route, provider, intermediary and model before
dispatch. Announce who will read this project and that review is read-only, not
internal diagnostics or scratch paths. A new recipient/intermediary needs approval
unless already authorized. An explicit user model is never swapped. A configured
default that is actually unavailable may use a permitted closest same-family,
same-tier equivalent only if the fixed-route contract allows it; record the fact.
Otherwise mark coverage incomplete. No active multi-harness dispatch is allowed.

## 4. Dispatch, wait, and collect

Build one complete canonical payload: framed question, subject shape, normalized
scope, repository identity, mode, subject file paths, required conversation-only
material with provenance, and `references/agents/pov-peer.md` plus
`references/pov-schema.json`. Rejecting all supplied options or the framing is
valid. Include user goals and their strength, but no host-curated architecture
summary or unsupported premises.

For initial `independent` peers, freeze and withhold the host's conclusion and all
other voices' conclusions. Include source-located facts and the subject itself;
withhold host risk rankings, advocacy and evaluative labels. Present host-authored
options symmetrically. A prior-opinion subject retains its original advocacy as
the subject, not as a new briefing. `skeptic` mode includes the position to critique.

Start independent native subagents concurrently where capacity permits and await
all results. Use fresh stateless subagents for reconciliation. Never truncate the
payload per peer; a route unable to accept it is unavailable. Record native task
IDs and terminal states; use native await/cancel facilities and shell only for
local mechanical payload/result processing, not a dispatch bridge. Preserve the
600-second default peer budget and any larger authorized `CROSS_MODEL_HARD_SECS`
budget; never shorten it to finish sooner. Bound waiting by the last start plus
that budget and a ten-second grace, and cancel only this run's unfinished tasks.
If native lifecycle controls cannot enforce the contract, disclose the limitation.

Accept only schema-shaped settled results with nonempty reasoning, a valid
movement, `final: true`, and independently recorded route/model receipts. Initial
movement is `initial`; reconcile movement is `moved` or `held` with explanation.
A settled Blocked answer is valid. Retry a non-final placeholder once on the
same permitted route within the remaining budget; then drop it as non-final.
Never invent serving evidence from a peer's own claims.

Use actual bounded diagnostics for failed tasks. Authentication-shaped text is
not proof the user's account is logged out without provider-capable execution
evidence. Report which peers started, returned, timed out or never launched.
A genuine argument error before launch may be corrected once if permitted;
never retry a denied operation. A required route or different-model pass that
cannot start remains incomplete. Inline host judgment cannot replace independent
peer coverage. A parent coordinator may perform a pass only where authorized and
the same scope, independence, recipient and fixed-route contract can be preserved.

## 5. Reconcile material dissent

Only independent voices enter convergence. Dissent is a different grade, selected
approach, document reader action, or fatal-risk judgment, not mere emphasis.
Default: initial round plus at most two reconciliation exchanges. A user's finite
limit overrides this, including one pass meaning no reconciliation.

For each exchange:
1. Revalidate identity and reconsider every surviving position.
2. Verify only disputed decision-relevant project claims against allowed scope;
   label them verified, contradicted or unverifiable with source locations.
3. Send every survivor the identical complete common evidence delta, full subject,
   and all current positions/reasoning, with at most five source-attributed
   evidence bullets per voice. Revalidate native routes and permission gates.
4. Dispatch fresh stateless peers. Drop failed voices from later rounds; never
   reuse an old position as though it participated in a new exchange.

Initial material dissent requires at least one exchange unless the user's limit
forbids it or capability failure prevents it; disclose incomplete reconciliation
in that case. Stop after fold-in at `confident` (reasoned host confidence),
`no-movement` (all survivors held but host is not confident), or `limit-reached`.
Convergence is not a vote. The latter two mean stalemate, not settled consensus.
At a cap, recommend a specific finite extension only if a named unresolved
question and new evidence/framing could move a position. Otherwise recommend
stopping. More rounds require approval unless already authorized.

## 6. Decide and disclose

Lead with the subject-shaped POV, followed by a compact panel note:
- **Confident:** alignment or the dissent and why the host's decision prevailed;
  concurrence does not eliminate correlated-model blind spots. Attribute any
  post-panel recommendation to the host, not peers who never judged it.
- **Stalemate:** current host and surviving positions/movement, dropped voices'
  last states, evidence gaps versus judgment differences, material tradeoffs and
  an honest recommendation or “Either is viable.” At a cap include further-round
  advice grounded in a concrete evidence path.
- **Partial:** surviving/dropped targets and observed failures, plus every unmet
  route, independence, depth or review requirement. Never label incomplete
  coverage fully verified.
- **No survivor:** solo POV plus “cross-model check unavailable or incomplete,”
  naming attempted peers or why none ran. Every summons receives panel status;
  no summons means no panel note.

Retain target, native route/provider/intermediary, requested/served models and
independence receipts in the record. In chat name the target/requested model,
position and movement, with material failure or independence caveats. Never
attribute a position to a model that did not run.

## 7. Skeptic mode, degradation and cleanup

A skeptic critiques the supplied position once, reports whether it changed the
host's POV, and does not enter convergence. Failure drops that voice, not the
ordinary grounded POV. Never silently weaken the grounding gate in method.md.
Recover only a new plausibly recoverable native infrastructure fault within the
aggregate deadline, keeping route, model, scope and independence fixed. Stop on
repeated failure; denials and depth failures never authorize a hand-dispatch bypass.

Stop/cancel this run's workers before deleting consumed payloads, raw logs and
results, on success, failure, timeout or interruption. Verify exact run ownership
and containment; never delete outside private scratch or unrelated files.
Peer reasoning and project context must not outlive their use.

The panel never mutates the project. After delivery, continuation requires all
four conditions: original explicit authorization, a non-stalemated result,
inherited scope, and non-destructive otherwise-authorized action. Otherwise
return judgment only; a calling workflow retains continuation ownership.
