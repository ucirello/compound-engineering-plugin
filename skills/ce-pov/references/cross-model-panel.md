# Cross-Model POV Panel

Obtain independent peer POVs, reconcile material disagreement, and return one
ce-pov decision. Peers are cross-checks, never substitutes or votes. The panel
is read-only and non-blocking: unavailable required coverage remains incomplete,
but does not prevent a solo POV or the ordinary blocked-on-missing-context result.

## 1. Resolve the subject, host, and participants

Resolve conversational shorthand against the active conversation. Return missing
context when competing subjects would materially change the judgment.

Keep target, actual route/provider/intermediaries, requested model, and served
model separate. Attest the host and served peer model from runtime evidence,
not installed CLIs, product names, environment markers copied by other harnesses,
or a model's self-report. A requested model is not a serving receipt. Record
`model_actual: unverified` without a receipt. Set `independence_verified: true`
only when the served peer family is attestably different from the host's.
Separate same-model reviewers are useful, but never cross-model corroboration.

A summons is an affirmative request to consult or reconcile peers, from the
user or caller's args. Negation or recounting a past panel is not a summons.
A caller's paraphrase never cancels a request still present in another readable
channel. Apply exactly one participation branch:

- **Named peers:** announce and attempt every exact named target, uncapped.
  Names override oracle discovery. Never silently replace an explicit model.
- **Bare oracle:** select up to two reachable, attestably different-model peers
  using conversation preferences, local configuration, project conventions,
  then `codex -> claude -> grok -> antigravity`. Unknown host family cannot
  establish independence and is not grounds to guess.
- **Explicit unnamed cross-check:** apply that selection/count rule without a
  correction-cost check. Zero reachable means solo plus availability disclosure.
- **No cross-check request:** after forming a POV, offer only when meaningful
  downstream work precedes error detection or a shared/public/security/data
  commitment depends on it. Adoption Tier 1 and warm invocations never offer.

Preserve configured target/model/tier choices as intent. `Cursor` means its
configured default/Auto choice, not Composer; `Composer` means a Composer model
through Cursor. Grok native and Grok through Cursor are different routes and
recipients; Antigravity denotes its Gemini route. These compatibility identities
are not instructions to launch those harnesses. Cursor and Composer are only
automatically selected when configured as a preference. A native route unable
to honor a named harness/intermediary is unavailable, not an equivalent pass.

**Prior-opinion subject:** an already-formed host or user position is the subject
artifact and ships intact; peers still form independent verdicts. Only fresh
host meta-judgment after the summons is withheld in round one. Skeptic mode is
different: it critiques a supplied POV and never enters convergence.

## 2. Normalize scope and freeze repository identity

Resolve the absolute target workspace root and optional ordered repository-
relative read root/include/exclude patterns once. Pass identical scope to all
peers. Never broaden inherited restrictions. Peers inspect existing files in
the shared tree directly; inline only otherwise unavailable conversation material.
Prompt-only restrictions, cwd, and read-only requests are cooperative controls,
not a confidentiality boundary or proof of a write sandbox. Require no edits,
mutating commands, or intentional reads outside scope; use native tool controls
where supported and disclose any material enforcement limitation.

Capture repository-scope identity before dispatch: exact JJ commit identity plus
a deterministic digest of current scoped tracked, ignored, and untracked content
(including paths and missing/deleted entries). Exclude only this run's owned
scratch outputs so peer artifacts do not invalidate themselves. Use native JJ
facts and local file processing, never direct Git. Every JJ command runs with
cwd set to the verified target workspace's absolute root, not merely `jj -R`.
See https://docs.jj-vcs.dev/latest/cli-reference/ and
https://docs.jj-vcs.dev/latest/git-command-table/.
Revalidate before each reconciliation and final fold-in; on change restart all
voices on the new identity or return incomplete, never fold stale results.

Use the Phase 1 private scratch directory beneath local `.tmp/`; no global temp
or cache fallback. Create payloads with umask 077 and chmod 600. Preserve one
complete canonical payload for every route; oversized routes are unavailable,
never fed individually truncated evidence.

