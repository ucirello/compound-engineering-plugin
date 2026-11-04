# Cross-Model POV Panel

The panel is read-only. ce-pov remains the decision-maker, not a vote counter.
Use native OpenCode model discovery and subagents, never external harness
dispatchers, shell-launched peer CLIs, or workspace bridges.

## 1. Authority, capability, and participation

These explicit reviewer instructions request permitted delegation when this
skill is loaded; actual host user-OR-loaded-skill permission suffices without
second approval. An unconditional higher policy, actual denial, or missing
subagent tool still prevents dispatch. Never bypass denial through shell or a
different harness. Delegation permission is not model-override permission.

Discover available native tools and models with `opencode.models`. Read existing
`.rocketclaw/config.yaml`, `config.local.yaml`, and `config.example.yaml` model
choices, role mappings and tiers using their established layering; retain these
choices in the route record. Resolve advertised provider/model IDs, not guessed
model names. If the host requires a user model request, configuration alone does
not authorize passing a model override. Use suitable inherited-model reviewers
where permitted and disclose the unmet configured route. Never substitute for an
explicitly named model or claim an inherited reviewer fulfilled that request.

Discover effective nesting configuration separately from permission and model
selection. Deep delegation requires package default and consuming configuration
`experimental.subagent_depth` integer >=3. Setup must merge it into the existing
global `opencode.json` or `opencode.jsonc`, preserving sibling settings and higher
values; locate the actual directory with `opencode debug paths` or
`opencode debug paths config` rather than creating a competing document. Plugin
installation alone does not enable consumer depth, and higher-precedence config
must not lower it. Document this prerequisite; do not edit global files here.

An affirmative panel, cross-check, named-peer, or `oracle` request is a summons.
Declining consultation or mentioning an earlier panel is not. A caller's
paraphrase does not erase a summons still readable elsewhere in the invocation.
Named peers override automatic discovery and its count cap; attempt every exact
requested model that is available and authorized. Bare oracle selects up to two
reachable, attestably different-model peers using user preferences, configured
choices, project conventions, then suitable discovered models. Legacy target
names such as Codex, Claude, Grok, Cursor, Composer, or Antigravity are
compatibility labels only, not instructions to launch those harnesses. Cursor
default/Auto is not Composer; an unavailable exact route is reported incomplete.

Without a summons, a cold Tier 2/3 consequential decision may offer a panel after
forming a POV. Tier 1 and warm invocations never proactively offer one. Announce
selected peers and read-only consultation before dispatch. Ask only for an
unexpected recipient/intermediary or separately required active approval.

## 2. Scope, evidence, and independence

Resolve the absolute JJ workspace root and one repository-relative read root,
plus ordered include/exclude patterns. Pass identical scope to each peer and
never broaden inherited scope. Prompt-only restrictions and working directories
are cooperative, not confidentiality or write sandboxes. Tell peers not to edit
or inspect outside scope; use native read-only controls when available.

Capture the exact current committed revision and a digest of scoped tracked,
conflicted, ignored and untracked content, excluding only this run's scratch.
Run all JJ commands with cwd at the target absolute workspace root, for example
`(cd "$workspace_root" && jj log --no-graph -r @ -T 'commit_id')` and
`(cd "$workspace_root" && jj diff --git)`. Never invoke Git. Revalidate identity
before every reconcile round and final fold-in; changed evidence requires a
complete restart or an incomplete result, not stale convergence.

Use the private project-local `.tmp` scratch supplied by Phase 1. Create payloads
with umask 077 and mode 600. Preserve one canonical complete payload containing
the framed question, subject shape, scope, identity, mode, subject paths and
necessary conversation-only material. Peers read existing subject files directly;
do not replace them with a host-curated architecture summary. An oversized
payload makes the affected peer unavailable; never truncate per provider.

Initial independent prompts exclude the host's fresh conclusion, risk rankings,
advocacy, and other voices' positions. Include source-located facts, the user's
goal and its strength, and supplied evidence. Rejecting all options or the frame
is valid. Present host-authored options symmetrically. If an already-formed
position is itself the subject, include it intact but withhold fresh host
meta-judgment. `skeptic` mode instead includes the position to critique and does
not enter independent convergence.

Record target, native route/provider, requested model (or inherited), actual
served model receipt (or `unverified`), and independence evidence separately.
Attest the host and peer serving families from runtime evidence, never product
names, configuration intent, environment guesses, or model self-claims. Set
`independence_verified` true only for attestably different serving families.
Same-model distinct reviewers are useful separate perspectives, not cross-model
independence. If required independence cannot run, the panel is incomplete even
when an inherited-model cross-check succeeds.

