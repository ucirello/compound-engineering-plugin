# Evidence and Delegation

Read before grounding or delegation. The skill body owns interaction, completion, and scratch creation; this reference owns the evidence pass and capability fallbacks.

## Interaction method

The skill body's interaction rule decides whether a question is needed. When it is, use the host's question capability already in the current tool list; never call a user-facing question tool to discover whether it exists. If no such tool is available, ask in chat only when a person is participating. Otherwise return the missing information to the calling workflow.

## Model tiers

Dispatch is tiered by task shape, never hardcoded to a model name:

- **Extraction tier** — the work-recap scout and each behavior-trace scout: search-and-quote work. Use the platform's cheapest capable model when the harness exposes a known override; otherwise inherit.
- **Ceiling tier** — the explainer composition, including its `Check yourself` section. This runs in the main conversation on the orchestrator's model; nothing is dispatched for it.

Configured role models and tiers remain authoritative intent. Resolve available models with `opencode.models` and use native subagents, never another harness. Apply overrides only when host policy permits them, including any explicit-user-model-request requirement; otherwise inherit a suitable model and disclose unmet configured intent. Project or skill settings do not override host policy.

**Permission and degradation.** These scout instructions explicitly authorize delegation where the host allows user-or-loaded-skill authorization; do not request redundant approval. Respect unconditional bans and tool denials. Evaluate delegation permission, model permission, and nesting capacity separately. When per-agent model selection is unavailable or forbidden, inherit a suitable model and keep read budgets. When native delegation is unavailable, denied, or actual depth is exhausted, run scout work inline with the same budgets and disclose the specific limitation. Concurrency limits are backpressure: retry after a slot frees. Correct invalid invocations, but never evade limits with shell dispatch or another harness. Missing tools and permission/model rejection are not depth exhaustion. Same-model scouts are not cross-model independence; disclose missing required independence or evidence coverage.

Installation guidance only: locate the user's existing config with `opencode debug paths` (or `opencode debug paths config`) and document merging integer `experimental.subagent_depth >= 3` into `~/.config/opencode/opencode.json`. Preserve higher values, JSONC, siblings and unrelated settings; do not create competing files or edit host config. Bundled config/plugin installation alone does not enable depth, and higher-precedence settings must not lower it.

Execute all JJ operations from the absolute target workspace cwd, never merely with `-R`; use JJ history and diff operations rather than the Git executable. Resolve requested base/head and refs exactly, report unresolved or empty ranges without substitution. Scope GitHub CLI calls as `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`.

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

Code shows behavior, not necessarily intent. Cite documented reasons separately from supported inferences; report contradictions and unknowns. A missing search result does not prove there was no reason. Establish whether a historical constraint still applies before presenting it as a current requirement. When the explanation informs a change, make the relevant constraints and unresolved risks usable by that next step without selecting an approach for it.
