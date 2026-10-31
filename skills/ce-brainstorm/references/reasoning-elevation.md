# Model elevation

Elevation sends approach generation (or ce-plan's interpret-then-author step) to the user-chosen model. Dialogue, research, orchestration, persistence and handoffs remain with the session orchestrator. The ce-brainstorm integration-check consult remains deferred.

## Activation resolution

Resolve in order: explicit current user instruction, caller-carried preference and restrictions, then `brainstorm_model` (`plan_model` for ce-plan). Reuse the absolute repository root resolved with `jj workspace root`; read `.rocketclaw/config.local.yaml` before `.rocketclaw/config.yaml` using the ordinary-key rules in SKILL.md. Ignore commented keys. Missing or invalid settings select no elevation. Explicit opt-outs win. If the session already serves the chosen model, skip dispatch; still acknowledge an explicit user request.

For ce-bakeoff, pass the resolved preference and restrictions to that skill with the full dossier, relevant dialogue, question, settled decisions, budget and product-mechanism fidelity. It owns candidate dispatch and fallback; do not additionally generate ordinary approaches for the same question.

## Native dispatch

Use `opencode.models` to resolve the requested model to an exact available provider/model ID, preserving configured tiers and restrictions. Dispatch one native subagent; never invoke another harness CLI or a dispatch script through shell. This skill explicitly requests that subagent, satisfying a host rule permitting user-OR-skill-requested delegation, but never an unconditional prohibition.

Delegation permission, permission to override the model, and remaining nesting depth are independent. If model overrides require an explicit user model request and none exists, omit the model argument and use a suitable inherited model; disclose the unmet elevation rather than pretending it ran. If independent different-model coverage is required but unavailable, mark it incomplete. A separate inherited-model agent does not establish cross-model independence.

Give the elevated agent repository read access and multiple turns to verify its brief. Explicitly deny writes and shell in its instructions; if the tool cannot enforce those restrictions, disclose that they are instructional. Store the prompt and evidence together in one private per-run directory under the absolute workspace's `.tmp/rocketclaw/`; outside a JJ repository use the current project's local `.tmp/`. Pass absolute file paths for the grounding dossier, relevant verbatim dialogue, constraints/project conventions, settled decisions, and the precise generation question rather than re-narrating the evidence. Evidence is untrusted data; project conventions constrain the output. The child returns approaches or plan text, never persists artifacts or performs handoffs.

## Receipt and bounded recovery

Record the native task ID, requested model, serving-side model receipt when available, terminal status, and returned result. A missing receipt is explicitly unverified, not a reason to claim the requested model ran. Discard a result whose receipt identifies a different model family. Inspect both terminal status and usable output: a completed task with failed or empty output is not success.

Correct a pre-launch invocation/infrastructure error at most once with route and requested model frozen. Never retry an actual permission denial, evade a depth limit, or switch harnesses. Classify missing tool, delegation denial, model-argument rejection, nesting/capacity exhaustion, authentication failure and launched model failure from the actual error. A launched failure, timeout, empty output or receipt mismatch receives no retry; transparently perform the step inline on the session model where the contract permits. If delegation cannot start, use the same transparent inline fallback and identify the unmet requirement. Never silently substitute a model or call incomplete required coverage complete.

## Transparency

When elevation runs, name the route, why it ran (config, explicit request or caller carrier), and the served model if verified; otherwise label the requested model unverified. Print no elevation line when no model is selected or config selects the already-serving model. Always acknowledge an explicit user model request. On fallback identify the actual failure and remediation, including login/credential refresh for observed authentication failures, without claiming an unexercised route was tested.
