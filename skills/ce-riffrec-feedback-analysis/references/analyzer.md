# Analyzer contract

All non-setup paths use the bundled analyzer through this one invocation shape. The path reference supplies a concrete `INPUT_PATH`. Set `OUTPUT_DIR` only when that path owns an override; otherwise leave it empty so the script owns its default.

Run the analyzer with the command's working directory set to the target workspace's absolute root (outside a repository, the absolute project directory). Set `SKILL_DIR` to the absolute directory containing the loaded `ce-riffrec-feedback-analysis` `SKILL.md`. Resolve Python by executing each candidate so a Windows Store stub is not mistaken for a working interpreter:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
INPUT_PATH="<absolute input path>";
OUTPUT_DIR="${OUTPUT_DIR:-}";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
ANALYZER_ARGS=("$INPUT_PATH"); [ -z "$OUTPUT_DIR" ] || ANALYZER_ARGS+=(--output-dir "$OUTPUT_DIR");
"$PY" "$SKILL_DIR/scripts/analyze_riffrec_zip.py" "${ANALYZER_ARGS[@]}"
```

Accepted inputs are a Riffrec `.zip` or unpacked capture directory containing `session.json` and `events.json`; `.mp4`, `.mov`, or `.webm` video; `.m4a`, `.mp3`, or `.wav` audio; or meeting-notes `.md`.

Temporary staging and rollback snapshots use the workspace-local `.tmp/` directory; ensure `.tmp/` is ignored. Promotion uses filesystem-atomic replacement: if a user-selected output is on another filesystem, report the failure and retain the existing destination rather than substituting a non-atomic copy. If no interpreter works or the analyzer fails, report the command's exit status and stderr and stop that path. Do not silently substitute a partial artifact set.
