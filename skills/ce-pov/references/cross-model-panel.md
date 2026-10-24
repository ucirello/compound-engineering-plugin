# Cross-Model POV Panel

Obtain independent peer POVs, reconcile material disagreement, and return one
ce-pov decision. Peers are cross-checks, not votes or substitutes for the host's
judgment. Every branch ends in a panel POV, solo POV with availability note, or
the ordinary explicit blocked-on-missing-context result. The panel is read-only.

## 1. Participation and permission

Resolve conversational shorthand against the active conversation. Return missing
context only when competing subjects would materially change the judgment.
A summons is an affirmative request for a panel, independent opinions, named
peers, cross-check, or `oracle`, including a calling skill's arguments. A refusal
or historical mention is not a summons. A paraphrase in one channel does not
cancel a request still present in another readable channel.

- Named peers are exact and uncapped; never replace or silently drop them.
- Bare `oracle` selects up to two reachable, attestably different-model peers,
  using conversation preference, local configuration, project conventions, then
  the intent order `codex -> claude -> grok -> antigravity`.
- An explicit unnamed cross-check skips the proactive correction-cost check.
- Without a summons, form the solo POV first. Offer a panel only when meaningful
  downstream work will precede detection of an error, or a shared, public,
  security, or data commitment depends on it. Adoption Tier 1 and warm invocations
  are ineligible for proactive offers.

This skill explicitly requests reviewer dispatch when this panel is selected.
Under a host rule permitting subagents requested by the user OR an applicable
loaded skill, that satisfies the exception; do not demand a second approval.
It does not override an unconditional higher-priority prohibition, tool absence,
or actual denial. Merely loading a skill without a dispatch request is not consent.

Delegation permission does not grant model-selection permission. If the host
requires an explicit user model request for overrides, omit the native optional
`model` argument when only configuration or skill tiers suggest it. Use a suitable
inherited-model reviewer when possible, disclose unmet intent, and never call
same-model reviewers cross-model independence. An unavailable required different
model or exact fixed route makes that coverage incomplete.

Verify effective delegation depth and remaining nesting capacity separately,
using discovered runtime configuration and current nesting level as described in
`grounding.md`; do not assume the package default controls this session. Classify
actual errors as permission denial, model-argument rejection, depth/capacity limit,
or missing tool. Never retry a denial or evade a depth limit through shell or
another harness. A parent-coordinator handoff is allowed only within its authority
and the same scope, payload, independence, and route contract. Inline solo work
is useful fallback, never a completed independent peer pass.

## 2. Scope, evidence, and identity

Resolve one absolute repository/workspace root, optional narrower repository-relative
read root, and ordered include/exclude patterns. Pass identical scope to all peers;
never broaden it. Prompt scope and read-only instructions are cooperative, not a
confidentiality sandbox. Deny writes using available native controls, but do not
promise that readable secrets are inaccessible. Peers inspect subject files in the
shared working tree rather than receiving copied files or a curated architecture
summary. Inline only otherwise unavailable conversational material.

Capture one scope identity before dispatch: exact JJ revision plus a deterministic
digest of scoped file paths and contents, including dirty, untracked, and relevant
ignored material. Exclude this run's own scratch artifacts consistently. Run JJ
with cwd at the absolute workspace root. Revalidate before each reconcile and final
fold-in; on change restart all voices on the new identity or report incomplete,
never fold stale results into the current project. For a non-repository project,
use the same scoped content digest and explicitly record no revision.
See https://docs.jj-vcs.dev/latest/cli-reference/.

Use Phase 1's resolved private local `.tmp/` scratch directory. Create payloads
with `umask 077`, verify ownership and containment, and chmod payloads to 600.
Keep payloads, logs, receipts, and results there; never use OS-global temporary
storage or reconstruct another scratch root.

## 3. Resolve native routes

