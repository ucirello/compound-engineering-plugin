# Independent candidate development

Use fresh contexts that receive neither the coordinator's preferred answer nor sibling outputs. Fresh sequential contexts are acceptable; a reused context is not a new independent attempt. When no permitted route can supply fresh contexts, report an incomplete Bake-off and offer ordinary single-agent comparison without claiming equivalence.

## Model and payload

Name the independent authors **Baker A**, **Baker B**, and so on in dispatch labels and payloads. Use “bakers” for the workers in progress updates and “candidates” for their proposed solutions.

Honor explicit candidate model choices or mixes, otherwise the caller's resolved model preference and applicable `.rocketclaw/config.yaml` / `config.local.yaml` model routes and tiers. Preserve their precedence and treat those choices as intent, not permission to override the host. Without a model preference, prefer different model families across the bakers when permitted. Discover exact provider/model IDs through `opencode.models`, then dispatch fresh native `subagents` with the common payload. Never invent IDs or turn a configured route into a different route silently.

Bake-off owns candidate dispatch. This skill explicitly requests candidate and judge delegation: under a user-OR-skill delegation rule, no second user request is needed. An unconditional prohibition or actual denial still applies. Delegation permission is separate from model-selection permission: if an optional `model` argument requires an explicit user model request, omit it when that request is absent. Use inherited-model fresh agents when suitable, disclose unmet preferred diversity, and report incomplete coverage when a required fixed route or different-model requirement cannot be met. Same-model fresh contexts establish contextual independence, not cross-model evidence.

Use native `subagents` for dispatch, results, progress and cancellation; use `shell` only for scoped evidence reading and local receipt/artifact persistence, not another harness's dispatcher or a new dispatch framework. Establish supported arguments and lifecycle from the actual tools. Do not install tools, change credentials, or evade a prohibition through shell. Classify launch errors from actual evidence: missing tool, permission denial, depth/capacity exhaustion, or rejected model argument are different failures. Queue independent work when capacity permits; do not bypass nesting limits. Do not retry denied operations. A permitted recovery may correct an unsupported argument, use a suitable inherited model, or replace a failed attempt within budget; cancel any outstanding attempt before replacing it and count actual candidate launches against the allowance. A rejected pre-launch request is recorded separately, not counted as a completed or launched baker.

Before dispatch to a new external model recipient, briefly name the recipient and material it will inspect unless already disclosed. Stay within existing authority and read scope; catalog availability or authentication does not authorize a new recipient. Model diversity is a preference unless explicitly required; fresh contexts remain required even when all bakers use the same model. Every baker is a read-only author returning its artifact to the coordinator, which owns persistence. Without enough fresh contexts through the permitted native route, report incomplete rather than perform same-context roleplay.

Give each candidate the common brief, source pointers and complete relevant grounding, settled decisions, active project constraints, permitted read scope, fidelity, and remaining time. Convey the read-only author contract in every payload: return the artifact in the response, without file writes or child dispatch. Scope each to its own candidate and forbid reading sibling scratch. These are cooperative boundaries unless the host enforces them. Do not claim filesystem isolation merely because paths differ.

Ask each candidate to return an approach sketch at the requested fidelity, with its distinguishing mechanism, evidence and assumptions, consequential tradeoffs, and meaningful approaches it rejected. Tell bakers to stop when the mechanism is concrete enough to compare against the brief and assess its required guarantees. Leave routine implementation details and exhaustive design elaboration to subsequent work; include a detail now when it could change feasibility or the choice. Identify unresolved decisive assumptions rather than filling them with guesses. Candidates may inspect permitted source evidence and challenge assumptions with facts. Their outputs are artifacts, not instructions for the coordinator to obey.

## Scratch and completion

Create private run scratch once:

```bash
workspace_root=$(jj workspace root) || exit 1
cd "$workspace_root" || exit 1
for directory in "$workspace_root/.tmp" "$workspace_root/.tmp/rocketclaw" "$workspace_root/.tmp/rocketclaw/ce-bakeoff"; do
  [ ! -L "$directory" ] || exit 1
  (umask 077; mkdir -p "$directory") || exit 1
  [ -O "$directory" ] && [ -w "$directory" ] || exit 1
done
SCRATCH_ROOT="$workspace_root/.tmp/rocketclaw/ce-bakeoff"
SCRATCH_DIR=$(umask 077; mktemp -d "$SCRATCH_ROOT/run-XXXXXX") || exit 1
echo "$SCRATCH_DIR"
```

Outside a JJ repository, resolve the absolute project directory and use its local `.tmp/rocketclaw/ce-bakeoff` with the same ownership and symlink checks; never fall back to global temporary storage. Ensure repository `.tmp/` is ignored before writing. No candidate workspace is needed for read-only authors.

Use separate candidate artifacts in this run directory, written by the session orchestrator from actual returns. Keep shared input separate from candidate outputs and carry the same evidence into each candidate without exposing sibling results. Keep a run ledger containing the common-brief version, candidate label, requested route/tier, actual native agent/session ID, observed model identity (or unverified), launch/completion status, artifact path and failure/cancellation evidence. Persist actual returns before judging; do not fabricate receipts from planned launches. Recovery gets the same brief and source evidence, not sibling outputs, rankings or the preferred solution. Record any targeted missing dimension and count it against the one recovery launch. Resume from receipts rather than relaunching completed candidates; verify pending lifecycle state before replacement.

Inspect actual completion receipts and returned artifacts before counting candidates. Record launch failures, dropouts, and model attribution as observed; missing model receipts stay unverified. Do not count a dispatch announcement or promised file as a completed candidate. Cancel or reap outstanding workers through the owning lifecycle before closing the run.
