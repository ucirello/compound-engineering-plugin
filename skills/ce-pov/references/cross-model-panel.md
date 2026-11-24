# Cross-Model POV Panel

Obtain independent peer POVs, reconcile material disagreement, and return one
ce-pov decision. Peers are cross-checks, never substitutes or votes. This
read-only panel is non-blocking: deliver a panel POV, a solo POV with a coverage
note, or the ordinary POV's explicit missing-context blocker.

## 1. Resolve the subject, host, and participants

Resolve “the approach,” “these options,” and other shorthand against the
conversation. Return missing context if several plausible subjects would
materially change the POV and the available context cannot distinguish them.

Keep four identities separate: the **target** the user or configuration named,
the **route** (native dispatcher, provider and any intermediary), the **requested
model and variant** (explicit pin, configured default or inherited/auto), and the
**served model** from runtime evidence. Attest the current OpenCode host and
serving family from runtime-provided session/model evidence, not installed CLIs,
branding, a configured/requested model, or a model's self-description. Record
missing serving evidence as `unverified`. Use `independence_verified: true` only
when authoritative session evidence shows the peer's served model family differs
from the host's. A fresh context gives a separate opinion but not different-model
independence. An attested same-family result is not cross-model corroboration.
Without host serving-family evidence, automatic discovery selects no peers whose
independence cannot be verified; do not guess.

