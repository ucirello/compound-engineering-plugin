# Cross-Model POV Panel

Obtain independent peer POVs, reconcile material disagreement, and return one
ce-pov decision. Peers are cross-checks, never votes or substitutes for the
decision-maker. The panel is read-only and non-blocking: return a panel POV,
a solo POV with an availability note, or the ordinary missing-context blocker.

## 1. Resolve subject and participation

Resolve conversational shorthand only when one subject fits. Otherwise return
missing context before dispatch. A summons is an affirmative request to consult
or reconcile peers, including `oracle`, named peers, or a calling skill's args.
Declining consultation or recounting an earlier panel is not a summons. A
caller's paraphrase does not cancel a summons still present in another readable
channel. No summons means no unsolicited panel note.

- Named peers: announce every named target, uncapped. Never silently replace an
  explicitly named model or rewrite Cursor to Composer.
- Bare `oracle`: select up to two reachable, attestably different-model peers,
  using conversation preference, local configuration, project conventions, then
  `codex -> claude -> grok -> antigravity` as preference intent.
- Explicit unnamed cross-check: select reachable appropriate peers without the
  proactive correction-cost test. Announce selected targets before dispatch.
- No summons: form the POV first. Offer a panel only if meaningful downstream
  work precedes error discovery, or the take feeds a shared, public, security,
  or data commitment. Adoption Tier 1 and warm invocations never offer.

Keep target, native harness route/provider/intermediary, requested model, served
model, and `independence_verified` separate. Targets such as `codex`, `claude`,
`grok`, `cursor`, `composer`, `opencode`, and `antigravity` express requested
intent, not permission to invoke their CLIs. Cursor default/Auto is not Composer;
Grok through Cursor is not native Grok; Antigravity expresses Gemini-family
intent. Preserve configured identities rather than pretending a native route is
the original intermediary. If that exact route is mandatory and unavailable,
report it unavailable. Cursor default and Composer are automatic choices only
when configured as preferences.

Attest the host's serving model from runtime evidence, never installed CLIs,
home directories, inherited environment markers, or a model's self-description.
Only receipt-supported different served families establish cross-model
independence. Otherwise record it unverified. Unknown host family excludes
unverified candidates from automatic different-model discovery; named peers can
still give useful checks with truthful caveats.

## 2. Native routing, authority, and capacity

Read applicable `.rocketclaw/config.yaml`, `config.local.yaml`, and documented
configuration examples for desired peers, routes, model choices, reasoning tiers,
allowlists, and budgets. Preserve their established precedence. Discover actual
available models with `opencode.models`; execute using native `subagents` and
`shell` for local evidence/scratch work, never another harness's dispatcher or a
replacement bridge script. Do not change host/global configuration.

Check these three constraints separately before dispatch:

1. **Delegation authority.** This skill explicitly requests reviewer subagents.
   Under a host rule allowing delegation when the user OR an applicable loaded
   skill requests it, that satisfies the skill exception: proceed without a
   second permission question. Merely loading a non-dispatching skill does not.
   Respect an unconditional higher-priority prohibition, actual permission denial,
   or unavailable tool; never evade it through shell or another harness.
2. **Model-selection authority.** Configuration and tiers remain desired intent,
   not permission. If an explicit user model request is required for overrides,
   omit the optional native `model` argument unless that condition is satisfied.
   Use suitable inherited-model reviewers when permitted. They are separate
   reviewers, not cross-model corroboration. If a required different-model pass,
   named model, fixed route, or tier cannot be satisfied, mark that coverage
   incomplete; never silently substitute or report full verification.
3. **Nesting capacity.** Inspect supported effective configuration via OpenCode's
   config interface and configuration source precedence, including
   `experimental.subagent_depth`, plus the current nesting depth when exposed.
   A configured depth of at least 3 is the installation prerequisite, not proof
   of remaining capacity. Package-local configuration is not automatically
   adopted by consumers. Do not mutate settings or launch a probe reviewer.
   Classify an actual dispatch failure from its error as depth/capacity,
   permission, model-argument rejection, missing tool, or another observed cause.
   Do not retry denials or evade nesting limits through another harness.

Resolve one concrete native route per peer. Probe capabilities without project
content first. Try configured intent; only an observed unavailable default may
use a closest same-family, same-tier compatible model when overrides are allowed
and no explicit user model binds it. Record the substitution. Confirm every
provider/intermediary is an allowed recipient. An unexpected recipient needs
approval; ordinary announced read-only consultation already authorized by a
summons does not. Separate active external-consultation gates still apply.

