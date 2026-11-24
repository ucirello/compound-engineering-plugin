# Troubleshooting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

| What the user sees | What to tell them |
|---|---|
| A skill is missing, or behaves the old way after an update | Check the configured OpenCode V2 plugin source and whether the package loaded and registered the skill in the current project. Follow the OpenCode V2 installation section in `README.md` and restart OpenCode after updating. |
| An old copy of a skill keeps running after an update | Check the active registration's source path for an older install shadowing the plugin. Confirm ownership before removing anything; do not remove unrelated skills. |
| The agent will not start a skill it recommended | The skill is manual-only, so the user has to type it. `references/skill-map.md` marks these. |
| The slash command is not recognized | On OpenCode, check that `/skill-name` is registered. The form differs on other hosts: Codex uses `$skill-name`, oh-my-pi uses `/skill:<name>` for manual-only skills, and Devin uses the installed plugin namespace. |
| A skill says a tool is missing | `ce-setup` reports which tools are missing and how to install them. Install only what the workflow needs. |
| A cross-model pass or oracle peer did not run | Check the run's report and actual OpenCode error. Distinguish delegation permission, model-selection permission or availability, and exhausted nesting depth. For depth, verify applicable configuration precedence and see `references/starting-and-running.md`; do not assume installation set it or advise another harness as a workaround. Config can also turn the automatic review pass off, so check `docs/guides/configuration.md`. |
| Plans or learnings are not where the user expected | `docs_root` in `.rocketclaw/config.yaml` moves every workflow artifact folder. Format options can also change ideation, brainstorm, and plan files from `.md` to `.html`. |
| `ce-compound` wrote nothing | It captures only what the final code, tests, standards, and docs do not already show, so skipping a routine fix is correct. If a lesson was missed, run it again and say what the lesson was. |
| Learnings are captured only when the user asks | A standing instruction fixes this. `ce-setup` offers one when the repo tracks its learnings. |
| New plans ignore past learnings | Check that `<root>/solutions/` holds learnings and that `ce-plan` ran in this repo. A `ce-compound` refresh handles learnings that have gone stale. |
| A hands-off run stopped before merging | That is expected. Merging normally stays with the user. The `lfg` guide page covers where a run ends. |
| The agent's last reply made no sense | `wtf` explains it plainly. |
| A session is out of context, or the work has to move to another agent | `ce-handoff` writes a handoff, and a new session can resume from it. |