A summons is an **affirmative** request in any readable invocation context
(including a calling skill's args) to consult or reconcile other models. A
declination or historical mention alone is not a summons and transmits no project
context. A paraphrase in one channel does not cancel a request in another.
Apply exactly one branch:

- **Named peers:** Resolve each exact named target, without a count cap. Report
  any that cannot run; never rewrite Cursor to Composer or replace a user
  model pin or explicit route. A compatible peer target that names a model family
  rather than a harness may run natively under that family.
- **Bare `oracle`:** Select up to two reachable targets with attestably
  different model families, using conversation preference, local configuration,
  active project conventions, then `codex → claude → grok → antigravity`.
- **Explicit unnamed cross-check:** Use the same count and selection rule
  without evaluating downstream correction cost.
- **No summons:** After independently forming the POV, offer a panel only when
  meaningful downstream work will build on it before an error would surface, or
  it feeds a shared, public, security, or data commitment. Adoption Tier 1 is
  ineligible; Tier 2/3 may qualify. Never offer in a warm invocation or a
  calling-workflow return. Wait for acceptance before dispatch and omit the panel
  note when no panel was requested.

Cursor default and Composer are never auto-discovered; only consider them if
named or configured as a preference. Zero reachable peers means solo plus one
availability line. Announce the reachable selected peers before dispatch.

**Prior-opinion subject.** If an earlier host POV or the user's stated view is
itself the subject, pass it intact as the subject artifact. Independent peers
answer the underlying question in their own words and enter convergence;
withhold only the host's fresh meta-judgment formed after the summons. A
`skeptic` critique, by contrast, does not enter convergence.

## 2. Normalize scope and freeze repository identity

Resolve the absolute JJ workspace root and one workspace-relative read root,
plus any ordered include/exclude patterns. For a non-JJ project use its absolute
local project directory, with no revision anchor. Pass the same scope to every
peer. Default to the project root; never broaden a narrower user or host scope.
Point peers at the existing subject files rather than copying them into prompts.
Inline only material that exists solely in the conversation or is otherwise
unavailable in the shared tree.

Treat prompt-only patterns and a working directory as cooperative, not a
confidentiality boundary. Use native read-only tool restrictions where supported;
never claim a write sandbox or that secrets are inaccessible without runtime
proof. Peers may read inside the declared scope but may not mutate the project
or deliberately inspect outside it. If the task requires isolation the native
route cannot enforce, do not send it.

Before dispatch, freeze one **repository-scope identity**: committed parent
revision(s) plus a digest covering dirty and untracked scoped content. Read the
parent IDs without forcing a snapshot, from the absolute workspace root:
`(cd "$workspace_root" && jj --ignore-working-copy log --no-graph -r '@-' -T 'commit_id ++ "\n"')`.
Sort multiple IDs for a stable anchor. Compute a deterministic local manifest
digest over the current permitted paths and on-disk state (including unsnapshotted
and untracked files): canonical relative paths, file types/modes, content hashes,
and symlink targets without following them. Hashing the whole approved file
set also captures dirty content and deletions without relying on a snapshot or
guessing which paths JJ has seen. Exclude VCS metadata and run scratch; do not
read excluded or out-of-root content. For a standalone directory use the same
digest without the revision component. Include the identity in each payload.
If scope or identity cannot be verified, do not count a panel against it.
Recompute before each reconciliation dispatch and final fold-in. If changed,
never fold stale voices into the current project: disclose and restart all voices
on the new identity within the authorized budget, or return incomplete.

Use the absolute run-specific scratch path from `references/grounding.md`, under
local `.tmp/`. Keep panel payloads, diagnostics and results there, never in
tracked paths or global temporary storage. Create saved payloads with `umask 077`
and confirm mode 600 before dispatch. Do not persist raw copies when the native
result and a private bounded record suffice.

## 3. Resolve and announce one fixed native route

Honor explicit user model pins and route restrictions; read the applicable
project's `.rocketclaw/config.yaml` and `.rocketclaw/config.local.yaml` for
configured choices, with local overrides and `config.example.yml` only as
documentation/default guidance when supplied. Treat these sources as intent,
not tool permission. Preserve the following defaults when no active instruction
or configuration overrides them. These are mappings to resolve against the
OpenCode catalog, not executable harness commands or invented catalog IDs.

| Target | Preferred model / variant when exposed by OpenCode |
|---|---|
| `codex` | `gpt-6.1-sol`, high |
| `claude` | `claude-opus-5-5`, high |
| `grok` | `grok-4.7`, xhigh; explicitly Cursor-mediated Grok used `grok-4.7[context=256k,reasoning_effort=high,fast=true]` |
| `cursor` | Cursor default/Auto, not Composer |
| `composer` | `composer-2.5[fast=true]`, via Cursor |
| `opencode` | OpenCode inherited/auto unless pinned |
| `antigravity` | Gemini family: `gemini-4-argon`, high, with `gemini-3.8-flash` as the declared unavailable-model fallback |
| `pi` | Pi's configured model or explicit `provider/model` pin; the target itself attests no family |

Use `opencode.models` to discover the exact `provider/model` ID, supported
variant, and availability without sending project content. Native availability
can establish a candidate's requested family for selection when the host's
served family is known, but does not attest this run's served model or prove
authentication. Map by the
requested family and tier only when the target allows that mapping; if the user
requires a Cursor, Antigravity, Pi, or other actual intermediary or an Auto
setting specific to that harness, another native provider selling the same
model does not satisfy it. Record the requested route as unavailable unless
the exact recipient/route is exposed natively. Never launch other harnesses,
adapters or a nested OpenCode process from shell to satisfy a route. Keep the
Antigravity/Gemini self-peer exclusion; Pi on its own harness is not a peer.

Resolve one target, exact native route, requested model/variant (or inherited
model) and all actual provider/intermediary recipients. Honor every active
recipient restriction, including `CROSS_MODEL_PEERS` if set: targets require
their sanctioned token, Gemini-through-Antigravity uses `antigravity`, and
Cursor-mediated Grok requires `grok` and either `cursor` or `composer`. An
allowlisted target is not authority to add an unexpected recipient. Announce
who will inspect the subject, where the material goes, and that the review is
read-only; omit scope mechanics, CLI versions, scratch paths and other plumbing
unless decision-relevant. A summons authorizes the usual read-only consultation;
ask before adding an unexpected recipient/intermediary or where active
instructions separately gate egress. If recipients cannot be verified or
sanctioned, skip that route before sending anything.

This skill explicitly requests one fresh native OpenCode subagent per selected
eligible peer. That satisfies a host rule permitting delegation at the user's
**or** loaded skill's explicit request; do not demand duplicate approval. A
higher-priority unconditional prohibition, missing tool or actual denial still
applies. Model override permission is separate: if the host requires an
explicit user model request, a role, preference, or configuration entry alone
does not authorize passing `model`. Omit it when prohibited. The inherited
model may run only when it satisfies the authorized route and task (for example,
a same-model skeptic where a different model is not required). If a required
fixed route, tier or different-model pass cannot be met, mark that coverage
incomplete. Do not present an inherited opinion as a substitute for a required
cross-model pass.

Nesting is separate from both permissions. Check `experimental.subagent_depth`
by inspecting the applicable sources and precedence (OpenCode V2:
`opencode api get '/api/config?location%5Bdirectory%5D=<URL-encoded-absolute-workspace-root>'`;
the response is a source array, not effective config). Compare the effective
configured limit with the current nesting when known. A bundled package config
does not establish the consuming project's value or prove remaining capacity.
Use the actual tool status/error to distinguish exhausted depth or runtime
capacity, delegation denial, model override rejection, a missing tool and
other pre-launch failures. Do not guess or change host settings mid-run.

## 4. Dispatch, collect and validate

Prepare one complete canonical payload: framed question, subject shape,
normalized scope, scope identity, mode, paths to subject material already in
the workspace, and required conversation-only material labeled as such. Use
`references/agents/pov-peer.md` as the native subagent brief and supply
`references/pov-schema.json` as its result contract. Let peers inspect the
shared tree; do not duplicate readable files or provide a host-curated project
summary. Never truncate the payload for just one provider. Drop any route that
cannot accept the complete brief (default payload budget of 200,000 bytes;
honor a valid `CROSS_MODEL_MAX_PAYLOAD_CHARS` override and native limits).

For an initial `independent` round, withhold the host's frozen position and
every other voice's conclusion, including risk rankings, decisive inferences,
advocacy framing and evaluative option labels. Keep the actual proposal,
document or options fully available. Include source-located facts and the
user's relevant goal, its strength and any evidence they supplied. Present
host-authored options symmetrically; rejecting every option or the framing is
valid. As in Section 1, a prior opinion that is itself the subject ships intact;
only fresh meta-judgment is withheld. `skeptic` includes the host position
because critiquing it is the task. Later reconciliation includes formed views.

Dispatch one fresh generic native subagent per peer on its fixed route, in
parallel when supported, and await all started calls. Record any native run or
session ID and bind returned artifacts and diagnostics to that call and round.
Allow up to 600 seconds per peer by default; honor a valid larger
`CROSS_MODEL_HARD_SECS` budget and any higher-priority/native deadline. Use the
native wait/cancel lifecycle when available; cap the round at the last initial
start plus that budget and up to 10 seconds grace, without renewing it for
retries. At the deadline cancel only this round's outstanding work if supported,
check its state once, and report timeouts or unresolved worker state. Do not
spawn detached processes, poll indefinitely, or assume a cancellation succeeded.

Accept only a route-bound, schema-shaped response that answers the framed
question with nonempty reasoning and the round's correct mode and movement:
`initial` first, `moved` or `held` with an explanation in reconciliation. A
completed call is not proof of a usable result. `final: true` declares a settled
answer, including a reasoned `Blocked — …` result. A non-final result gets one
retry with an explicit final-answer requirement on the same route and within the
original deadline. Otherwise drop it as non-final, not as a peer vote.

Record target, native route/provider/intermediary, requested model/variant,
served model, and independence separately (`cross_model_*`, `model_requested`,
`model_actual`, `serving_family`, `independence_verified`). Populate receipt
fields from trusted native run metadata or a supported session read tied to
the call; ignore inline model self-reports. Without a receipt set
`model_actual: unverified`; do not infer model or verified independence from
the target, requested model, or a successful answer. Keep a useful
unverified or mismatched voice only as an explicitly qualified cross-check;
it neither fills a required fixed route nor establishes cross-model coverage.

Classify unstarted and started failures from bounded native diagnostics:
pre-dispatch failures sent nothing; for a started call do not claim no egress
without evidence. Distinguish missing native tool, permission denial, depth or
capacity, rejected model, provider authentication/quota, timeout or unusable
answer. Attribute login/account failure and suggest remediation only when a
provider-capable launch or provider receipt establishes it; an
authentication-shaped message from an unverified execution context is not proof.

If a **default** model was unavailable/rejected, and model selection is
permitted, allow one same-route, same-recipient recovery to a catalog-backed
equivalent in the same family and tier (or the declared Gemini fallback).
Keep user pins exact. For a new, plausibly transient pre-launch infrastructure
error, recover through the same permitted native call within the original
deadline, keeping target, route, model, scope and withheld context fixed. Stop on
the first repeated failure or the deadline. Never retry a denied operation or
use shell or another dispatcher to bypass permission, unavailable tools or
nesting. Do not retry a model argument forbidden by policy. No required
independent panel pass can be performed inline or by the host's own
reconsideration; the ordinary solo POV is the fallback.

## 5. Detect dissent, verify claims, and reconcile

Only `mode: independent` voices enter convergence; independence of initial
reasoning is separate from model-family independence. Material dissent means
a different adoption grade, a different selected approach, or document bottom
lines that imply different reader actions (`proceed`, `revise-first`, `reject`)
or disagree on whether a risk is fatal. Wording, emphasis, confidence or
supporting detail with the same decision is concurrence.

The default limit is the initial round plus at most two reconcile exchanges.
Honor an explicit pass/round limit: “one pass” or “one round” allows no reconcile
exchange, and a larger explicit limit replaces the default. After material
initial dissent, run at least one reconcile exchange unless the pass limit,
permitted routes or available time preclude it; do not call untested dissent
reasoned convergence. For each exchange:

1. Revalidate scope identity; restart or return incomplete on change.
2. Reconsider all current positions and their evidence.
3. Verify only disputed project claims that could change the decision.
   Classify them `verified`, `contradicted`, or `unverifiable`, citing sources.
4. Send the identical complete evidence delta, full original subject and all
   surviving positions/reasoning (at most five source-attributed evidence
   bullets per voice) to each survivor, without per-route truncation.
5. Re-resolve each fixed route under Section 3 and dispatch a fresh stateless
   round. The same recipients need no new question; unexpected recipients do.
   Drop failed peers from later rounds; don't reuse older positions as if
   they had participated.

Stop at the first applicable condition: **`confident`** — a reasoned POV
weighing every survivor; **`no-movement`** — all survivors held and ce-pov is
still not confident; **`limit-reached`** — the authorized limit completed
after dissent and ce-pov is still not confident. The latter two are stalemates,
not settled results. Convergence is reasoned confidence, not a vote.

At the cap, recommend a specific bounded extension only when you can name the
unresolved decision-relevant question, the new evidence/framing, and why it
could move a position. Otherwise recommend stopping. Further rounds need user
approval unless already authorized; each extension establishes a finite cap.

## 6. Decide and disclose

Lead with ce-pov's POV, then give a compact coverage note when summoned:

- **Confident:** state whether voices aligned on what they actually judged.
  Correlated-model blind spots remain. If deciding over dissent, explain why;
  distinguish any additional host recommendation from peer agreement.
- **Stalemate:** state the host and surviving peers' positions and movement,
  dropped voices' last state, and whether the disagreement is evidence or
  judgment. Say “Either is viable” and explain the tradeoffs if no recommendation
  is warranted. At the cap recommend bounded further rounds or stopping.
- **Partial:** name surviving and dropped targets, observed failures and unmet
  requirements. Even when a usable separate opinion ran, explicitly mark a
  missing fixed route, requested independent family, or unverified coverage as
  incomplete. State when reconciliation over material dissent was unavailable.
- **No survivor:** give the solo POV and say “cross-model check unavailable or
  incomplete.” If no dispatch occurred, say none ran and why. Do not add a
  panel note without a summons.

Keep receipts in the private panel record, but in chat or a requested write-up
name the target and requested model (or inherited/auto), useful position and
movement, observed failure, and any serving mismatch or independence caveat that
bears on coverage. Never attribute an answer to a model that did not run.

After delivery, apply `references/followup.md`: the original request must
explicitly authorize the named downstream action, the result must not be
stalemated, and the action must stay in inherited scope, non-destructive and
otherwise authorized. A calling workflow owns any continuation.

## 7. Skeptic mode and degradation

When asked to challenge ce-pov rather than form an independent POV, use
`mode: skeptic`. Fold each valid critique into ce-pov once, outside convergence,
and disclose whether it moved the POV. Mid-round failure drops only that voice;
an oversized payload drops only routes that cannot receive the identical
payload. No peer failure blocks a properly grounded solo POV.

## 8. Cleanup

Stop or cancel outstanding run-owned native jobs through their supported
lifecycle where available. Report unresolved execution or retention
limitations without attempting out-of-band cleanup. Remove private panel
payloads, raw logs and results once consumed, including on failure, timeout or
interruption. Delete only known panel artifacts under the exact owned run
directory; preserve a requested write-up and any still-needed dossier.
OpenCode session/provider retention is separate from local scratch cleanup;
never promise to erase records you cannot control or delete other sessions.
