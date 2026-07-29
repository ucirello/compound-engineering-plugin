---
name: ce-riffrec-feedback-analysis
description: Analyze Riffrec feedback captures from bundles or standalone recordings. Always load for `riffrec-*.zip`, `session.json` + `events.json` + `recording.webm` + `voice.webm` bundles, `.mp4`/`.mov`/`.webm` videos, `.m4a`/`.mp3`/`.wav` audio, or capture/share requests.
---

# RocketClaw Riffrec Feedback Analysis

Turn raw product feedback into structured evidence for downstream work. This skill is the consumption side of [Riffrec](https://github.com/kieranklaassen/riffrec), a capture tool that records synchronized screen + voice + event sessions and emits a `riffrec-*.zip` bundle.

## Choose the path

Route to the matching reference based on the input. Read only that reference; do not load the others.

- **Setup** — user has no recording yet and asks how to install Riffrec, capture a session, or share feedback. Read `references/install-riffrec.md`.
- **Quick bug report** — input is a short recording (under ~60 seconds), the user describes a single specific issue, or asks for "quick", "small", or "just transcribe". Read `references/quick-bug-report.md`. Emit one concise bug report; skip the full artifact set and brainstorm handoff.
- **Extensive analysis** — input is a longer recording, contains multiple issues / requirements / workflow walkthroughs, or the user wants requirements or brainstorm material. Read `references/extensive-analysis.md`. Always continue into the `ce-brainstorm` skill.

When the input is ambiguous (e.g., a zip arrived without context), inspect the recording length and event count before choosing. If still unclear, ask the user which path applies before running anything heavy.

## Common rules

- Keep raw recordings, audio chunks, zip contents, session dumps, and extracted screenshots local-only by default. Do not include `raw/` or `frames/` directories in a described Jujutsu change unless the user explicitly asks and privacy is acceptable.
- Text/metadata artifacts (requirements kickoff material, analysis summaries, problem analyses, source manifests) may be included in a Jujutsu change when they are needed for traceability and contain no sensitive data.
- Use workspace-relative screenshot paths in any preserved document so later reviewers can open the evidence without absolute local paths.
- Use Jujutsu for local version-control operations. GitHub and `gh` remain allowed, as does necessary `jj git` interoperability; the exact `git log` wording below is not an operational command, so inspect history with syntax supported by the installed `jj log`.
- Inspect preservable artifacts with `jj status` and `jj diff`. When the user asks to preserve them in history, keep unrelated work out of the change. Repository-local instructions and observed history syntax take precedence. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Derive the description from the actual artifact diff and describe the change using locally supported `jj describe` syntax; do not impose a fixed prefix, type, scope, template, or example. Pass the neutral actor `ai:assistant` if an actor identifier is required. Use `jj new` before unrelated work. Create or move an explicit bookmark with `jj bookmark create <bookmark> -r <revision>` or `jj bookmark move <bookmark> --to <revision>`, and publish only when requested with `jj git push --bookmark <bookmark> --remote <remote>`.

## Analyzer entrypoint

All non-setup paths share the same analyzer, which ships in this skill's `scripts/` directory. The Bash tool's working directory is the user's project, not the skill directory, so a bare `scripts/<name>` path will not resolve. Invoke it by the skill's own absolute path: set `SKILL_DIR` to the directory you loaded this `ce-riffrec-feedback-analysis` SKILL.md from, in the same command (shell state does not persist between Bash calls):

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
python "$SKILL_DIR/scripts/analyze_riffrec_zip.py" /path/to/input
```

Accepted inputs: a Riffrec `.zip`, an `.mp4` / `.mov` / `.webm` video, an `.m4a` / `.mp3` / `.wav` audio file, or a meeting-notes `.md`. Use `--output-dir <dir>` to control where artifacts land. In workspaces with `docs/brainstorms/`, the default remains `docs/brainstorms/riffrec-feedback/` as a documented evidence/kickoff-artifact exception; it is not the durable `ce-brainstorm` output convention. The quick path overrides the output directory with workspace-local `.tmp/rocketclaw/` scratch so nothing pollutes the product tree.

The RocketClaw output format used by the extensive path is documented in `references/rocketclaw-feedback-format.md`.
