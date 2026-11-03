# Reviewer Dispatch

Read this before dispatching the Step 2 reviewers. It covers what happens when the harness is full, how review agents are released, and the permission mode.

A generic subagent is one whose whole brief is the prompt you send it. When the host's subagent tool makes you name an agent, use only a name you have seen the host list, and list its agents before the first dispatch if you have not. Pick the plain one that adds no role of its own, which still counts as a generic subagent. Never pick a specialist, such as a reviewer or worker agent, whose own role prompt, output format, or tool limits would replace or narrow your prompt.

**Bounded dispatch.** Queue the reviewers and launch only as many as the harness accepts at once. An actual concurrency, nesting-depth, or active-agent-limit error means capacity is exhausted, not that reviewer permission or model permission was denied: leave the reviewer queued and retry after a slot frees where supported. Classify missing tools, permission denials, and model rejections separately; never bypass them with shell or another harness. When a dispatch cannot recover through active work, supported release, or a corrected invocation, this skill permits that pass inline using the same prompt asset; disclose the substitution and any unmet independence or coverage.

**Agent lifecycle.** Collect terminal outcomes, including failures, before cleanup. Close or release review-owned agents when the harness provides caller-owned cleanup, before refilling slots, advancing stages, or returning. Do not message completed agents with no remaining work. Do not infer released capacity from completion or interruption, or invent cleanup operations.

**Permission mode.** Omit the `mode` parameter on the dispatch call so the user's configured permission settings apply.

**Depth setup (documentation only).** Bundled plugin configuration does not enable nested delegation in a consuming project. Locate the existing user configuration with `opencode debug paths` or `opencode debug paths config`, usually `~/.config/opencode/opencode.json`. The user should merge an integer `experimental.subagent_depth` of at least `3` into that existing configuration, preserving a higher value, sibling settings, unrelated configuration, and JSONC syntax. Do not create a competing config file or edit host configuration automatically; ensure higher-precedence settings do not lower the depth. Depth capacity is independent of delegation and model permissions.
