# Depth and session-history: why neither is a question

```bash
/ce-compound [brief context]
/ce-compound mode:non-interactive depth:lightweight [context]
/ce-compound mode:non-interactive depth:full [context]
```

An interactive run picks its own depth rather than asking the user. Default to **Full** in this session. Near the context limit, delegate Full instead of selecting Lightweight.

## Delegated Full under interactive context pressure

- Read the source ID with the shell tool (`printf '%s\n' "$OPENCODE_SESSION_ID"`); never guess it or use a remembered ID. Resolve the absolute workspace root with `jj workspace root`. Give **one fresh native OpenCode subagent** the instruction to load `ce-compound` with `mode:non-interactive depth:full`, that source ID, the source title when known, the absolute workspace root, the path of any learning doc this capture already wrote, and a one-sentence problem topic. Do not summarize or pre-digest the conversation. Use the target workspace as the child's working directory; it is not a request to create another workspace.
- This instruction expressly requests delegation where the host permits a user **or skill** request. Do not ask again on that basis. Use the inherited model; this handoff needs fresh context, not a different model.
- Verify the configured depth prerequisite (at least 3 for deep workflows; plugin installation alone does not configure it). Use the authenticated connection to the running OpenCode server, e.g. `opencode api get '/api/config?location%5Bdirectory%5D=<percent-encoded absolute project root>'`. This discovers configuration source entries, not merged/effective runtime configuration. Inspect `info.experimental.subagent_depth` in the returned entries and apply [OpenCode V2 source precedence](https://opencode.ai/v2/docs/config) to determine which explicit value wins. If the sources or precedence cannot be verified, report the configured depth as unverified; this endpoint does not read back available nesting slots.
- Treat actual nesting capacity separately from permission and model selection. Classify any failure from the actual tool or error; correct an ordinary pre-launch argument error once. Never retry a denial or bypass a prohibition or nesting limit with shell or another harness.
- Fall back to Lightweight only when delegation is actually unavailable (missing native tool, prohibited or denied, or nesting depth exhausted). Report which. A missing source ID, unresolved workspace, export error, or child failure is not a delegation denial: report the blocker, do not guess, start a second Full run, or treat a failed handoff as a completed capture.
- The delegated child treats the source session as primary evidence, per `references/session-history.md`; use the already-written learning path to avoid a duplicate. On return, the parent follows **Delegated Full handoff** in `references/report.md`, without running Full again or editing the child's learning.

A non-interactive run takes its depth only from an explicit token, and at most one depth token is accepted. `depth:lightweight` routes directly to Lightweight Mode. `depth:full` or no depth token enters Full Mode, including its automatic session-history probe. A non-interactive call carrying no depth token therefore behaves as it always has. Non-interactive lightweight asks no blocking questions and launches no subagents. If the invocation carries an unknown `depth:` token, multiple `depth:` tokens, or a `depth:` token without non-interactive intent, do not guess: emit the non-interactive failure report with the reason and end with `Documentation skipped`.

Lightweight mode skips session history entirely; non-interactive Full runs the same automatic probe, which asks nothing and so preserves the non-interactive contract.

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

**Full is the right choice for essentially every documented learning.** Lightweight buys back context at the cost of cross-referencing, overlap detection, and semantic grounding validation. For interactive context pressure it is a fallback, not the default correction.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a lesson qualifies. The Preconditions in `SKILL.md` decide that on every run, automatic or explicit, and a run where nothing qualifies writes nothing.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
