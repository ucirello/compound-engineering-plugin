# Cross-Model POV Panel

Obtain independent peer POVs and reconcile material disagreement. ce-pov remains
the decision-maker, not a vote counter. The panel is read-only and non-blocking:
return a panel POV, a solo POV with an availability/coverage note, or the ordinary
blocked-on-missing-context result. Dispatch through OpenCode-native subagents;
do not invoke another harness's CLI or a detached dispatch bridge.

## 1. Resolve subject, host, and participants

Resolve conversational shorthand from the single unambiguous subject in context.
Return missing context rather than inventing a question. Keep target, native
route/provider/intermediary, requested model, and served model separate. The
request is known; the served model requires a runtime receipt and otherwise is
`unverified`. Attest the host from runtime serving evidence, never installed
CLIs, home directories, or harness brand. `independence_verified: true` requires
an attestably different served model family from the host. Same-model separate
reviewers are useful independent readers, not cross-model independence.

Apply one participation branch:

- **Named peers:** announce and attempt every exact named target, uncapped.
  Names override automatic discovery. Never silently replace an explicit model.
- **Bare oracle:** select up to two reachable, attestably different-model peers
  by conversation preference, local configuration, project conventions, then
  the default order codex, claude, grok, composer. If host family is unknown,
  do not guess independence for automatic selection.
- **Explicit unnamed cross-check:** skip the correction-cost check; select
  reachable different-model peers with the same count rule and announce them.
- **No cross-check request:** form the solo POV first. Offer a panel only when
  consequential downstream work would hide an error, or the take feeds a shared,
  public, security, or data commitment. Adoption Tier 1 is ineligible; Tier 2/3
  are eligible. Warm invocations and returns to calling workflows never offer.

Zero reachable peers means solo plus an availability line after a summons.
One or more selected peers means one concise read-only progress announcement.
Cursor and Composer are distinct compatibility targets: Cursor means configured
default/Auto with serving family unverified absent a receipt; Composer means a
Composer model, not an alias for Cursor. Grok through Cursor adds an intermediary
and is not the native Grok route. These are identity semantics, not instructions
to execute Cursor/Grok CLIs; a required harness-specific route unavailable
natively remains incomplete. A configured or explicitly named default/Auto peer
may run without verified independence, with that limitation disclosed.

An already-formed host or user position can itself be the subject. Ship it intact
and let peers form their own verdict; only fresh host meta-judgment after the
summons is withheld. This is independent mode, not skeptic mode.

## 2. Freeze scope and repository identity

Resolve the absolute `$workspace_root` and normalize one repository-relative
read root plus ordered include/exclude patterns. Pass identical scope to every
peer. Narrow caller/user scope is binding; never broaden it. Peers inspect shared
files directly; inline only conversation-only or otherwise unavailable material.
Prompt scope and a working directory are cooperative controls, not a security
boundary. Never promise inaccessible secrets or misrepresent native tool access.
Peers cannot mutate or intentionally read outside scope.

Capture the current committed revision and a digest of dirty and untracked
content within scope. Use native JJ from the absolute root, for example
`(cd "$workspace_root" && jj log -r @ --no-graph)` and
`(cd "$workspace_root" && jj diff --summary)`, plus bounded file reads to digest
actual scoped content, including untracked files. Do not treat a diff summary
alone as a content digest. Include the identity in every payload; revalidate
before reconciliation and final fold-in. Changed identity requires restarting
all voices or returning incomplete, never folding stale results into new state.
Returned source paths remain repository-relative; do not use `jj -R`.
See https://docs.jj-vcs.dev/latest/git-experts/ and
https://docs.jj-vcs.dev/latest/cli-reference/.

Use the Phase 1 absolute scratch directory under project-local `.tmp/rocketclaw`.
No global temporary fallback. Check ownership, symlinks, and containment before
creating or reading run artifacts. Create private directories (0700 or the
platform's equivalent owner-private ACL) and payload/result/log files (0600 or
equivalent), with exclusive creation and atomic publication. Never overwrite
another run's files. Keep the scope and canonical payload digest in each receipt.

## 3. Resolve fixed native routes and authority

Read configured peer choices and reasoning tiers from `.rocketclaw/config.yaml`
and applicable local overrides. Discover exact available provider/model IDs and
variants with `opencode.models` before dispatch; discovery supplies no project
content to candidate providers. Preserve configured choices as authoritative
intent. The former defaults are codex `gpt-6.1-sol` high, claude
`claude-opus-5-5` high, native grok `grok-4.7` xhigh, Grok through Cursor
`grok-4.7-xhigh`, Composer `composer-2.5-fast` at its ceiling, and Cursor/OpenCode
default/Auto. These are tier/compatibility intent, not mandatory stale IDs.
If a default is observed obsolete/unavailable, resolve only a compatible model
within the same target, family, and reasoning tier and record the evidence.
An explicit user model cannot silently become another model.

