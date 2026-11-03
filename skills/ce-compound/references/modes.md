# Depth and session-history: why neither is a question

An interactive run picks its own depth rather than asking the user. Default to **Full**. Under context pressure, delegate ONE fresh native subagent running `ce-compound mode:non-interactive depth:full`, rather than selecting Lightweight. Read the source session ID through shell `printenv OPENCODE_SESSION_ID`; never guess it. Pass that ID, title if known, absolute JJ workspace root, any learning doc already written, and a one-sentence topic. Do not predigest the conversation. The delegate retrieves source evidence as specified in `session-history.md`, performs Full once, and returns its report and document path. The parent relays them and offers only consented interactive discoverability and pack-destination steps: no second Full pass or re-edit.

These skill instructions explicitly authorize native delegation where the host permits user-OR-loaded-skill authorization; do not request a second approval. An unconditional host ban or tool denial still wins. Discover permitted models with `opencode.models` and dispatch through native subagents/shell only. Configured model intent remains authoritative; override only when the host permits an explicit user model request, otherwise inherit a suitable model and disclose unmet cross-model independence. Same-model work is not cross-model independence. Distinguish permission denial, model rejection, missing tool, and actual nesting-capacity errors; never bypass them using another harness or shell dispatch. Depth does not grant permission.

Interactive Lightweight is a fallback only when native delegation is unavailable, denied, or actual depth is exhausted. Report the precise blocker and recommend rerunning from the SAME source session once available. A missing source ID/export is an evidence blocker: report it rather than guessing or substituting a different session.

A non-interactive run takes its depth only from an explicit token, and at most one depth token is accepted. `depth:lightweight` routes directly to Lightweight Mode. `depth:full` or no depth token enters Full Mode, including its automatic session-history probe. A non-interactive call carrying no depth token therefore behaves as it always has. Non-interactive lightweight asks no blocking questions and launches no subagents. If the invocation carries an unknown `depth:` token, multiple `depth:` tokens, or a `depth:` token without non-interactive intent, do not guess: emit the non-interactive failure report with the reason and end with `Documentation skipped`.

Lightweight mode skips session history entirely; non-interactive Full runs the same automatic probe, which asks nothing and so preserves the non-interactive contract.

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

**Full is the right choice for essentially every documented learning.** Its token cost is small next to the engineering work that produced the learning, and it is dwarfed by the value of a doc that compounds. Context pressure delegates Full as above; interactive Lightweight is only the classified delegation-unavailable fallback. Explicit non-interactive depth tokens still control their own runs. Lightweight omits cross-referencing, overlap detection, and semantic grounding validation; after a delegation blocker clears, rerun from this same source session rather than losing its evidence in a fresh session.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a learning is worth documenting. Auto-invoke only when the Preconditions in `SKILL.md` qualify the learning.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
