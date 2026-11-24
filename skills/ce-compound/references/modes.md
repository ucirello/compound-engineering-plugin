# Depth and session-history: why neither is a question

```bash
/ce-compound [brief context]
/ce-compound mode:non-interactive depth:lightweight [context]
/ce-compound mode:non-interactive depth:full [context]
```

An interactive run picks its own depth rather than asking the user. Default to **Full**. When nearing the context limit would otherwise force Lightweight, use **delegated Full** before doing the research or drafting in the parent:

1. Use the shell to read `printf '%s\n' "${OPENCODE_SESSION_ID-}"` and `jj workspace root`; never guess the ID. Dispatch one fresh native OpenCode generic subagent to load `ce-compound` with `mode:non-interactive depth:full`. Pass the exact source session ID, title if known, absolute workspace root, path of any learning doc this run already wrote, and a one-sentence problem topic. Do not pass conversation excerpts, summaries, or prior conclusions. The child reads the source evidence as described in `references/session-history.md`; it is the sole Full capture orchestrator.
2. This skill explicitly requests delegation where the host allows user-or-skill authorization; no separate consent to dispatch is needed. Inherit the model, with no override for this handoff. Respect a higher-priority prohibition or actual denial. Distinguish a missing native tool, permission denial, nesting-depth exhaustion, model rejection, and malformed arguments from the actual capability or error. Correct a purely malformed pre-launch call once; never retry a denied call or bypass the host through another harness. Only missing tool, permission denial/prohibition, or exhausted nesting depth routes to interactive Lightweight. Report that reason and advise re-running from **this same session** when delegation is available. An unverifiable source ID, another launch error, or a child that launches but cannot load the source is a reported blocker, not a Lightweight trigger.
3. Relay the child's report and learning doc path (or the reason no doc was written). Keep the interactive consent steps in the parent as specified in `references/report.md`. Do not run another Full pass, re-edit or regenerate the learning doc, or treat an optional follow-up as already approved.

A non-interactive run takes its depth only from an explicit token, and at most one depth token is accepted. `depth:lightweight` routes directly to Lightweight Mode. `depth:full` or no depth token enters Full Mode, including its automatic session-history probe. A non-interactive call carrying no depth token therefore behaves as it always has. Non-interactive lightweight asks no blocking questions and launches no subagents. If the invocation carries an unknown `depth:` token, multiple `depth:` tokens, or a `depth:` token without non-interactive intent, do not guess: emit the non-interactive failure report with the reason and end with `Documentation skipped`.

Lightweight mode skips session history entirely; ordinary non-interactive Full runs the same automatic probe, which asks nothing and so preserves the non-interactive contract. Delegated non-interactive Full loads the supplied source directly.

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. For ordinary Full, a cheap probe determines whether earlier sessions add relevant context. For delegated Full, the passed source session is primary evidence and is never gated by that probe.

**Full is the right choice for essentially every documented learning.** Delegated Full preserves that coverage when the source session is long. Lightweight buys back context at the cost of cross-referencing, overlap detection, and semantic grounding validation; use it only via the interactive capability fallback above or an explicit non-interactive `depth:lightweight` token.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a lesson qualifies. The Preconditions in `SKILL.md` decide that on every run, automatic or explicit, and a run where nothing qualifies writes nothing.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
