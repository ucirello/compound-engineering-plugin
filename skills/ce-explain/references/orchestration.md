# Evidence and Delegation

Read before grounding or delegation. The skill body owns interaction, completion, and scratch creation; this reference owns the evidence pass and capability fallbacks.

## Interaction method

The skill body's interaction rule decides whether a question is needed. When it is, use the host's question capability already in the current tool list; never call a user-facing question tool to discover whether it exists. If no such tool is available, ask in chat only when a person is participating. Otherwise return the missing information to the calling workflow.

## Model tiers

Dispatch is tiered by task shape, never hardcoded to a model name:

- **Extraction tier** — the work-recap scout and each behavior-trace scout: search-and-quote work. Use OpenCode's `opencode.models` to resolve the cheapest capable configured route when model selection is permitted; otherwise inherit.
- **Ceiling tier** — the explainer composition, including its `Check yourself` section. This runs in the main conversation on the orchestrator's model; nothing is dispatched for it.

If the user's or project's active instructions or the live prompt name a model for this subagent, prefer that model over the default tier above, subject to the host's model-selection permissions. They can name it by the subagent's tier, by its prompt-asset name, or for the subagents being dispatched. Without such an instruction, a model configured for this subagent's role takes precedence over the default tier. Configuration remains the source of route intent, not permission to override the host: when overrides require an explicit user model request, omit the optional `model` argument and use a suitable inherited model. Disclose any unmet required route; same-model scouts do not establish cross-model independence.

Use native OpenCode subagents for the explicit scout dispatches here. Under a user-or-loaded-skill delegation rule, these instructions satisfy the skill-requested exception without a second approval. Respect unconditional prohibitions and actual denials; never bypass them with shell or another harness. Verify effective delegation depth separately from permission using the runtime configuration inspection procedure; permission alone does not imply remaining capacity.

**Degradation rule.** When model selection is unavailable or forbidden, dispatch suitable inherited-model scouts and keep their read budgets. When no subagent tool exists or delegation is prohibited, run the scout work inline with the same budgets and disclose the limitation. Classify actual launch errors separately as concurrency backpressure, nesting-depth exhaustion, permission denial, model-argument rejection, or missing capability. Wait for a slot only for backpressure; do not retry denied delegation or evade depth limits. Correct an allowed invocation error or use the inline fallback, disclosed in one line. Never describe inline work as an independent pass or an unmet required route as complete.

A generic subagent is one whose whole brief is the prompt you send it. When the host's subagent tool makes you name an agent, use only a name you have seen the host list, and list its agents before the first dispatch if you have not. Pick the plain one that adds no role of its own, which still counts as a generic subagent. Never pick a specialist, such as a reviewer or worker agent, whose own role prompt, output format, or tool limits would replace or narrow your prompt.

## Run directory

The skill body carries the ownership-checked block that creates `$RUN_DIR`; run it from there so this file cannot drift from it.

## Grounding by input shape

**Repo-touching inputs** (a concept with footprint in this repo, a diff, a recap): use the project's active instructions already in context and go directly to the diff, call-sites, current source, or commits. Read `CONCEPTS.md` when canonical vocabulary matters. If the topic cannot be scoped from the input and existing context, allow one targeted root or workspace probe.

**Diff mode:** resolve the change (the `diff:` ref, or the most recent substantial change when the request points at one implicitly) and gather its evidence — the diff itself, the files it touches, any plan or solution doc that motivated it.

**Recap mode:** seed the scout with `references/agents/work-recap-scout.md` (extraction tier), passing the resolved window, the repo root, and `$RUN_DIR`. It returns an evidence summary with commit shas and `file:line` pointers, and writes `recap-evidence.md`. **Empty window** follows the skill body: report the absence of activity without an explainer artifact.

**External concepts** (no footprint in this repo): skip repo grounding entirely — do not force repo context into the output. Research with whatever web tools are reachable. When none are, you may explain from model knowledge, but label that content **Unverified — from model knowledge, not checked against current sources** in the response or artifact metadata.

**Idea mode:** the idea is a fixed given. Explain its implications, mechanics, and trade-offs for the user's understanding. Never scope it (`ce-brainstorm`'s job), never generate and rank alternatives (`ce-ideate`'s job).

## Behavior and rationale

For a how question, trace the relevant trigger through its state changes, ownership boundaries, and effect. Inspect actual source and relevant tests; a filename or conversation claim does not establish behavior. Preserve the conditions and failure paths that matter to the requested use.

One pass is enough when that trace can name those boundaries without hand-waving. When one pass cannot, split the question into one slice per ownership boundary the answer depends on and dispatch a behavior-trace scout for each slice. Read `references/agents/behavior-trace-scout.md` and seed a generic subagent at the extraction tier with the question, its slice, and a distinct dossier path under `$RUN_DIR`. Dispatch the slices together. Two slices is the smallest split. More than four means the question is still unscoped: narrow it and trace again rather than adding scouts. Read each dossier from its path, and reconcile overlap or contradiction by reading the source. A gist is not the trace.

For a why question, look for the decision record: motivating docs, comments, JJ history, PR discussions, or linked issues. Follow evidence to available sources when the local record cannot answer the question, within the request's source restrictions. Access to team chat is not permission to search it when the calling workflow makes that opt-in. Expand investigation to resolve material gaps, not to satisfy a source quota.

Use native JJ history and diff operations, never the Git executable (including read-only fallbacks); see https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-command-table/. Preserve the exact verified revision or range requested. Run commands from the target workspace's absolute root. For repository-scoped PR or issue queries, use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)` with the actual `gh` arguments.

Code shows behavior, not necessarily intent. Cite documented reasons separately from supported inferences; report contradictions and unknowns. A missing search result does not prove there was no reason. Establish whether a historical constraint still applies before presenting it as a current requirement. When the explanation informs a change, make the relevant constraints and unresolved risks usable by that next step without selecting an approach for it.
