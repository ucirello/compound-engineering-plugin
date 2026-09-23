# Per-stage routing carriers

A carrier is the prefix string that passes a stage assignment (which model or harness should do that stage's work) to a child skill. LFG has two routable stages, each with its own carrier. This file defines how to detect an assignment, how to resolve its scope and strength, the carrier grammar, the ordered-fallback case, how to strip routing from the feature request, and how each carrier is passed when LFG invokes the child skill.

LFG is otherwise hands-off and never stops to ask. The single question it may ask is the one in scope rule 3 below, and only on an interactive host.

## What is routable

Interpret whether the invoking conversation expresses **semantic intent to assign a pipeline stage** — planning or implementation — to a specific model or harness. This is judgment, not keyword or prompt-token matching: an explicit instruction such as "plan with fable" or "use Codex for implementation" creates an assignment, while a plain mention of Codex, Composer, Fable, or another model/harness in feature content, quoted material, comparison text, or a filename does not. Two pipeline stages are routable, each with its own carrier:

- **Planning** routes to `ce-plan` as a `plan_model:<alias>` carrier. This names the **model** that authors the plan (model elevation). Example aliases: `fable`, `opus`. An explicit OpenCode V2 planning assignment uses `plan_harness:opencode` alongside `plan_model:provider/modelname#variant`; never encode a harness name as a model. Other harness assignments without a supported carrier stop as routing-carrier blockers rather than silently falling back to the session model.
- **Implementation** routes to `ce-work` as an `implementation_engine` object (grammar below). This names the harness and model that write the code.

## Resolve each directive by scope

1. **Scoped directive** — the instruction names the stage ("plan with fable", "codex for implementation", "plan fable, codex work"). Route it to that stage's carrier. Multiple scoped directives may resolve at once, each to its own stage.
2. **Unscoped directive** — a bare model/harness assignment with no stage named ("use fable", "with codex"). Bind it to the **implementation stage only**; never broaden an unscoped directive to planning or to every stage. Disclose the resolved binding in LFG's opening line before step 1 (e.g. "Routing implementation to Codex; planning retains its existing routing settings.").
3. **Unscoped and genuinely ambiguous, human present** — ask exactly **one** upfront question to bind the stage before step 1, then proceed hands-off. Ask only when all three hold: an unscoped directive could credibly belong to more than one stage, mis-binding would be materially costly, and the host is interactive (it exposes a blocking-question tool and is not a `disable-model-invocation`/headless run). In a `disable-model-invocation`/headless run, never ask; apply the implementation default and disclose it. The default path is mandatory: LFG runs from schedulers, loops, and nested orchestrators with no user to answer, so an unresolved directive must always fall to the disclosed default rather than block.

Requirement strength is inferred from the whole instruction, not one word: "use Codex for implementation" is preference-strength (`prefer`); "only use Composer for implementation" is requirement-strength (`require`) because its meaning rejects native fallback.

## Implementation carrier grammar

When implementation resolves to one candidate, retain one transient `implementation_engine` object with exactly these four fields:

- `mode`: `prefer` or `require`
- `target`: exactly one of `codex`, `claude`, `grok`, `cursor`, `composer`, or `opencode` — a **harness** name, never a model name
- `model`: the explicit model pin, otherwise `null`
- `source`: a caller-visible string saying where the binding came from, identifying the current LFG instruction

A directive that names a bare **model** with no harness (e.g. "use fable", "with opus") is a model *pin*, not a target: encode it as the harness that serves that model family with the alias in `model`. A Claude-family model (`fable`, `opus`, `sonnet`, `haiku`) is `{"target":"claude","model":"<alias>"}`. Never put a model name in `target`. If you cannot map the named model to one of the harnesses above, that is a routing-carrier blocker, not a `null` binding that silently drops the user's instruction.

When the implementation instruction instead names an ordered fallback list, do not truncate it to the scalar carrier (the single-candidate object above). Instead, retain the whole ordered assignment as current-task implementation intent and pass no `implementation_engine:` object. When LFG invokes `ce-work`, that still-active current-task assignment outranks configuration, and `ce-work` normalizes and preflights the candidates in order. This is context scoped to the implementation stage, not plan content. If the host cannot preserve that context across its skill invocation, stop with a routing-carrier blocker rather than silently dropping later candidates.

## Sanitize product input

Remove every routing directive from the feature request that enters planning, keeping the request otherwise unchanged. Never pass the `implementation_engine` object or any removed directive to `ce-plan`, `ce-doc-review`, `ce-code-review`, the settled-decisions brief, or any planning or review **product** input. A carrier is a routing instruction for one stage, not product content or a settled product decision. Planning carriers (`plan_model:<alias>` and, for OpenCode V2, `plan_harness:opencode`) are structured routing data handed to `ce-plan` *alongside* the sanitized request, never woven into it. Do not construct a carrier from standing configuration here: when no explicit binding exists for a stage, `ce-work` and `ce-plan` each decide for themselves how to apply still-applicable session/project intent and standing per-checkout configuration.

## Pass the planning carrier at step 1

When a planning-stage directive resolved, prefix the `ce-plan` invocation with its `plan_model:<alias>` carrier and, for OpenCode V2, `plan_harness:opencode`. These are structured routing data beside the request, never woven into it, so `ce-plan` authors the plan on the chosen model and harness even in pipeline mode.

## OpenCode V2 delegation

OpenCode is a distinct harness (`opencode`), not an alias for another engine. Pass an explicit OpenCode implementation assignment using `implementation_engine.target: opencode`. Preserve a supplied `provider/model#variant` model pin verbatim; when no model was supplied, retain `model: null` and let `ce-work` resolve it under its routing contract. Child skills own effective `.rocketclaw/config.yaml` plus `config.local.yaml` loading: preserve their explicit subagent and harness settings, including `cross_model_peer: opencode`, `work_engine_preferences: [{harness: opencode, model: provider/model#variant}]`, `plan_model` plus `plan_harness: opencode`, and `brainstorm_model` plus `brainstorm_harness: opencode`. Planning and brainstorming carriers stay beside product input; neither enters the settled-decisions brief.

When the effective merged configuration and current instructions specify no explicit subagent or alternative-harness delegation, the current harness is OpenCode, and `opencode.models` plus native `subagent(model)` are available, the child skill discovers exact IDs and variants with `opencode.models` and delegates through native `subagent` with the exact model reference, preserving any `#variant`. Use no shell delegation under those conditions. Preserve cross-model intent and model tiers; never guess an ID or silently reuse the current model. Otherwise preserve the configured routing behavior. LFG passes this routing context to each affected child; a child that cannot honor an explicit assignment must disclose the blocker rather than dropping it.

## Pass the implementation carrier at step 2

Use `mode:return-to-caller <plan-path-from-step-1>` when no scalar transient carrier exists, including when a retained ordered current-task assignment is still active in context. When the scalar carrier exists, use the exact string-host form `mode:return-to-caller implementation_engine:<compact-json> <plan-path-from-step-1>`.

Serialize its exact `implementation_engine.{mode,target,model,source}` data as compact JSON immediately after the `implementation_engine:` prefix (for example `implementation_engine:{"mode":"prefer","target":"codex","model":null,"source":"lfg-current-turn"}`). This is structured caller data in a portable string any host can pass through, not part of the plan path or implementation prompt. Pass no empty carrier when it does not exist. `ce-work` then resolves a retained ordered current-task assignment when present, otherwise applicable session/project intent and standing per-checkout configuration. LFG is an automatic, headless caller: it never prompts to weaken a requirement-strength route.

The optional `implementation_run:<safe-id>` carrier is recovery-only. Never include it on the initial step-2 call. On the one evidence-reconciliation recovery, place it after the same engine carrier when one existed and before the unchanged plan path: `mode:return-to-caller implementation_run:<safe-id> <plan-path-from-step-1>` or `mode:return-to-caller implementation_engine:<compact-json> implementation_run:<safe-id> <plan-path-from-step-1>`. A safe id matches `^[A-Za-z0-9._-]{1,128}$` and contains at least one non-period character. Reject a malformed or duplicate run/engine carrier instead of launching work.
