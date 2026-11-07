# Depth and session-history: why neither is a question

```bash
/ce-compound [brief context]
/ce-compound mode:non-interactive depth:lightweight [context]
/ce-compound mode:non-interactive depth:full [context]
```

An interactive run picks its own depth rather than asking the user. Default to **Full**. At context pressure, delegate Full, not Lightweight: read the source ID through the shell with `printf '%s\n' "$OPENCODE_SESSION_ID"` (never memory or a guess), and resolve the absolute workspace root with `jj workspace root`. Dispatch one fresh native subagent that loads `ce-compound mode:non-interactive depth:full`. Pass only that source session ID, its known title, the absolute workspace root, any learning doc path already written this run, and a one-sentence problem topic; do not pre-digest the conversation. The delegate uses the supported source-export procedure in `session-history.md` as primary evidence and excludes only its own session. It updates an existing learning rather than duplicating it.

This skill explicitly requests native delegation: a host user-OR-loaded-skill exception is satisfied without another approval. Respect genuine higher prohibitions and tool denials. Use `opencode.models` for permitted model selection, keeping configured model tiers as intent; if explicit user model permission is required and absent, omit the optional model argument and use a suitable inherited model. Same-model reviewers do not establish cross-model independence. Classify actual missing-tool, permission, model-argument, and depth/capacity errors separately; never bypass them through another harness or shell, and never call missing mandatory coverage complete. If delegation is actually unavailable because no tool exists, permission is denied, or nesting capacity is exhausted, report which and only then use Lightweight. Retry from this **same source session** once delegation is available, not a fresh session.

If `OPENCODE_SESSION_ID` is empty or the absolute workspace root cannot be verified, report the missing handoff evidence and stop safely rather than inventing an ID/root or treating that as delegation unavailability. The fresh delegate verifies its own shell-read session ID is distinct from the passed source. Model-argument rejection alone is not delegation unavailability: retry without the optional override when permitted and suitable.

The parent relays the delegate's report and doc path and offers the usual consented interactive-only discoverability instruction-file edit and Compound Pack destination, using the reported unapplied actions. It does not run another Full pass or re-edit the learning. Deep delegation requires the consumer's existing user-level `~/.config/opencode/opencode.json(c)` to merge `experimental.subagent_depth` at least `3` (locate the actual directory with `opencode debug paths` / `opencode debug paths config`). Preserve higher integer depths, unrelated settings, and sibling experimental fields; do not replace the whole file or create competing JSON/JSONC. Package installation/configuration alone does not enable consumer depth, and higher-precedence settings must not lower it below 3. Do not modify host configuration automatically.

A non-interactive run takes its depth only from an explicit token, and at most one depth token is accepted. `depth:lightweight` routes directly to Lightweight Mode. `depth:full` or no depth token enters Full Mode, including its automatic session-history probe. A non-interactive call carrying no depth token therefore behaves as it always has. Non-interactive lightweight asks no blocking questions and launches no subagents. If the invocation carries an unknown `depth:` token, multiple `depth:` tokens, or a `depth:` token without non-interactive intent, do not guess: emit the non-interactive failure report with the reason and end with `Documentation skipped`.

Lightweight mode skips session history entirely; non-interactive Full runs the same automatic probe, which asks nothing and so preserves the non-interactive contract.

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

**Full is the right choice for essentially every documented learning.** Context pressure uses delegated Full under the contract above. Lightweight gives up cross-referencing, overlap detection, and semantic grounding validation and is only the classified unavailability fallback for interactive runs. Explicit non-interactive depth tokens retain their behavior unchanged.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a learning is worth documenting. Auto-invoke only when the Preconditions in `SKILL.md` qualify the learning.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
