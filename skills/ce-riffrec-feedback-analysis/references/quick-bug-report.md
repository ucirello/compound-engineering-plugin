# Quick bug report path

Use this path when the input is a short recording (under ~60 seconds), the user describes a single specific issue, or the user explicitly asks for "quick", "small", "simple", or "just transcribe". The goal is one concise bug report, not a multi-artifact requirements package.

## Workflow

1. Resolve `<workspace-root>` with `jj workspace root`; outside a JJ workspace, use the current directory. Create one private run directory under `<workspace-root>/.tmp/rocketclaw/ce-riffrec-feedback-analysis/`, set it as `OUTPUT_DIR`, set `INPUT_PATH` to the supplied capture, and use the invocation in `references/analyzer.md`. In a JJ workspace, existing ignore rules must exclude `.tmp/rocketclaw/` before creating the directory; otherwise stop rather than snapshotting scratch into `@`. Capture the analyzer's printed output directory because later steps read from it. Use this POSIX and Git Bash-compatible command:

   ```bash
   WORKSPACE_ROOT="$(jj workspace root 2>/dev/null)" || WORKSPACE_ROOT="$PWD"; SCRATCH_ROOT="$WORKSPACE_ROOT/.tmp/rocketclaw/ce-riffrec-feedback-analysis"; mkdir -p "$SCRATCH_ROOT"; OUTPUT_DIR="$SCRATCH_ROOT/quick-$(date +%Y%m%dT%H%M%S)-$$"; (umask 077; mkdir "$OUTPUT_DIR") || exit 1
   ```

2. Read only `analysis.md` from the scratch output. Skip `problem-analysis.md`, `review-prompt.md`, `requirements-kickoff.md`, and `source-materials.md` because they are designed for the extensive path.

3. Pick at most one or two screenshots from `frames/` that directly show the reported issue. Prefer frames near a verbal complaint, a failed click, a console error, or a failed network request.

4. Emit a single concise bug report. Default to printing it inline in the chat so the user can confirm before anything is written to disk. Only write a file if the user asks for one — and even then, prefer a single `bug-report.md` next to the source recording or in a path the user names. Do not auto-create `docs/brainstorms/...` for this path.

## Bug report shape

Keep it focused and short. Include only what the recording supports:

- **Title** — one short sentence naming the broken behavior.
- **Steps to reproduce** — bullet list reconstructed from clicks and transcript.
- **Expected vs. actual** — what the user said should happen vs. what happened.
- **Evidence** — transcript quote(s) with timestamps, plus 0–2 screenshot references.
- **Suggested next step** — single sentence: file an issue, open `ce-debug`, or escalate to extensive analysis if more issues surfaced.

## Source mapping (optional, only if obvious)

If the workspace is the product source code AND the broken surface is named clearly in the transcript or visible UI, add one short "Likely surface" line with file path and confidence (`High` / `Medium` / `Low`). Skip this section entirely when the mapping is speculative — speculative mappings belong in the extensive path, not a quick bug report.

## What to skip

- No `problem-analysis.md`, no `requirements-kickoff.md`, no Visual / Functional / Requirement / UX category split.
- No automatic handoff to `ce-brainstorm`. The quick path ends with the bug report.
- Keep `raw/` and `frames/` out of the JJ working-copy change. They live only in this run's workspace-local scratch directory; remove that directory after the report is delivered.
- No source-mapping pass across the codebase.

## Escalation

If the transcript contains multiple distinct issues, requirements, or a workflow walkthrough, stop the quick route, explain that the input requires extensive analysis using details from the recording, then load `references/extensive-analysis.md` and re-run the analyzer with its durable output policy.
