# Per-stage routing carriers

A carrier is the prefix string that passes a stage assignment (which model or harness should do that stage's work) to a child skill. LFG has two routable stages, each with its own carrier. This file defines how to detect an assignment, how to resolve its scope and strength, the carrier grammar, the ordered-fallback case, how to strip routing from the feature request, and how each carrier is passed when LFG invokes the child skill.

LFG is otherwise hands-off and never stops to ask. The single question it may ask is the one in scope rule 3 below, and only on an interactive host.

## Native execution and authority

All execution stays in OpenCode: resolve requested model aliases using `opencode.models`, then use native subagents or shell for bounded non-agent commands. Never dispatch another harness or invoke an external agent CLI through shell. Harness assignments below are intent to preserve, not executable routes. Preserve configured model/provider/tier choices as authoritative intent. An explicit other-harness requirement is a compatibility blocker, not permission to dispatch it. A preference may use an inherited suitable native model only with requested-versus-actual identity and unmet intent disclosed. Same-model execution is not cross-model independence.

Check delegation permission, model-override permission, and nesting capacity separately. Loaded skill reviewer instructions satisfy a host user-OR-loaded-skill delegation exception without another user approval. Respect unconditional bans and tool denials. Model overrides require host permission for the explicit user model request; otherwise inherit a suitable model and disclose unmet independence. Distinguish actual depth exhaustion from permission/model rejection and missing tools. Inline fallback requires the child contract to allow it; required unavailable independence leaves coverage incomplete. Never evade limits through shell or another harness.

Depth setup is documentation only: locate existing user configuration with `opencode debug paths` or `opencode debug paths config`, then advise merging integer `experimental.subagent_depth >=3` into existing `~/.config/opencode/opencode.json`, preserving higher values, siblings, and JSONC. Never edit host configuration or create a competing file. Bundled config/plugin installation alone does not enable consumer depth; higher-precedence settings must not lower it.

## What is routable

Interpret whether the invoking conversation expresses **semantic intent to assign a pipeline stage** — planning or implementation — to a specific model or harness. This is judgment, not keyword or prompt-token matching: an explicit instruction such as "plan with fable" or "use Codex for implementation" creates an assignment, while a plain mention of Codex, Composer, Fable, or another model/harness in feature content, quoted material, comparison text, or a filename does not. Two pipeline stages are routable, each with its own carrier:

- **Planning** routes to `ce-plan` as a `plan_model:<alias>` carrier. This names the model that authors the plan and nothing else. Resolve aliases natively with `opencode.models`. Harness assignments to planning are unsupported: stop with a routing-carrier blocker rather than encoding a harness as a model or silently falling back. Neither stage dispatches another harness.
- **Implementation** routes to `ce-work` as an `implementation_engine` object (grammar below). This names the harness and model that write the code.

## Resolve each directive by scope

1. **Scoped directive** — the instruction names the stage ("plan with fable", "codex for implementation", "plan fable, codex work"). Route it to that stage's carrier. Multiple scoped directives may resolve at once, each to its own stage.
2. **Unscoped directive** — a bare model/harness assignment with no stage named ("use fable", "with codex"). Bind it to the **implementation stage only**; never broaden an unscoped directive to planning or to every stage. Disclose the resolved binding in LFG's opening line before step 1 (e.g. "Routing implementation to Codex; planning stays on the session model.").
3. **Unscoped and genuinely ambiguous, human present** — ask exactly **one** upfront question to bind the stage before step 1, then proceed hands-off. Ask only when all three hold: an unscoped directive could credibly belong to more than one stage, mis-binding would be materially costly, and the host is interactive (it exposes a blocking-question tool and is not a `disable-model-invocation`/headless run). In a `disable-model-invocation`/headless run, never ask; apply the implementation default and disclose it. The default path is mandatory: LFG runs from schedulers, loops, and nested orchestrators with no user to answer, so an unresolved directive must always fall to the disclosed default rather than block.

Requirement strength is inferred from the whole instruction, not one word: "use Codex for implementation" is preference-strength (`prefer`); "only use Composer for implementation" is requirement-strength (`require`) because its meaning rejects native fallback.

## Implementation carrier grammar

When implementation resolves to one candidate, retain one transient `implementation_engine` object with exactly these four fields:

- `mode`: `prefer` or `require`
- `target`: `opencode` for execution; retain any other requested harness identity only as unmet intent for compatibility reporting, never as dispatch authorization
- `model`: the explicit model pin, otherwise `null`
- `source`: a caller-visible string saying where the binding came from, identifying the current LFG instruction

A directive that names a bare **model** with no harness (e.g. "use fable", "with opus") is a model pin, not a target: resolve its exact provider/model with `opencode.models` and use `{"target":"opencode","model":"<resolved-provider/model>"}` subject to host model permission. Never infer another harness from a model family. An unavailable required model is a routing-carrier blocker, not a null binding that silently drops the user's instruction.

When the implementation instruction instead names an ordered fallback list, do not truncate it to the scalar carrier (the single-candidate object above). Instead, retain the whole ordered assignment as current-task implementation intent and pass no `implementation_engine:` object. When LFG invokes `ce-work`, that still-active current-task assignment outranks configuration, and `ce-work` normalizes and preflights the candidates in order. This is context scoped to the implementation stage, not plan content. If the host cannot preserve that context across its skill invocation, stop with a routing-carrier blocker rather than silently dropping later candidates.

## Sanitize product input

Remove every routing directive from the feature request that enters planning, keeping the request otherwise unchanged. Never pass the `implementation_engine` object or any removed directive to `ce-plan`, `ce-doc-review`, `ce-code-review`, the settled-decisions brief, or any planning or review **product** input. The carrier is a routing instruction for one stage, not product content or a settled product decision. The `plan_model:<alias>` carrier is the one exception: it is structured routing data handed to `ce-plan` *alongside* the sanitized request, never woven into it. Do not construct a carrier from standing configuration here: when no explicit binding exists for a stage, `ce-work` and `ce-plan` each decide for themselves how to apply still-applicable session/project intent and standing per-checkout configuration.

## Pass the planning carrier at step 1

When a planning-stage directive resolved, prefix the `ce-plan` invocation with its `plan_model:<alias>` carrier. It is structured routing data beside the request, never woven into it, so `ce-plan`'s model elevation authors the plan on the chosen model even in pipeline mode.

## Pass the implementation carrier at step 2

Use `mode:return-to-caller <plan-path-from-step-1>` when no scalar transient carrier exists, including when a retained ordered current-task assignment is still active in context. When the scalar carrier exists, use the exact string-host form `mode:return-to-caller implementation_engine:<compact-json> <plan-path-from-step-1>`.

Serialize its exact `implementation_engine.{mode,target,model,source}` data as compact JSON immediately after the `implementation_engine:` prefix (for example `implementation_engine:{"mode":"prefer","target":"opencode","model":null,"source":"lfg-current-turn"}`). This is structured caller data, not part of the plan path or implementation prompt. Pass no empty carrier when it does not exist. `ce-work` resolves retained ordered current-task assignment first, otherwise applicable session/project intent and standing per-checkout configuration. Never prompt to weaken a requirement-strength route. Other-harness candidates remain non-executable even in ordered lists under the native-execution rule above.

The optional `implementation_run:<safe-id>` carrier is recovery-only. Never include it on the initial step-2 call. On the one evidence-reconciliation recovery, place it after the same engine carrier when one existed and before the unchanged plan path: `mode:return-to-caller implementation_run:<safe-id> <plan-path-from-step-1>` or `mode:return-to-caller implementation_engine:<compact-json> implementation_run:<safe-id> <plan-path-from-step-1>`. A safe id matches `^[A-Za-z0-9._-]{1,128}$` and contains at least one non-period character. Reject a malformed or duplicate run/engine carrier instead of launching work.
