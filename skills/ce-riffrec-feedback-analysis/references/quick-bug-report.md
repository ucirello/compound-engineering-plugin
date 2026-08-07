# Quick bug report path

Use this path when the input is a short recording (under ~60 seconds), the user describes a single specific issue, or the user explicitly asks for "quick", "small", "simple", or "just transcribe". The goal is one concise bug report, not a multi-artifact requirements package.

## Workflow

1. Resolve the workspace root with `jj workspace root` in a standalone shell call. If that fails because the input is outside a JJ workspace, use the current working directory. Then run the analyzer below that root's `.tmp` directory (`SKILL_DIR` is the directory containing the `ce-riffrec-feedback-analysis` SKILL.md; set it in the same command because shell state does not persist between Bash calls):

   ```bash
   SKILL_DIR="<absolute path of the directory containing the ce-riffrec-feedback-analysis SKILL.md>";
   WORKSPACE_ROOT="<absolute workspace root resolved above>";
   OUTPUT_DIR="$WORKSPACE_ROOT/.tmp/rocketclaw-quick-$(date +%Y%m%d-%H%M%S)-$$";
   mkdir -p "$OUTPUT_DIR";
   python "$SKILL_DIR/scripts/analyze_riffrec_zip.py" /path/to/input --output-dir "$OUTPUT_DIR"
   ```

   Capture the printed output directory; later steps read from it. Remove this run directory after the report is complete unless the user asks to retain it.

2. Read only `analysis.md` from the workspace-local scratch output. Skip `problem-analysis.md`, `review-prompt.md`, `requirements-kickoff.md`, and `source-materials.md` — they are designed for the extensive path.

3. Pick at most one or two screenshots from `frames/` that directly show the reported issue. Prefer frames near a verbal complaint, a failed click, a console error, or a failed network request.

4. Emit a single concise bug report. Default to printing it inline in the chat so the user can confirm before anything is written to disk. Only write a file if the user asks for one, and keep that generated file below the run directory in `<workspace-root>/.tmp/`.

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
- Do not track `raw/` or `frames/` in a JJ change. They live only in the workspace-local scratch directory and are removed after the report.
- No source-mapping pass across the codebase.

## Escalation

If the recording turns out to contain multiple distinct issues, requirements, or a workflow walkthrough, report that the quick path is escalating, then load `references/extensive-analysis.md` and re-run the analyzer in a new run directory below `<workspace-root>/.tmp/`. Preserve the escalation fact without requiring fixed wording.
