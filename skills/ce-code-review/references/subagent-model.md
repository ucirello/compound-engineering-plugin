# Native reviewer dispatch: permission, model, and depth

Read this before **every** reviewer, trivial-PR check, finish leaf, validator,
peer, or fallback dispatch. This skill explicitly requests those subagents.

Preserve the step's default tier intent. For Codex compatibility, the existing
default intent for all spawned roles remains `gpt-6.1-terra` with `high`
reasoning effort; explicit user/project role requests, then role configuration,
take precedence. This is not permission to pass forbidden overrides. Native
OpenCode executes only permitted models discovered through `opencode.models`.

1. **Delegation permission.** Interpret the actual host rule. Under a user-OR-
   applicable-skill rule, these explicit dispatch instructions satisfy the skill
   exception; do not demand a second user request or approval. Loading a skill
   that never requests delegation is not authorization. An unconditional
   higher-priority prohibition, unavailable tool, or actual denial still wins.
   Never bypass it through shell or another harness.
2. **Model-selection permission.** This is separate. Read the desired model and
   effort from the user's instructions, then the role's `review_subagents`
   configuration, then the step's tier default. Resolve ordinary scalar keys
   from `<workspace-root>/.rocketclaw/config.local.yaml`, then `config.yaml`:
   first valid nonempty value wins; lists/maps replace the whole key, including
   empty values. `docs_root` remains config.yaml-only. The `review_subagents`
   map's current-harness entry (`opencode` here) has optional string `model` and
   `effort`; omitted/invalid fields retain defaults. Preserve configured routes
   and tiers as intent. Discover permitted concrete IDs with `opencode.models`
   and dispatch with native subagents, not another harness's CLI.
   If the host forbids overrides without an explicit user model request, omit
   the optional `model` argument (and forbidden effort arguments), even when
   this skill or configuration suggests a tier. Inherit the session model when
   it satisfies the contract. Record requested versus applied model/effort and
   unmet tier requirements in Coverage. Same-model contexts are separate
   reviewers, not cross-model independence. A required fixed route or
   different-model pass that cannot run makes that coverage **incomplete**.
3. **Nesting/capacity.** Check effective OpenCode configuration from its supported
   configuration interface/source documents, including precedence; package-
   local configuration is not automatically merged into an installed plugin's
   consumer. Deep delegation requires effective `experimental.subagent_depth`
   at least 3, and the current nesting level must leave room. Do not modify host
   configuration. Classify actual launch errors as nesting-depth exhaustion,
   active-agent capacity, delegation denial, model/effort rejection, or missing
   tool; never call one another. Capacity may queue until active agents finish.
   A model rejection may get one inherited-model attempt only if allowed and
   suitable; do not retry denied delegation or evade depth through shell.

Use the supported V2 configuration query with the target absolute workspace
location explicitly URL-encoded, not an unscoped request (which defaults to
`/root`). For a target root `/absolute/target/workspace`, the query is
`opencode api get '/api/config?location%5Bdirectory%5D=%2Fabsolute%2Ftarget%2Fworkspace'`.
Substitute the URL-encoded actual absolute `workspace_root`, not that example
path. Use its actual response shape to inspect discovered source documents and
precedence; source-entry arrays are not a single effective config object.
Confirm the winning `experimental.subagent_depth` and remaining nesting
capacity, not merely a shipped value in the plugin package. See
https://opencode.ai/v2/docs/config . A runtime launch error is authoritative
evidence of exhausted remaining depth even when the configured ceiling is 3.
Do not launch a probe reviewer or modify global/project configuration to test it.

When delegation is unavailable, only contract-permitted parent/inline work may
continue. Attribute it to the parent, exclude it from `independent_reviewers`,
and retain all missing independent coverage and validator gates. Focused mode
requires an independent read; without one its verdict is Not ready. Full review
cannot claim all selected reviewers or required cross-model passes completed
when they did not. Merge/report mechanics may run in the parent if necessary;
that never substitutes for an independent reviewer or validator.
