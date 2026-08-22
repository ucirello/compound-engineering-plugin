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

- Keep raw recordings, audio chunks, zip contents, session dumps, and extracted screenshots local-only by default. Do not include `raw/` or `frames/` directories in a Jujutsu change unless the user explicitly asks and privacy is acceptable.
- Text/metadata artifacts (requirements kickoff material, analysis summaries, problem analyses, source manifests) may remain in the current Jujutsu change when they are needed for traceability and contain no sensitive data.
- Use repo-relative screenshot paths in any durable document so later agents can open the evidence without absolute local paths.

## Jujutsu workflow

Use `jj status`, `jj diff`, and `jj log -r ::@` for repository inspection. Jujutsu snapshots the working copy automatically, so keep local-only evidence under the workspace's ignored paths or outside the durable artifact tree and verify that it is absent from the intended change before handing off.

When composing a Jujutsu change description, inspect the project's active instructions and the description syntax visible in `jj log -r ::@`; those runtime conventions win. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Apply compatible Go guidance only to quality, clarity, and structure; do not impose fixed syntax or content. Use `jj describe -m "<description-composed-from-runtime-conventions>"` to describe the current change, or `jj commit -m "<description-composed-from-runtime-conventions>"` only when the workflow must also start a new change.

The output format used by the extensive path is documented in `references/rocketclaw-feedback-format.md`.
