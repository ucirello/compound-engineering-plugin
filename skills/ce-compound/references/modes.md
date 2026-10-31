# Depth and session-history: why neither is a question

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

**Full is the right choice for essentially every documented learning.** Under interactive context pressure, dispatch exactly one fresh native subagent to load `ce-compound mode:non-interactive depth:full`. First shell-read `printf '%s\n' "$OPENCODE_SESSION_ID"` (never guess or recall it), and resolve `jj workspace root` from the target absolute workspace cwd. Pass the source session ID, known session title, absolute workspace root, any learning-doc path already written by this run, and a one-sentence problem topic. Do not pre-digest the conversation. The delegated run obtains and reduces the supported source export as required by `session-history.md`; that source is primary evidence, not a prior session to exclude.

This skill explicitly requests delegation under a user-or-skill permission rule; do not ask again merely because the user did not request subagents separately. Respect unconditional host prohibitions. Model permission is separate: use `opencode.models` for permitted configured choices, but omit the optional model argument under a user-only override rule and use a suitable inherited model. Preserve configured tiers as intent; same-model passes do not establish cross-model independence. Report any unmet required independent coverage. Classify actual errors as permission denial, missing tool, model-argument rejection, or depth/capacity exhaustion; never evade a denial or nesting limit through shell or another harness.

After the delegated run returns, relay its report and doc path, then offer the reported discoverability instruction-file edit and eligible Compound Pack destination with the usual interactive consent. Only these interactive-only follow-ups remain in the parent; do not repeat Full research or re-edit the learning in the parent. A selected pack move is a consented destination follow-up, not a second synthesis pass.

Choose Lightweight for interactive context pressure only if delegation is actually unavailable: no native subagent tool, an actual permission denial/prohibition, or exhausted nesting/capacity classified from the actual error. State which prevented delegation. A model override rejection alone is not unavailability when inherited-model delegation is suitable. If source export fails after launch, report the evidence failure; never invent conversation evidence. Retry `ce-compound` from this same source session once delegation is available, not from a fresh session. Explicit non-interactive `depth:` behavior is unchanged.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a learning is worth documenting. Auto-invoke only when the Preconditions in `SKILL.md` qualify the learning.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