Announce who will inspect this project read-only, without internal diagnostics,
scratch paths, hashes, or unsupported confidentiality promises.

## 3. Freeze scope and repository identity

Resolve the absolute workspace root with `jj workspace root`; normalize the
read root as a repository-relative path plus ordered include/exclude patterns.
Pass the same scope to every peer. Narrower inherited scope is binding. Prompt
patterns, cwd, and read-only instructions are cooperative restrictions, not a
security sandbox. Require no edits, mutating commands, or intentional reads
outside scope; use native read-only tool restrictions where supported.

Capture the exact working-copy revision with JJ and a local digest of scoped
working files, including tracked, dirty, and untracked content. Revalidate before
every reconcile dispatch and final fold-in. On change, restart all voices on the
new identity or return incomplete; never fold stale voices into current work.
Run every JJ command with the target workspace's absolute root as cwd, e.g.
`(cd "$workspace_root" && jj log -r @ --no-graph -T 'commit_id')`.
Use latest JJ only; never invoke Git directly for history, review, or transport.
See https://docs.jj-vcs.dev/latest/cli-reference/ and
https://docs.jj-vcs.dev/latest/git-command-table/.
Repository-scoped GitHub calls use
`(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`.

Use the absolute private `$SCRATCH_DIR` from grounding. Put payloads, logs, and
results only there, inside local `.tmp/`; create private directories with mode
700 and payloads with mode 600 after checking ownership and symlink containment.
No OS-temp fallback or separate workspace is needed.

## 4. Dispatch, wait, and collect

Prepare one complete canonical payload: framed question, subject shape, scope,
repository identity, mode, subject paths, schema, and necessary conversation-only
material labeled by provenance. Peers inspect readable subject files directly;
do not duplicate them or invent a host-curated architecture summary.

For initial `independent` rounds withhold the frozen host position, other voices'
conclusions, risk rankings, advocacy, and evaluative option labels. Source-located
facts and the user's decision-relevant need, its strength, and supporting evidence
are allowed. Rejection of every option or the framing is valid. Present host-made
options symmetrically. A prior position that is itself the supplied subject ships
intact; only fresh host meta-judgment about it is withheld. In `skeptic` mode,
include the position being critiqued. Reconcile rounds deliberately include
already-formed positions. Never truncate the canonical payload per provider;
drop a route that cannot accept it and disclose partial coverage.

Seed native generic subagents with `references/agents/pov-peer.md` and
`references/pov-schema.json`. Use a supported generic agent whose role does not
override the brief. Launch independent peers concurrently when supported, before
waiting; record native handles and collect every started peer. Retain the
requested/actual native route and model receipt separately. Keep each result at
an owned private path such as `<round-dir>/pov-<target>.json`.

The coordinator adds receipt fields to the validated peer object from native
dispatch evidence: `cross_model_route`, `cross_model_target`,
`cross_model_harness`, `serving_family`, `model_requested`, `model_actual`, and
`independence_verified`. Never trust peer self-attestation for those fields.
Preserve declared defaults as intent where configuration does not override them:
Codex `gpt-6.1-sol` with high reasoning, Claude `claude-opus-5-5` with high
effort, and Antigravity `gemini-4-argon` with high thinking (its declared
compatible fallback is `gemini-3.8-flash`). These are not permission to override
the native model or invoke those harnesses; apply Section 2 and disclose any
unavailable route or tier.

Honor the configured/user budget; the default per-peer hard window is 600s,
with a 10s collection grace after the last start. A larger authorized
`CROSS_MODEL_HARD_SECS` remains larger; never shorten it for convenience. Use
native bounded wait/status/cancel facilities, not detached process bridges or
shell polling that evades host lifecycle. If a native limit cannot support the
window, report the actual limitation. At deadline stop remaining workers through
their supported lifecycle, collect settled results, and disclose timeouts.
Do not delete scratch while a worker still uses it.

Accept only schema-shaped JSON with nonempty reasoning, a settled `position`,
`final: true`, valid movement, and route/model receipt fields. A settled Blocked
answer is valid. Initial movement is `initial`; reconcile movement is `moved` or
`held` with an explanation. A non-final placeholder gets one same-route retry
within the same hard window; recurrence or exhausted time drops that voice as
`non-final position`. Native completion alone is not usable evidence.