Read applicable `.rocketclaw/config.yaml` and `config.local.yaml` model/peer
settings, respecting their existing precedence and explicit user choices. They
remain the source of routing intent, tiers, budgets, and recipients. Discover exact
available model IDs with `opencode.models`; execute through native `subagents`,
using shell only for bounded local evidence and artifact handling, not another
harness dispatcher. Never launch Codex, Claude, Cursor, Grok, ACP, or another
OpenCode process as a dispatch bridge.

Preserve configured targets and operational provider identities. `Cursor` means
its configured default/Auto, not Composer; `Composer` is a distinct requested
model. Grok native and Grok through Cursor are different recipient routes;
Antigravity denotes a Gemini route. If a requested harness-specific fixed route
cannot be represented natively, report it unavailable rather than relabeling a
different model or silently invoking the old harness. Cursor default and Composer
are never auto-selected unless configured as a preference or named.

Keep target, actual native route/provider/intermediaries, requested model, served
model, host harness, and host serving family separate. Attest the host from runtime
serving evidence, not installed CLIs, home directories, inherited environment
markers, or model self-claims. A requested model is not a serving receipt. Set
`independence_verified: true` only when runtime receipts attest a different served
model family from the host; otherwise retain useful review but disclose unverified
independence. With unknown host family, exclude unverifiable candidates from
automatic different-model discovery. Keep absent receipts as `unverified`.

Probe model capabilities without project content. Try configured routing first;
an observed unavailable default may receive one closest same-target/family/tier
substitute only when model selection is permitted and no user exact model request
would be violated. Record the fact and substitution. An explicitly named model
is never swapped. Verify every actual recipient is permitted. Unexpected new
recipients or intermediaries require explanation and approval; an active external
consultation gate still applies. Otherwise an authorized summons needs no repeat
approval. Announce selected peers and read-only consultation concisely before
dispatch, without internal scratch, hashes, tier, lifecycle, or probe diagnostics.

## 4. Dispatch, wait, collect, and bounded recovery

Prepare one canonical payload: framed question, subject shape, scope, identity,
mode, subject paths, and essential unavailable conversation material. Require
`references/pov-schema.json` and seed `references/agents/pov-peer.md`.
Every selected peer receives the complete same payload; no route-specific
truncation. An incompatible payload makes that route unavailable.

For initial `independent` mode, withhold the host's fresh judgment and all other
voices' conclusions, candidate-risk rankings, advocacy, and evaluative labels.
Include source-located facts and the user's decision-relevant goal and strength
of preference; label conversation-only material. Permit rejection of every option
and the framing. Present host-authored options symmetrically. When an already
formed host or user position is itself the subject, ship that position intact;
withhold only fresh meta-judgment formed after the summons. In `skeptic` mode,
include the host position because critique is the task.

Start all permitted native peer calls before waiting. Record native task IDs,
target, route, exact requested model, start/deadline, output ownership, and state.
Use native wait/status/result/cancel facilities; no detached runner. Preserve a
600-second per-peer default hard budget and any configured larger budget. Never
shorten a configured budget merely to finish sooner. Bound overall waiting by the
last start plus its authorized budget and ten-second collection grace. Wait in
bounded slices, collect finished peers promptly, then cancel only owned pending
tasks on deadline and collect terminal status once more. Never leave workers
running during cleanup. Missing native lifecycle capabilities mean unavailable
coverage, not permission to spawn another harness.

A terminal success alone is not a usable answer. Validate owned results against
the schema: settled `position`, nonempty reasoning, `final: true`, correct movement,
and route/model receipt fields. A final blocked verdict is usable; a non-final
placeholder is not. Retry a non-final result once on the identical route with an
explicit final-answer requirement, inside the original deadline; then drop it
with observed `non-final position` evidence. Initial movement is `initial`;
reconcile movement is `moved` or `held` with explanation.

Read only contained, run-owned artifacts and bounded logs. Attribute served
models solely from runtime receipts, never peer prose or requested IDs. Diagnose
quota, authentication, timeout, rejected model, permission, depth, and tool errors
from actual evidence. Do not infer account logout from sandbox-shaped failures
or ask for login without provider-capable dispatch evidence. A shared native
infrastructure failure does not become a model failure.