## 3. Resolve and announce one fixed native route

Read applicable `.rocketclaw/config.yaml` and `config.local.yaml` model/peer
settings with their documented layering (local overrides shared); explicit user
choices win. The SKILL.md `docs_root` setting remains shared-only. Configuration
choices and reasoning tiers remain authoritative desired behavior, not authority
to violate permissions or silently substitute a target.

Discover available IDs with `opencode.models`, without project content. Resolve
each requested target to an available native provider/model/variant and record
all recipients. Try its declared preferred mapping first. An observed obsolete
or unavailable default may receive one closest same-target, same-family,
same-reasoning-tier equivalent, recorded with the observed reason. Never swap an
explicit user model. A fixed route that cannot be honored remains incomplete.
Discovery is not proof of authentication or successful service; classify actual
dispatch diagnostics, not binary presence or generic terminal text.

Separate three constraints before launch:

1. **Delegation permission:** these reviewer instructions explicitly request
   native subagents. Under a user-or-loaded-skill policy this qualifies without
   another user approval. A genuine higher-priority prohibition, missing tool,
   or actual denial still applies.
2. **Model permission:** where overrides require an explicit user model request,
   omit the optional native `model` argument otherwise. Suitable inherited-model
   reviewers may run, preserving configured intent in the record, but cannot
   satisfy a required different-model or fixed-route pass. Disclose that coverage
   as incomplete; never relabel it independent.
3. **Depth/capacity:** inspect effective OpenCode configuration with supported
   `opencode debug config` and classify actual launch errors. Do not confuse
   exhaustion with policy denial or model-argument rejection. Permission and a
   configured depth do not prove remaining runtime capacity.

Announce who will inspect this project and that the consultation is read-only.
Ask only for an unexpected new recipient/intermediary or a separately required
approval; ordinary explicit panel requests authorize normal consultation subject
to host policy. Never bypass denial, depth, or model restrictions through shell
or another harness. Shell is for permitted local payload, evidence, and receipt
processing, not a replacement dispatcher.

## 4. Dispatch, wait, collect

Use native subagents seeded with `references/agents/pov-peer.md` and the schema
in `references/pov-schema.json`. Use a discovered generic agent whose own role
does not replace this brief. Launch all independent peers concurrently where
capacity allows and await every result through native lifecycle controls. Record
native job/session IDs; stop outstanding workers before scratch cleanup.

The complete canonical payload contains framed question, subject shape, scope,
identity, mode, subject paths, required conversation-only material, and the
user's decision-relevant goal, strength of preference, and supporting evidence.
Rejecting every option or the framing is valid. For initial independent rounds,
withhold host conclusions, advocacy, rankings, evaluative labels, and other
voices' conclusions. Source-located facts and user needs may ship. Present
host-authored options symmetrically while retaining access to the whole subject.
An already-formed position supplied as the subject ships intact, but fresh host
meta-judgment waits for reconciliation. Skeptic payloads include the POV.

Use the user-configured `CROSS_MODEL_HARD_SECS` deadline, default 600 seconds;
never shorten it just to finish sooner. Keep one aggregate deadline across
recovery; grant supported lifecycle termination a 10-second grace and stop
timed-out workers through native cancellation. If the native tool cannot enforce
the required deadline or cancellation, report that capability limitation rather
than claiming bounded completion. Retain private per-peer result/log paths and
structured terminal diagnostics until collection; do not guess causes from text.

Accept only schema-shaped objects with nonempty settled position/reasoning,
valid mode/movement, evidence, and `final: true`. A settled Blocked answer counts.
Initial movement is `initial`; reconciliation is `moved` or `held` with a reason.
Retry a non-final response once on the same fixed route inside the deadline with
the final-answer requirement, then drop it as `non-final position`. A completed
job alone is not a usable result. Attach runtime-supported target, route,
requested/served model, serving family, and independence receipts separately;
never turn the peer's own claim into backend attestation.

