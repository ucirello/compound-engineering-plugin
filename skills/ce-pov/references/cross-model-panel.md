# Cross-Model POV Panel

The panel is read-only and non-blocking. ce-pov owns the decision; peers are evidence-bearing cross-checks, not votes. A requested cross-model check that cannot run remains incomplete, even when a useful solo POV can be delivered.

## 1. Permission, models, and nesting are separate gates

This skill explicitly authorizes native grounding-scout delegation and, for an affirmative panel request, native reviewer dispatch under a user-OR-applicable-skill delegation policy. Do not ask for second approval for that authorized read-only work. Loading an unrelated skill does not authorize delegation. Unconditional prohibitions and denied tools still win: never evade them through shell dispatch, escalation, another harness, or another intermediary.

Discover available model IDs with `opencode.models`, and use the native subagent capability exposed by this runtime. Read applicable `.rocketclaw/config.yaml`, `config.local.yaml`, and `config.example.yml` routing/tier settings as authoritative intent with their declared precedence; do not invent a parallel dispatcher configuration. Preserve explicit pins and requested families/reasoning tiers. If policy forbids model override without a user model request, omit the optional model argument and use a suitable inherited model; disclose the unmet configured tier. Model discovery is not permission to override. Never silently substitute a user-named model.

Inspect effective nesting configuration through supported discovery separately from permission and model selection. Setup requires users to MERGE `experimental.subagent_depth` >= 3 into the existing `~/.config/opencode/opencode.json` (or existing `opencode.jsonc`). Discover the actual directory using `opencode debug paths` / `opencode debug paths config`; preserve unrelated and sibling fields and any higher integer, do not create a competing file or replace the whole config. Higher-precedence config must not lower the depth. Package-local config and plugin installation alone do not enable deep delegation. Document this requirement; never modify host configuration here.

Classify observed launch failures as permission/tool denial, missing native tool, model rejection, actual depth limit, or capacity. Do not diagnose depth from a generic failure. Correct one malformed pre-launch argument once. Capacity may queue only within the aggregate deadline. A denied/depth-limited operation must not be retried through a forbidden path. Native inline/parent grounding is permitted by the grounding contract, but cannot replace required independent panel coverage.

## 2. Resolve participants and freeze scope

A summons is an affirmative request to consult/reconcile peers, including `oracle`, a named model, or cross-check args from a calling workflow. A decline or historical mention is not a summons. Without one, a cold Tier 2/3 POV may offer a panel only for consequential downstream commitments; Tier 1 and warm invocations never offer. An offer is not dispatch authorization until accepted.

Run every explicitly named peer, uncapped by automatic discovery. Bare `oracle` selects at most two reachable, attestably different-family models using conversation preference, authoritative configuration, and project conventions. Announce selected models and read-only consultation before launch. Report every unavailable named target rather than replacing it. Compatibility names such as Codex, Claude, Grok, Gemini, Cursor default/Auto, and Composer describe requested families or product routes, not authorization to launch those harnesses. Resolve them only through a verified native model mapping. A harness-specific request with no equivalent native route is unavailable; Cursor and Composer are not interchangeable.

Record target, native route, requested model (or inherited), actual served model from runtime receipts, host served model, and independence separately. Do not infer served models from requests, self-claims, installed CLIs, environment markers, or brands. Set `independence_verified: true` only when receipts establish a different serving family. Same-model fresh contexts are useful but not cross-model independence. If the required different-model coverage is unavailable or unverified, mark the panel incomplete, never complete.

Normalize one absolute JJ workspace root and optional ordered include/exclude patterns; give every peer the identical scope. Prompts are cooperative constraints, not a security sandbox. Require read-only inspection and deny mutations with available native permission controls. If required controls cannot be honored, do not launch.

