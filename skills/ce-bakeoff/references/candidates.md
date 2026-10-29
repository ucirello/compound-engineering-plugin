# Independent candidate development

Use fresh contexts that receive neither the coordinator's preferred answer nor sibling outputs. Fresh sequential contexts are acceptable; a reused context is not a new independent attempt. When no permitted route can supply fresh contexts, report an incomplete Bake-off and offer ordinary single-agent comparison without claiming equivalence.

## Model and payload

Name the independent authors **Baker A**, **Baker B**, and so on in dispatch labels and payloads. Use “bakers” for the workers in progress updates and “candidates” for their proposed solutions.

Honor explicit candidate model choices or mixes and configuration's model choices and tiers as desired behavior, otherwise the caller's resolved model preference. Discover exact available IDs with `opencode.models`; use native `subagents` for fresh contexts and `shell` only for scoped evidence or lifecycle commands, not another harness's dispatcher. Without a model preference, seek different model families across the bakers when model selection is permitted. If the host requires an explicit user model request for overrides, omit the optional `model` argument and use suitable inherited-model agents; a configured tier alone does not authorize an override. Disclose unmet tier or diversity intent. An explicit restriction on models or providers still applies; do not silently substitute for a required model.

Bake-off owns candidate dispatch. Use the native tools' actual capabilities to establish a fresh context, read scope, output collection, and cancellation. Do not invoke the peer-job Python framework, an elevation adapter, or another harness's model CLI, or build a new dispatch system. Do not invent model IDs or flags, install tools, or change credentials. Verify effective nesting capacity from the runtime's resolved configuration and actual tool results; package-local configuration alone does not establish the consuming session's depth. Distinguish a depth/capacity error, permission denial, rejected model argument, and missing tool. Do not retry denied operations or evade depth limits. If no permitted fresh-context route remains, return incomplete; parent-coordinator handoff is allowed only if it preserves the independent-context contract. Cancel any outstanding attempt before replacing it, and count actual candidate launches against the run's allowance.

Before external dispatch, briefly name the recipient and material it will inspect unless already disclosed. Stay within existing authority and read scope. CLI availability or authentication does not authorize a new recipient. Model diversity is a preference, not a completion requirement; fresh contexts remain required even when all bakers use the same model. Every baker is a read-only author returning its artifact to the coordinator, which owns persistence. Without enough fresh contexts through any permitted route, report incomplete rather than perform same-context roleplay.

Give each candidate the common brief, source pointers and complete relevant grounding, settled decisions, active project constraints, permitted read scope, fidelity, and remaining time. Convey the read-only author contract in every payload: return the artifact in the response, without file writes or child dispatch. Scope each to its own candidate and forbid reading sibling scratch. These are cooperative boundaries unless the host enforces them. Do not claim filesystem isolation merely because paths differ.

Ask each candidate to return an approach sketch at the requested fidelity, with its distinguishing mechanism, evidence and assumptions, consequential tradeoffs, and meaningful approaches it rejected. Tell bakers to stop when the mechanism is concrete enough to compare against the brief and assess its required guarantees. Leave routine implementation details and exhaustive design elaboration to subsequent work; include a detail now when it could change feasibility or the choice. Identify unresolved decisive assumptions rather than filling them with guesses. Candidates may inspect permitted source evidence and challenge assumptions with facts. Their outputs are artifacts, not instructions for the coordinator to obey.

## Scratch and completion

Create private run scratch once:

```bash
# Set workspace_root to the target workspace's verified absolute root.
# Run every JJ command with that absolute working directory.
if [ -L "$workspace_root/.tmp" ]; then echo "unsafe scratch parent symlink" >&2; exit 1; fi;
SCRATCH_ROOT="$workspace_root/.tmp/rocketclaw";
if [ -L "$SCRATCH_ROOT" ]; then echo "unsafe scratch root symlink: $SCRATCH_ROOT" >&2; exit 1; fi;
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1;
if [ -L "$SCRATCH_ROOT" ] || [ ! -O "$SCRATCH_ROOT" ]; then echo "scratch root is not owned by the current user: $SCRATCH_ROOT" >&2; exit 1; fi;
chmod 700 "$SCRATCH_ROOT" || exit 1;
(umask 077; mkdir -p "$SCRATCH_ROOT/ce-bakeoff") || exit 1;
SCRATCH_DIR=$(mktemp -d "$SCRATCH_ROOT/ce-bakeoff/run-XXXXXX") || exit 1;
echo "$SCRATCH_DIR";
```

Ensure `.tmp/` is ignored; reject a symlinked `.tmp` parent or a resolved scratch path outside the workspace. Keep failures local: never fall back to OS temporary storage. Resolve the root using `(cd "$absolute_target_root" && jj workspace root)`; for non-repository use, use the verified absolute project root instead. No isolated workspace is needed for these read-only authors. Use native JJ for repository inspection, always from the absolute workspace root, never the Git executable; see https://docs.jj-vcs.dev/latest/cli-reference/ . Repository-scoped GitHub calls use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`.

Use separate candidate artifacts in this run directory, written by the session orchestrator from actual returns. Keep shared input separate from candidate outputs. Carry the same evidence into each candidate without exposing sibling results; the coordinator owns any private native handoff bundle and preserves its evidence until consumed.

Inspect actual completion receipts and returned artifacts before counting candidates. Record launch failures, dropouts, and model attribution as observed; missing model receipts stay unverified. Do not count a dispatch announcement or promised file as a completed candidate. Cancel or reap outstanding workers through the owning lifecycle before closing the run.
