# Evidence and Delegation

Read before grounding or delegation on the full path. The skill body owns interaction and completion; this reference owns the run directory, the evidence pass, and capability fallbacks.

## Interaction method

The skill body's interaction rule decides whether a question is needed. When it is, use the host's question capability already in the current tool list; never call a user-facing question tool to discover whether it exists. If no such tool is available, ask in chat only when a person is participating. Otherwise return the missing information to the calling workflow.

## Model tiers

Use OpenCode's native `opencode.models` lookup and `subagent` tool. Scout work is search and extraction; composition, including `Check yourself`, stays in the main conversation.

For a scout, prefer a model specified by the user or project for that dispatch, tier, or prompt asset, then a role-configured model, then the cheapest capable model from OpenCode's live model list. Resolve overrides to a listed provider/model ID and pass it to `subagent`. If native per-agent selection is unavailable, inherit the current model without changing the scout's budget.

Dispatch with `agent: "general"` when listed and a self-contained prompt seeded from the scout asset. Effective `experimental.subagent_depth` must be at least `3` for deep delegation; if configuration blocks it, report that prerequisite rather than editing configuration.

**Degradation rule.** On a concurrency or active-agent limit, retry once after a slot frees. Correct a fixable invocation error once. If delegation is unavailable or still fails, perform only the affected scout's work inline with the same sources, budget, and dossier contract, and disclose the fallback in one line.

## Run directory

Set `$scratch_base` to the verified absolute JJ workspace root, or, outside JJ, the absolute local working directory. Create `$RUN_DIR` under its `.tmp/` before writing an artifact or scout dossier. Run this block from that absolute directory. If local scratch cannot be created safely, report the blocker rather than falling back outside it.

```bash
case "$scratch_base" in /*) ;; *) exit 1 ;; esac
SCRATCH_ROOT="${scratch_base:?set the absolute scratch base}/.tmp"
[ ! -L "$SCRATCH_ROOT" ] || exit 1
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1
[ ! -L "$SCRATCH_ROOT" ] && [ -d "$SCRATCH_ROOT" ] && [ -O "$SCRATCH_ROOT" ] && [ -w "$SCRATCH_ROOT" ] || exit 1
RUN_DIR="$(umask 077; mktemp -d "$SCRATCH_ROOT/ce-explain-XXXXXXXX")" || exit 1
printf '%s\n' "$RUN_DIR"
```

## Grounding by input shape

**Repo-touching inputs** (a concept with footprint in this repo, a diff, a recap): read `references/repository-evidence.md`. Use the project's active instructions already in context and go directly to the diff, call-sites, current source, or commits. Read `CONCEPTS.md` when canonical vocabulary matters. If the topic cannot be scoped from the input and existing context, allow one targeted root or workspace probe.

**Diff mode:** resolve the change (the `diff:` ref, or the most recent substantial change when the request points at one implicitly) and gather its evidence — the diff itself, the files it touches, any plan or solution doc that motivated it. **Empty range** or missing subject: do not silently explain something else. Report that before explaining an adjacent thing. Use a substitute only when the request permits it or the user agrees; name the substitution in the result and artifact `Subject` when present. Otherwise return the unresolved scope to the caller.

**Recap mode:** Do not pre-scan, count, or characterize the window in the main conversation. Dispatch a scout with `references/agents/work-recap-scout.md`, the repository-evidence rules, the resolved window, the absolute workspace root, and `$RUN_DIR`. It returns an evidence summary with commit IDs and `file:line` pointers, and writes `recap-evidence.md`. **Empty window:** report the absence of activity and finish without an explainer artifact. Apply the degradation rule if needed; on either path, form no view of the window until the scout evidence is complete.

**External concepts** (no footprint in this repo): skip repo grounding entirely — do not force repo context into the output. Research with whatever web tools are reachable. When none are, you may explain from model knowledge, but label that content **Unverified — from model knowledge, not checked against current sources** in the response or artifact metadata.

**Idea mode:** the idea is a fixed given. Explain its implications, mechanics, and trade-offs for the user's understanding. Never scope it (`ce-brainstorm`'s job), never generate and rank alternatives (`ce-ideate`'s job).

## Behavior and rationale

For a how question, trace the relevant trigger through its state changes, ownership boundaries, and effect. Inspect actual source and relevant tests; a filename or conversation claim does not establish behavior. Preserve the conditions and failure paths that matter to the requested use.

One pass is enough when that trace can name those boundaries without hand-waving. When one pass cannot, split the question into one slice per ownership boundary the answer depends on and dispatch a behavior-trace scout for each slice. Seed each scout with `references/agents/behavior-trace-scout.md`, the question, its slice, the absolute workspace root and repository-evidence rules, and a distinct dossier path under `$RUN_DIR`. Dispatch the slices together. Two slices is the smallest split. More than four means the question is still unscoped: narrow it and trace again rather than adding scouts. Read each dossier from its path, and reconcile overlap or contradiction by reading the source. A gist is not the trace.

For a why question, look for the decision record: motivating docs, comments, JJ history, PR discussions, or linked issues. Follow evidence to available sources when the local record cannot answer the question, within the request's source restrictions. Access to team chat is not permission to search it when the calling workflow makes that opt-in. Expand investigation to resolve material gaps, not to satisfy a source quota.

Code shows behavior, not necessarily intent. Cite documented reasons separately from supported inferences; report contradictions and unknowns. A missing search result does not prove there was no reason. Establish whether a historical constraint still applies before presenting it as a current requirement. When the explanation informs a change, make the relevant constraints and unresolved risks usable by that next step without selecting an approach for it.
