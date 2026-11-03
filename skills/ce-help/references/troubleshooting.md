# Troubleshooting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

| What the user sees | What to tell them |
|---|---|
| A skill is missing, or behaves the old way after an update | Follow the installed package's OpenCode upgrade instructions, then start a new session. Check plugin readiness and skill registration before assuming an update succeeded. |
| An old copy of a skill keeps running after an update | An earlier Bun install may be shadowing the plugin. `docs/install/upgrading.md` has the cleanup command. |
| The agent will not start a skill it recommended | The skill is manual-only, so the user has to type it. `references/skill-map.md` marks these. |
| The slash command is not recognized | OpenCode uses `/skill-name`. Check the installed plugin's readiness and registered skill/command names. |
| A skill says a tool is missing | `ce-setup` reports which tools are missing and how to install them. Install only what the workflow needs. |
| A cross-model pass or oracle peer did not run | Distinguish tool availability, delegation permission, model permission, and actual depth exhaustion. Explicit reviewer skill instructions satisfy a user-or-loaded-skill delegation exception, not unconditional bans. Preserve configured tiers and model intent; same-model work is not cross-model independence. Do not bypass a denial with shell or another harness. Check the setup depth prerequisite in `starting-and-running.md` and configuration opt-outs; report incomplete required independent coverage truthfully. |
| Plans or learnings are not where the user expected | `docs_root` in `.rocketclaw/config.yaml` moves every RocketClaw artifact folder. Format options can also change ideation, brainstorm, and plan files from `.md` to `.html`. |
| `ce-compound` wrote nothing | It captures only what the final code, tests, standards, and docs do not already show, so skipping a routine fix is correct. If a lesson was missed, run it again and say what the lesson was. |
| Learnings are captured only when the user asks | A standing instruction fixes this. `ce-setup` offers one when the repo tracks its learnings. |
| New plans ignore past learnings | Check that `<root>/solutions/` holds learnings and that `ce-plan` ran in this repo. A `ce-compound` refresh handles learnings that have gone stale. |
| A hands-off run stopped before merging | That is expected. Merging normally stays with the user. The `lfg` guide page covers where a run ends. |
| The agent's last reply made no sense | `wtf` explains it plainly. |
| A session is out of context, or the work has to move to another agent | `ce-handoff` writes a handoff, and a new session can resume from it. |
