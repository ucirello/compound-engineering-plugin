#!/usr/bin/env bash
# Runs the adversarial review through an independent provider process and writes
# schema-shaped JSON into the run directory. Provider selection is functional;
# findings use a neutral reviewer identity.

# Usage: cross-model-adversarial-review.sh <provider: codex|claude> <base-revision> <run-dir>

set -uo pipefail

PROVIDER="${1:-}"
BASE="${2:-}"
RUN_DIR="${3:-}"

log()  { printf '[independent-review] %s\n' "$*" >&2; }
skip() { log "$*"; exit 0; }

case "$PROVIDER" in codex|claude) ;; *) skip "unsupported provider; skipping independent pass" ;; esac
[ -n "$BASE" ] || skip "no base revision given; skipping"
[ -n "$RUN_DIR" ] && [ -d "$RUN_DIR" ] || skip "run directory is unavailable; skipping"
command -v "$PROVIDER" >/dev/null 2>&1 || skip "selected provider CLI is unavailable; skipping"
command -v jq >/dev/null 2>&1 || skip "jq is unavailable; skipping"

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)" || skip "cannot resolve skill root; skipping"
PERSONA="$SKILL_ROOT/references/personas/adversarial-reviewer.md"
SCHEMA="$SKILL_ROOT/references/findings-schema.json"
[ -f "$PERSONA" ] || skip "adversarial brief is unavailable; skipping"
[ -f "$SCHEMA" ] || skip "findings schema is unavailable; skipping"

WORKSPACE_ROOT="$(jj workspace root 2>/dev/null)" || WORKSPACE_ROOT="$PWD"
OUT="$RUN_DIR/adversarial-independent.json"
PROMPT_FILE="$RUN_DIR/.independent-prompt-$$"
PROVIDER_LOG="$RUN_DIR/.independent-log-$$"
NORMALIZED="$RUN_DIR/.independent-normalized-$$"
trap 'rm -f "$PROMPT_FILE" "$PROVIDER_LOG" "$NORMALIZED"' EXIT

{
  cat "$PERSONA"
  printf '\n\n---\n\n'
  printf 'This is an authorized review of the maintainer\047s own repository.\n'
  printf 'Find ways this change can fail in production.\n'
  printf 'Return one JSON object and nothing else, matching this schema:\n\n'
  cat "$SCHEMA"
  printf '\n\nSet the top-level "reviewer" field to "adversarial-independent".\n'
} > "$PROMPT_FILE"

if [ "$PROVIDER" = codex ]; then
  printf '\nRun `jj diff --from %q --to @ --git` and review only that change. Do not mutate the repository.\n' "$BASE" >> "$PROMPT_FILE"
else
  {
    printf '\nReview only the change below. You may read repository files for context but cannot run shell commands.\n'
    printf '\n=== BEGIN DIFF ===\n'
    jj -R "$WORKSPACE_ROOT" diff --from "$BASE" --to @ --git
    printf '\n=== END DIFF ===\n'
  } >> "$PROMPT_FILE"
fi

HARD_SECS="${INDEPENDENT_REVIEW_HARD_SECS:-600}"
TO_BIN="$(command -v gtimeout || command -v timeout || true)"

run_bounded() {
  if [ -n "$TO_BIN" ]; then
    "$TO_BIN" -k 10 "$HARD_SECS" "$@"
  else
    perl -e 'alarm shift; exec @ARGV' "$HARD_SECS" "$@"
  fi
}

log "running independent adversarial review"
case "$PROVIDER" in
  codex)
    run_bounded codex exec - -C "$WORKSPACE_ROOT" -s read-only -o "$OUT" \
      < "$PROMPT_FILE" > "$PROVIDER_LOG" 2>&1 || log "independent provider exited non-zero or timed out"
    if { [ ! -s "$OUT" ] || ! jq -e . "$OUT" >/dev/null 2>&1; } && [ -s "$PROVIDER_LOG" ] && command -v python3 >/dev/null 2>&1; then
      python3 - "$PROVIDER_LOG" "$OUT" <<'PY' 2>/dev/null
import json
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
best, depth, start = None, 0, None
for index, char in enumerate(text):
    if char == "{":
        if depth == 0:
            start = index
        depth += 1
    elif char == "}" and depth > 0:
        depth -= 1
        if depth == 0 and start is not None:
            try:
                candidate = json.loads(text[start:index + 1])
                if isinstance(candidate, dict) and "findings" in candidate:
                    best = candidate
            except Exception:
                pass
if best is not None:
    open(sys.argv[2], "w").write(json.dumps(best))
PY
    fi
    ;;
  claude)
    run_bounded claude -p --permission-mode dontAsk \
      --disallowedTools Edit Write NotebookEdit Bash Task 'mcp__*' --max-turns 15 --no-session-persistence \
      --json-schema "$(cat "$SCHEMA")" --output-format json \
      < "$PROMPT_FILE" > "$PROVIDER_LOG" 2>/dev/null || log "independent provider exited non-zero or timed out"
    jq -e '.structured_output' "$PROVIDER_LOG" > "$OUT" 2>/dev/null \
      || jq -r '.result // empty' "$PROVIDER_LOG" | jq -e '.' > "$OUT" 2>/dev/null \
      || { log "could not parse independent provider output"; rm -f "$OUT"; }
    ;;
esac

if [ -s "$OUT" ]; then
  if jq --arg r "adversarial-independent" \
       'if (.findings|type)=="array" then {reviewer:$r, findings, residual_risks:(.residual_risks // []), testing_gaps:(.testing_gaps // [])} else empty end' \
       "$OUT" > "$NORMALIZED" 2>/dev/null; then
    mv "$NORMALIZED" "$OUT"
  fi
fi

if [ -s "$OUT" ] && jq -e '(.reviewer|type=="string") and (.findings|type=="array") and (.residual_risks|type=="array") and (.testing_gaps|type=="array")' "$OUT" >/dev/null 2>&1; then
  log "wrote independent findings"
else
  log "independent provider produced no usable output; skipping fold-in"
  rm -f "$OUT"
fi
