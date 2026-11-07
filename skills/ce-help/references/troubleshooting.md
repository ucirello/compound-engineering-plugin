# Troubleshooting RocketClaw

`docs/` and `README.md` paths are public pages. `SKILL.md` gives their URLs.

| What the user sees | What to tell them |
|---|---|
| A skill is missing, or behaves the old way after an update | Follow the installed package's OpenCode V2 update instructions, then start a new session. `docs/install/upgrading.md` and `README.md#more-install-options` hold host-specific compatibility instructions; do not run another harness to repair OpenCode dispatch. |
| An old copy of a skill keeps running after an update | An earlier Bun install may be shadowing the plugin. `docs/install/upgrading.md` has the cleanup command. |
| The agent will not start a skill it recommended | The skill is manual-only, so the user has to type it. `references/skill-map.md` marks these. |
| The slash command is not recognized | OpenCode uses `/skill-name`. Compatibility mappings: Codex uses `$skill-name`; on oh-my-pi, a manual-only skill needs `/skill:<name>`; Devin uses its installed package namespace. |
| A skill says a tool is missing | `ce-setup` reports which tools are missing and how to install them. Install only what the workflow needs. |
| A cross-model pass or oracle peer did not run | The run's report says why. `ce-setup` reports missing tools, and the `ce-pov` guide page lists what peers need. Config can also turn the automatic review pass off, so check `docs/guides/configuration.md`. |
| Plans or learnings are not where the user expected | `docs_root` in `.rocketclaw/config.yaml` moves every artifact folder. Format options can also change ideation, brainstorm, and plan files from `.md` to `.html`. |
| `ce-compound` wrote nothing | It captures only what the final code, tests, standards, and docs do not already show, so skipping a routine fix is correct. If a lesson was missed, run it again and say what the lesson was. |
| Learnings are captured only when the user asks | A standing instruction fixes this. `ce-setup` offers one when the repo tracks its learnings. |
| New plans ignore past learnings | Check that `<root>/solutions/` holds learnings and that `ce-plan` ran in this repo. A `ce-compound` refresh handles learnings that have gone stale. |
| A hands-off run stopped before merging | That is expected. Merging normally stays with the user. The `lfg` guide page covers where a run ends. |
| The agent's last reply made no sense | `wtf` explains it plainly. |
| A session is out of context, or the work has to move to another agent | `ce-handoff` writes a handoff, and a new session can resume from it. |
| `ce-compound` faces context pressure in an interactive session | Delegate Full mode to one fresh native subagent loading `ce-compound mode:non-interactive depth:full`. Pass the source session ID read via shell from `OPENCODE_SESSION_ID`, known title, absolute JJ workspace root, existing learning-doc path and a one-sentence topic, without predigesting the conversation. The delegate reads the source through `opencode session export <id>` or `opencode api get /api/session/<id>/message`, saves under local `.tmp/`, and reduces it to user/assistant text and tool names/short results; never read internal storage. The source session is primary evidence; exclude only the delegate's own session. Parent relays the report/doc and offers consented interactive-only discoverability and pack destination, without a second Full pass or doc rewrite. Lightweight is only for actual unavailable-tool, permission or depth errors; rerun from the same source session once delegation is available. Explicit non-interactive depth tokens remain authoritative. |
