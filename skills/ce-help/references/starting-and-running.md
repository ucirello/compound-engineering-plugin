# Starting out, cost, and adapting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

## Starting out

1. Use the installed package's OpenCode V2 installation instructions in `README.md#install` rather than another harness's dispatcher. Before using deep delegation, merge `"experimental": { "subagent_depth": 3 }` into `~/.config/opencode/opencode.json`. Use `opencode debug paths` or `opencode debug paths config` to locate the actual global configuration directory and update its existing `opencode.json(c)`. Preserve unrelated settings, sibling `experimental` fields, and any existing integer depth above `3`; do not replace the file or create a competing JSON/JSONC file. At least `3` is required for deep agentic delegation. Installing the plugin or shipping package-local configuration does not enable this global prerequisite, and higher-precedence configuration must not lower it below `3`.
2. A host loads skills at session start, so begin a new session after any install or update.
3. Run `ce-setup` in the project. It reports optional tools and offers to create the repo config. A missing optional tool is not a failure, and only the workflows that use it need it.
4. Begin on real work: `ce-brainstorm` for an idea, or `ce-debug` for a bug.

## What runs cost

Name the expensive runs this user is actually making, and what reduces each one. Fetch `docs/guides/configuration.md` before naming a config key.

- Skills that dispatch several agents cost more: `ce-code-review`, `ce-doc-review`, `ce-plan`, `ce-ideate`, `ce-bakeoff`, and a full `lfg` run.
- A cross-model pass also bills the other model provider. Config can turn the automatic pass off.
- Configured models and tiers remain authoritative intent. Native execution uses `opencode.models` to resolve available models and native subagents/shell, never a cross-harness dispatch bridge. Delegation permission, model-selection permission, and remaining nesting depth are separate checks. Under a user-or-loaded-skill rule, an explicit reviewer-dispatch request in the loaded skill permits delegation without a second approval; an unconditional prohibition still wins. If model overrides require an explicit user request, use suitable inherited-model reviewers without passing a model override. Record actual dispatch receipts and classify permission, model, missing-tool, and depth/capacity failures accurately. Same-model reviewers are not cross-model independence: report unmet required routes or independent coverage as incomplete. Use only contract-permitted inline or parent fallbacks; never evade denials or nesting limits through another harness.
- After `ce-commit-push-pr` hands off to `ce-babysit-pr`, a standing watch runs until the PR is ready, blocked, out of budget, merged, or closed. Config can opt out of that handoff.
- `ce-optimize` and `ce-retune` run measured loops, so their cost grows with the number of runs.

## Adapting RocketClaw to a project

- `.rocketclaw/config.yaml` holds per-skill defaults, such as artifact format, the artifact folder, and cross-model review.
- Compound Packs are an experimental way to declare prescriptive rules, in a local folder or a shared repo, that planning grounds in and review checks work against. `ce-setup pack:<id>` scaffolds one.
- `ce-setup standards` drafts or refreshes the project's coding standards and review docs.
- A standing instruction in the project's agent instructions makes a skill run automatically at the right point. The "Make it automatic" sections of the `ce-plan`, `ce-work`, and `ce-noslop` guide pages give the wording, and `ce-setup` offers the one for `ce-compound`.