On prelaunch invalid argument, verify nothing launched and correct once; omit
a forbidden model argument. On actual permission denial or exhausted depth,
do not retry or evade it. On a model refusal, a non-user-selected default can
receive the single same-family/tier substitution allowed in Section 3. For other
infrastructure failures, retry the identical route only while each failure is
new and plausibly recoverable and the aggregate deadline remains; stop on a
repeated failure. Never widen scope, add recipients, or leak withheld positions
in recovery. A route that ran but yielded no usable artifact is dropped.
Report authentication/quota/timeout only when observed diagnostics establish it;
without provider-capable execution, do not assert the user's account is logged
out. Missing tool, policy denial, model-argument rejection, and depth/capacity
remain separate classifications. Inline or parent-coordinator work may produce
a solo POV, never satisfy missing independent peer coverage.

## 5. Detect dissent, verify claims, reconcile

Only independent voices enter convergence. Material dissent means different
adoption grades, selected approaches, or document actions (proceed/revise-first/
reject), or disagreement about whether a risk is fatal; emphasis alone is not.

The default is one independent initial round plus at most two reconciliation
exchanges. User pass limits replace it: one pass means no reconciliation. After
initial material dissent run at least one exchange unless that user limit bars
it; deciding over an unheard dissenter is not reasoned convergence.

For each exchange:
1. Revalidate identity; restart or return incomplete on change.
2. Reconsider every surviving position and evidence.
3. Verify only decision-relevant disputed project claims in scope, classifying
   each verified, contradicted, or unverifiable with source locations.
4. Send the identical common evidence delta and full original subject to every
   survivor, plus every survivor's current position/reasoning and at most five
   succinct source-attributed evidence bullets per voice.
5. Re-resolve fixed native routes and dispatch fresh stateless peers. Same
   recipients need no new question. Failed peers are dropped; older positions
   never masquerade as participation in later rounds.

Stop at the first matching state: `confident` (reasoned host confidence after
weighing survivors), `no-movement` (every survivor held and host not confident),
or `limit-reached` (finite authorized cap reached without confidence).
Convergence is not a vote; a split can yield a reasoned decision or stalemate.
At a cap recommend a specific finite extension only when naming the unresolved
question, new evidence/framing, and why it could move a position. Otherwise
recommend stopping. Further rounds need approval unless authorized in advance.

## 6. Decide and disclose

Lead with the POV in the subject's shape, followed by a compact panel note:
- **Confident:** say whether voices aligned, identify overridden dissent and
  why, and distinguish host-added recommendations from what peers judged.
  Concurrence does not eliminate correlated-model blind spots.
- **Stalemate:** give host/survivor positions and movement, dropped voices' last
  state, evidence-gap versus judgment difference, and real tradeoffs. Say
  "Either is viable" when warranted. At a cap include the bounded extension or
  reason to stop.
- **Partial:** name survivors and dropped targets and observed failure states,
  plus unmet fixed-route or cross-model requirements. Useful inherited-model
  work is not completed different-model coverage.
- **No survivor:** deliver solo with "cross-model check unavailable or
  incomplete." After any summons state who ran, or that none ran and why,
  even if the branch never entered. Without a summons add no panel note.

Keep full target/route/request/served/independence receipts in the private record;
default chat names targets/requested models, positions, movement, failures, and
only decision-relevant serving/independence caveats. Never attribute a position
to a model that did not run. Skeptic critique folds in once, never convergence;
disclose whether it changed the POV. A failed skeptic degrades likewise.

The panel never mutates. Downstream handoff requires all four SKILL.md Phase 4
conditions: original request explicitly authorized the named action, result is
non-stalemated, action remains in inherited scope, and action is non-destructive
and otherwise authorized. A caller retains continuation ownership.

## 7. Cleanup

After all workers stop, remove only this run's owned consumed payloads, raw logs,
round outputs, and results on success, failure, interruption, and timeout. Never
delete outside its private scratch root or retain project context beyond use.
Deliver a requested report before retiring its scratch output; preserve any
artifact the user still needs rather than claiming cleanup while deleting it.
