# Evidence and Delegation

Read before grounding or delegation. The skill body owns interaction, completion, and scratch creation; this reference owns the evidence pass and capability fallbacks.

## Interaction method

The skill body's interaction rule decides whether a question is needed. When it is, use the host's question capability already in the current tool list; never call a user-facing question tool to discover whether it exists. If no such tool is available, ask in chat only when a person is participating. Otherwise return the missing information to the calling workflow.

## Model tiers

Dispatch is tiered by task shape, never hardcoded to a model name:

- **Extraction tier** — the work-recap scout and each behavior-trace scout: search-and-quote work. The cheapest capable model is the desired tier; inherit unless the user explicitly requests a model and the host permits that override.
- **Ceiling tier** — the explainer composition, including its `Check yourself` section. This runs in the main conversation on the orchestrator's model; nothing is dispatched for it.

Configured role choices and tiers remain desired intent. When the user explicitly requests a model and the host permits selection, resolve it with `opencode.models` and use the native subagent tool. Do not pass a model argument merely because project configuration or this skill suggests one. Suitable inherited-model scouts can perform this extraction; disclose any unmet fixed-route requirement and never claim cross-model independence from same-model scouts.

**Delegation and degradation rule.** This skill explicitly requests native scout subagents, satisfying a host rule that permits delegation on user OR skill request; no second approval is needed under that rule. An unconditional higher-priority prohibition or actual permission denial still wins. Do not bypass it with shell or another harness, or repeat denied calls. When no native subagent tool is available, run the scout work inline with the same budgets. Classify launch failures from the actual error: concurrency backpressure may wait for a slot; exhausted nesting depth, model-argument rejection, missing tools, and permission denial are distinct. For an unavailable or prohibited dispatch, use inline extraction only if the host permits that work, disclose the fallback in one line, and retain the same budgets and any incomplete evidence coverage. Do not evade nesting limits. Permission to delegate does not establish remaining nesting capacity.

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

For a why question, look for the decision record: motivating docs, comments, JJ history, PR discussions, or linked issues. Run JJ from the target workspace's absolute root; use `jj log` with full descriptions at the verified relevant history head. Repository-scoped GitHub CLI calls use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh <arguments>)`. Never invoke Git directly. Follow evidence to available sources when the local record cannot answer the question, within the request's source restrictions. Access to team chat is not permission to search it when the calling workflow makes that opt-in. Expand investigation to resolve material gaps, not to satisfy a source quota.

Code shows behavior, not necessarily intent. Cite documented reasons separately from supported inferences; report contradictions and unknowns. A missing search result does not prove there was no reason. Establish whether a historical constraint still applies before presenting it as a current requirement. When the explanation informs a change, make the relevant constraints and unresolved risks usable by that next step without selecting an approach for it.