Resolve one fixed native route including every provider and intermediary;
confirm allowed recipients. Announce which peers will inspect this project
read-only, without dumping paths, hashes, tiers, or diagnostics. A summons is
normal consultation authority, but unexpected recipients/intermediaries or an
active separate external-consultation gate require approval before dispatch.
Do not preflight account authentication from binary presence or generic errors;
the native provider attempt and runtime diagnostics establish usability.

**Three independent gates apply:**

1. This skill explicitly requests peer reviewers. Under a host user-OR-loaded-
   skill delegation exception that satisfies permission, with no second ask or
   false user-not-requested refusal. An unconditional prohibition, actual denial,
   or missing native tool remains binding; never bypass it via shell/another
   harness.
2. Model override permission is separate. If an optional native `model` argument
   requires an explicit user model request, configured tiers do not grant it.
   Use suitable inherited-model reviewers where allowed; record unmet fixed
   route/tier intent. A required different-model pass then remains incomplete,
   not fully verified, even if same-model separate reviewers agree.
3. Discover effective nesting configuration and precedence for the absolute
   project location as described in `grounding.md` and
   https://opencode.ai/v2/docs/config. Package defaults are not automatically
   consumer settings, and configured depth does not prove remaining capacity.
   Use actual launch errors to distinguish depth/capacity, permission,
   model-argument rejection, missing tool, and recoverable invalid arguments.
   Do not mutate configuration, retry denials, or evade nesting limits.

If a fixed route cannot be satisfied, report its coverage incomplete. An allowed
parent-coordinator dispatch may preserve independent coverage only if it obeys
the same permissions, payload, scope, tier, and finite limits; never use it to
evade a prohibition or depth limit. Solo inline judgment is an allowed degraded
result, not a completed independent peer pass.

## 4. Dispatch, wait, cancel, and collect

Build one complete canonical payload: framed question, subject shape, normalized
scope, repository identity, mode, subject file paths, and necessary conversation-
only material. Seed each native subagent with `agents/pov-peer.md` and
`pov-schema.json`. Do not add a host-curated architecture summary or duplicate
readable files. Every route must accept the identical complete payload; an
oversized route is unavailable, never given a truncated version.

In the initial independent round, withhold host and other voices' conclusions,
advocacy, risk rankings, and evaluative labels. Include source-located facts and
the user's decision-relevant needs, including intensity; label conversation-only
material. The subject proposal remains readable. Present host-authored options
symmetrically in the payload; rejection of all options or the framing is valid.
An already-formed position supplied as the subject retains its own premises;
only newly formed host meta-judgment is withheld. Skeptic mode deliberately
receives the host position; reconciliation receives already-formed views.

Start every allowed peer before waiting, using concurrent native calls where
available; record native task/session IDs, target, route, requested model/tier,
payload digest, scope, and start time. Use native lifecycle tools to wait and
cancel owned tasks, not detached shell processes. Default worker hard window is
600 seconds; honor an explicit `CROSS_MODEL_HARD_SECS` budget, preserving any
route-specific lower non-streaming bound. The aggregate collection deadline is
the worker hard window plus 10 seconds after the final launch. Poll in bounded
slices of at most 30 seconds without crossing the deadline, until all terminal
or time spent. Do not mistake one short wait for completion. If supervision is
separate, its cap must be at least `max(1230, worker hard window + 30)` rather
than undercut a healthy worker. Cancel each owned nonterminal task at deadline
and perform a final bounded collection. Do not claim cancellation succeeded
without confirmation; disclose lifecycle limitations and preserve remaining
owned state for safe recovery. Observe idle/liveness diagnostics where native
tools provide them (former idle default 240 seconds), never infer a hung task
from absent streaming on a buffered route.

Classify tasks as running, done, failed, timeout, died-without-result,
never-started, or unreadable from actual native evidence. Completion alone is
not a usable result. Read only ownership-checked artifacts, bounded to 5 MiB
for results and 10 MiB for logs; keep diagnostic excerpts small. Accept only
schema-shaped JSON with nonempty reasoning, a settled position, `final: true`,
and valid movement. Initial movement is `initial`; reconciliation is `moved`
or `held` with an explanation. A settled Blocked verdict is usable. Retry one
non-final placeholder on the same permitted route within the original hard
window with a final-answer requirement; otherwise drop it with observed
`non-final position` evidence. Publish accepted artifacts atomically as
`<round-dir>/pov-<target>.json`, without confusing host family with peer target.

Record served model only from a native runtime receipt, never the requested
value or peer self-assertion. Retain `unverified` literally when no attestation
exists. Track `independence_verified` separately and disclose mismatch or
unverified required independence. Schema receipts describe the actual native
route, not the deleted CLI mapping. Never invent quota/authentication causes.
The coordinator validates the peer's core JSON, namespaces `voice` to its
resolved target, and adds or replaces receipt fields from native launch/serving
evidence before publication: `cross_model_route`, `cross_model_target`,
`cross_model_harness` (OpenCode), `serving_family`, `model_requested`,
`model_actual`, and `independence_verified`. Peer-supplied receipts are not
authoritative. Store unavailable serving family as `unknown` and actual model
as `unverified`; never infer either from the requested model.
An account-login remediation requires positively established provider-capable
dispatch and an observed provider authentication failure; authentication-shaped
text without that proof may describe only the execution context.

