---
name: ce-riffrec-feedback-analysis
description: Analyze RocketClaw feedback captures from bundles or standalone recordings. Always load for `rocketclaw-*.zip`, `session.json` + `events.json` + `recording.webm` + `voice.webm` bundles, `.mp4`/`.mov`/`.webm` videos, `.m4a`/`.mp3`/`.wav` audio, or capture/share requests.
---

# RocketClaw Feedback Analysis

Turn raw product feedback into structured evidence for downstream agents. RocketClaw records synchronized screen, voice, and event sessions and emits a `rocketclaw-*.zip` bundle. Its capture format builds on [Kieran Klaassen's Riffrec project](https://github.com/kieranklaassen/riffrec).

## Choose the path

Route to the matching reference based on the input. Read only that reference; do not load the others.

- **Setup** — user has no recording yet and asks how to install RocketClaw, capture a session, or share feedback. Read `references/install-riffrec.md`.
- **Quick bug report** — input is a short recording (under ~60 seconds), the user describes a single specific issue, or asks for "quick", "small", or "just transcribe". Read `references/quick-bug-report.md`. Emit one concise bug report; skip the full artifact set and brainstorm handoff.
- **Extensive analysis** — input is a longer recording, contains multiple issues / requirements / workflow walkthroughs, or the user wants requirements or brainstorm material. Read `references/extensive-analysis.md`. Always continue into the `ce-brainstorm` skill.

When the input is ambiguous (e.g., a zip arrived without context), inspect the recording length and event count before choosing. If still unclear, ask the user which path applies before running anything heavy.

## Common rules

- Keep raw recordings, audio chunks, zip contents, session dumps, and extracted screenshots untracked by default. Do not include `raw/` or `frames/` directories in a JJ change unless the user explicitly asks and privacy is acceptable.
- Text/metadata artifacts (requirements kickoff material, analysis summaries, problem analyses, source manifests) may be tracked in a JJ change when they are needed for traceability and contain no sensitive data.
- Use workspace-relative screenshot paths in any tracked document so later agents can open the evidence without absolute local paths.
- Write analyzer outputs only below `<workspace-root>/.tmp/`. Resolve the workspace root with `jj workspace root`; when the input is outside a JJ workspace, use the current working directory as the workspace root. Do not write generated artifacts beside the source or under a durable documentation directory.
- Do not add branding, generated-by text, or creator, model, provider, tool, agent, runtime, workflow, co-author, or other attribution.
- Do not add product branding, generated-by text, or creator, model, provider, tool, agent, runtime, workflow, or co-author attribution to generated artifacts or workflow messages. RocketClaw and Riffrec references that identify the capture format or operational source are product facts, not generated attribution.

## Analyzer entrypoint

All non-setup paths share the same analyzer, which ships in this skill's `scripts/` directory. The Bash tool's working directory is the user's project, not the skill directory, so a bare `scripts/<name>` path will not resolve. Invoke it by the skill's own absolute path: set `SKILL_DIR` to the directory you loaded this `ce-riffrec-feedback-analysis` SKILL.md from, in the same command (shell state does not persist between Bash calls):

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
python "$SKILL_DIR/scripts/analyze_riffrec_zip.py" /path/to/input
```

Accepted inputs: a RocketClaw `.zip`, an `.mp4` / `.mov` / `.webm` video, an `.m4a` / `.mp3` / `.wav` audio file, or a meeting-notes `.md`. The default output is `<workspace-root>/.tmp/rocketclaw-feedback/<source-stem>`. Use `--output-dir <dir>` to choose another location below `<workspace-root>/.tmp/`; the analyzer rejects output paths outside that boundary.

The RocketClaw output format used by the extensive path is documented in `references/rocketclaw-feedback-format.md`.