Capture repository identity before dispatch: verified `@` commit identity plus a digest of all scoped content including tracked changes, conflicts, ignored and untracked files (without following paths outside the scope). Use JJ commands only with the absolute target workspace root as cwd, for example `(cd "$workspace_root" && jj log --no-graph -r @ -T 'commit_id')` and `(cd "$workspace_root" && jj status)`. Revalidate before each reconcile and final fold-in. On change restart all voices or return incomplete; never combine stale voices. Repository-scoped `gh` operations use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`.

Keep payloads, logs and results under the private workspace-local `.tmp` run directory supplied by Phase 1. Never reconstruct global temporary paths.

**Prior-opinion subjects.** When the subject is an already-formed position —
ce-pov's own prior POV or the user's stated view — that position is the subject
artifact and ships in the payload; peers answer the underlying question with
their own verdict, and those `independent` voices enter convergence (unlike
`skeptic` mode, where the critique does not). Any fresh host meta-judgment formed
after the panel request (the summons) is withheld per Section 3's round-1 sequencing. A user-supplied
position is handled identically to a host-authored one — shipped as the subject,
never capitulated to.

## 3. Canonical payload and independence

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
option" waits for reconcile). Label inlined conversation-only material as such.
When the user's goal bears on the decision, include the goal, how strongly they
hold it, and any evidence they gave for it. State in the payload that rejecting every supplied option, or the
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

## 4. Native dispatch, wait, and collect

Seed each fresh native generic subagent with `references/agents/pov-peer.md`, the complete canonical payload, and `references/pov-schema.json`. Start all allowed peers before waiting, using native lifecycle handles. No shell/ACP/other-harness dispatcher is permitted. Track run ownership, peer handle, round, route, model intent and actual receipts in the private run record.

Preserve the default 600-second peer budget; an authorized larger `CROSS_MODEL_HARD_SECS` intent widens it, never shorten it to finish sooner. Native lifecycle supervision must allow the peer window plus cleanup grace (at least 30 seconds); preserve an aggregate deadline measured from the last peer start and avoid duplicate launches while waiting. Collect completed peers while others run. On deadline cancel only owned live peers, await terminal confirmation, and record timeout; never abandon running workers or claim them completed. If native lifecycle cannot provide required supervision, report the limitation rather than inventing receipts.

Validate each returned JSON against the schema. Require nonempty settled position and reasoning, cited evidence, `final: true`, and `movement: initial` for the initial round or `moved`/`held` with explanation for reconciliation. A settled Blocked answer counts. Retry a non-final response once on the same authorized model within the same window; a second placeholder drops the voice. Attach runtime route/model receipts separately; peer claims are not serving evidence.

Recover a transient infrastructure failure only on the same permitted native route, model intent, scope and independence contract within the aggregate deadline. Stop on a repeated failure. A model rejection is distinct from permission/depth: a configured default may get one closest compatible same-family/tier replacement discovered through `opencode.models`, if override policy permits. Never replace a user-named model. Ask before adding an unexpected recipient or intermediary. Authentication/quota errors must be observed, not guessed; do not prescribe account login from ambiguous execution-context errors.

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
5. Revalidate every fixed native route under Sections 1–2, then dispatch a fresh stateless
   round. The same recipients need no question; an unexpected new recipient or
   intermediary does. A failed peer is dropped for later rounds; do not reuse its
   older position as if it participated.

When the initial independent voices materially dissent, run at least one
reconcile exchange before any stop, unless the user limited the run to one
pass. Deciding over a dissenter who never saw the counter-evidence is not a
reasoned convergence.

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
  dissent, name the disagreement and why its result prevailed. Claim peer
  agreement only for what the peers judged; name any recommendation you added
  after the panel as your own.
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

## 8. Cleanup

Stop and await owned peers before removing only this run's consumed payloads, logs, raw outputs and results beneath its verified private scratch root, including failure/timeout/interruption paths. Do not delete outside the run root or remove user-requested durable outputs. Preserve the decision-relevant coverage/failure/receipt summary in the returned result without retaining private peer context unnecessarily.
