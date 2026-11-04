# Depth and session-history: why neither is a question

An interactive run picks its own depth rather than asking the user. Default to **Full**. Context pressure delegates Full, not Lightweight.

## Context-pressure handoff

Read the source session ID through shell from `$OPENCODE_SESSION_ID`, never memory. Launch one fresh native OpenCode subagent loading `ce-compound mode:non-interactive depth:full`. Pass only that ID, known title, absolute JJ workspace root, any learning document path, and one sentence of topic: NO predigested conversation. The loaded skill requests delegation, subject to actual host denial/missing tools. Use `opencode.models` for discovery when needed; model override permission is separate from delegation permission.

The delegate exports the exact passed source using supported `opencode session export <id>` or `opencode api get /api/session/<id>/message` into the workspace's `.tmp/`, reduces to user/assistant text, tool names and short results before reading, and uses it as PRIMARY evidence. Never inspect SQLite/internal storage. Exclude only the delegate's OWN current session, never the passed source.

Verify discovered package default and consuming configuration allow `experimental.subagent_depth` integer >=3. Installation alone does not enable consumer depth. Setup must merge this into existing `~/.config/opencode/opencode.json`, or the actual global `opencode.json(c)` located via `opencode debug paths`, preserving siblings and higher depth with no competing file. Higher precedence must not lower depth. Document only; do not modify global settings.

Only actual unavailability, denial, or demonstrated depth/capacity failure permits Lightweight fallback; classify which. Do not retry denial. Advise rerun from the SAME source session once delegation is available, not a fresh one. Explicit non-interactive depth tokens below never silently downgrade.

The parent relays the report and document path, then offers interactive-only discoverability editing or Compound Pack destination with normal consent; the delegate did not apply these. Do not repeat Full or re-edit the learning as part of handoff.

A non-interactive run takes its depth only from an explicit token, and at most one depth token is accepted. `depth:lightweight` routes directly to Lightweight Mode. `depth:full` or no depth token enters Full Mode, including its automatic session-history probe. A non-interactive call carrying no depth token therefore behaves as it always has. Non-interactive lightweight asks no blocking questions and launches no subagents. If the invocation carries an unknown `depth:` token, multiple `depth:` tokens, or a `depth:` token without non-interactive intent, do not guess: emit the non-interactive failure report with the reason and end with `Documentation skipped`.

Lightweight mode skips session history entirely; non-interactive Full runs the same automatic probe, which asks nothing and so preserves the non-interactive contract.

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

**Full is the right choice for essentially every documented learning.** Delegate it under context pressure. Lightweight loses cross-referencing, overlap detection and semantic grounding; use it only for an explicit non-interactive request or the classified handoff failures above.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a learning is worth documenting. Auto-invoke only when the Preconditions in `SKILL.md` qualify the learning.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
