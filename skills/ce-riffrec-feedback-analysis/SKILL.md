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

- Use JJ for repository state and mutations: inspect the working-copy change with `jj status` and `jj diff`, and inspect history with `jj log`. JJ has no staging index and snapshots non-ignored files automatically.
- Keep raw recordings, audio chunks, zip contents, session dumps, and extracted screenshots local-only by default. Keep `raw/` and `frames/` out of the JJ working-copy change unless the user explicitly requests versioning and privacy is acceptable.
- Text and metadata artifacts may remain in the working-copy change when traceability needs them and they contain no sensitive data. Use workspace-relative screenshot paths in versioned documents.
- Use `gh` for GitHub operations. In a non-colocated Git-backed JJ workspace, point `GIT_DIR` at `jj git root` when `gh` needs the underlying Git repository. Preserve operational provider, GitHub, Git interoperability, and Git Bash constraints when they affect the workflow.
- When this skill composes, edits, validates, or recommends a JJ change description or commit message, apply this sentence exactly: Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime repository syntax wins; apply only compatible Go quality guidance. Derive the description from the actual change and do not impose a fixed prefix, type, scope, subject, body, template, or example.
- Do not add creator identity, generated-by text, model or harness identity, badges, bylines, signatures, or product branding to artifacts. Preserve model, provider, research, or human attribution only when it is evidence or an operational requirement. When a protocol requires a neutral actor, use `ai:assistant`; render it as `AI Assistant` in prose.

The output format used by the extensive path is documented in `references/rocketclaw-feedback-format.md`.
