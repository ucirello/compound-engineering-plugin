# Lightweight mode

### Lightweight Mode

<critical_requirement>
**Single-pass alternative — same artifact type, reduced research and validation.**

This mode skips parallel subagents entirely. The orchestrator performs all work in a single pass and writes the same solution-doc artifact type, but omits cross-referencing, duplicate detection, session-history research, and semantic grounding validation.

Non-interactive mode enters Lightweight only when explicitly invoked with `depth:lightweight`; otherwise it defaults to Full for backward compatibility.
</critical_requirement>

The orchestrator (main conversation) performs ALL of the following in one sequential pass:

1. **Extract from conversation**: Identify the problem and solution from conversation history. Also scan the "user's auto-memory" block injected into your system prompt, if present (Claude Code only) -- use any relevant notes as supplementary context alongside conversation history. Tag any memory-sourced content incorporated into the final doc with "(auto memory [claude])". Before asserting how code behaves (enum values, status semantics, limits, defaults), Read the defining line at the current tree — soften or attribute any claim you cannot verify. Cite PR numbers over bare commit SHAs, and phrase unmerged fixes as pending
2. **Classify**: Read `references/schema.yaml` and `references/yaml-schema.md`, then determine track, category, and filename. Sample existing docs under `.context/solutions/` and apply the corpus-first vocabulary rule.
3. **Write minimal doc**: Check the proposed `.context/solutions/[category]/[filename].md`. Update it only for the same problem; otherwise choose and re-check a distinct filename. This is exact-path collision handling only. Use the appropriate track template from `assets/resolution-template.md`.
   - YAML frontmatter with track-appropriate fields, applying the YAML-safety quoting rule for array items (see `references/yaml-schema.md` > YAML Safety Rules)
   - Bug track: Problem, root cause, solution with key code snippets, one prevention tip
   - Knowledge track: Context, guidance with key examples, one applicability note
4. **Vocabulary capture (update-only)**: if `.context/CONCEPTS.md` exists, read `references/concepts-vocabulary.md`, scan the doc and conversation, and refine qualifying entries silently. Do not bootstrap in lightweight mode. Record the outcome and emit a discoverability tip when needed.
5. **Read-only discoverability check**: assess whether active project instructions surface `.context/solutions/` using `references/refresh-and-discoverability.md`. Lightweight reports only; it never edits instructions.
   - `no gap` when active project instructions surface the knowledge store
   - `gap noted — instruction-file tip emitted` when active project instructions exist but do not surface it
   - `not applicable — no active project instructions` when no project instructions are active; emit no discoverability tip
6. **Mechanical claims check**: run `scripts/validate-doc-claims.py` against the written doc exactly as in `references/assembly.md` Phase 2.45 step 1 (same `SKILL_DIR` anchor, same adjudicate-not-auto-fix rule — read `references/grounding-validation.md` for the adjudication table when it flags anything). Lightweight skips only the semantic validator subagent, not this deterministic check.
7. **Frontmatter parser-safety check**: validate the written doc exactly as in `references/assembly.md` Phase 2 step 8, using the same bundled-script existence guard and manual fallback checklist. Fix any violation and repeat the check; do not report success until the written frontmatter is parser-safe.
8. **Skip specialized agent reviews** (`references/enhancement.md`) and the semantic grounding validator (`references/assembly.md` Phase 2.45 step 2) to conserve context

**User-runnable retry rendering.** In the lightweight completion output below, default to `/ce-compound`; use `$ce-compound` only when the active host is Codex or explicitly documents dollar-prefixed skill invocation. Render only the invocation as inline code and output one form only.

**Lightweight completion output:** In non-interactive Lightweight, do not emit this interactive block; use the depth-specific report under `Non-interactive mode` in `references/report.md` instead. In interactive Lightweight, emit:
```
✓ Documentation complete (lightweight mode)

File created:
- .context/solutions/[category]/[filename].md

[If discoverability check found instruction files don't surface the knowledge store:]
Tip: The project's active instructions do not surface .context/solutions/ to agents -
a brief mention helps all agents discover these learnings.

[If .context/CONCEPTS.md was refined and is not surfaced:]
Tip: The project's active instructions do not surface .context/CONCEPTS.md -
a one-line mention helps agents find the shared vocabulary.

Note: This was created in lightweight mode. For richer documentation
(cross-references, detailed prevention strategies, specialized reviews,
semantic grounding validation), re-run <rendered invocation> in a fresh session.
```

**No subagents are launched.** The learning is the deliverable; update-only vocabulary capture may also refine `.context/CONCEPTS.md`.

In lightweight mode, the overlap check is skipped (no Related Docs Finder subagent). This means lightweight mode may create a doc that overlaps with an existing one. That is acceptable — `ce-compound-refresh` will catch it later. Only suggest `ce-compound-refresh` if there is an obvious narrow refresh target. Do not broaden into a large refresh sweep from a lightweight session.

---
