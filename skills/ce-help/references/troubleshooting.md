# Troubleshooting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

| What the user sees | What to tell them |
|---|---|
| A skill is missing, or behaves the old way after an update | Follow the installed package's OpenCode V2 update instructions, verify plugin activation and skill/command registration, then start a new session. For other hosts, use their documented update procedure in `docs/install/upgrading.md` or `README.md#more-install-options`. |
| An old copy of a skill keeps running after an update | An earlier Bun install may be shadowing the plugin. `docs/install/upgrading.md` has the cleanup command. |
| The agent will not start a skill it recommended | The skill is manual-only, so the user has to type it. `references/skill-map.md` marks these. |
| The slash command is not recognized | OpenCode uses `/skill-name`; verify the V2 plugin registered the skill and command. Codex uses `$skill-name`. On oh-my-pi, a manual-only skill needs `/skill:<name>`. Other hosts use their documented form. |
| A skill says a tool is missing | `ce-setup` reports which tools are missing and how to install them. Install only what the workflow needs. |
| A cross-model pass or oracle peer did not run | The run's receipts/report must distinguish disabled configuration, delegation denial, forbidden model override, unavailable model/tool, and actual nesting-capacity failure. See `references/starting-and-running.md` for the separate permission and depth checks and global depth prerequisite. Required cross-model coverage remains incomplete when only same-model reviewers ran. `ce-setup` reports tools, and the installed `ce-pov` instructions list peer requirements. |
| Plans or learnings are not where the user expected | `docs_root` in `.rocketclaw/config.yaml` moves every artifact folder. Format options can also change ideation, brainstorm, and plan files from `.md` to `.html`. |
| `ce-compound` wrote nothing | It captures only what the final code, tests, standards, and docs do not already show, so skipping a routine fix is correct. If a lesson was missed, run it again and say what the lesson was. |
| Learnings are captured only when the user asks | A standing instruction fixes this. `ce-setup` offers one when the repo tracks its learnings. |
| New plans ignore past learnings | Check that `<root>/solutions/` holds learnings and that `ce-plan` ran in this repo. A `ce-compound` refresh handles learnings that have gone stale. |
| A hands-off run stopped before merging | That is expected. Merging normally stays with the user. The `lfg` guide page covers where a run ends. |
| The agent's last reply made no sense | `wtf` explains it plainly. |
| A session is out of context, or the work has to move to another agent | `ce-handoff` writes a handoff, and a new session can resume from it. |
