# Cross-Model POV Panel

Obtain independent peer POVs, reconcile material disagreement, and return one
decision. Peers are cross-checks, never votes or substitutes for ce-pov's own
assessment. The panel is read-only and non-blocking: unavailable peers do not
prevent a grounded solo POV, but required cross-model coverage remains incomplete.

## 1. Participation and authority

A panel, cross-check, oracle, or request to consult named models is a summons,
including a calling workflow's request. Declining or merely mentioning a panel
is not. Resolve shorthand from the conversation; return missing context when
multiple subjects materially change the answer. An existing host or user position
can itself be the subject: ship it intact, withholding only fresh host judgment.

- Named peers are exact and uncapped; never silently replace or drop a name.
- Bare oracle selects up to two reachable, attestably different-model peers by
  conversation preference, configuration, project conventions, then
  `codex -> claude -> grok -> antigravity`.
- Explicit unnamed cross-check skips the correction-cost test. Zero reachable
  peers means solo plus an availability line; otherwise announce selections.
- Without a summons, offer only when downstream work precedes error detection or
  the take feeds shared/public/security/data commitments. Adoption Tier 1 and
  warm mid-session second opinions do not offer. A calling workflow receives
  the result without follow-up offers.

This skill explicitly requests native reviewer subagents for an authorized panel.
Under a user-OR-loaded-skill rule this satisfies delegation permission; no second
approval is needed. A genuine unconditional prohibition, missing tool, or actual
denial still applies. Never evade one through shell or another harness.

Delegation permission, model-selection permission, and remaining nesting depth
are separate checks. Inspect effective runtime depth; permission does not imply
capacity. If model overrides require an explicit user model request, omit the
optional `model` argument and use inherited-model reviewers only where suitable.
Separate same-model reviewers are not cross-model corroboration. If a required
different-model pass or fixed route cannot run, disclose incomplete coverage.

## 2. Identity, configuration, and native routes

Use `opencode.models` to discover exact available provider/model IDs and native
subagents to execute reviews. Use shell only for bounded local evidence and
artifact preparation, never another harness dispatcher. Read configured peer
choices and reasoning tiers from the project's configuration; they remain the
source of desired behavior, ahead of defaults. Preserve these default intents:

| Target | Model intent | Reasoning intent |
| --- | --- | --- |
| codex | gpt-6.1-sol | high |
| claude | claude-opus-5-5 | high |
| grok | grok-4.7 | xhigh |
| grok through Cursor | grok-4.7 | high/fast |
| composer | composer-2.5 | fast (ceiling exception) |
| cursor | configured default/Auto | configured |
| opencode | configured default/auto | configured |
| antigravity / Gemini | gemini-4-argon, then gemini-3.8-flash if unavailable | high |

Cursor and Composer are distinct requested targets, not aliases. Neither is
automatically selected unless configured as a preference. Grok's native and
Cursor-intermediated intents are distinct. The compatibility names above do not
authorize launching those CLIs: if native OpenCode cannot satisfy a requested
target/model/intermediary, report it unavailable rather than claiming equivalence.

Keep target, requested model, actual native route/provider/intermediaries, served
model receipt, and `independence_verified` separate in the panel record. Attest
the host harness and serving family from runtime evidence, not installed CLIs,
home directories, model self-claims, or inherited environment markers alone.
Served model is `unverified` without a runtime receipt. Independence is verified
only when served families attestably differ. An unknown host family excludes
automatic discovery candidates with unprovable independence; named peers may
still provide a useful explicitly unverified check.

Discover capabilities without exposing project content. Resolve and announce
one fixed native route per peer before dispatch; confirm every provider and
intermediary is an allowed recipient. An explicit user model is never swapped.
For an unavailable default, permit only an observed compatible same-target,
same-family, same-tier substitute, recording the evidence. New recipients require
approval; same authorized recipients do not. Respect separate external-consultation
approval policies. Announce who will inspect the subject read-only without
dumping CLI diagnostics, scratch paths, or promising a confidentiality sandbox.

## 3. Freeze scope and prepare independent context

Normalize one repository-relative read root plus ordered include/exclude patterns
and pass identical scope to every peer. Pass the actual absolute workspace root
separately. Prompt scope and read-only instructions are cooperative, not filesystem
or secrecy boundaries. Deny writes where native permissions support it and tell
peers not to mutate or deliberately inspect outside scope.

Before dispatch capture the committed revision plus a digest of dirty and
untracked content in scope. Use native JJ and local file hashing, including local
untracked files rather than assuming a clean revision identifies the tree. Run
JJ from the absolute target workspace root; never invoke Git directly. See
https://docs.jj-vcs.dev/latest/cli-reference/. For repository-scoped GitHub reads,
use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Outside JJ use
local project evidence and report history unavailable.

Revalidate identity before reconciliation and final fold-in. On change restart
all voices at the new identity or return an incomplete panel, never stale consensus.
Keep payloads, receipts, outputs and bounded logs under the resolved Phase 1
`SCRATCH_DIR` inside local `.tmp/`. Create private payloads with `umask 077`
and `chmod 600`; never use global temporary or fallback paths.

