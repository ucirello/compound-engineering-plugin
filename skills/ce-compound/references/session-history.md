# Session history (Phase 1 step 4)

## Session context

Resolve two values at runtime with the shell tool before Phase 1 session-history filtering. Run each as its own command and read its exit status — a non-zero exit is a normal state here, not an error to route around:

- **Workspace bookmarks** - run `jj bookmark list -r 'heads(::@ & bookmarks())'`. Use returned names for provider-label filtering; skip label filtering when empty or unavailable.
- **Workspace root** - run `jj root`. Use it for repository filtering; fall back to the working directory when unavailable.

#### 4. **Session History** (internal flow after launching the parallel block — automatic in Full mode, including non-interactive)
   - This is a two-stage probe: the cheap discovery+metadata pass below always executes, and the expensive extraction+synthesis executes only when the probe clears the relevance gate (see **Escalation gate** below).
   - Run session discovery, bookmark-label/keyword filtering, scan-window selection, deep-dive selection, and per-session extraction with `scripts/session-history/`.
   - Read the skill-local synthesis prompt at `references/agents/session-historian.md`, then dispatch a generic subagent using that prompt content. Do not dispatch a standalone agent by type/name.

   **Session-history payload — keep tight.** A long, keyword-rich payload licenses widening. Use this shape:

   - **Session context** (only when resolved): workspace name and nearest bookmark names.
   - **Time window**: explicit `7 days` unless the documented problem clearly spans a longer arc.
   - **Problem topic**: one sentence naming the concrete issue — error message, module name, what broke and how it was fixed. Not a paragraph; not a bullet list of related topics.
   - **Filter rule (one line)**: "Only surface findings directly relevant to this specific problem. Ignore unrelated work from the same sessions or bookmarks."
   - **Output schema**:

     ```
     Structure your response with these sections (omit any with no findings):
     - What was tried before
     - What didn't work
     - Key decisions
     - Related context
     ```

   Do not append additional context blocks, exclusion lists, or topic-keyword bullets — verbose payloads give the session-history flow license to keep widening the search and rapidly compound wall time. If keyword search is needed, the internal flow owns that decision based on the topic.
   - Returns a structured digest, or `no relevant prior sessions`. Either is a valid final Phase 1 input, and the documentation gets written without session context when it is the latter.

   **Script resolution.** Set `SKILL_DIR` to the absolute path of the directory containing the SKILL.md you just read, and run the bundled scripts from `"$SKILL_DIR/scripts/session-history/"`. Set `SKILL_DIR` inline in each bash block below (shell state does not persist between commands). If the bundled scripts are genuinely not present on disk under `"$SKILL_DIR/scripts/session-history/"`, skip session history visibly with: "Session history bundled scripts were not found in this skill's directory; skipping the session-history probe for this run." Continue Phase 2 without session context.

   **Discovery pipeline.** Infer the scan window from the problem topic, starting with 7 days. Run discovery and metadata extraction:

   ```bash
   SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
   if [ -f "$SKILL_DIR/scripts/session-history/discover-sessions.sh" ] && [ -f "$SKILL_DIR/scripts/session-history/extract-metadata.py" ]; then
     PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
     REPO_ROOT=$(jj root 2>/dev/null || pwd); REPO_NAME=$(basename "$REPO_ROOT"); SCAN_DAYS="7"; bash "$SKILL_DIR/scripts/session-history/discover-sessions.sh" "$REPO_NAME" "$SCAN_DAYS" --cwd "$REPO_ROOT" | tr '\n' '\0' | xargs -0 "$PY" "$SKILL_DIR/scripts/session-history/extract-metadata.py" --cwd-filter "$REPO_ROOT";
   else echo "Session history bundled scripts were not found in this skill's directory; skipping the session-history probe for this run."; fi
   ```

   Scan the supported providers documented by the bundled discovery script. Use recorded `cwd` for workspace filtering and provider ref labels only as hints against the nearest Jujutsu bookmarks. Sessions without usable workspace identity are dropped unless the provider lacks that field by design. If no files are processed, return `no relevant prior sessions`. When bookmark labels do not match, derive 2-4 topic keywords and rerun metadata extraction. Retain at most five candidates ranked by bookmark-label match, keyword count, useful size, and recency. Exclude the current session.

   **Escalation gate.** Escalate only when a candidate has a nearest-bookmark label match or at least two topic-keyword matches. Otherwise record `no relevant prior sessions` and skip extraction and synthesis.

   **Extraction pipeline.** Create `SCRATCH="$RUN_DIR/sessions"` with mode `0700`. For each selected session, write extracted content there:

   ```bash
   SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
   SCRATCH="$RUN_DIR/sessions"; (umask 077; mkdir -p "$SCRATCH") || exit 1; chmod 700 "$SCRATCH" || exit 1;
   if [ -f "$SKILL_DIR/scripts/session-history/extract-skeleton.py" ]; then
     PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
     "$PY" "$SKILL_DIR/scripts/session-history/extract-skeleton.py" --output "$SCRATCH/<session-id>.skeleton.txt" < <session-file>;
   else echo "Session history bundled scripts were not found in this skill's directory; skipping the session-history probe for this run."; fi
   ```

   Use `extract-errors.py` selectively when dead ends or recurring errors are likely useful. Pass only the scratch file paths and metadata to the synthesis subagent.

   **Synthesis dispatch.** Build a generic subagent prompt containing:
   - the full content of `references/agents/session-historian.md`
   - `problem_topic`
   - `scratch_dir`
   - a `sessions` array with extracted file paths and metadata
   - the output schema above
   - the filter rule above

   The subagent reads only the scratch paths, **writes its prose findings to `{run_dir}/session-history.md`, and returns only that artifact path once the write is confirmed** (same #956 reliability rationale — session-history findings are long-form prose prone to summary-collapse). If `{run_id}` did not resolve or the artifact write failed, it returns the prose inline instead (per the inline-fallback rule above). If synthesis fails, note the failure and continue without session context.
