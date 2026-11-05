# Per-stage routing carriers

A carrier is the prefix string that passes a stage assignment (which model or harness should do that stage's work) to a child skill. LFG has two routable stages, each with its own carrier. This file defines how to detect an assignment, how to resolve its scope and strength, the carrier grammar, the ordered-fallback case, how to strip routing from the feature request, and how each carrier is passed when LFG invokes the child skill.

LFG is otherwise hands-off and never stops to ask. The single question it may ask is the one in scope rule 3 below, and only on an interactive host.

## What is routable

Interpret whether the invoking conversation expresses **semantic intent to assign a pipeline stage** — planning or implementation — to a specific model or harness. This is judgment, not keyword or prompt-token matching: an explicit instruction such as "plan with fable" or "use Codex for implementation" creates an assignment, while a plain mention of Codex, Composer, Fable, or another model/harness in feature content, quoted material, comparison text, or a filename does not. Two pipeline stages are routable, each with its own carrier:

- **Planning** routes to `ce-plan` as a `plan_model:<alias>` carrier. This names the **model** that authors the plan (model elevation) and nothing else. Example aliases: `fable`, `opus`. LFG has no way to pass a harness assignment to planning: an assignment that scopes a *harness* to planning ("plan with codex", "plan on cursor") is **not supported**. Stop and report it as a routing-carrier blocker rather than encoding a harness name as `plan_model:<harness>` or silently falling back.
- **Implementation** routes to `ce-work` as an `implementation_engine` object (grammar below). Its legacy harness identity preserves requested routing intent, not permission to launch another harness. Resolve permitted models with `opencode.models` and execute through native subagents/shell only; never use a cross-harness dispatcher. Configuration remains authoritative for desired models and tiers. Preserve requested-versus-actual route/model reporting, run receipts, bounded recovery, isolation, independence and failure semantics. A required route that native execution cannot satisfy remains incomplete/blocked, not silently equivalent.

These stage instructions explicitly request native delegation when needed, as do the reviewer skills invoked by LFG. Under a host rule permitting user-OR-loaded-skill-requested delegation, this satisfies the skill-requested exception without another approval. It does not override an unconditional prohibition or actual tool denial. Model-selection permission is separate: when a model override needs an explicit user model request, omit the optional model argument unless that request exists, and use a suitable inherited model if allowed. Preserve configured tiers as intent and disclose unmet requirements; separate same-model reviewers do not establish cross-model independence. Verify effective nesting capacity separately (use the setup depth-discovery procedure; a depth of at least 3 must be adopted in the consumer's configuration, not merely bundled with the plugin). Classify actual failures as permission denial, missing tool, model-argument rejection, or depth/capacity limit. Never retry denied dispatch or evade depth through another harness. Use inline or parent-coordinator fallback only where the child's review contract permits it; required unavailable independence or fixed-model coverage remains incomplete and cannot pass LFG's complete-and-evidenced gate.

## Resolve each directive by scope

1. **Scoped directive** — the instruction names the stage ("plan with fable", "codex for implementation", "plan fable, codex work"). Route it to that stage's carrier. Multiple scoped directives may resolve at once, each to its own stage.
2. **Unscoped directive** — a bare model/harness assignment with no stage named ("use fable", "with codex"). Bind it to the **implementation stage only**; never broaden an unscoped directive to planning or to every stage. Disclose the resolved binding in LFG's opening line before step 1 (e.g. "Routing implementation to Codex; planning stays on the session model.").
3. **Unscoped and genuinely ambiguous, human present** — ask exactly **one** upfront question to bind the stage before step 1, then proceed hands-off. Ask only when all three hold: an unscoped directive could credibly belong to more than one stage, mis-binding would be materially costly, and the host is interactive (it exposes a blocking-question tool and is not a `disable-model-invocation`/headless run). In a `disable-model-invocation`/headless run, never ask; apply the implementation default and disclose it. The default path is mandatory: LFG runs from schedulers, loops, and nested orchestrators with no user to answer, so an unresolved directive must always fall to the disclosed default rather than block.

Requirement strength is inferred from the whole instruction, not one word: "use Codex for implementation" is preference-strength (`prefer`); "only use Composer for implementation" is requirement-strength (`require`) because its meaning rejects native fallback.

## Implementation carrier grammar

When implementation resolves to one candidate, retain one transient `implementation_engine` object with exactly these four fields:

- `mode`: `prefer` or `require`
- `target`: exactly one of `codex`, `claude`, `grok`, `cursor`, `composer`, `opencode`, or `antigravity` — a **harness** name, never a model name
- `model`: the explicit model pin, otherwise `null`
- `source`: a caller-visible string saying where the binding came from, identifying the current LFG instruction

A directive that names a bare **model** with no harness (e.g. "use fable", "with opus") is a model *pin*, not a target: encode it as the harness that serves that model family with the alias in `model`. A Claude-family model (`fable`, `opus`, `sonnet`, `haiku`) is `{"target":"claude","model":"<alias>"}`. Never put a model name in `target`. If you cannot map the named model to one of the harnesses above, that is a routing-carrier blocker, not a `null` binding that silently drops the user's instruction.

When the implementation instruction instead names an ordered fallback list, do not truncate it to the scalar carrier (the single-candidate object above). Instead, retain the whole ordered assignment as current-task implementation intent and pass no `implementation_engine:` object. When LFG invokes `ce-work`, that still-active current-task assignment outranks configuration, and `ce-work` normalizes and preflights the candidates in order. This is context scoped to the implementation stage, not plan content. If the host cannot preserve that context across its skill invocation, stop with a routing-carrier blocker rather than silently dropping later candidates.

## Sanitize product input

Remove every routing directive from the feature request that enters planning, keeping the request otherwise unchanged. Never pass the `implementation_engine` object or any removed directive to `ce-plan`, `ce-doc-review`, `ce-code-review`, the settled-decisions brief, or any planning or review **product** input. The carrier is a routing instruction for one stage, not product content or a settled product decision. The `plan_model:<alias>` carrier is the one exception: it is structured routing data handed to `ce-plan` *alongside* the sanitized request, never woven into it. Do not construct a carrier from standing configuration here: when no explicit binding exists for a stage, `ce-work` and `ce-plan` each decide for themselves how to apply still-applicable session/project intent and standing per-checkout configuration.

## Pass the planning carrier at step 1

When a planning-stage directive resolved, prefix the `ce-plan` invocation with its `plan_model:<alias>` carrier. It is structured routing data beside the request, never woven into it, so `ce-plan`'s model elevation authors the plan on the chosen model even in pipeline mode.

## Pass the implementation carrier at step 2

Use `mode:return-to-caller <plan-path-from-step-1>` when no scalar transient carrier exists, including when a retained ordered current-task assignment is still active in context. When the scalar carrier exists, use the exact string-host form `mode:return-to-caller implementation_engine:<compact-json> <plan-path-from-step-1>`.

Serialize its exact `implementation_engine.{mode,target,model,source}` data as compact JSON immediately after the `implementation_engine:` prefix (for example `implementation_engine:{"mode":"prefer","target":"codex","model":null,"source":"lfg-current-turn"}`). This is structured caller data in a portable string any host can pass through, not part of the plan path or implementation prompt. Pass no empty carrier when it does not exist. `ce-work` then resolves a retained ordered current-task assignment when present, otherwise applicable session/project intent and standing per-checkout configuration. LFG is an automatic, headless caller: it never prompts to weaken a requirement-strength route.

The optional `implementation_run:<safe-id>` carrier is recovery-only. Never include it on the initial step-2 call. On the one evidence-reconciliation recovery, place it after the same engine carrier when one existed and before the unchanged plan path: `mode:return-to-caller implementation_run:<safe-id> <plan-path-from-step-1>` or `mode:return-to-caller implementation_engine:<compact-json> implementation_run:<safe-id> <plan-path-from-step-1>`. A safe id matches `^[A-Za-z0-9._-]{1,128}$` and contains at least one non-period character. Reject a malformed or duplicate run/engine carrier instead of launching work.