## 5. Reconcile material dissent

Only `mode: independent` voices enter convergence. Material dissent changes
adoption grade, selected approach, reader action (proceed/revise-first/reject),
or whether a risk is fatal. Different wording with the same decision concurs.
Default cap is the independent initial round plus two reconcile exchanges.
An explicit user pass/round limit wins: one pass permits no reconciliation;
a larger authorized limit replaces the default, never an open-ended loop.

For each exchange:

1. Revalidate identity; restart or return incomplete if changed.
2. Reconsider every surviving position and its evidence.
3. Verify only disputed decision-relevant project claims within allowed scope;
   mark verified, contradicted, or unverifiable with source locations.
4. Send every survivor the same complete evidence delta, full original subject,
   and all survivors' current reasoning/positions (at most five succinct,
   source-attributed evidence bullets per voice), never route-specific cuts.
5. Re-resolve fixed native routes and launch fresh stateless reviewers. Same
   recipients need no new question; unexpected recipients/intermediaries do.
   Drop failed voices from future rounds; do not reuse old positions as current.

Stop at the first matching state: `confident` (ce-pov has a reasoned decision),
`no-movement` (all survivors held and host is not confident), or `limit-reached`
(authorized cap spent after dissent without confidence). Convergence is not a
vote; a three-way split can still produce a reasoned confident decision.
No-movement/limit-reached mean stalemate, not settled consensus. At the cap,
recommend a specific bounded extension only with a named unresolved question,
new evidence/framing, and why it could move a position; otherwise recommend
stopping. Additional rounds require approval unless authorized in advance.

## 6. Decide and disclose

Lead with the POV in its active subject shape and a compact panel note:

- **Confident:** say whether voices aligned; note correlated blind spots. If
  deciding over dissent, name the disagreement and why the host result prevailed.
- **Stalemate:** give current host position, survivors' positions/movement,
  dropped voices' last states, and evidence-gap versus judgment disagreement.
  Recommend only with a real basis, otherwise say "Either is viable" and explain
  tradeoffs. Include the bounded-extension recommendation or reason to stop.
- **Partial:** name surviving/dropped targets and observed failure states.
  Explicitly mark any required different-model/fixed-route coverage incomplete;
  confidence in the judgment does not make missing coverage fully verified.
- **No survivor:** deliver solo with "cross-model check unavailable or incomplete."
  After any summons, even a branch never entered, say which peers ran or that
  none did and the observed reason. Never ship a bare solo verdict after a summons.

Keep target, route, requested model, served model, and independence receipts in
the private panel record. Default chat names target/requested model, position,
movement, and material failure; add serving/independence caveats when receipts
disagree, no model was requested, or credibility/required coverage depends on
them. Do not dump diagnostics or attribute a position to a model that did not run.
These operational receipts are not an artifact-author byline.
The same incomplete-coverage disclosure applies to a Confident or Stalemate
judgment when any required route or model independence remains unmet.

The panel never mutates. Handoff requires the original prompt explicitly
authorized the named downstream action, a non-stalemated result, inherited
scope, and non-destructive otherwise-authorized action. All four must pass.
A calling workflow owns continuation; recommendation grants no implementation
authority.

## 7. Skeptic mode and bounded recovery

Set `mode: skeptic` when challenging the host position. Fold a valid attributed
critique in once and disclose whether it changed the POV; it never enters
independent convergence. Failure degrades like any unavailable voice.

A peer failure never blocks the solo POV, but missing required coverage stays
incomplete. Distinguish a started provider/route failure from native dispatch
infrastructure failure before launch. For a genuinely recoverable infrastructure
error, correct the same permitted route while preserving target/model intent,
scope, payload, and withheld initial positions. Continue only for new plausible
recoverable failures within the original deadline; stop on repetition or expiry.
Never retry denied permission, bypass a missing tool with shell/another harness,
or evade depth. Any fallback must preserve independence and required coverage
or disclose the unmet requirement, never mark it completed.

## 8. Cleanup and summons

Stop/cancel owned tasks before removing consumed payloads, round outputs, logs,
and results within this run's verified private scratch root on success, failure,
timeout, or interruption. Never delete outside it, unrelated state, or still-
referenced artifacts. Peer reasoning/project context should not outlive use;
report a blocked cleanup if native lifecycle authority prevents safe completion.
Requested delivered write-ups remain available to their consumer.

A summons is an affirmative consultation/reconciliation request in any readable
invocation channel, including a calling skill's arguments. Declining consultation
or recounting a past cross-check is not a summons. A caller's paraphrase cannot
cancel one still present elsewhere; only an upstream-erased request is
unrecoverable. No summons means no panel note and no unsolicited warm panel.
Keep the frozen host judgment out of initial independent context except when
the already-formed judgment itself is the subject; expose it for skeptic or
later reconciliation as specified above.
