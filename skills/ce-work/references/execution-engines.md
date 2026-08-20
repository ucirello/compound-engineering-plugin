# Execution Engines

`ce-work` selects inline/subagent, goal-mode, dynamic-workflow, or cross-model execution for code work. Engine choice changes implementation authorship, never shipping-tail ownership.

Resolve routing from the host instruction hierarchy, then within equal authority prefer narrower/current sources: current task, active session intent, typed caller binding, active project conventions, enabled checkout configuration, then native execution. Incidental route words do not activate routing. Conflicting equal-authority directions block guessing.

A live route request is `prefer` unless strict intent makes it `require`. Preserve ordered candidate lists. A typed caller binding contains exactly `mode`, `target`, `model`, and `source`; it remains scalar and enters only at the `ce-work` return-to-caller seam. Recovery adds a separate safe `implementation_run` carrier.

Targets remain `codex`, `claude`, `grok`, `cursor`, and `composer`. Keep target, route/intermediary, requested model, served model, and receipt status distinct. Same-host default with no distinct model collapses to native execution.

Standing configuration uses `work_engine_mode: off|prefer|require` and ordered `work_engine_preferences` objects from `.workflow/config.local.yaml` then `.workflow/config.yaml`. Each object has `harness` and optional `model`. Configuration carries intent, never shell flags. Traverse candidates until the first qualified route; after dispatch, stop traversal.

An engine is usable only when the host exposes its callable capability. Inline/subagent is always available. Goal-mode requires a callable goal tool; a user-only command is not callable. Dynamic workflow requires a callable orchestration primitive. Cross-model execution requires a qualified fixed adapter satisfying every restriction. Missing one binary is evidence about one adapter, not the whole capability surface.

Choose by plan shape: ordinary sequential/shared work uses inline/subagent; large independent fan-out may use dynamic workflow or parallel isolated subagents; cross-model execution applies when higher-authority routing selects it. Bare prompts require grounded goal, scope, and verification first.

Goal-mode and dynamic-workflow never own publishing. On hosts without callable support, standalone interactive use may emit one copyable prompt and continue natively if unused; return-to-caller cannot strand its caller with a copy/paste handoff.

After any engine completes, inspect the Jujutsu change and continue the owning tail. Progress stays in task state, described Jujutsu changes, and envelopes, never in the plan body.
