# Depth and session-history: why neither is a question

Both are decisions the agent is better positioned to make than the user. Depth depends on the context budget the agent can observe and the user cannot. Neither party can know in advance whether session history will pay off, because the payoff is an unrelated earlier session the current agent was never in. So a cheap probe decides it instead of a question to the user.

**Full is the right choice for essentially every documented learning.** Under interactive context pressure, dispatch one fresh native subagent to load `ce-compound mode:non-interactive depth:full`. Before dispatch, use the shell tool to read `OPENCODE_SESSION_ID` from the environment (never guess or recall it) and obtain the absolute workspace root with `jj workspace root` from the target workspace's absolute cwd. Pass that source session ID, its title when known, the absolute workspace root, any learning-doc path already written by this run, and a one-sentence problem topic. Do not pre-digest the conversation. The fresh run is the Full orchestrator and may write its one product doc; Phase 1 researchers retain their scratch-only boundary. Read `references/session-history.md` for supported source export and reduction.

The parent retains interactive steps: relay the returned report and doc path, then offer with normal consent the discoverability instruction-file edit and Compound Pack destination reported but not applied by the delegated run. Do not run a second Full pass or re-edit the doc in the parent. A consented pack destination follows the existing assembly transfer rules, not another research/write pass.

Fall back to Lightweight only for an actually unavailable subagent tool, permission denial, or exhausted nesting depth; report the specific reason from the actual capability/error. Do not evade a prohibition or depth limit through shell or another harness. Advise retrying `ce-compound` from this same session once delegation is available, not from a fresh session. Explicit non-interactive `depth:` selection is unchanged.

## Native dispatch contract

Capture the source ID with a shell command such as `printf '%s\n' "$OPENCODE_SESSION_ID"` and reject an empty value; do not substitute the delegated run's own ID. Capture `jj workspace root` with the shell cwd set to the target workspace's absolute path. Pass the values as literal resolved metadata, not unexpanded shell placeholders. A missing source ID/export is an evidence blocker, not permission to fabricate evidence or call Full complete.

This skill explicitly requests its research/review subagents. Under a user-or-loaded-skill delegation rule that satisfies the skill-requested exception without renewed consent; an unconditional higher-priority prohibition still wins. Delegation permission, model-selection permission, and remaining nesting depth are distinct. Use `opencode.models` for permitted configured model selection, preserving configured choices/tiers as intent. If model override requires an explicit user model request, omit the optional model argument and use a suitable inherited model; disclose unmet routes. Same-model reviewers are not cross-model independence. Classify actual depth/capacity, permission, model-argument, and missing-tool failures separately. Use inline/parent fallbacks only where the individual review contract permits; report missing independence or coverage as incomplete, never fully verified. Do not retry denials or bypass depth limits. See https://opencode.ai/v2/docs/config for effective delegation-depth configuration; the package-local default alone does not establish the host's effective depth.

**The session-history probe is near-free on wall-clock** because it runs alongside the Related Docs Finder and your drafting, and it escalates to the expensive extraction and synthesis only when genuinely relevant candidate sessions turn up (`references/session-history.md`). This support exists only inside the compounding workflow; there is no standalone session-history feature for users.

## Auto-Invoke

Completion phrases such as "that worked", "it's fixed", "working now", and "problem solved" identify the completion checkpoint; they do not establish that a learning is worth documenting. Auto-invoke only when the Preconditions in `SKILL.md` qualify the learning.

An explicit invocation with optional context requests immediate evaluation without waiting for auto-detection. It does not waive the solved, verified, and durable-learning preconditions.
