# Starting out, cost, and adapting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

## Starting out

1. For OpenCode V2, take install steps from the installed package's `README.md#install` rather than guessing. Before deep delegation, merge `"experimental": { "subagent_depth": 3 }` into `~/.config/opencode/opencode.json`, or locate the actual global configuration directory with `opencode debug paths` / `opencode debug paths config` and update its existing `opencode.json(c)`. Preserve unrelated settings, sibling experimental fields, and an existing integer depth above 3; do not replace the file or create a competing JSON/JSONC file. Installing the plugin or its package-local config does not merge this prerequisite into the user's configuration. Higher-precedence configuration must not lower the effective depth below 3.
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
- Compound Packs are an experimental way to declare prescriptive rules, in a local folder or a shared repo, that planning grounds in and review checks work against. `ce-setup pack:<id>` scaffolds one.
- `ce-setup standards` drafts or refreshes the project's coding standards and review docs.
- A standing instruction in the project's agent instructions makes a skill run automatically at the right point. The "Make it automatic" sections of the `ce-plan`, `ce-work`, and `ce-noslop` guide pages give the wording, and `ce-setup` offers the one for `ce-compound`.
