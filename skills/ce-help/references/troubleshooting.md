# Troubleshooting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

| What the user sees | What to tell them |
|---|---|
| A skill is missing, or behaves the old way after an update | Check the installed package's OpenCode V2 installation and update instructions, then start a new session. Do not apply V1 plugin routes. Compatibility hosts' update steps are in `README.md#more-install-options`. |
| An old copy of a skill keeps running after an update | An earlier Bun install may be shadowing the plugin. `docs/install/upgrading.md` has the cleanup command. |
| The agent will not start a skill it recommended | The skill is manual-only, so the user has to type it. `references/skill-map.md` marks these. |
| The slash command is not recognized | OpenCode V2 uses `/skill-name`. For compatibility hosts, Codex uses `$skill-name`, oh-my-pi manual-only skills need `/skill:<name>`, and Devin uses the installed plugin's verified namespace. |
| A skill says a tool is missing | `ce-setup` reports which tools are missing and how to install them. Install only what the workflow needs. |
| A cross-model pass or oracle peer did not run | The run's report says why. `ce-setup` reports missing tools, and the `ce-pov` guide page lists what peers need. Config can also turn the automatic review pass off, so check `docs/guides/configuration.md`. |
| Reviewer dispatch failed | Distinguish delegation permission, model-selection permission, tool availability, and nesting capacity using the actual error. Under a user-or-loaded-skill delegation rule, explicit reviewer dispatch in the loaded skill satisfies the skill exception without another approval. A genuine higher-priority prohibition still applies. Model overrides may require an explicit user request even when delegation is allowed; suitable inherited-model reviewers remain possible, but do not count as cross-model independence. Discover permitted models through native `opencode.models` and dispatch through native subagents/shell, never another harness to evade a restriction. Preserve configured routes and tiers as intent and report unsatisfied independence or coverage as incomplete. Verify effective delegation depth, including the user-level prerequisite in `references/starting-and-running.md`; do not mistake depth exhaustion for denied permission or retry a denied operation. |
| Plans or learnings are not where the user expected | `docs_root` in `.rocketclaw/config.yaml` moves every artifact folder. Format options can also change ideation, brainstorm, and plan files from `.md` to `.html`. |
| `ce-compound` wrote nothing | It captures only what the final code, tests, standards, and docs do not already show, so skipping a routine fix is correct. If a lesson was missed, run it again and say what the lesson was. |
| Learnings are captured only when the user asks | A standing instruction fixes this. `ce-setup` offers one when the repo tracks its learnings. |
| New plans ignore past learnings | Check that `<root>/solutions/` holds learnings and that `ce-plan` ran in this repo. A `ce-compound` refresh handles learnings that have gone stale. |
| A hands-off run stopped before merging | That is expected. Merging normally stays with the user. The `lfg` guide page covers where a run ends. |
| The agent's last reply made no sense | `wtf` explains it plainly. |
| A session is out of context, or the work has to move to another agent | `ce-handoff` writes a handoff, and a new session can resume from it. |
