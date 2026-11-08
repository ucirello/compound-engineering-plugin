# Depth and session-history: why neither is a question

```bash
/ce-compound [brief context]
/ce-compound mode:non-interactive depth:lightweight [context]
/ce-compound mode:non-interactive depth:full [context]
```

An interactive run picks its own depth rather than asking the user. Default to **Full**. Near the context limit, delegate exactly one fresh native subagent loading `ce-compound mode:non-interactive depth:full`. Read the source session ID with shell (`printenv OPENCODE_SESSION_ID`, never guess or recall it), resolve the absolute root with `jj workspace root`, and pass those with the title when known, any learning-doc path already written, and a one-sentence problem topic. Do not pre-digest the conversation. The child exports and reduces the source via `session-history.md`; it is primary evidence, not an excluded prior session. Reuse an existing doc path rather than duplicating it.

This skill explicitly requests delegation under a user-OR-skill permission rule; no second approval is needed. Resolve configured model/tier intent with `opencode.models`, but do not pass a model override without a permitted explicit user model request. Suitable inherited-model workers are allowed, not proof of cross-model independence. Respect unconditional prohibitions and actual denials. Classify actual launch errors as missing tool, permission denial, model-argument rejection, or exhausted nesting/capacity. Never repeat denied calls or bypass depth through shell/another harness.

Only when delegation is actually unavailable (missing tool, permission denial, or exhausted nesting depth) fall back to Lightweight and state which. Missing source evidence is a truthful failure, not permission to invent a digest. Re-run `ce-compound` from this same session once delegation is available, never a fresh session without the evidence.

After return, the parent relays the report and doc path, then offers with usual consent only the interactive-only actions the child reported but did not apply: the discoverability instruction-file edit and a Compound Pack destination. No second Full pass or parent doc re-edit. Explicit non-interactive depth tokens remain unchanged.

A non-interactive run takes its depth only from an explicit token, and at most one depth token is accepted. `depth:lightweight` routes directly to Lightweight Mode. `depth:full` or no depth token enters Full Mode, including its automatic session-history probe. A non-interactive call carrying no depth token therefore behaves as it always has. Non-interactive lightweight asks no blocking questions and launches no subagents. If the invocation carries an unknown `depth:` token, multiple `depth:` tokens, or a `depth:` token without non-interactive intent, do not guess: emit the non-interactive failure report with the reason and end with `Documentation skipped`.

Lightweight mode skips session history entirely; non-interactive Full runs the same automatic probe, which asks nothing and so preserves the non-interactive contract.

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

**Full is the right choice for essentially every documented learning.** Lightweight sacrifices cross-referencing, overlap detection, and semantic grounding validation. Interactive context pressure uses it only after unavailable delegation as above; explicit non-interactive depth tokens retain their existing meaning.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a learning is worth documenting. Auto-invoke only when the Preconditions in `SKILL.md` qualify the learning.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
