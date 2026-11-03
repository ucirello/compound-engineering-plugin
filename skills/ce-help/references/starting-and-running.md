# Starting out, cost, and adapting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

## Starting out

1. Use the installed package's OpenCode installation instructions rather than guessing. Before delegated workflows, merge `experimental.subagent_depth` of at least integer `3` into the user's existing `~/.config/opencode/opencode.json`; locate the actual config with `opencode debug paths` or `opencode debug paths config`. Preserve a higher integer, sibling and unrelated settings, and existing JSONC; do not create a competing file. This is user guidance only: this help skill never edits host config. Bundled configuration or npm/Git plugin installation alone does not enable this depth in consuming projects, and higher-precedence settings must not lower it. Depth enables nesting capacity, not delegation or model permission.
2. A host loads skills at session start, so begin a new session after any install or update.
3. Run `ce-setup` in the project. It reports optional tools and offers to create the repo config. A missing optional tool is not a failure, and only the workflows that use it need it.
4. Begin on real work: `ce-brainstorm` for an idea, or `ce-debug` for a bug.

## What runs cost

Name the expensive runs this user is actually making, and what reduces each one. Fetch `docs/guides/configuration.md` before naming a config key.

- Skills that dispatch several agents cost more: `ce-code-review`, `ce-doc-review`, `ce-plan`, `ce-ideate`, `ce-bakeoff`, and a full `lfg` run.
- A cross-model pass also bills the other model provider. Config can turn the automatic pass off.
- After `ce-commit-push-pr` hands off to `ce-babysit-pr`, a standing watch runs until the PR is ready, blocked, out of budget, merged, or closed. Config can opt out of that handoff.
- `ce-optimize` and `ce-retune` run measured loops, so their cost grows with the number of runs.

## Adapting RocketClaw to a project

- `.rocketclaw/config.yaml` holds per-skill defaults, such as artifact format, the artifact folder, and cross-model review.
- Packs are an experimental way to declare prescriptive rules, in a local folder or a shared repo, that planning grounds in and review checks work against. `ce-setup pack:<id>` scaffolds one.
- `ce-setup standards` drafts or refreshes the project's coding standards and review docs.
- A standing instruction in the project's agent instructions makes a skill run automatically at the right point. The "Make it automatic" sections of the `ce-plan`, `ce-work`, and `ce-noslop` guide pages give the wording, and `ce-setup` offers the one for `ce-compound`.
