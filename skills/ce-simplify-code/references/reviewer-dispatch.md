# Reviewer Dispatch

Read this before dispatching the Step 2 reviewers. It covers what happens when the harness is full, how review agents are released, and the permission mode.

A generic subagent is one whose whole brief is the prompt you send it. When the host's subagent tool makes you name an agent, use only a name you have seen the host list, and list its agents before the first dispatch if you have not. Pick the plain one that adds no role of its own, which still counts as a generic subagent. Never pick a specialist, such as a reviewer or worker agent, whose own role prompt, output format, or tool limits would replace or narrow your prompt.

**Bounded dispatch.** Queue the reviewers and launch only as many as the harness accepts at once. A concurrency or active-agent-limit error means the harness is full, not that the reviewer failed: leave the reviewer queued and retry after a slot frees. When a dispatch cannot recover through active work, supported release, or a corrected invocation, run that pass inline using the same prompt asset and disclose the substitution.

**Permission and depth are separate.** This skill explicitly requests reviewer delegation, satisfying a user-OR-skill delegation rule without a second ask. An unconditional prohibition, actual denial, or missing native tool still prevents dispatch; do not bypass it with scripts or retry a denial. Classify actual errors separately as capacity, nesting-depth, delegation permission, model rejection, or missing tool. On unavailable or denied delegation or exhausted depth, use the inline fallback above and disclose the reason. Do not treat depth as permission or model permission as delegation permission. Resolve allowed model choices using native `opencode.models` and preserve configured tier intent; omit optional model overrides where explicit user model authorization is required but absent. Inherited or same-model reviews do not establish cross-model independence; if a caller requires it and it is unavailable, report incomplete coverage rather than claim it.

**Agent lifecycle.** Collect terminal outcomes, including failures, before cleanup. Close or release review-owned agents when the harness provides caller-owned cleanup, before refilling slots, advancing stages, or returning. Do not message completed agents with no remaining work. Do not infer released capacity from completion or interruption, or invent cleanup operations.

**Permission mode.** Omit the `mode` parameter on the dispatch call so the user's configured permission settings apply.
