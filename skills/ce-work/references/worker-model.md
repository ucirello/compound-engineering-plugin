# Choosing the model for a native worker

Read this before dispatching the first native implementation worker. It decides the model each worker runs on. The orchestrator keeps the session model, and so does every unit that runs inline. A cross-model unit takes its model from its route, not from this file.

**Pick the tier per unit, from the unit itself.** Decide it while you plan the wave and record it with the unit in the task list, so each dispatch passes the tier you chose for that unit.

- **Mid-tier** when the unit's plan section settles what to build: its Files, Approach, and test scenarios leave no design choice open, and the plan lists every file the change touches. Pass the balanced mid-tier model: the host's general-purpose model one tier below its most capable one, not its smallest or fastest.
- **Session model** (no override) for every other unit: one that leaves the approach open, changes a contract other code depends on, needs debugging or investigation to find the change, or spans several subsystems. When you cannot tell which kind a unit is, it gets the session model.

Do not use a model cheaper than mid-tier. Cheaper models take more turns on multi-step work and end up costing more. When the session model is itself mid-tier or cheaper, every worker gets the session model with no override.

**Take the model name from OpenCode, not from memory.** When override is permitted, discover an exact provider/model and supported variant with `opencode.models`, and check that the subagent tool accepts it. If the host requires an explicit user model request and none exists, omit the `model` argument even if the skill or project suggests one. Use suitable inherited execution and disclose unmet fixed-model or tier requirements; same-model workers are not cross-model evidence.

When the tool and authority allow a reasoning effort with an override, pass the session effort as the supported native variant. Do not claim an unsupported effort.

Subject to override permission, the model named by active user or project instructions overrides the default tier; otherwise a configured role model takes precedence over the default tier.

**No model selector.** On a host whose subagent tool takes no model or custom-agent selector, omit the override and let every worker inherit the session model. Naming a model in the worker's prompt does not change the model it runs on.

**Rejected model value.** When an actual pre-launch argument/model rejection (not denial or a possible launch) makes an optional override unusable, correct it once by omitting the override if the inherited model is suitable. Do not try another model; report the rejection. Permission denial, depth exhaustion and missing tool are distinct outcomes; follow `references/execution-strategy.md`, not this retry.

**Escalate once on reasoning, not on environment.** Escalate when a mid-tier worker reports it could not work out how to build the unit, or when its change fails verification and the failure is not caused by a missing credential, tool, service, or other fact outside the code. Retire that worker without sending it a correction, and give the unit to one fresh worker on the session model. That worker starts from the first worker's changes in the workspace and gets the unit packet plus what the first worker reported. It may undo those changes within the unit's files. A step the first worker held because the environment blocked it is not a reason to escalate.
