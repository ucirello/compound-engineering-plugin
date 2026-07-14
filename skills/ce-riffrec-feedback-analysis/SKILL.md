---
name: ce-riffrec-feedback-analysis
description: Analyze Riffrec feedback captures from bundles or standalone recordings. Always load for `riffrec-*.zip`, `session.json` + `events.json` + `recording.webm` + `voice.webm` bundles, `.mp4`/`.mov`/`.webm` videos, `.m4a`/`.mp3`/`.wav` audio, or capture/share requests.
---

# Riffrec Feedback Analysis

Turn raw product feedback into structured evidence for downstream agents. This skill is the consumption side of [Riffrec](https://github.com/kieranklaassen/riffrec), a capture tool that records synchronized screen + voice + event sessions and emits a `riffrec-*.zip` bundle.

## Choose the path

Route to the matching reference based on the input. Read only that reference; do not load the others.

- **Setup** — user has no recording yet and asks how to install Riffrec, capture a session, or share feedback. Read `references/install-riffrec.md`.
- **Quick bug report** — input is a short recording (under ~60 seconds), the user describes a single specific issue, or asks for "quick", "small", or "just transcribe". Read `references/quick-bug-report.md`. Emit one concise bug report; skip the full artifact set and brainstorm handoff.
- **Extensive analysis** — input is a longer recording, contains multiple issues / requirements / workflow walkthroughs, or the user wants requirements or brainstorm material. Read `references/extensive-analysis.md`. Always continue into the `ce-brainstorm` skill.

When the input is ambiguous (e.g., a zip arrived without context), inspect the recording length and event count before choosing. If still unclear, ask the user which path applies before running anything heavy.

## Common rules

- Keep raw recordings, audio chunks, zip contents, session dumps, and extracted screenshots local-only by default. The analyzer writes output-local `.gitignore` rules to prevent newly created `raw/` or `frames/` files from being tracked. These rules do not protect media already tracked by JJ: the analyzer queries the exact output media paths and refuses to overwrite them unless the user explicitly approves `--allow-untrack-tracked-media`.
- Text/metadata artifacts (requirements kickoff material, analysis summaries, problem analyses, source manifests) may remain in the JJ working-copy change when they are needed for traceability and contain no sensitive data.
- Use repo-relative screenshot paths in any document retained in JJ history so later agents can open the evidence without absolute local paths.

## Analyzer entrypoint

All non-setup paths share the same analyzer, which ships in this skill's `scripts/` directory. The Bash tool's working directory is the user's project, not the skill directory, so a bare `scripts/<name>` path will not resolve. Invoke it by the skill's own absolute path: set `SKILL_DIR` to the directory you loaded this `ce-riffrec-feedback-analysis` SKILL.md from, in the same command (shell state does not persist between Bash calls):

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
python "$SKILL_DIR/scripts/analyze_riffrec_zip.py" /path/to/input
```

Accepted inputs: a Riffrec `.zip`, an `.mp4` / `.mov` / `.webm` video, an `.m4a` / `.mp3` / `.wav` audio file, or a meeting-notes `.md`. Use `--output-dir <dir>` to control where artifacts land. In repos with `docs/brainstorms/`, the default remains `docs/brainstorms/riffrec-feedback/` as a documented evidence/kickoff-artifact exception; it is not the durable `ce-brainstorm` output convention. The quick path overrides the output dir to `$(jj workspace root)/.tmp/rocketclaw/` scratch, falling back to local `.tmp/rocketclaw/` when no JJ workspace root is available, so generated evidence does not pollute durable project paths.

JJ honors the generated `.gitignore`; there is no `.jjignore`. Ignore rules do not retroactively untrack paths. Never claim they protect already tracked media and never untrack it implicitly. When the analyzer refuses an existing output, obtain explicit user approval before re-running with `--allow-untrack-tracked-media`; that option writes the ignore rules, runs `jj file untrack` for the exact output `raw/` and `frames/` paths, and proceeds only if untracking succeeds.

The output format used by the extensive path is documented in `references/feedback-format.md`.
