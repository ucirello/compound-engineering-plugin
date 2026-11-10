# Depth and session-history: why neither is a question

```bash
/ce-compound [brief context]
/ce-compound mode:non-interactive depth:lightweight [context]
/ce-compound mode:non-interactive depth:full [context]
```

An interactive run picks its own depth rather than asking the user. Default to **Full**. Under context pressure, first delegate Full to a fresh native subagent with `mode:non-interactive depth:full`, following the source-session handoff below. Lightweight is only a fallback for an actually unavailable or denied dispatch, or a reported depth/capacity limit; identify the exact limitation and suggest retrying Full in the same source session later.

## Context-pressure Full handoff

Read `OPENCODE_SESSION_ID` with the shell, not from an inferred tool/session identifier:

```bash
source_session_id="${OPENCODE_SESSION_ID:?source session ID is required}"
printf '%s\n' "$source_session_id"
jj root
```

Pass that source ID, its title if known, the verified absolute `jj root` workspace, the existing learning document path if any, and a one-sentence topic to **one** fresh native delegate. Do not predigest or summarize the source conversation. The delegate loads this skill and runs `mode:non-interactive depth:full`. From that absolute workspace root, it obtains source evidence via `opencode session export <source-session-id>` **or** `opencode api get /api/session/<id>/message`, saving the JSON response under the workspace's local `.tmp/`. Use the API alternative when the session-export interface is unavailable; do not substitute `opencode export` or invent another runtime interface. Never query a session database. Reduce exported user/assistant text and tool names, inputs and short results into bounded evidence files before reading; omit reasoning and bulky irrelevant output, and redact secrets before passing evidence onward. Use `scripts/session-history/reduce-opencode-export.py` for the reduction. The passed source session is primary evidence, not an optional prior-session match. Exclude only the delegate's own current session ID; never exclude its parent/source. If both prescribed source interfaces are unavailable, report that evidence gap rather than inventing conversation details.

Use native delegation only, subject to host permission. This skill requests delegation; permission to override a model is separate. Discover available model IDs with native `opencode.models` when needed; honor configured role choices when allowed, otherwise inherit a suitable model and disclose missing required cross-model coverage. Distinguish denial, missing tools, depth/capacity exhaustion and pre-launch model-argument rejection; correct a rejected argument once without evading policy through shell or another harness. Never label incomplete coverage Full.

The parent relays the delegate's report and document, then handles interactive discoverability and pack-destination consent. It must not run a second Full pass. Explicit non-interactive depth routing below remains unchanged.

A non-interactive run takes its depth only from an explicit token, and at most one depth token is accepted. `depth:lightweight` routes directly to Lightweight Mode. `depth:full` or no depth token enters Full Mode, including its automatic session-history probe. A non-interactive call carrying no depth token therefore behaves as it always has. Non-interactive lightweight asks no blocking questions and launches no subagents. If the invocation carries an unknown `depth:` token, multiple `depth:` tokens, or a `depth:` token without non-interactive intent, do not guess: emit the non-interactive failure report with the reason and end with `Documentation skipped`.

Lightweight mode skips session history entirely; non-interactive Full runs the same automatic probe, which asks nothing and so preserves the non-interactive contract.

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

**Full is the right choice for essentially every documented learning.** Its token cost is small next to the engineering work that produced the learning, and it is dwarfed by the value of a doc that compounds. Lightweight buys back context at the cost of cross-referencing, overlap detection, and semantic grounding validation, so it is for real context pressure only. If Lightweight turns out to be the wrong call for the user's taste, re-running is a rare, cheap correction. It is cheaper than taxing every run with a question.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a learning is worth documenting. Auto-invoke only when the Preconditions in `SKILL.md` qualify the learning.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