The coordinator adds or verifies `cross_model_route`, `cross_model_target`,
`cross_model_harness`, `serving_family`, `model_requested`, `model_actual`, and
`independence_verified` in the collected panel record against native task metadata.
These optional schema fields are not permission for a peer to self-attest runtime
identity. Store absent serving receipts as `unverified` and independence as false.

For recoverable prelaunch argument/infrastructure errors, correct once on the same
native route, preserving target/model, payload, scope, and independence; stop on a
repeated failure or aggregate deadline. Never retry denial/depth failure. A rejected
configured default may receive at most one permitted same-family substitute from
advertised models; exact user models cannot. No open-ended recovery, recipient
hopping, withheld-position leakage, or silent coverage claims.

## 5. Dissent and reconciliation

Only independent voices enter convergence. Material dissent changes adoption
grade, selected approach, proceed/revise-first/reject bottom line, or whether a
risk is fatal; wording and confidence differences alone are concurrence.

Default: one initial round and at most two reconcile exchanges. Honor explicit
user limits exactly: one pass means no reconcile; larger limits replace the cap.
After material initial dissent, run at least one reconcile unless the user limited
the panel to one pass. For each exchange:

1. Revalidate scope identity; reconsider every surviving position and evidence.
2. Verify decision-relevant disputed project claims as verified, contradicted, or
   unverifiable with source locations.
3. Send every survivor the identical full original subject and common evidence
   delta, plus every current position/reasoning with at most five concise,
   source-attributed evidence bullets per voice.
4. Revalidate native fixed routes and dispatch stateless fresh rounds. New
   recipients require approval; failed peers are dropped, never represented by
   their older position as though they participated again.

Stop at the first applicable state: `confident` (reasoned host judgment after
weighing survivors), `no-movement` (all survivors held and host not confident),
or `limit-reached` (finite authorized limit exhausted without confidence).
Confidence is not a vote. The latter two require stalemate disclosure, not a
fabricated consensus. At a cap, recommend a specific bounded extension only with
a named unresolved question and new evidence/framing likely to move it; otherwise
recommend stopping. Extra rounds require authorization unless already covered
by the user's larger finite limit.

## 6. Delivery and cleanup

Lead with the host POV in the active subject shape, then a compact panel note:

- Confident: say whether voices aligned; if deciding over dissent, explain why.
  Distinguish later host recommendations from what peers actually judged.
- Stalemate: state each survivor's position/movement, dropped voices' last state,
  evidence gap versus judgment difference, and material tradeoffs. At a cap,
  recommend the bounded extension and evidence path or explain why to stop.
- Partial: name surviving/dropped targets and observed failures. Missing required
  fixed routes or cross-model independence remain incomplete, even if a solo or
  same-model review is useful.
- No survivor: deliver solo with “cross-model check unavailable or incomplete.”
  Every summons gets status naming which peers ran or that none ran and why.
  No summons means no panel note.

Retain target/route/requested/served model and independence receipts in the panel
record. In chat name target and requested model, position/movement, relevant
failures, and receipt/independence caveats when they affect credibility. Never
attribute a position to a model that did not run. `unverified` serving evidence
does not erase a known requested model.

A skeptic critique is folded in once and never enters convergence; disclose
whether it changed the POV. Peers never block a solo POV. Preserve the ordinary
missing-context outcome when evidence cannot support judgment.

The panel never mutates the project. Downstream action requires all four:
original prompt explicitly authorized the named action, result is non-stalemated,
action remains in inherited scope, and action is non-destructive and otherwise
authorized. Otherwise return judgment and control to the caller.

On success, failure, timeout, or interruption, stop and collect owned workers
first. Remove only consumed run-owned payloads, logs, results, and round directories
inside the verified private scratch root; never delete outside it. Preserve an
explicitly requested undelivered write-up for delivery, and report cleanup failure
without broad deletion. Peer reasoning and project context must not outlive use.