## 3. Native dispatch, bounded recovery, and collection

Use fresh native OpenCode subagents seeded with `agents/pov-peer.md`, the
canonical payload and `pov-schema.json`. Use only tools and arguments actually
advertised by the runtime. Start all permitted peers before waiting; record each
session/task ID and lifecycle state. Native wait/result/cancel capabilities own
the lifecycle. Shell is for bounded local evidence/configuration work only, not
an alternative dispatcher. Keep a finite aggregate deadline, default 600 seconds
or a larger user-configured budget; never shorten an authorized budget merely to
finish sooner. Stop/cancel timed-out workers before deleting their artifacts.

Classify observed errors independently: permission denial, missing tool,
depth limit, capacity, model rejection, authentication, quota, timeout, invalid
arguments, and malformed/non-final output. Do not infer a depth failure from
denial or infer account logout from generic authentication-shaped text. Check
whether a worker launched before retrying. Correct a prelaunch argument error
once; bounded capacity recovery may wait within the same deadline. Never retry
denial or silently change a named model. A configured default rejected by the
provider can use one discovered compatible same-family/tier substitute only if
model-selection and recipient permissions allow it; disclose the failed route.

Validate returned JSON against the schema and verify nonempty reasoning, a
settled `final: true` position, and receipts. A settled Blocked answer counts;
a placeholder does not. Retry non-final output once on the same authorized
route within the original deadline, then drop it. Initial movement is `initial`;
reconcile movement is `moved` or `held` with reasons. Missing actual-model
receipts remain `unverified`, never fabricated from the request.

No parent/inline fallback can satisfy required independent or cross-model
coverage. When dispatch is unavailable, return the solo POV with incomplete
coverage rather than pretending the parent performed a peer pass. Keep every
requested but failed voice and its observed cause in the panel record.

## 4. Dissent and reconciliation

Material dissent means different adoption grades, selected approaches, document
bottom lines (`proceed`, `revise-first`, `reject`), or disagreement on a fatal
risk. Wording differences with the same decision are concurrence.

Default: one independent initial round plus at most two reconcile exchanges.
User pass limits win: one pass means no reconciliation. After material initial
dissent run at least one exchange unless the user limited the run to one pass.
For each exchange:

1. Revalidate scope identity and reconsider every surviving position.
2. Verify decision-relevant disputed project claims against authoritative scope;
   mark them verified, contradicted, or unverifiable with source locations.
3. Send the same complete evidence delta, original subject, and every survivor's
   position/reasoning (up to five source-attributed evidence bullets per voice)
   to fresh stateless peers on the same authorized routes.
4. Drop failed voices; never reuse old positions as current participation.

Stop at reasoned `confident` convergence, `no-movement` (all survivors held and
host remains uncertain), or `limit-reached`. Confidence is not majority vote.
The latter two are stalemates, never settled results inferred from a cap.
At the cap recommend a specific finite extension only when a named unresolved
question and new evidence/framing could move the decision; otherwise recommend
stopping. Extensions require approval unless already authorized by a larger
user limit. Never run an open-ended model-review loop.

## 5. Decide, disclose, and clean up

Lead with the POV in its active subject shape, then a compact panel note:

- Confident: say whether voices aligned; explain decisive evidence when deciding
  over dissent. Attribute post-panel recommendations to the host, not peers.
- Stalemate: give each survivor's position/movement, dropped voices' last state,
  and whether the gap is evidence or judgment. Say "Either is viable" when
  warranted, with tradeoffs and a bounded-extension or stop recommendation.
- Partial/incomplete: name missing requested coverage, observed failures, and
  any unverified or same-model independence caveat. A missing required pass
  remains incomplete, not a successful cross-model panel.
- No survivor: return the solo POV plus "cross-model check unavailable or
  incomplete," including which peers were attempted or why none ran.

Every summons requires a panel-status line even when the panel never starts.
No summons and no panel needs no panel note. Keep full receipts privately but
show only decision-relevant diagnostics; never attribute a result to a model
that did not run. A skeptic critique is folded in once and its effect disclosed,
not counted as convergence.

After collecting results or on failure/interruption, stop owned workers using
native lifecycle controls and remove only this run's consumed payloads, logs and
artifacts under its verified private scratch. Retain/report unresolved active
worker state rather than deleting evidence underneath it. Never remove a
workspace as scratch cleanup.

The panel never mutates the project. Apply SKILL.md Phase 4's four-part authority
check before continuation: original explicit downstream authorization,
non-stalemated decision, inherited scope, and non-destructive otherwise
authorized action. Calling workflows retain continuation ownership.
