# Depth and session-history: why neither is a question

An interactive run picks its own depth rather than asking the user. Default to **Full**. When near the context limit, delegate Full using the protocol below, not Lightweight merely because the conversation is long.

## Context-pressure delegation

Dispatch one fresh native OpenCode subagent that loads `ce-compound` with `mode:non-interactive depth:full`. Read the actual source session ID with the shell tool (`printf '%s\n' "$OPENCODE_SESSION_ID"`), never from memory or a guessed value. Resolve the absolute workspace root with `jj workspace root` from the target workspace's absolute working directory. Pass only that ID, the title when known, absolute root, path of any learning doc already written this run, and a one-sentence problem topic. Do not pre-digest the conversation. An absent source ID is an evidence blocker, never invent one.

The worker follows `references/session-history.md`: supported session export/API, local `.tmp/` storage, reduced source evidence, and exclusion of only its own session. The passed source is primary evidence, not an excluded prior session. Reuse any supplied doc as the candidate deliverable rather than creating a duplicate.

The parent relays the returned report and doc path, then offers with usual consent the interactive-only steps reported but not applied: the discoverability instruction-file edit and a writable Compound Pack destination. Do not run a second Full pass or re-edit the doc in the parent. An accepted destination handoff retains assembly's consent and ownership rules.

Fall back to Lightweight only when delegation is unavailable: no subagent tool, an actual permission denial, or exhausted nesting depth. Classify the actual error and report which. A model-argument rejection is not delegation denial: omit a forbidden override and use a suitable inherited model. Other failures are reported accurately. Retry from this same source session once delegation is available, not a fresh session without its evidence. Explicit non-interactive `depth:` routing remains unchanged.

## Native dispatch constraints

These Full-worker and reviewer instructions explicitly request native subagents. A host rule permitting user OR applicable-skill requested delegation therefore needs no second approval. Respect unconditional prohibitions, actual denials and unavailable tools; never bypass them with shell or another harness. Delegation permission, model-selection permission and nesting capacity are separate. Resolve permitted configured routes with `opencode.models`; omit optional model overrides unless host policy permits them. Suitable inherited-model reviewers may proceed, but same-model reviewers are not cross-model independence; required unavailable independence is incomplete coverage. Verify effective depth through supported configuration discovery/debug interfaces, not the bundled package default. Classify depth/capacity, permission, model-argument and missing-tool errors separately. Use inline/parent fallback only where the review contract permits it, preserving independence and reporting unmet coverage. Do not retry denials or evade depth limits.

A non-interactive run takes its depth only from an explicit token, and at most one depth token is accepted. `depth:lightweight` routes directly to Lightweight Mode. `depth:full` or no depth token enters Full Mode, including its automatic session-history probe. A non-interactive call carrying no depth token therefore behaves as it always has. Non-interactive lightweight asks no blocking questions and launches no subagents. If the invocation carries an unknown `depth:` token, multiple `depth:` tokens, or a `depth:` token without non-interactive intent, do not guess: emit the non-interactive failure report with the reason and end with `Documentation skipped`.

Lightweight mode skips session history entirely; non-interactive Full runs the same automatic probe, which asks nothing and so preserves the non-interactive contract.

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

**Full is the right choice for essentially every documented learning.** Its token cost is small next to the engineering work that produced the learning, and it is dwarfed by the value of a doc that compounds. Lightweight buys back context at the cost of cross-referencing, overlap detection, and semantic grounding validation, so it is for real context pressure only. If Lightweight turns out to be the wrong call for the user's taste, re-running is a rare, cheap correction. It is cheaper than taxing every run with a question.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a learning is worth documenting. Auto-invoke only when the Preconditions in `SKILL.md` qualify the learning.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
