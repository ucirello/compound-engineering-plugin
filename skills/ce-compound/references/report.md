# Completion reports

## Success Output

**User-runnable refresh rendering.** The reports below print a `ce-compound-refresh` invocation for the user to copy. Default to `/ce-compound-refresh <scope>`; use `$ce-compound-refresh <scope>` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

### Non-interactive mode

Emit a structured terminal report and end the turn. No "What's next?" question, no blocking prompt. End with `Documentation complete` as the terminal signal so callers can detect completion.

For `depth:lightweight`, use this lower-overhead report after the Lightweight Mode workflow:

```
✓ Documentation complete (non-interactive lightweight mode)

File: <root>/solutions/<category>/<filename>.md  (created | updated)
Track: <bug | knowledge>
Category: <category>
Grounding: <mechanical check clean | N flags adjudicated>
Discoverability: <no gap | gap noted — instruction-file tip emitted | not applicable — no active project instructions>
CONCEPTS.md: <not present | scanned, no qualifying terms | updated — N added, N refined, N folded, N scrubbed>
CONCEPTS.md discoverability: <not checked — CONCEPTS.md unchanged | no gap | gap noted — instruction-file tip emitted | not applicable — no active project instructions>
Refresh recommendation: <none | scope hint for /ce-compound-refresh>

Documentation complete
```

For `depth:full` or backward-compatible non-interactive calls with no depth token, use the Full report:

```
✓ Documentation complete (non-interactive mode)

File: <root>/solutions/<category>/<filename>.md  (created | updated)
Track: <bug | knowledge>
Category: <category>
Overlap: <none | low | moderate — see <path> | high — existing doc updated>
Grounding: <clean | N flags adjudicated (X fixed, Y annotated, Z confirmed) | N claims softened or corrected | degraded — change-state claims unverified offline>
Instruction-file edit: <none needed | gap noted, not applied>
CONCEPTS.md: <scanned, no qualifying terms | created with N entries (M seeded from the learning's area) | updated — N added, N refined, N folded, N scrubbed>
Refresh recommendation: <none | scope hint for /ce-compound-refresh>

Documentation complete
```

When no doc was written, emit a structured failure and end with `Documentation skipped` so callers can distinguish success from no-op:

```
✗ Documentation skipped (non-interactive mode)

Reason: <one-sentence explanation>

Documentation skipped
```

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
| Asserting code behavior or change-state from conversation memory | Read the defining source line before asserting; cite PR numbers over bare commit IDs; soften unverifiable claims (Phase 1 extractor rules, re-checked in Phase 2.45) |
| Batching several learnings through one run and stitching cross-references between drafts | One learning per run; run the skill sequentially for each additional learning |
