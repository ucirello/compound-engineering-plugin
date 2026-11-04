# Depth and session-history: why neither is a question

An interactive run defaults to **Full**. Context pressure does not by itself select Lightweight: delegate the complete capture to one fresh native subagent as described below.

A non-interactive run takes its depth only from an explicit token, and at most one depth token is accepted. `depth:lightweight` routes directly to Lightweight Mode. `depth:full` or no depth token enters Full Mode, including its automatic session-history probe. A non-interactive call carrying no depth token therefore behaves as it always has. Non-interactive lightweight asks no blocking questions and launches no subagents. If the invocation carries an unknown `depth:` token, multiple `depth:` tokens, or a `depth:` token without non-interactive intent, do not guess: emit the non-interactive failure report with the reason and end with `Documentation skipped`.

Lightweight mode skips session history entirely; non-interactive Full runs the same automatic probe, which asks nothing and so preserves the non-interactive contract.

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

## Context-pressure handoff

For an interactive capture near its context limit, launch **one fresh native subagent** that loads `ce-compound mode:non-interactive depth:full`. This skill explicitly requests delegation; do not ask for a second delegation approval where user-OR-skill permission suffices. An unconditional prohibition, denial, or missing tool still applies. Read the source session ID using the shell command `printf '%s\n' "$OPENCODE_SESSION_ID"`; never guess it from titles, files, or the delegate's ID. Pass that ID, title if known, absolute JJ workspace root, existing learning document path if any, and a one-sentence problem topic. Do not paste a pre-digested conversation. The delegate retrieves the source using the supported interfaces in `session-history.md`, and owns the entire Full capture, including final artifact writes. This is an exception to the Phase 1 scratch-only boundary, not a research-only subagent.

The delegate retrieves and reduces that source **before** preconditions and Phase 1; it must not judge an empty fresh context or draft from the topic alone. Source retrieval failure is an evidence blocker, not proof that no lesson qualifies and not permission to choose Lightweight. Report it explicitly with `Documentation skipped` when the full capture cannot proceed.

Keep delegation permission, optional model selection, and nesting capacity separate. Preserve configured model/tier intent; discover native models with `opencode.models` when needed. Where the host requires an explicit user model request, omit an optional override absent that request. An inherited suitable model is allowed; it does not establish cross-model independence. Classify actual tool errors as permission, model rejection, depth exhaustion, or unavailable tooling; do not bypass denial through a helper or retry it. The delegate uses contract-permitted inline research if further nesting is unavailable and reports incomplete coverage honestly.

The parent relays the delegate's report and document path. It does not run a second Full pass or re-edit that document. In the interactive parent only, offer consented discoverability edits and, for a prescriptive lesson with a writable declared pack, a pack-destination follow-up using the existing assembly rules; only apply the selected narrow follow-up after consent, preserving the completed lesson rather than rewriting it.

Lightweight fallback is permitted only when delegation is actually unavailable, denied, or depth-limited, not merely because the parent is low on context. Report the classified reason and advise rerunning `/ce-compound` from the **same source session** when delegation becomes available. An explicit non-interactive depth remains authoritative: never silently downgrade `depth:full` or upgrade `depth:lightweight`. If source identity/export is unavailable, report that evidence limitation rather than inventing a session or treating it as delegation unavailability.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a learning is worth documenting. Auto-invoke only when the Preconditions in `SKILL.md` qualify the learning.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
