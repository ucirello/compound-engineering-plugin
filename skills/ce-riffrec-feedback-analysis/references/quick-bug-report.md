# Quick bug report path

Use this path when the input is a short recording (under ~60 seconds), the user describes a single specific issue, or the user explicitly asks for "quick", "small", "simple", or "just transcribe". The goal is one concise bug report, not a multi-artifact requirements package.

## Workflow

1. Run the analyzer in the workspace-local RocketClaw temp namespace so generated evidence does not pollute tracked paths (`SKILL_DIR` is the directory containing the `ce-riffrec-feedback-analysis` SKILL.md; set it in the same command because shell state does not persist between Bash calls):

   ```bash
   SKILL_DIR="<absolute path of the directory containing the ce-riffrec-feedback-analysis SKILL.md>"
    if WORKSPACE_ROOT="$(jj workspace root 2>/dev/null)"; then
      OUTPUT_DIR="$WORKSPACE_ROOT/.tmp/rocketclaw/riffrec-quick/$(date +%Y%m%d-%H%M%S)-$$"
    else
      OUTPUT_DIR="$PWD/.tmp/rocketclaw/riffrec-quick/$(date +%Y%m%d-%H%M%S)-$$"
    fi
   python "$SKILL_DIR/scripts/analyze_riffrec_zip.py" /path/to/input --output-dir "$OUTPUT_DIR"
   ```

   Capture the printed output directory; later steps read from it.

2. Read only `analysis.md` from the workspace-local temp output. Skip `problem-analysis.md`, `review-prompt.md`, `requirements-kickoff.md`, and `source-materials.md` — they are designed for the extensive path.

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
- Do not include `raw/` or `frames/` in a JJ change. They remain under `.tmp/rocketclaw/` and may be removed after the report is complete.
- No source-mapping pass across the codebase.

## Escalation

If, while reading the transcript, the recording turns out to contain multiple distinct issues, requirements, or a workflow walkthrough, stop and tell the user: "This recording has more than one issue — switching to the extensive path." Then load `references/extensive-analysis.md` and re-run the analyzer with a non-temp output directory.
