# Native peer panel

## Participation and authority

A summons is an affirmative user or calling-skill request to consult or reconcile peers, including `oracle`, named peers, or a cross-check. A mere mention or refusal is not a summons. Honor an explicit opt-out. Named peers are exact and uncapped; never substitute another model. Bare `oracle` selects up to two reachable, attestably different-model peers using conversation preferences, configuration, project conventions, then available capable models. Announce selected peers before dispatch. A POV following a summons always states which peers ran, or that none did and the observed reason. No summons means no panel note.

Without a summons, first form the POV independently. Offer consultation only for consequential Tier 2/3 decisions whose errors would be costly to discover downstream, never Tier 1 or a warm mid-session second opinion. Do not dispatch a proactive offer before acceptance.

This skill's explicit reviewer request satisfies a host's user-OR-skill delegation exception; do not ask again solely for delegation. An unconditional prohibition, actual permission denial, or missing native subagent tool still blocks dispatch. Model override permission is separate: where the host requires an explicit user model request, configuration or this skill does not authorize supplying an optional model override. Preserve configured models and tiers as routing intent. Suitable inherited-model reviewers may gather useful opinions, but the same model is not cross-model corroboration and an unmet required different-model route remains incomplete coverage. Nesting depth is a separate capacity constraint, not delegation or model permission.

## Resolve scope, models, and receipts

Use native `opencode.models` to discover current model IDs and capabilities, then the host's native subagent tool to dispatch. Never invoke external harness CLIs, dispatch bridge scripts, shell-based model engines, or elevation to bypass constraints. Model discovery is not model-use authorization. Explicit model requests remain exact; unavailable or denied models are reported, not silently replaced. Keep configured role/model choices authoritative where permitted.

**Discover effective depth without mutation or a startup gate.** Consult `ce-setup`'s user-level `experimental.subagent_depth >= 3` prerequisite and locate the existing global config with supported `opencode debug paths` / `opencode debug paths config` discovery. Package/plugin config alone is insufficient. Use the supported authenticated CLI/server context to run `opencode api get '/api/config?location%5Bdirectory%5D=<URL-encoded-absolute-target-root>'`, encoding the absolute target root and never exposing credentials. Read the **top-level source-entry array**, inspecting document `path` and `info.experimental.subagent_depth`; determine effective depth from actual source precedence, including higher-precedence project/managed settings. Preserve higher integers and unrelated fields; this panel does not change global/project/plugin config. Unavailable discovery or depth below 3 is an unknown/unmet prerequisite to report with `ce-setup` remediation, not a new blocker to otherwise permitted solo work or consultation. Configured depth does not guarantee remaining nesting capacity or a free slot: classify actual tool errors separately from delegation/model permission, retain bounded collection, and name any independent panel coverage that could not run.

Resolve an absolute workspace root using `jj root` from the target directory. Run every subsequent JJ subprocess from that absolute root, e.g. `(cd "$workspace_root" && jj log ...)`. For a non-repository project, retain its absolute project root and use local files as evidence. Repository-scoped `gh` calls run from the target absolute root with `GIT_DIR=$(jj git root)`; no direct Git executable calls.

Freeze one normalized read scope: root plus ordered include/exclude patterns. Pass the identical scope to every peer; do not broaden it. Peers may inspect shared files directly but must not edit or intentionally read outside scope. Prompt-only boundaries are not a confidentiality sandbox. Disclose the content and provider recipients; ask before an unexpected recipient or intermediary receives it, or when active instructions require approval.

Capture a repository-scope identity before dispatch: verified committed revision plus a digest of dirty, ignored, and untracked content in scope. Use JJ and local file processing, never Git. Revalidate before reconciliation and final fold-in. Changed identity requires restarting all voices or reporting incomplete coverage; do not fold stale opinions into the new state.

Use only the resolved private workspace-local `$SCRATCH_DIR` from grounding. Store canonical payloads, logs, receipts, and schema-valid results there with private permissions. Record target, native route, requested model (or inherited), actual model from runtime receipt (otherwise `unverified`), agent/session ID, status, scope identity, and `independence_verified`. Keep `cross_model_harness` in the schema as a compatibility field with value `opencode-native`. A request or a model's self-description is not proof of the served model. Verify independence only from runtime evidence that the serving model family differs from the host; unknown or same-family receipts cannot establish cross-model completeness.

## Independent round

