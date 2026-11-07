# Starting out, cost, and adapting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

## Starting out

1. Take OpenCode V2 install steps from `README.md#install` or `README.md#more-install-options` rather than guessing. Before using deep delegation, merge `"experimental": { "subagent_depth": 3 }` into the existing user-level `~/.config/opencode/opencode.json`. Use `opencode debug paths` or `opencode debug paths config` to locate the actual config directory and existing `opencode.json(c)` if different. Preserve higher integer depths, unrelated settings and sibling experimental fields; never replace the whole file or create a competing JSON/JSONC file. Installing the plugin or its package-local config does not enable consumer depth. Higher-precedence configuration must not lower effective depth below 3. This is user installation guidance, not permission to modify host config from this help skill.
2. A host loads skills at session start, so begin a new session after any install or update.
3. Run `ce-setup` in the project. It reports optional tools and offers to create the repo config. A missing optional tool is not a failure, and only the workflows that use it need it.
4. Begin on real work: `ce-brainstorm` for an idea, or `ce-debug` for a bug.

## What runs cost

Name the expensive runs this user is actually making, and what reduces each one. Fetch `docs/guides/configuration.md` before naming a config key.

- Skills that dispatch several agents cost more: `ce-code-review`, `ce-doc-review`, `ce-plan`, `ce-ideate`, `ce-bakeoff`, and a full `lfg` run.
- A cross-model pass also bills the other model provider. Config can turn the automatic pass off.
- Configured model routes and tiers remain intent, executed through native `opencode.models` selection and subagents/shell, never another harness dispatcher. Skill-requested reviewers satisfy a host's user-or-loaded-skill delegation rule without another approval. A genuine prohibition or tool denial still applies. Model override permission is separate: omit the optional model argument when explicit user model authorization is required but absent; use a suitable inherited reviewer and disclose unmet routes. Same-model reviewers are not cross-model independence. Classify actual permission, model, missing-tool and depth/capacity errors separately; use inline/parent fallback only when the review contract allows it, and report incomplete mandatory coverage honestly. Never evade restrictions through shell or another harness.
- After `ce-commit-push-pr` hands off to `ce-babysit-pr`, a standing watch runs until the PR is ready, blocked, out of budget, merged, or closed. Config can opt out of that handoff.
- `ce-optimize` and `ce-retune` run measured loops, so their cost grows with the number of runs.

## Adapting RocketClaw to a project

- `.rocketclaw/config.yaml` holds per-skill defaults, such as artifact format, the artifact folder, and cross-model review.
- Compound Packs are an experimental way to declare prescriptive rules, in a local folder or a shared repo, that planning grounds in and review checks work against. `ce-setup pack:<id>` scaffolds one.
- `ce-setup standards` drafts or refreshes the project's coding standards and review docs.
- A standing instruction in the project's agent instructions makes a skill run automatically at the right point. The "Make it automatic" sections of the `ce-plan`, `ce-work`, and `ce-noslop` guide pages give the wording, and `ce-setup` offers the one for `ce-compound`.
