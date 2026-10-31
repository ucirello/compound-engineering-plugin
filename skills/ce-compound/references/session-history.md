# Session history (Phase 1 step 4)

## Session context

Resolve two values at runtime with the shell tool before Phase 1 session-history filtering. Run each as its own command and read its exit status. A non-zero exit is a normal state here, not an error to route around:

- **Bookmark**: run `jj log -r @ --no-graph -T 'bookmarks'` from the target absolute workspace root. Use an unambiguous bookmark to filter session history; otherwise skip bookmark filtering.
- **Repo root**: run `jj workspace root` from the target absolute workspace root. Use it as the session-history repo filter. Outside a JJ repository, fall back to the absolute working directory.

### Passed OpenCode source session (mandatory primary evidence)

For a delegated Full run, read the passed source session before drafting. Shell-read the delegated run's own `OPENCODE_SESSION_ID`; exclude only that ID, never the passed parent source ID. Use only `opencode session export <source-session-id>` or `opencode api get /api/session/<source-session-id>/message`, saving the response to `<absolute-workspace-root>/.tmp/rocketclaw/ce-compound/<run-id>/source.json`. Never read OpenCode SQLite or internal session storage. Reduce the saved export before reading: run the bundled `scripts/session-history/reduce-opencode.py` with the saved input and a `.txt` output in that same run directory. It preserves user/assistant text, tool names and short tool results, excluding reasoning and tool inputs. Read only the reduced output. Treat an empty, malformed, unsupported, or failed export as missing primary evidence and report `Documentation skipped` rather than inferring evidence from a topic hint. An already-written learning path must be read and updated rather than duplicated when it covers this problem.

This mandatory source read precedes and is independent of the optional prior-session probe below. Legacy discovery finding zero sessions does not erase the passed source evidence. The source is not subject to prior-session recency, keyword, branch, or five-candidate gates. Supported OpenCode prior-session exports may also be reduced with this helper; do not inspect internal storage to discover them.

