---
name: ce-riffrec-feedback-analysis
description: "Analyze recorded product feedback into evidence for bugs and requirements. Use when a Riffrec capture or other screen, voice, or notes artifact needs interpretation. Use for Riffrec setup, capture, or sharing help when no recording exists yet."
---

# Riffrec Feedback Analysis

Turn raw product feedback into structured evidence for downstream agents. This skill is the consumption side of [Riffrec](https://github.com/kieranklaassen/riffrec), a capture tool that records synchronized screen + voice + event sessions and emits a `riffrec-*.zip` bundle.

**Done:**

- Setup ends with a current capture/share path.
- Quick analysis ends with one evidence-backed bug report and no durable artifact unless requested.
- Extensive analysis ends with the complete evidence set and a `ce-brainstorm` handoff unless the user asked for extraction only.
- A missing input, analyzer failure, or unresolved route ends with an actionable blocker rather than a partial success claim.

## Choose the path

Route from the input. Read only the references named for that route; do not load the other path references.

- **Setup** — user has no recording yet and asks how to install Riffrec, capture a session, or share feedback. Read `references/install-riffrec.md`.
- **Quick bug report** — input is a short recording (under ~60 seconds), the user describes a single specific issue, or asks for "quick", "small", or "just transcribe". Read `references/analyzer.md`, then `references/quick-bug-report.md`.
- **Extensive analysis** — input is longer, contains multiple issues, requirements, or a workflow walkthrough, or the user wants requirements material. Read `references/analyzer.md`, then `references/extensive-analysis.md`. Continue into `ce-brainstorm` unless the user explicitly asked only to extract or analyze artifacts.

When the input is ambiguous (e.g., a zip arrived without context), inspect the recording length and event count before choosing. If still unclear, ask the user which path applies before running anything heavy.

## Common rules

- Resolve the workspace root with `jj workspace root`. If it is unavailable, use the physical current directory only for local `.tmp` scratch; do not treat that fallback as a Jujutsu workspace root.
- Keep raw recordings, audio chunks, zip contents, session dumps, and extracted screenshots local-only and untracked by default. Do not track `raw/` or `frames/` unless the user explicitly asks and privacy is acceptable.
- Text and metadata artifacts may be tracked when needed for traceability and they contain no sensitive data. Inspect local state with `jj status`; Jujutsu snapshots non-ignored files and has no staged/unstaged split.
- Use workspace-relative screenshot paths in any tracked document so later agents can open the evidence without absolute local paths.
- Whenever an output composes, edits, recommends, or validates a commit message or Jujutsu change description, include this exact sentence at that site: "Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards." Apply the project's active instructions first and the conventions visible in the current `jj log` second; the quoted `git log` wording is non-operational and does not authorize Git commands. Use compatible Go guidance only for message quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example.

The output format used by the extensive path is documented in `references/rocketclaw-feedback-format.md`.

When printing a user-runnable brainstorm handoff, default to `/ce-brainstorm <requirements-kickoff-path>`; use `$ce-brainstorm <requirements-kickoff-path>` only on Codex or a host that documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only. Agent-to-agent routing remains semantic through `ce-brainstorm`.
