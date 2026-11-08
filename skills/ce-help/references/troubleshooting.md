# Troubleshooting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

| What the user sees | What to tell them |
|---|---|
| A skill is missing, or behaves the old way after an update | Refresh the marketplace before updating the plugin, because updating alone reads a stale snapshot. Then start a new session. `docs/install/upgrading.md` has the commands for Claude Code, Codex, and Grok Bot. Other hosts' update steps are in `README.md#more-install-options`. |
| An old copy of a skill keeps running after an update | An earlier Bun install may be shadowing the plugin. `docs/install/upgrading.md` has the cleanup command. |
| The agent will not start a skill it recommended | The skill is manual-only, so the user has to type it. `references/skill-map.md` marks these. |
| The slash command is not recognized | OpenCode uses `/skill-name`. Codex uses `$skill-name`. On oh-my-pi, a manual-only skill needs `/skill:<name>`. On Devin, check the installation's command namespace. |
| A skill says a tool is missing | `ce-setup` reports which tools are missing and how to install them. Install only what the workflow needs. |
| A cross-model pass or oracle peer did not run | The run's report says why. `ce-setup` reports missing tools, and the `ce-pov` guide page lists what peers need. Config can also turn the automatic review pass off, so check `docs/guides/configuration.md`. |
| Plans or learnings are not where the user expected | `docs_root` in `.rocketclaw/config.yaml` moves every artifact folder. Format options can also change ideation, brainstorm, and plan files from `.md` to `.html`. |
| `ce-compound` wrote nothing | It captures only what the final code, tests, standards, and docs do not already show, so skipping a routine fix is correct. If a lesson was missed, run it again and say what the lesson was. |
| Learnings are captured only when the user asks | A standing instruction fixes this. `ce-setup` offers one when the repo tracks its learnings. |
| New plans ignore past learnings | Check that `<root>/solutions/` holds learnings and that `ce-plan` ran in this repo. A `ce-compound` refresh handles learnings that have gone stale. |
| A hands-off run stopped before merging | That is expected. Merging normally stays with the user. The `lfg` guide page covers where a run ends. |
| The agent's last reply made no sense | `wtf` explains it plainly. |
| A session is out of context, or the work has to move to another agent | `ce-handoff` writes a handoff, and a new session can resume from it. |
| Review delegation fails or nested reviewers cannot start | Follow the user-level depth prerequisite in `references/starting-and-running.md` and check effective configuration precedence. Distinguish an actual nesting-capacity error from a permission denial, forbidden model override, or unavailable tool. Do not bypass a denial or claim missing independent coverage was completed. |
