# Reviewer Dispatch

Read this before dispatching the Step 2 reviewers. It covers what happens when the harness is full, how review agents are released, and the permission mode.

A generic subagent is one whose whole brief is the prompt you send it. When the host's subagent tool makes you name an agent, use only a name you have seen the host list, and list its agents before the first dispatch if you have not. Pick the plain one that adds no role of its own, which still counts as a generic subagent. Never pick a specialist, such as a reviewer or worker agent, whose own role prompt, output format, or tool limits would replace or narrow your prompt.

**Bounded dispatch.** Queue the reviewers and launch only as many as the harness accepts at once. A concurrency or active-agent-limit error means the harness is full, not that the reviewer failed: leave the reviewer queued and retry after a slot frees. When a dispatch cannot recover through active work, supported release, or a corrected invocation, run that pass inline using the same prompt asset and disclose the substitution.

**Agent lifecycle.** Collect terminal outcomes, including failures, before cleanup. Close or release review-owned agents when the harness provides caller-owned cleanup, before refilling slots, advancing stages, or returning. Do not message completed agents with no remaining work. Do not infer released capacity from completion or interruption, or invent cleanup operations.

**Permission mode.** Omit the `mode` parameter on the dispatch call so the user's configured permission settings apply.

**Delegation permission.** This skill explicitly requests reviewer subagents. Under a host rule allowing delegation when the user OR a loaded skill requests it, that request is sufficient; do not require a second user approval. A genuine higher-priority prohibition, missing tool, or actual denial still applies. Never bypass it with shell or another harness, or retry a denied operation. Model-selection permission is separate: obey Step 2's override rules even when delegation is allowed.

**Nesting and coverage.** Check the effective runtime depth and remaining capacity separately from permissions; a package setting is not proof of the consuming session's effective depth. Use the host's supported configuration/capability inspection and classify dispatch errors accurately as depth/capacity, permission, rejected model argument, or missing tool. Do not retry an exhausted nesting limit as if it were a temporary concurrency slot. This workflow permits the same prompt assets inline or serially when native dispatch cannot start; disclose the reason and which passes used that fallback. Do not call inline work an independent reviewer or claim unavailable required cross-model coverage was completed. If a required route or independent pass remains unmet, report incomplete coverage in the summary before proceeding under the caller's safe decision path.