Prepare a complete canonical payload: framed question, subject shape, scope,
identity, mode, workspace source paths, and conversation-only material labeled
by provenance. Let peers inspect files rather than copying readable source or
adding a host-curated architecture summary. Require the same complete payload
to fit every peer; an undersized route is unavailable, not silently truncated.

Freeze ce-pov's own independent position before dispatch. Initial independent
peers receive no host conclusion, risk ranking, advocacy labels, or other peer
conclusions. Include source-located facts, the user's goal and strength of
preference, evidence they supplied, and the subject itself. State that rejecting
all options or the framing is valid. Present host-authored options symmetrically.
An already-formed position that is itself the subject ships intact; withhold only
fresh meta-judgment. Skeptic mode includes the host position because critique is
the task, but never enters independent convergence.

## 4. Native dispatch and bounded recovery

Dispatch one native subagent per selected peer with the canonical context,
`references/agents/pov-peer.md`, and `references/pov-schema.json`. Start independent
calls concurrently when supported, record native session/task IDs, and await
every started call using the native lifecycle. Keep the ordinary 600-second
peer budget, honoring a user-configured `CROSS_MODEL_HARD_SECS` larger budget;
do not shorten it to finish sooner. Use supported native deadlines/cancellation,
not detached shell supervisors. If native lifecycle cannot enforce a required
bound, disclose the limitation instead of pretending it did.

Require nonempty reasoning, a settled position with `final: true`, correct mode,
and a route/model receipt tuple. The coordinator attaches route, target, native
harness, requested model, actual served model (or `unverified`), serving family,
and independence fields from native runtime evidence; a peer's self-report is
not a serving receipt. Initial responses require `movement: initial`;
reconciliation requires `moved` or `held` with why. A settled blocked verdict is
usable; a non-final placeholder is not. Retry a non-final result once on the
same permitted route inside the existing budget, then drop it if still non-final.
Record actual failures from native errors: permission denial, missing tool,
model-argument rejection, depth/capacity exhaustion, timeout, quota, or provider
failure. Do not invent authentication diagnoses from generic network failures.

For a recoverable prelaunch argument or transient infrastructure failure, correct
once on the same allowed route within the aggregate deadline. Verify whether a
child actually launched before retrying. Never retry denied actions, bypass a
depth limit, widen scope, switch recipient silently, or expose withheld judgment.
An inherited-model fallback is allowed only when suitable under the review
contract; an unmet exact-model or cross-family requirement remains incomplete.
For an unavailable default model one same-family substitution may follow the
observed advertised models; explicit user models are never substituted.

## 5. Reconcile material dissent

Only independent voices enter convergence. Material dissent is a different grade,
selected approach, document action (proceed/revise-first/reject), or fatal-risk
assessment, not wording differences. Default limit: one independent initial
round plus at most two reconcile exchanges. User pass limits win; one pass means
no reconciliation. Initial material dissent requires at least one exchange unless
the user limited the run to one pass or the required native capability is absent
(disclose incomplete reconciliation in that case).

For each exchange:

1. Revalidate scope identity and reconsider every current position.
2. Verify only disputed decision-changing project claims as verified,
   contradicted, or unverifiable with source locations.
3. Send every survivor the identical complete evidence delta, original subject,
   and all surviving positions/reasons, capped at five succinct attributed
   evidence bullets per voice. Do not truncate differently by provider.
4. Dispatch fresh stateless native peers on the same fixed routes. A failed
   peer drops from later rounds; its older position is not current participation.

Stop at the first matching state: `confident` (reasoned host confidence),
`no-movement` (all survivors held and host is not confident), or `limit-reached`.
Confidence is not a vote. The latter two states are stalemate, not consensus.
At the cap recommend a specific bounded extension only with an unresolved
decision-changing question and new evidence likely to move it; otherwise recommend
stopping. Further rounds need approval unless already authorized by a larger limit.

## 6. Deliver, disclose, and clean up

Lead with the grounded POV and a compact panel note after any summons:

- Confident: state alignment or dissent and why ce-pov's conclusion prevailed.
  Attribute additions after the panel to the host, not peer agreement.
- Stalemate: state current positions, movement, dropped voices' last state,
  evidence gaps versus judgment differences, tradeoffs, and bounded next-round
  recommendation. Do not imply convergence.
- Partial: name survivors and dropped peers with actual observed failures and
  explicitly identify unmet required cross-model or reconciliation coverage.
- No survivor: solo POV plus “cross-model check unavailable or incomplete,”
  which peers were attempted (or none), and the observed reason.

Never attribute a position to a peer that did not run. Keep route/requested/served
model receipts in the record; chat names target and requested model, relevant
position/movement and failures, and any material receipt or independence caveat.
A requested model without a receipt is not a verified served model. A POV with
no summons has no panel note. Skeptic mode folds in one attributed critique and
discloses whether it changed the POV, without convergence.

The panel never mutates the project. Downstream handoff requires all four:
original prompt authorization for the named action, non-stalemated result,
inherited scope, and non-destructive otherwise-authorized action. A calling
workflow retains continuation ownership.

After all children settle or are stopped, remove only consumed payloads, logs,
outputs and results proven to belong beneath this run's private scratch root,
including failure/timeout paths. Never delete outside it or delete required
receipts before recording coverage. Retain a requested deliverable or blocker
evidence as required by the caller; do not remove a live child's files.
