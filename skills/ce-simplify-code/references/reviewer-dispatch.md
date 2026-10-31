# Reviewer Dispatch

Read this before dispatching the Step 2 reviewers. It covers what happens when the harness is full, how review agents are released, and the permission mode.

A generic subagent is one whose whole brief is the prompt you send it. When the host's subagent tool makes you name an agent, use only a name you have seen the host list, and list its agents before the first dispatch if you have not. Pick the plain one that adds no role of its own, which still counts as a generic subagent. Never pick a specialist, such as a reviewer or worker agent, whose own role prompt, output format, or tool limits would replace or narrow your prompt.

**Bounded dispatch.** Queue the reviewers and launch only as many as the harness accepts at once. A concurrency or active-agent-limit error means the harness is full, not that the reviewer failed: leave the reviewer queued and retry after a slot frees. Check remaining nesting capacity separately from permission. Classify actual errors as capacity/depth exhaustion, permission denial, model-argument rejection, or missing tool; do not repeatedly retry denied operations or evade limits through shell or another harness. When dispatch cannot recover through active work, supported release, or a corrected permitted invocation, run that pass inline using the same prompt asset and disclose the substitution. An inline pass cannot satisfy required independent or cross-model coverage; report that coverage incomplete.

**Agent lifecycle.** Collect terminal outcomes, including failures, before cleanup. Close or release review-owned agents when the harness provides caller-owned cleanup, before refilling slots, advancing stages, or returning. Do not message completed agents with no remaining work. Do not infer released capacity from completion or interruption, or invent cleanup operations.

**Permission mode.** Omit the `mode` parameter on the dispatch call so the user's configured permission settings apply.

**Delegation authority.** This skill explicitly requests reviewers. Under a host rule allowing delegation when the user OR an applicable skill requests it, that satisfies the skill-requested exception without another approval. Respect an unconditional higher-priority prohibition, missing capability, or actual denial. Model-selection permission and remaining depth are separate: omit a model override when policy requires an explicit user model request that is absent, and use suitable inherited-model reviewers where allowed. Preserve configured tier intent and truthfully report unmet coverage.
