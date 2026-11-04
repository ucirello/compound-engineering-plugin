# Starting out, cost, and adapting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

## Starting out

1. Install steps differ across hosts, so take them from `README.md#install` or `README.md#more-install-options` rather than guessing. For OpenCode, locate the actual global config directory with `opencode debug paths` / `opencode debug paths config`. In the existing `~/.config/opencode/opencode.json` (or actual existing `opencode.json(c)`), merge `experimental.subagent_depth` as an integer at least `3`; preserve unrelated and sibling settings and any higher depth. Do not create a competing JSON/JSONC file. Package configuration alone does not enable consumer depth; verify both package defaults and consuming configuration, with no higher-precedence source lowering it. Explain these changes; this help skill never edits global files.
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

## Delegation and workspace recommendations

Use native OpenCode model discovery (`opencode.models`) and subagent tools, not external dispatch or workspace-bridge helpers. Preserve the choices and tiers in `config.yaml`, `config.local.yaml`, and `config.example` when explaining routes. A loaded skill's explicit reviewer instructions authorize delegation unless actual host policy denies it; no second approval is needed. Model selection is separate: when an explicit user model request is required, use suitable inherited reviewers instead of forcing a configured model, and disclose the unmet route. Distinct same-model reviewers are not cross-model independence. Missing required coverage remains incomplete. Preserve receipts, bounded recovery, and failure details; do not retry denial or evade policy. Distinguish depth/capacity, denial, model rejection, and missing-tool failures. Inline fallback is valid only when the review's independence and coverage contract permits it.

For `ce-worktree`, detect and verify existing isolation first and reuse it without renaming or recreating it. For new isolation, capture local date once and normalize the task/PR/revision slug to `YYYYMMDD-meaningful-kebab-case-slug` without a doubled date. Use that same JJ workspace name and destination basename under the existing absolute local `.tmp` layout. Check registered names and destination paths, suffix collisions with `-2`, `-3`, and retain the selected identity across retries, resumes, and midnight. Preserve source/PR bookmarks and the exact verified base. Prefer harness-native ownership and session adoption only when it supports and verifies both colocation and the requested name; otherwise follow the skill's safe decision path, never bypass the harness. A native JJ creation example is `(cd "$workspace_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$absolute_destination")`, followed by `(cd "$absolute_destination" && jj git colocation status)`. All artifacts and temporary files stay under the target root's `.tmp`, never OS temporary directories. Completion alone never authorizes destructive cleanup; route cleanup to the owning skill's verified lifecycle rather than suggesting forget-and-delete.
