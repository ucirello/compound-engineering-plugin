# Depth and session-history: why neither is a question

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

**Full is the right choice for essentially every documented learning.** Under interactive context pressure, delegate Full rather than losing the evidence in a new session. Explicit non-interactive `depth:lightweight` and `depth:full` tokens retain their existing meaning; do not reroute those callers.

## Context-pressure Full handoff

This skill explicitly requests one fresh native subagent. A host rule allowing user-OR-skill-requested delegation is satisfied; no second consent is needed. Respect genuine higher-priority prohibitions and actual tool permissions. Delegation permission, model override permission, and remaining nesting capacity are separate. Discover models with `opencode.models` when needed, honoring configured tiers; if a model override requires a user model request and none exists, omit the optional model argument and use a suitable inherited model. Report any required unavailable model coverage as incomplete. Never dispatch through another harness or shell to evade a denial or depth limit.

1. With the shell tool, read `printf '%s\n' "$OPENCODE_SESSION_ID"`; never guess or recall the ID. Resolve the absolute workspace root with `jj workspace root` from the actual workspace. Pass the ID, title when known, absolute root, path of any learning doc already written (or none), and a one-sentence problem topic. Do not pre-digest the conversation.
2. Dispatch **one** fresh native subagent instructed to load `ce-compound mode:non-interactive depth:full`. It uses the passed source session as primary evidence, follows `references/session-history.md`'s supported export/reduction contract, and updates the already-written learning doc rather than duplicating it. It excludes only its own child session, never the passed source session. The child runs the whole Full workflow, including the final doc write; research-only subagents retain their scratch-only contracts.
3. On return, relay the child's report and doc path. Keep interactive-only steps in the parent: offer the discoverability instruction-file edit and an eligible pack destination with their usual consent. Do not run a second Full pass or rewrite the doc in the parent. A consented pack placement is a destination operation, not a new drafting pass.
4. Lightweight is allowed only when native delegation is actually unavailable, denied, or nesting/capacity is exhausted. Classify the real tool absence or returned error precisely, distinguishing permission denial, depth exhaustion, and model-argument rejection; do not call every failure a context limit or retry a denied dispatch. A rejected optional model argument is not by itself unavailable delegation when inherited-model dispatch remains allowed. Export/evidence failures are reported as evidence blockers, not fabricated delegation failures. If Lightweight is necessary, state the actual reason and advise: re-run `ce-compound` **from this same session** once delegation is available. Never recommend a fresh session that lacks the source conversation.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a learning is worth documenting. Auto-invoke only when the Preconditions in `SKILL.md` qualify the learning.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
