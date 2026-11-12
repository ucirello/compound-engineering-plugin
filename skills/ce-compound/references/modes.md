# Depth and session-history: why neither is a question

```bash
/ce-compound [brief context]
/ce-compound mode:non-interactive depth:lightweight [context]
/ce-compound mode:non-interactive depth:full [context]
```

An interactive run picks its own depth rather than asking the user. Default to **Full**. Near the context limit, use the delegated Full handoff below, not an automatic Lightweight downgrade.

A non-interactive run takes its depth only from an explicit token, and at most one depth token is accepted. `depth:lightweight` routes directly to Lightweight Mode. `depth:full` or no depth token enters Full Mode, including its automatic session-history probe. A non-interactive call carrying no depth token therefore behaves as it always has. Non-interactive lightweight asks no blocking questions and launches no subagents. If the invocation carries an unknown `depth:` token, multiple `depth:` tokens, or a `depth:` token without non-interactive intent, do not guess: emit the non-interactive failure report with the reason and end with `Documentation skipped`.

Lightweight mode skips session history entirely; non-interactive Full runs the same automatic probe, which asks nothing and so preserves the non-interactive contract.

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

**Full is the right choice for essentially every documented learning.** Context pressure moves Full work to one fresh native subagent rather than removing coverage.

## Context-pressure interactive handoff

1. Use the shell to read `printenv OPENCODE_SESSION_ID`; never guess the source ID. Pass its known title, the absolute workspace root returned by `jj root`, the existing learning-doc path (or `none`), and a one-sentence topic. Pass no predigested conversation, selected excerpts, or narrative summary.
2. Dispatch **ONE** fresh OpenCode-native subagent loading `ce-compound mode:non-interactive depth:full`, with the absolute skill path and those source fields. It becomes the Full orchestrator and owns the ordinary product-write boundary, including normal research/validation workers. No second capture or parallel product writer; research workers remain scratch-only.
3. Delegate exports the passed source with supported `opencode session export <id>` or the supported API session-message route into a private directory under `<absolute-workspace-root>/.tmp/rocketclaw/compound/`. Reduce it to chronological user/assistant text and tool names/short results, retaining failures but not raw verbose tool dumps. Never query SQLite or internal storage. Read this primary evidence before judging eligibility or drafting. Exclude only the delegate's own session, never the passed parent/source session. Report inaccessible source evidence as a blocker, not as an empty history or a license to invent the lesson.
4. Delegate returns the complete Full terminal report, resulting doc path, and deferred discoverability/Compound Pack opportunities. Parent relays report and doc without a second pass, re-edit, or second invocation, then offers the normal-consent interactive discoverability change and applicable pack destination/scaffold choice from `assembly.md`. Show proposals and obtain ordinary consent before deferred writes. A selected pack move preserves the validated capture, not a redraft. This is the explicit exception to the normal no-follow-up report rule.
5. Delegation permission, model permission, and nesting capacity are separate. Preserve configured model/tier intent; resolve available routes with `opencode.models`, use inherited model when suitable, and disclose unmet routes. Do not supply optional model arguments where the host requires an explicit user model request. Respect higher prohibitions. Classify actual depth/permission/model/tool errors; never retry denied operations via another harness or call same-model work independent cross-model coverage.
6. Lightweight fallback is allowed only for an actual no-tool, permission-denial, or depth blocker. State the reason and reduced coverage; model mismatch alone is not a downgrade reason. Never call partial Full coverage complete. Recommend rerunning from the **same source session** once delegation/export is available, never a fresh session. Explicit non-interactive depth tokens keep their behavior above.

OpenCode setup prerequisite (document only): locate active global config with `opencode debug paths` or `opencode debug paths config`. Ask users to merge `experimental.subagent_depth >= 3` into their existing `~/.config/opencode/opencode.json` or `.jsonc`, preserving higher integers, sibling experimental settings, and unrelated config. Do not create a competing file. Plugin/package config alone does not enable it; higher-precedence config must not lower it. Never change host config in this skill.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a lesson qualifies. The Preconditions in `SKILL.md` decide that on every run, automatic or explicit, and a run where nothing qualifies writes nothing.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
