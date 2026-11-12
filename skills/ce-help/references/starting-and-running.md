# Starting out, cost, and adapting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

## Starting out

1. Take current OpenCode install steps from `README.md#install` or `README.md#more-install-options` rather than guessing. Other hosts' compatibility instructions are host-specific.
2. A host loads skills at session start, so begin a new session after any install or update.
3. Run `ce-setup` in the project. It reports optional tools and offers to create the repo config. A missing optional tool is not a failure, and only the workflows that use it need it.
4. Begin on real work: `ce-brainstorm` for an idea, or `ce-debug` for a bug.

For OpenCode nested delegation, the user must merge `experimental.subagent_depth` of at least `3` into the existing global `~/.config/opencode/opencode.json` or `.jsonc`. Locate the active config with `opencode debug paths` (or `opencode debug paths config` where supported). Preserve a higher integer and all unrelated and sibling settings; do not create a competing config file. A plugin/package-local config alone does not enable this prerequisite, and higher-precedence config must not lower it. Explain this requirement only: do not change the host configuration on the user's behalf.

## What runs cost

Name the expensive runs this user is actually making, and what reduces each one. Fetch `docs/guides/configuration.md` before naming a config key.

- Skills that dispatch several agents cost more: `ce-code-review`, `ce-doc-review`, `ce-plan`, `ce-ideate`, `ce-bakeoff`, and a full `lfg` run.
- A cross-model pass also bills the other model provider. Config can turn the automatic pass off.
- OpenCode-native dispatch resolves available models with `opencode.models` and uses native subagents, not harness-dispatch scripts. Configured model/tier intent remains authoritative, but delegation permission and model-selection permission are separate: a skill's explicit reviewer dispatch authorizes delegation under a user-or-skill rule, not an optional model override when the host requires an explicit user model request. In that case use a suitable inherited model, disclose any unmet route or independence, and never label same-model review cross-model. Actual higher prohibitions and tool denial still apply.
- After `ce-commit-push-pr` hands off to `ce-babysit-pr`, a standing watch runs until the PR is ready, blocked, out of budget, merged, or closed. Config can opt out of that handoff.
- `ce-optimize` and `ce-retune` run measured loops, so their cost grows with the number of runs.

## Adapting RocketClaw to a project

- `.rocketclaw/config.yaml` holds per-skill defaults, such as artifact format, the artifact folder, and cross-model review.
- Compound Packs are an experimental way to declare prescriptive rules, in a local folder or a shared repo, that planning grounds in and review checks work against. `ce-setup pack:<id>` scaffolds one.
- `ce-setup standards` drafts or refreshes the project's coding standards and review docs.
- A standing instruction in the project's agent instructions makes a skill run automatically at the right point. The "Make it automatic" sections of the `ce-plan`, `ce-work`, and `ce-noslop` guide pages give the wording, and `ce-setup` offers the one for `ce-compound`.
