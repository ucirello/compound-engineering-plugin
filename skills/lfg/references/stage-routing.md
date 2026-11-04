# Per-stage routing carriers

A carrier is the prefix string that passes a stage assignment (which model or harness should do that stage's work) to a child skill. LFG has two routable stages, each with its own carrier. This file defines how to detect an assignment, how to resolve its scope and strength, the carrier grammar, the ordered-fallback case, how to strip routing from the feature request, and how each carrier is passed when LFG invokes the child skill.

LFG is otherwise hands-off and never stops to ask. The single question it may ask is the one in scope rule 3 below, and only on an interactive host.

## What is routable

Interpret whether the invoking conversation expresses **semantic intent to assign a pipeline stage** — planning or implementation — to a specific model or harness. This is judgment, not keyword or prompt-token matching: an explicit instruction such as "plan with fable" or "use Codex for implementation" creates an assignment, while a plain mention of Codex, Composer, Fable, or another model/harness in feature content, quoted material, comparison text, or a filename does not. Two pipeline stages are routable, each with its own carrier:

- **Planning** routes to `ce-plan` as a `plan_model:<alias>` carrier. This names the requested model, not an external harness. Resolve it through native OpenCode `opencode.models` discovery and native subagents. An explicit external-harness requirement is unsupported: report a routing-carrier blocker rather than launching another harness or silently changing the requirement.
- **Implementation** routes to `ce-work` as an `implementation_engine` compatibility object (grammar below), executed only through native OpenCode model discovery and subagents, never an external-harness dispatcher.

## Resolve each directive by scope

1. **Scoped directive** — the instruction names the stage ("plan with fable", "codex for implementation", "plan fable, codex work"). Route it to that stage's carrier. Multiple scoped directives may resolve at once, each to its own stage.
2. **Unscoped directive** — a bare model/harness assignment with no stage named ("use fable", "with codex"). Bind it to the **implementation stage only**; never broaden an unscoped directive to planning or to every stage. Disclose the resolved native model route, or unavailable external-harness route, in LFG's opening line before step 1; planning stays on the session model.
3. **Unscoped and genuinely ambiguous, human present** — ask exactly **one** upfront question to bind the stage before step 1, then proceed hands-off. Ask only when all three hold: an unscoped directive could credibly belong to more than one stage, mis-binding would be materially costly, and the host is interactive (it exposes a blocking-question tool and is not a `disable-model-invocation`/headless run). In a `disable-model-invocation`/headless run, never ask; apply the implementation default and disclose it. The default path is mandatory: LFG runs from schedulers, loops, and nested orchestrators with no user to answer, so an unresolved directive must always fall to the disclosed default rather than block.

Requirement strength is inferred from the whole instruction, not one word: "use Codex for implementation" is preference-strength (`prefer`); "only use Composer for implementation" is requirement-strength (`require`) because its meaning rejects native fallback.

## Implementation carrier grammar

When implementation resolves to one candidate, retain one transient `implementation_engine` object with exactly these four fields:

- `mode`: `prefer` or `require`
- `target`: exactly one of `codex`, `claude`, `grok`, `cursor`, `composer`, `opencode`, or `antigravity` — a **harness** name, never a model name
- `model`: the explicit model pin, otherwise `null`
- `source`: a caller-visible string saying where the binding came from, identifying the current LFG instruction

A directive naming a bare **model** is a model pin: discover its exact provider/model ID through `opencode.models` and encode `{"target":"opencode","model":"<resolved-provider/model>"}`. The other target names above are compatibility vocabulary only, not authorization to run their CLIs or dispatchers. An explicit requirement for another harness blocks; a preference can fall back natively only with requested-versus-actual disclosure. Never silently discard a model pin or requirement.

Native delegation requested by this loaded skill is permission to delegate unless higher policy or an actual denial forbids it; do not ask again. Model override permission is separate: where an explicit user model request is required, configuration tiers alone do not authorize a model argument. Preserve layered `config.yaml`, `config.local.yaml`, and example-config choices and tiers as intent, disclose unavailable routes, and use inherited models only when the contract permits. Same-model distinct reviewers are not cross-model independence; missing required coverage is incomplete. Discover nesting configuration separately from permission: package defaults and the consuming global OpenCode configuration must provide `experimental.subagent_depth` as an integer at least 3. Document merging that setting into the existing `~/.config/opencode/opencode.json` (or actual global location found through `opencode debug paths` / `opencode debug paths config`), preserving sibling settings and higher depth, without creating a competing JSON/JSONC file; package installation alone does not enable it. Respect higher-precedence configuration. Distinguish actual depth/capacity errors from denied delegation, model rejection, and missing tools. Never bypass denial. Preserve unit receipts, exact source/head evidence, one bounded reconciliation retry, and truthful independence/coverage reporting through native execution.

When the implementation instruction instead names an ordered fallback list, do not truncate it to the scalar carrier (the single-candidate object above). Instead, retain the whole ordered assignment as current-task implementation intent and pass no `implementation_engine:` object. When LFG invokes `ce-work`, that still-active current-task assignment outranks configuration, and `ce-work` normalizes and preflights the candidates in order. This is context scoped to the implementation stage, not plan content. If the host cannot preserve that context across its skill invocation, stop with a routing-carrier blocker rather than silently dropping later candidates.

## Sanitize product input

Remove every routing directive from the feature request that enters planning, keeping the request otherwise unchanged. Never pass the `implementation_engine` object or any removed directive to `ce-plan`, `ce-doc-review`, `ce-code-review`, the settled-decisions brief, or any planning or review **product** input. The carrier is a routing instruction for one stage, not product content or a settled product decision. The `plan_model:<alias>` carrier is the one exception: it is structured routing data handed to `ce-plan` *alongside* the sanitized request, never woven into it. Do not construct a carrier from standing configuration here: when no explicit binding exists for a stage, `ce-work` and `ce-plan` each decide for themselves how to apply still-applicable session/project intent and standing per-checkout configuration.

## Pass the planning carrier at step 1

When a planning-stage directive resolved, prefix the `ce-plan` invocation with its `plan_model:<alias>` carrier. It is structured routing data beside the request, never woven into it, so `ce-plan`'s model elevation authors the plan on the chosen model even in pipeline mode.

## Pass the implementation carrier at step 2

Use `mode:return-to-caller <plan-path-from-step-1>` when no scalar transient carrier exists, including when a retained ordered current-task assignment is still active in context. When the scalar carrier exists, use the exact string-host form `mode:return-to-caller implementation_engine:<compact-json> <plan-path-from-step-1>`.

Serialize its exact `implementation_engine.{mode,target,model,source}` data as compact JSON immediately after the `implementation_engine:` prefix (for example `implementation_engine:{"mode":"prefer","target":"codex","model":null,"source":"lfg-current-turn"}`). This is structured caller data in a portable string any host can pass through, not part of the plan path or implementation prompt. Pass no empty carrier when it does not exist. `ce-work` then resolves a retained ordered current-task assignment when present, otherwise applicable session/project intent and standing per-checkout configuration. LFG is an automatic, headless caller: it never prompts to weaken a requirement-strength route.

The optional `implementation_run:<safe-id>` carrier is recovery-only. Never include it on the initial step-2 call. On the one evidence-reconciliation recovery, place it after the same engine carrier when one existed and before the unchanged plan path: `mode:return-to-caller implementation_run:<safe-id> <plan-path-from-step-1>` or `mode:return-to-caller implementation_engine:<compact-json> implementation_run:<safe-id> <plan-path-from-step-1>`. A safe id matches `^[A-Za-z0-9._-]{1,128}$` and contains at least one non-period character. Reject a malformed or duplicate run/engine carrier instead of launching work.