Read `references/agents/pov-peer.md` and `references/pov-schema.json`. Send every peer the identical original subject, framed question, allowed scope, verified grounding, and output contract. Each produces a supported position and evidence, not an implementation. Withhold the host's newly formed verdict and other peers' answers until all initial opinions are complete. When the subject itself is a prior position, include that position as the subject and request an independent underlying verdict. A critique-only request uses `mode: skeptic` and never enters convergence.

Use independent fresh native subagents, parallel where permitted. Preserve source artifacts until validated and consumed. Validate result shape, scope identity, usable final position, receipt attribution, and evidence before fold-in. A non-final placeholder is not a completed opinion. Do not infer a verdict from a tool-success status alone.

Observe each actual launch/result error. Classify separately: delegation permission denial, model-override rejection, missing tool, depth exhaustion, capacity, quota, timeout, authentication, invalid argument, or malformed/non-final output. Check whether an agent launched before any retry. One correction of a pre-launch bad argument is allowed if it changes neither authority nor scope. Never retry a denial through another harness, elevation, or shell engine. A user-named model is never swapped. Depth or missing-tool failures may return bounded work to the authorized parent; inline evidence can support the solo POV but cannot impersonate an independent reviewer. Record incomplete coverage and lower confidence as appropriate. Do not infer account logout from authentication-shaped prose without provider-backed evidence.

Bound each peer and the aggregate panel by the host's available timeout/cancellation mechanisms. On timeout, cancel owned work and preserve the observed failure receipt. A failed peer drops out of later rounds; its old opinion is not a current survivor. No peer blocks delivery of a solo POV.

## Reconcile and decide

Only independent voices enter convergence. Material dissent changes adoption grade, selected approach, required reader action (`proceed`, `revise-first`, `reject`), or whether a risk is fatal; wording differences alone are concurrence.

Default limit: initial round plus at most two reconcile exchanges. A user-supplied finite limit overrides it; one pass means no reconciliation. When initial voices materially dissent, run at least one exchange unless that limit or actual dispatch constraints prevent it; disclose prevented reconciliation as incomplete, not convergence.

For each exchange:
1. Revalidate scope identity and reconsider every position.
2. Verify decision-changing disputed project claims against allowed sources; label them verified, contradicted, or unverifiable with locations.
3. Send each surviving fresh peer the identical complete evidence delta, original subject, and every surviving voice's current reasoning, capped at five source-attributed bullets per voice. No route-specific truncation.
4. Preserve recipients, model intent, scope, authority, and receipts. A new recipient requires approval; unavailable peers are dropped rather than replaced implicitly.

Stop at the first applicable state: `confident` (a reasoned host decision after weighing survivors), `no-movement` (all held and host still uncertain), or `limit-reached` (finite cap exhausted without confidence). Convergence is not a vote. The latter two states require stalemate disclosure, not an invented settled result. Recommend a specific bounded extension only when new evidence or framing could resolve a named material question; otherwise recommend stopping. Further rounds require authorization beyond the existing cap.

Lead with the POV and a compact panel note:
- Confident: state alignment or the dissent and why the host decision prevailed; recommendations added after the panel remain the host's own.
- Stalemate: state survivor positions/movement, dropped voices' last states, evidence gaps versus judgment differences, and whether a bounded extension could help.
- Partial: name surviving/dropped targets and actual failure classifications; disclose unverified independence or unmet required routes.
- No survivor: deliver the solo POV with “cross-model check unavailable or incomplete,” attempted peers, and observed reasons.

Attribute only models that ran and only receipt-supported independence. Same-model opinions can be useful but never satisfy a different-model requirement. Keep detailed receipts in run artifacts while the chat stays decision-relevant. Skeptic mode folds an attributed critique once, discloses whether it changed the result, and does not join convergence.

The panel never mutates the project. Downstream handoff requires all four: the original prompt explicitly authorizes the named action, the result is non-stalemated, inherited scope is preserved, and the action is non-destructive and otherwise authorized. Otherwise return judgment only; the calling workflow owns continuation.

## Cleanup

After consuming results, stop owned agents and remove only this run's private payloads, raw logs, and result artifacts on normal and failure paths. Preserve required receipts/recovery evidence in an authorized durable location before removing originals, verify the copy, and report incomplete cleanup without force-deleting ambiguous content. Never remove another run's files or an entire shared scratch root.