#### 4. **Session History** (internal flow after dispatching the Related Docs Finder; automatic in Full mode, including non-interactive)
   - This is a two-stage probe: the cheap discovery+metadata pass below always executes, and the expensive extraction+synthesis executes only when the probe clears the relevance bar (see **Escalation check** below).
   - Run session discovery, branch/keyword filtering, scan-window selection, deep-dive selection, and per-session extraction directly inside this skill using `scripts/session-history/`.
   - Read the skill-local synthesis prompt at `references/agents/session-historian.md`, then dispatch a generic subagent using that prompt content. Do not dispatch a standalone agent by type/name.

   **Keep the session-history payload tight.** A long, keyword-rich payload invites the flow to widen its search. Use this shape:

   - **Session context** (only if the values resolved cleanly above; otherwise omit): repo name, current JJ bookmark.
   - **Time window**: explicit `7 days` unless the documented problem clearly spans a longer arc.
   - **Problem topic**: one sentence naming the concrete issue — error message, module name, what broke and how it was fixed. Not a paragraph; not a bullet list of related topics.
   - **Filter rule (one line)**: "Only surface findings directly relevant to this specific problem. Ignore unrelated work from the same sessions or branches."
   - **Output schema**:

     ```
     Structure your response with these sections (omit any with no findings):
     - What was tried before
     - What didn't work
     - Key decisions
     - Related context
     ```

   Do not append additional context blocks, exclusion lists, or topic-keyword bullets. Verbose payloads let the session-history flow keep widening the search, which rapidly compounds wall time. If keyword search is needed, the internal flow decides that from the topic.
   - Returns a structured digest, or `no relevant prior sessions`. Either is a valid final Phase 1 input, and the documentation gets written without session context when it is the latter.

   **Script resolution.** Set `SKILL_DIR` to the absolute path of the directory containing the SKILL.md you just read, and run the bundled scripts from `"$SKILL_DIR/scripts/session-history/"`. Set `SKILL_DIR` inline in each bash block below (shell state does not persist between commands). If the bundled scripts are genuinely not present on disk under `"$SKILL_DIR/scripts/session-history/"`, skip session history visibly with: "Session history bundled scripts were not found in this skill's directory; skipping the session-history probe for this run." Continue Phase 2 without session context.

   **Discovery pipeline.** Infer the scan window from the problem topic, starting with 7 days. Run discovery and metadata extraction:

   ```bash
   SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
   if [ -f "$SKILL_DIR/scripts/session-history/discover-sessions.sh" ] && [ -f "$SKILL_DIR/scripts/session-history/extract-metadata.py" ]; then
     PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
     REPO_ROOT=$(jj workspace root 2>/dev/null || pwd -P); REPO_NAME=$(basename "$REPO_ROOT"); SCAN_DAYS="7"; bash "$SKILL_DIR/scripts/session-history/discover-sessions.sh" "$REPO_NAME" "$SCAN_DAYS" --cwd "$REPO_ROOT" | tr '\n' '\0' | xargs -0 "$PY" "$SKILL_DIR/scripts/session-history/extract-metadata.py" --cwd-filter "$REPO_ROOT";
   else echo "Session history bundled scripts were not found in this skill's directory; skipping the session-history probe for this run."; fi
   ```

   The command prints JSONL. `xargs` may split a long file list across several runs of the script; each run prints one object per kept session, then its own `_meta` line. Parse the output one line at a time, because the stream as a whole is not one JSON document. A pass's `files_processed` total is the sum across its `_meta` lines; a `--keyword` re-run is a new pass, not more files. Optional fields are omitted, not set to null, so a missing key is not an error. Rank recency by `last_ts`, falling back to `ts`. If you process the output with code, look at a few lines first and use the keys you see.

   Claude sessions live under `~/.claude/projects/` unless `CLAUDE_CONFIG_DIR` is set, in which case they live under that directory's `projects/`. Codex sessions live under `~/.codex/sessions/` unless `CODEX_HOME` is set, in which case they live under that directory's `sessions/`; `~/.agents/sessions/` is also scanned. Pi sessions are included when present under `~/.pi/agent/sessions/` (`PI_CODING_AGENT_DIR` / `PI_CODING_AGENT_SESSION_DIR` override), and oh-my-pi (`omp`) sessions under `~/.omp/agent/sessions/` (named profiles: `~/.omp/profiles/<name>/agent/sessions/`; XDG: `$XDG_DATA_HOME/omp/sessions` and `$XDG_DATA_HOME/omp/profiles/<name>/sessions`; `PI_CONFIG_DIR` / `PI_CODING_AGENT_DIR` / `PI_CODING_AGENT_SESSION_DIR` override). Claude, Codex, Pi, and oh-my-pi (`omp`) sessions carry a recorded `cwd` (Claude also has git branch; Pi/omp do not). `--cwd-filter` keeps a session when that cwd is the repo root, an ancestor of it, or a path inside it (path-component boundaries: `my-repo` vs `my-repo-old` do not match). Claude, Codex, Pi, and omp sessions with no recorded cwd are dropped. Cursor has no cwd and stays. Do not drop a Claude session because its project folder name lacks the repo basename. That is how Claude stores parent-started sessions. If the first pass's `files_processed` total is `0`, return `no relevant prior sessions`. If the first pass finds no relevant branch matches, or if processing Codex, Pi, or oh-my-pi (`omp`) sessions, derive 2-4 keywords from the topic and re-run metadata extraction with `--keyword K1,K2,...`. Keep at most 5 prior sessions across Claude Code, Codex, Cursor, Pi, and oh-my-pi (`omp`), ranked by branch match, keyword match count, file size over 30KB, and recency. Exclude only this executing run's own session ID; the passed OpenCode source session remains mandatory primary evidence outside these prior-session gates.

   **Escalation check.** The discovery+metadata pass above is the cheap probe and always runs in Full mode. Escalate to the extraction and synthesis stages below **only** when at least one retained candidate clears the relevance bar: a current-branch match, or ≥2 topic-keyword matches. If no candidate clears the bar (including a `files_processed` total of `0`), stop here, record `no relevant prior sessions` as the session-history input, and skip extraction and synthesis. This check is what keeps the always-on probe cheap. The expensive synthesis runs only when a prior session is genuinely relevant.

   **Extraction pipeline.** Create `SCRATCH=$(mktemp -d "$RUN_DIR/sessions-XXXXXX")` under the already-created workspace-local `.tmp/` run directory. For each selected session, write extracted content to scratch files. Exclude only this executing run's own session; keep any passed source session as primary evidence.

   ```bash
   SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
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

   The subagent reads only the scratch paths, **writes its prose findings to `{run_dir}/session-history.md`, and returns only that artifact path once the write is confirmed** (the same #956 reliability reason applies, because session-history findings are long-form prose prone to summary-collapse). If `{run_id}` did not resolve or the artifact write failed, it returns the prose inline instead (per the inline-fallback rule above). If synthesis fails, note the failure and continue without session context.
