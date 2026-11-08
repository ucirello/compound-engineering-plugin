# Starting out, cost, and adapting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

## Starting out

1. Take OpenCode V2 install steps from `README.md#install` or `README.md#more-install-options` rather than guessing. Before using deep delegation, merge `"experimental": { "subagent_depth": 3 }` into the existing user-level `~/.config/opencode/opencode.json`, or locate the actual global config directory with `opencode debug paths` / `opencode debug paths config` and update its existing `opencode.json(c)`. Preserve unrelated settings, sibling experimental fields, and any existing integer depth higher than `3`; do not replace the file or create competing JSON/JSONC files. A depth of at least `3` is required for deep agentic delegation. Installing the plugin or shipping package-local configuration alone does not enable this in a consuming project; higher-precedence configuration must not lower it below `3`. This is advice for the user, not authorization for this help skill to edit host configuration.
2. A host loads skills at session start, so begin a new session after any install or update.
3. Run `ce-setup` in the project. It reports optional tools and offers to create the repo config. A missing optional tool is not a failure, and only the workflows that use it need it.
4. Begin on real work: `ce-brainstorm` for an idea, or `ce-debug` for a bug.

## What runs cost

Name the expensive runs this user is actually making, and what reduces each one. Fetch `docs/guides/configuration.md` before naming a config key.

- Skills that dispatch several agents cost more: `ce-code-review`, `ce-doc-review`, `ce-plan`, `ce-ideate`, `ce-bakeoff`, and a full `lfg` run.
- A cross-model pass also bills the other model provider. Config can turn the automatic pass off.
- Configured models and tiers express routing intent. Execution uses `opencode.models` and native subagents/shell, not another harness's dispatcher. Skill-requested reviewers satisfy a user-or-skill delegation rule, but not an unconditional prohibition. Model override permission is separate: without a permitted explicit user model request, use suitable inherited-model reviewers without a model argument. Report unmet cross-model requirements as incomplete coverage, not independent-model verification. Classify actual dispatch errors as permission, model selection, missing tool, or nesting capacity; never retry a denial or bypass a depth limit through another harness.
- After `ce-commit-push-pr` hands off to `ce-babysit-pr`, a standing watch runs until the PR is ready, blocked, out of budget, merged, or closed. Config can opt out of that handoff.
- `ce-optimize` and `ce-retune` run measured loops, so their cost grows with the number of runs.

## Adapting RocketClaw to a project

- `.rocketclaw/config.yaml` holds per-skill defaults, such as artifact format, the artifact folder, and cross-model review.
- Compound Packs are an experimental way to declare prescriptive rules, in a local folder or a shared repo, that planning grounds in and review checks work against. `ce-setup pack:<id>` scaffolds one.
- `ce-setup standards` drafts or refreshes the project's coding standards and review docs.
- A standing instruction in the project's agent instructions makes a skill run automatically at the right point. The "Make it automatic" sections of the `ce-plan`, `ce-work`, and `ce-noslop` guide pages give the wording, and `ce-setup` offers the one for `ce-compound`.
