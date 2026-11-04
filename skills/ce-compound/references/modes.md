# Depth and session-history: why neither is a question

An interactive run picks its own depth rather than asking the user. Default to **Full**. Under context pressure, delegate Full rather than losing the conversation evidence. Read the source session ID with the shell tool from `$OPENCODE_SESSION_ID` (never guess or recall it), and resolve the absolute workspace root with `jj workspace root`. Dispatch exactly one fresh native subagent loading `ce-compound` with `mode:non-interactive depth:full`. Pass only the source session ID, title when known, absolute workspace root, any learning-doc path already written by this run, and a one-sentence problem topic. Do not pre-digest the conversation. The child follows the supported export procedure in `session-history.md`, treating the passed session as primary evidence and reconciling any existing learning rather than duplicating it.

This skill explicitly requests delegation where host policy permits user-or-skill-requested subagents; no second approval is needed. Delegation permission, model-selection permission, and remaining nesting depth are distinct. Use `opencode.models` for configured model intent only when selection is allowed; when overrides require an explicit user model request, omit the optional model argument and use a suitable inherited model. Same-model reviewers are not cross-model independence. Verify effective depth from OpenCode's discovered configuration; deep delegation requires at least 3, and package-local configuration is not automatically adopted by consumers. Classify actual launch errors as missing tool, permission denial, depth/capacity exhaustion, or model-argument rejection. Do not bypass policy or depth through shell or another harness. Required unavailable independent coverage is incomplete.

Only when delegation is unavailable (no native tool, actual permission denial, or exhausted nesting depth) fall back to Lightweight and name the blocker. Do not claim Full completed after an export failure. Retry `ce-compound` from this same source session once delegation is available, not from a fresh session.

The parent retains interaction: relay the child's report and doc path, then offer with usual consent any reported-but-unapplied discoverability instruction-file edit and writable pack destination. Do not run another Full pass or re-edit the doc in the parent; a consented destination handoff is not another capture pass.

A non-interactive run takes its depth only from an explicit token, and at most one depth token is accepted. `depth:lightweight` routes directly to Lightweight Mode. `depth:full` or no depth token enters Full Mode, including its automatic session-history probe. A non-interactive call carrying no depth token therefore behaves as it always has. Non-interactive lightweight asks no blocking questions and launches no subagents. If the invocation carries an unknown `depth:` token, multiple `depth:` tokens, or a `depth:` token without non-interactive intent, do not guess: emit the non-interactive failure report with the reason and end with `Documentation skipped`.

Lightweight mode skips session history entirely; non-interactive Full runs the same automatic probe, which asks nothing and so preserves the non-interactive contract.

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

**Full is the right choice for essentially every documented learning.** Its cost is small next to the engineering work and the value of the learning. Under context pressure prefer the delegated Full handoff above. Lightweight trades cross-referencing, overlap detection, and semantic grounding validation for context only when that delegation is unavailable, or when an explicit non-interactive depth token requests it.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a learning is worth documenting. Auto-invoke only when the Preconditions in `SKILL.md` qualify the learning.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
