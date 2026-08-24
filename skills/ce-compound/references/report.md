# Completion reports

## Success Output

**User-runnable refresh rendering.** The reports below print a `ce-compound-refresh` invocation for the user to copy. Default to `/ce-compound-refresh <scope>`; use `$ce-compound-refresh <scope>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

### Non-interactive mode

Emit a structured terminal report and end the turn. No "What's next?" question, no blocking prompt. End with `Documentation complete` as the terminal signal so callers can detect completion.

For `depth:lightweight`, report the mode, artifact path and write result, track, category, mechanical grounding result, solution-store discoverability result, vocabulary result and discoverability result, and any narrowly scoped refresh recommendation. End with the literal terminal signal `Documentation complete`.

For `depth:full` or a backward-compatible non-interactive call with no depth token, report the mode, artifact path and write result, track, category, overlap decision, grounding adjudication, instruction-file result, vocabulary result, and any narrowly scoped refresh recommendation. End with the literal terminal signal `Documentation complete`.

When no doc was written, report non-interactive mode and one sentence naming the unmet precondition. End with the literal terminal signal `Documentation skipped` so callers can distinguish success from no-op.

### Interactive mode

Report the selected mode, supplementary evidence used, each Phase 1 result, grounding checks and adjudications, optional specialist reviews, files written, discoverability outcome, vocabulary outcome, and any narrowly scoped refresh recommendation. Use neutral placeholders for project-specific values and omit sections with no result.

**End the turn after the summary — `ce-compound` does not present a "What's next?" menu.** The doc is written and any cross-references the workflow found are already in it. Cross-doc maintenance (fixing references in *other* docs, consolidation) is deferred to `ce-compound-refresh` via the `Refresh recommendation` line above — the skill designed for it — not auto-applied here, which would edit tracked docs beyond the one deliverable. If the user wants to view the file or take a follow-up action, they will ask. (Interactive mode only.)

**Interactive high-overlap update:** report the existing artifact path, matched overlap dimensions, update action, and `last_updated` result with neutral placeholders. In non-interactive mode, carry the same facts in the overlap field rather than a separate block.

## Common Mistakes to Avoid

| Wrong | Correct |
|----------|-----------|
| Subagents write product files into `docs/` or edit tracked paths | Subagents write only scratch artifacts under `<run-dir>/` and return the path; orchestrator writes the one final doc |
| Subagent returns a long prose body only as its inline response | Subagent writes full output to its run artifact; orchestrator Reads it back (inline return is fallback only) |
| Research and assembly run in parallel | Research completes → then assembly runs |
| Non-interactive Discoverability Check edits AGENTS.md/CLAUDE.md | non-interactive Full reports `Instruction-file edit: gap noted, not applied`; non-interactive Lightweight emits a discoverability tip; only interactive Full applies the edit after consent |
| Creating a new doc when an existing doc covers the same problem | Check overlap assessment; update the existing doc when overlap is high |
| Asserting code behavior or merge-state from conversation memory | Read the defining source line before asserting; cite PR numbers over SHAs; soften unverifiable claims (Phase 1 extractor rules, re-checked in Phase 2.45) |
| Batching several learnings through one run and stitching cross-references between drafts | One learning per run; run the skill sequentially for each additional learning |