Read artifacts only after verifying exact path containment, ownership, and no
symlink escape. Attribute served models only from native receipts; otherwise use
`unverified`. A requested model is not proof it served the response. Keep
`independence_verified` false unless served family differs attestably from host.

Classify failures from observed native errors, not generic terminal status.
An invalid argument rejected before launch may be corrected once if permitted,
including removing an unauthorized optional model override. Missing tool,
permission denial, and depth exhaustion are not transient infrastructure errors.
For a genuinely recoverable infrastructure failure, retry only the same allowed
route, scope, payload, and independence contract within the aggregate deadline;
stop when a failure repeats. Never switch recipients, widen scope, leak withheld
positions, or bypass policy in recovery. If the default model is refused, one
same-family/tier substitution is allowed only under Section 2; explicitly named
models are never swapped.

Report quota, timeout, or authentication only when supported by actual evidence.
An authentication-shaped peer statement does not prove the user's account is
logged out: require provider-capable launch context or a provider response before
attributing account failure or suggesting credential refresh. Distinguish a peer
that never started from a started peer that returned no usable result.

## 5. Reconcile material dissent

Only independent voices enter convergence. Different grades, selected options,
reader actions (`proceed`, `revise-first`, `reject`), or fatal-risk judgments are
material dissent; emphasis with the same decision is concurrence.

Default: one independent initial round plus at most two reconcile exchanges.
Explicit user limits replace this cap: one pass means no reconcile. When initial
voices materially dissent, run at least one exchange unless the user limited the
run to one pass. Do not decide over a dissenter who never saw counter-evidence.

For each exchange: revalidate identity; reconsider every current position;
verify only decision-changing disputed claims as verified, contradicted, or
unverifiable with sources. Send every surviving peer the identical complete
evidence delta, original subject, and every survivor's current position and
reasoning (at most five succinct attributed evidence bullets per voice).
Re-resolve each fixed route and dispatch fresh stateless reviewers. Same
recipients need no new approval. Drop failed voices in later rounds; an older
position does not count as current participation.

Stop at the first matching state:
- `confident`: ce-pov has reasoned confidence after weighing all survivors;
- `no-movement`: every survivor held and ce-pov remains unconfident;
- `limit-reached`: the authorized finite cap ended without confidence.

Convergence is not a vote. The latter two states are stalemate, not settled
agreement. At a cap recommend a specific bounded extension only if there is a
decision-relevant unresolved question, new evidence/framing, and a reason it
could move a position; otherwise recommend stopping. Further rounds need user
approval unless already authorized, and always have a finite cap.

## 6. Decide and disclose

Lead with the subject-shaped POV and a compact panel note:
- Confident: say whether voices aligned. Concurrence does not eliminate correlated
  blind spots. Name material dissent and why the final reasoning prevailed.
  Recommendations added after the panel are the host's, not peer agreement.
- Stalemate: give current host and survivor positions/movement, dropped voices'
  last states, and whether the gap is evidence or judgment. Recommend only when
  supported; otherwise say “Either is viable” with tradeoffs. Include the bounded
  extension recommendation or reason to stop.
- Partial: name surviving/dropped targets and observed failures, including unmet
  model/tier/route/independence requirements. Same-model reviewers do not complete
  required different-model coverage.
- No survivor: deliver the solo POV with “cross-model check unavailable or
  incomplete.” After every summons state which peers ran, or none and why,
  even when the panel branch could not start. Never ship a bare solo verdict.

Retain target, native route, requested model, served model, and independence
receipts in the private record. Default chat names target/requested model and
decision-relevant caveats, not raw diagnostics. Never attribute a position to a
model that did not run. A missing receipt stays unverified, not guessed.

## 7. Degradation, handoff, and cleanup

A skeptic critiques the supplied position once, uses `mode: skeptic`, and never
enters convergence. Disclose whether it changed the POV. Failure drops only that
voice. A peer never blocks the solo POV. Inline or parent-coordinator fallback
may provide bounded grounding where allowed, but cannot impersonate an
independent or required different-model peer. Disclose incomplete coverage.

The panel never mutates. Handoff requires all four Phase 4 conditions: the original
request explicitly authorized the named downstream action, the result is not
stalemated, scope is inherited, and the action is non-destructive and otherwise
authorized. Calling workflows retain continuation ownership.

After workers stop, remove consumed round outputs, payloads, raw logs, and results
inside this run's verified private scratch root on success, failure, timeout,
interruption, or cancellation. Never delete outside it or retain project context
longer than necessary. Preserve a requested deliverable until it is delivered.
