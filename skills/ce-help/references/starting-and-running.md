# Starting out, cost, and adapting RocketClaw

`docs/` and `README.md` paths refer to the RocketClaw package sources described in `SKILL.md`.

## Starting out

1. Follow RocketClaw's OpenCode V2 installation steps in `README.md` rather than guessing. For a separate legacy installation, use that installation's own host-specific instructions.
2. For deep delegation, merge `"experimental": { "subagent_depth": 3 }` into the user-level `~/.config/opencode/opencode.json`. Use `opencode debug paths` or `opencode debug paths config` to locate the actual user config and update the existing `opencode.json` or `opencode.jsonc` there. Preserve unrelated settings, sibling `experimental` keys, and any existing integer depth above `3`; do not create a competing file. A higher-precedence config must not lower the effective depth below `3`. Installing the plugin or relying on its package-local `opencode.json` alone does not enable this in consuming projects.
3. Start a new session after installing or updating.
4. Run `ce-setup` in the project. It reports optional tools and offers to create the repo config. A missing optional tool is not a failure, and only the workflows that use it need it.
5. Begin on real work: `ce-brainstorm` for an idea, or `ce-debug` for a bug.

## What runs cost

Name the expensive runs this user is actually making, and what reduces each one. Fetch `docs/guides/configuration.md` before naming a config key.

- Skills that dispatch several agents cost more: `ce-code-review`, `ce-doc-review`, `ce-plan`, `ce-ideate`, `ce-bakeoff`, and a full `lfg` run.
- A cross-model pass can bill the other model provider. Config can turn the automatic pass off. OpenCode resolves configured routes through `opencode.models` and uses permitted native subagents; a requested provider or tier is not a guarantee that the route can run.
- After `ce-commit-push-pr` hands off to `ce-babysit-pr`, a standing watch runs until the PR is ready, blocked, out of budget, merged, or closed. Config can opt out of that handoff.
- `ce-optimize` and `ce-retune` run measured loops, so their cost grows with the number of runs.

## Adapting RocketClaw to a project

- `.rocketclaw/config.yaml` holds per-skill defaults, such as artifact format, the artifact folder, and cross-model review.
- Compound Packs are an experimental way to declare prescriptive rules, in a local folder or a shared repo, that planning grounds in and review checks work against. `ce-setup pack:<id>` scaffolds one.
- `ce-setup standards` drafts or refreshes the project's coding standards and review docs.
- A standing instruction in the project's agent instructions makes a skill run automatically at the right point. The "Make it automatic" sections of the `ce-plan`, `ce-work`, and `ce-noslop` guide pages give the wording, and `ce-setup` offers the one for `ce-compound`.
