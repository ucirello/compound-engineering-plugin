# Troubleshooting RocketClaw

`docs/` and `README.md` paths refer to the RocketClaw package sources described in `SKILL.md`.

| What the user sees | What to tell them |
|---|---|
| A skill is missing, or behaves the old way after an update | For OpenCode V2, check the configured RocketClaw plugin source against the package `README.md`, then start a new session. For a separate legacy marketplace installation, refresh the marketplace before updating; use that installation's `docs/install/upgrading.md` for Claude Code, Codex, and Grok Bot or its instructions for other hosts. |
| An old copy of a skill keeps running after an update | Check for a second skill or plugin registration shadowing RocketClaw. If an earlier Bun install is responsible, use that installation's applicable cleanup instructions; do not remove a copy until it is identified. |
| The agent will not start a skill it recommended | The skill is manual-only, so the user has to type it. `references/skill-map.md` marks these. |
| The slash command is not recognized | OpenCode uses `/skill-name`. Codex uses `$skill-name`. On oh-my-pi, a manual-only skill needs `/skill:<name>`. Devin uses `/<installed-plugin-namespace>:<skill>`. |
| A skill says a tool is missing | `ce-setup` reports which tools are missing and how to install them. Install only what the workflow needs. |
| A cross-model pass or oracle peer did not run | Read the actual error and run report. Distinguish a depth limit (check the effective setting against `starting-and-running.md`), delegation denial, rejected or unavailable model route, and missing tool. A skill that explicitly requests reviewers qualifies where the host permits user- or skill-requested delegation; that does not grant model overrides or bypass a denial. An inherited-model review may be useful where allowed, but it is not a cross-model pass; report a missing required route as incomplete. `ce-setup` reports missing tools, the `ce-pov` guide lists peer requirements, and `docs/guides/configuration.md` covers opting out of the automatic pass. |
| Plans or learnings are not where the user expected | `docs_root` in `.rocketclaw/config.yaml` moves every artifact folder. Format options can also change ideation, brainstorm, and plan files from `.md` to `.html`. |
| `ce-compound` wrote nothing | It captures only what the final code, tests, standards, and docs do not already show, so skipping a routine fix is correct. If a lesson was missed, run it again and say what the lesson was. |
| Learnings are captured only when the user asks | A standing instruction fixes this. `ce-setup` offers one when the repo tracks its learnings. |
| New plans ignore past learnings | Check that `<root>/solutions/` holds learnings and that `ce-plan` ran in this repo. A `ce-compound` refresh handles learnings that have gone stale. |
| A hands-off run stopped before merging | That is expected. Merging normally stays with the user. The `lfg` guide page covers where a run ends. |
| The agent's last reply made no sense | `wtf` explains it plainly. |
| A session is out of context, or the work has to move to another agent | `ce-handoff` writes a handoff, and a new session can resume from it. |
