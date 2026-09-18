#!/usr/bin/env bash
# elevation-dispatch.sh — off-host model-elevation worker for ce-plan / ce-brainstorm.
#
# Runs one reasoning-heavy step on a user-chosen model via Claude CLI, opencode,
# or opencode2 (distinct harnesses — never fold opencode2 into opencode), as a
# detached job supervised by peer-job-runner.py. Streams output so the idle
# window observes genuine progress, not just liveness — a buffered format would
# make a healthy long run byte-identical to a wedged one. See
# docs/solutions/skill-design/cli-output-buffering-for-progress-detection.md.
#
# Read-only posture (R7): Claude is allowlisted to Read/Glob/Grep plus
# WebSearch/WebFetch; opencode uses a v1 permission denylist; opencode2 is
# cooperative read-only (no --auto). Writes, shell, skills, and MCP stay
# unavailable on the Claude route; the model reads the repo and web to verify
# its brief and returns prose.
#
# Usage:
#   elevation-dispatch.sh <model> <prompt-file> <result-path> [harness]
#   elevation-dispatch.sh --emit-adapter <model> [handoff-dir] [harness]
#
# harness is claude | opencode | opencode2. Default: claude.
# plan_harness: opencode2 is a DISTINCT branch from opencode: binary `opencode2`,
# model `provider/modelname#variant` (preserved as one --model token), flags from
# `opencode2 run --help` (v2.0.8): --standalone --format json --file --model,
# cwd = the handoff directory, without --auto.
# PLAN_HARNESS / ELEVATION_HARNESS env also select the harness.
#
# NOTE ON THE FUNCTION NAMED run_codex_cmd: it is NOT codex-specific here. It is
# the $PEERLOG byte-growth idle loop that implements R11's primary supervision
# signal (run_timeout_cmd, hard-cap-only, would leave a stalled run undetected).
# It keeps that name because the shared heartbeat-parity regex in
# tests/peer-job-runner-parity.test.ts uses `run_codex_cmd()` as the terminator
# that forces BOTH heartbeat functions into the byte-compared kernel; renaming it
# would weaken that cross-skill guard.

set -uo pipefail
trap '' HUP

ACTIVE_PEER_PID=""
RUN_SUCCEEDED=false

log() { printf '[elevation] %s\n' "$*" >&2; }

EFFORT="high"   # settled: elevation runs at high effort

# Read-only tool posture (R7): the available built-in set, not a denylist. The
# elevated step reads the repo (Read/Glob/Grep) and may check current facts on
# the web (WebSearch/WebFetch) while authoring; it never needs Write/Bash/Task or
# any mutating tool. Its output is returned prose, not a file write.
ALLOWED=(Read Glob Grep WebSearch WebFetch)

normalize_harness() {
  case "$1" in
    claude|opencode|opencode2) printf '%s' "$1" ;;
    "") printf 'claude' ;;
    *) printf '' ;;
  esac
}

resolve_harness() {
  local raw="${1:-}"
  [ -n "$raw" ] || raw="${PLAN_HARNESS:-}"
  [ -n "$raw" ] || raw="${ELEVATION_HARNESS:-}"
  [ -n "$raw" ] || raw="claude"
  local n; n="$(normalize_harness "$raw")"
  if [ -z "$n" ]; then
    log "unknown harness '$raw' (want claude|opencode|opencode2); opencode2 is not opencode"
    exit 2
  fi
  printf '%s' "$n"
}

# <model> <handoff-dir> <harness> -> sets CMD array
build_cmd() {
  local model="$1" handoff="${2:-}" harness="$3"
  case "$harness" in
    opencode)
      # Distinct v1 OpenCode route: binary `opencode`, --dir, optional --model,
      # v1 OPENCODE_CONFIG_CONTENT denylist. Never used for plan_harness: opencode2.
      CMD=(env 'OPENCODE_DISABLE_PROJECT_CONFIG=1'
           'OPENCODE_CONFIG_CONTENT={"permission":{"edit":"deny","bash":"deny","webfetch":"deny","task":"deny"}}'
           opencode run --dir "${handoff:-.}" --format json --file "$PROMPT_FILE")
      if [ -n "$model" ] && [ "$model" != "auto" ]; then
        CMD+=(--model "$model")
      fi
      ;;
    opencode2)
      # Distinct from opencode: binary `opencode2`, model `provider/modelname#variant`
      # passed through --model unchanged (including #variant), no --dir/--variant,
      # no v1 OPENCODE_CONFIG_CONTENT denylist. CWD is the handoff dir. Do not
      # pass --auto: this is a cooperative read-only elevation route.
      # Flags from `opencode2 run --help` (v2.0.8).
      CMD=(bash -c 'cd "$1" && shift && exec "$@"' _ "${handoff:-.}"
           opencode2 run --standalone --format json --file "$PROMPT_FILE")
      if [ -n "$model" ] && [ "$model" != "auto" ]; then
        CMD+=(--model "$model")
      fi
      ;;
    claude)
      # --safe-mode suppresses the user environment's hooks, plugins, and MCP
      # servers; --disable-slash-commands blocks skills. --tools RESTRICTS the
      # available built-in set to this list — Write/Edit/Bash are not present at all.
      # This is the real read-only boundary: --allowedTools ALONE only pre-approves
      # (verified — it leaves every other tool available), so --allowedTools here
      # just lets --permission-mode dontAsk run these five without a prompt instead
      # of denying them.
      local csv; csv="$(IFS=,; printf '%s' "${ALLOWED[*]}")"
      # Grant read access to ONLY the single per-run handoff dir ($2, where the
      # orchestrator co-located the prompt and evidence), which sits outside the
      # launch dir. Claude's file access defaults to the launch dir and is extended
      # via --add-dir. Adding the whole workspace scratch root instead would expose
      # every other same-user scratch file and credential to the elevated
      # model; the scoped dir does not. Read-only (only Read/Glob/Grep available).
      local add_dirs=()
      [ -n "$handoff" ] && add_dirs=(--add-dir "$handoff")
      # --no-session-persistence: this is a one-shot background model call, so the
      # prompt and scratch-file references must not be saved as a resumable session
      # on disk (matches the other scripted Claude peer routes in this repo).
      CMD=(claude -p --model "$model" --effort "$EFFORT"
           --output-format stream-json --verbose
           --safe-mode --no-session-persistence --disable-slash-commands --strict-mcp-config
           --permission-mode dontAsk
           "${add_dirs[@]}"
           --tools "$csv" --allowedTools "${ALLOWED[@]}"
           --max-turns "${ELEVATION_MAX_TURNS:-30}")
      ;;
    *)
      log "unknown harness '$harness' (want claude|opencode|opencode2)"
      exit 2
      ;;
  esac
}

# Test hook: print the argv the worker would exec, without calling a model.
# Accepts an optional handoff dir ($3) so the emitted argv shows the scoped
# --add-dir / cwd; without it the flag is omitted (no dir to grant). Optional
# $4 (or PLAN_HARNESS) selects claude | opencode | opencode2.
if [ "${1:-}" = "--emit-adapter" ]; then
  [ -n "${2:-}" ] || { log "--emit-adapter requires <model>"; exit 2; }
  MODEL="$2"
  HANDOFF_DIR="${3:-}"
  HARNESS_ARG="${4:-}"
  if [ -z "$HARNESS_ARG" ]; then
    case "${HANDOFF_DIR}" in
      claude|opencode|opencode2) HARNESS_ARG="$HANDOFF_DIR"; HANDOFF_DIR="" ;;
    esac
  fi
  HARNESS="$(resolve_harness "$HARNESS_ARG")" || exit $?
  PROMPT_FILE="${PROMPT_FILE:-<prompt-file>}"
  build_cmd "$MODEL" "$HANDOFF_DIR" "$HARNESS"
  printf '%s\0' "${CMD[@]}"
  exit 0
fi

MODEL="${1:?model required}"
PROMPT_FILE="${2:?prompt-file required}"
RESULT_PATH="${3:?result-path required}"
HARNESS="$(resolve_harness "${4:-}")" || exit $?
[ -f "$PROMPT_FILE" ] || { log "prompt file not found: $PROMPT_FILE"; exit 2; }

# The orchestrator co-locates the prompt and every evidence file in one private
# per-run dir; grant the elevated model read access to just that dir (resolved
# to an absolute path), never the whole workspace scratch root. Pure-bash dirname (no
# external `dirname`): strip the last /component, defaulting to cwd if none.
HANDOFF_DIR="${PROMPT_FILE%/*}"
[ "$HANDOFF_DIR" = "$PROMPT_FILE" ] && HANDOFF_DIR="."
HANDOFF_DIR="$(cd "$HANDOFF_DIR" 2>/dev/null && pwd || printf '%s' "$HANDOFF_DIR")"

# jq builds every result envelope; it is only an optional capability (ce-setup),
# so preflight it here rather than spending the CLI call and failing to parse.
# Exit 0 with a failure envelope, NOT nonzero: the runner classifies a nonzero
# exit as `failed`, and its `result` command then refuses to emit the artifact,
# so the recovery flow could never read this envelope. Exit 0 makes the job
# `done`, the envelope's status:failed is read, and it degrades to inline.
if ! command -v jq >/dev/null 2>&1; then
  log "jq not found on PATH; cannot parse the elevated result — degrading to inline"
  printf '{"status":"failed","requested_model":"%s","evidence":"jq unavailable on PATH"}' "$MODEL" > "$RESULT_PATH" 2>/dev/null || true
  exit 0
fi

WORKSPACE_ROOT="$(jj workspace root 2>/dev/null || pwd -P)"
SCRATCH_ROOT="$WORKSPACE_ROOT/.tmp/rocketclaw/elevation"
(umask 077; mkdir -p "$SCRATCH_ROOT") || { log "cannot create workspace scratch root: $SCRATCH_ROOT"; exit 2; }
PEERLOG="$SCRATCH_ROOT/peer-$(date +%Y%m%dT%H%M%S)-$$-$RANDOM.log"
(umask 077; set -C; : > "$PEERLOG") || { log "cannot reserve peer log: $PEERLOG"; exit 2; }

# Idle window is the primary stall signal; the hard cap is a raised backstop (R11).
# Keep this inner cap >= the runner's ROCKETCLAW_PEER_HARD_SECS so it never reaps a
# healthy run before the outer supervisor's own raised backstop.
IDLE_SECS="${ROCKETCLAW_ELEVATION_IDLE_SECS:-180}"
HARD_SECS="${ROCKETCLAW_ELEVATION_HARD_SECS:-5400}"
POLL_SECS="${ROCKETCLAW_ELEVATION_POLL_SECS:-5}"   # $PEERLOG growth poll interval

reap() {
  local pid="$1" grp
  if kill -TERM -- -"$pid" 2>/dev/null; then grp=1; else kill -TERM "$pid" 2>/dev/null; grp=0; fi
  for _ in 1 2 3 4 5; do
    if [ "$grp" = 1 ]; then kill -0 -- -"$pid" 2>/dev/null || return 0
    else kill -0 "$pid" 2>/dev/null || return 0; fi
    sleep 1
  done
  if [ "$grp" = 1 ]; then kill -KILL -- -"$pid" 2>/dev/null; else kill -KILL "$pid" 2>/dev/null; fi
}

on_term() {
  if [ -n "${_HEARTBEAT_PID:-}" ]; then
    stop_heartbeat
  fi
  if [ -n "${ACTIVE_PEER_PID:-}" ]; then
    log "received TERM/INT; reaping peer process group $ACTIVE_PEER_PID"
    reap "$ACTIVE_PEER_PID" 2>/dev/null || true
    ACTIVE_PEER_PID=""
  fi
  exit 0
}
trap 'on_term' TERM INT

write_result() {   # <json-string> -> atomic publish to RESULT_PATH
  local tmp="${RESULT_PATH}.tmp.$$"
  printf '%s' "$1" > "$tmp" && mv -f "$tmp" "$RESULT_PATH"
}

# Bounded stderr/stdout tail for a failed run. tail -c avoids the macOS bash
# negative-slice bug that erased sub-300-char evidence in the review worker.
bounded_failure_evidence() { tail -c 800 "$PEERLOG" 2>/dev/null || true; }

# Expected served-id prefix for a requested model alias, or empty if unknown.
# provider/modelname#variant (opencode2) has no Claude family prefix.
model_prefix() {   # <requested> -> prefix | ""
  case "$1" in
    fable)    printf 'claude-fable-' ;;
    opus)     printf 'claude-opus-' ;;
    sonnet)   printf 'claude-sonnet-' ;;
    haiku)    printf 'claude-haiku-' ;;
    claude-*) printf '%s' "$1" ;;
  esac
}

# Requested family vs served id (R6/R16). matched | mismatch | unverified.
classify_receipt() {   # <requested> <served>
  local served="$2" prefix
  { [ -z "$served" ] || [ "$served" = "unverified" ]; } && { printf 'unverified'; return; }
  prefix="$(model_prefix "$1")"
  [ -z "$prefix" ] && { printf 'unverified'; return; }
  case "$served" in
    "$prefix"*) printf 'matched' ;;
    *)          printf 'mismatch' ;;
  esac
}

# --- liveness heartbeat -----------------------------------------------------
# Emits one stderr line every CROSS_MODEL_HEARTBEAT_SECS so the OUTER
# peer-job-runner idle window (out.log byte-growth) sees the supervising script
# as alive during a long model call. It writes to stderr, NOT $PEERLOG, so it
# never masks this worker's OWN $PEERLOG idle detection (run_codex_cmd below) —
# a stalled model still stops growing $PEERLOG and is reaped. This block is
# byte-identical across all peer workers (kernel parity, tests/peer-job-runner-parity.test.ts).
_HEARTBEAT_PID=""
start_heartbeat() {
  local every="${CROSS_MODEL_HEARTBEAT_SECS:-60}" parent_pid="$$"
  # Floor to 1s: a non-numeric or 0 value would make `sleep` return instantly and
  # spin the loop, flooding out.log into the runner's byte cap.
  case "$every" in ''|*[!0-9]*) every=60 ;; esac; [ "$every" -lt 1 ] && every=1
  _HEARTBEAT_READY=0
  trap '_HEARTBEAT_READY=1' USR1
  # Callers restore set +m after launching the peer, so without this the
  # heartbeat inherits the worker pgid and kill -- -PID cannot reach the sleep.
  local prev_m; case "$-" in *m*) prev_m=1;; *) prev_m=0;; esac
  set -m
  ( local t0 n sleeper=""
    trap 'kill "${sleeper:-}" 2>/dev/null || true; exit 0' TERM INT
    kill -USR1 "$parent_pid"
    t0="$(date +%s)"
    while kill -0 "$parent_pid" 2>/dev/null; do
      sleep "$every" & sleeper=$!
      wait "$sleeper" 2>/dev/null || exit 0
      sleeper=""
      kill -0 "$parent_pid" 2>/dev/null || break
      n="$(date +%s)"; log "peer alive ($(( n - t0 ))s elapsed)"
    done ) &
  _HEARTBEAT_PID=$!
  [ "$prev_m" = 0 ] && set +m
  while [ "$_HEARTBEAT_READY" != 1 ] && kill -0 "$_HEARTBEAT_PID" 2>/dev/null; do sleep 0.01 || true; done
  trap - USR1
}
stop_heartbeat() {
  if [ -n "$_HEARTBEAT_PID" ]; then
    # Leader-only TERM is deferred until the inner `wait $sleeper` returns, so
    # the default 60s interval would block this wait. Signal the process group.
    kill -- -"$_HEARTBEAT_PID" 2>/dev/null || kill "$_HEARTBEAT_PID" 2>/dev/null || true
    wait "$_HEARTBEAT_PID" 2>/dev/null || true
  fi
  _HEARTBEAT_PID=""
}

run_codex_cmd() {
  RUN_SUCCEEDED=false
  local prev; case "$-" in *m*) prev=1;; *) prev=0;; esac
  set -m
  case "$HARNESS" in
    opencode|opencode2)
      command "${CMD[@]}" > "$PEERLOG" 2>&1 &
      ;;
    *)
      command "${CMD[@]}" < "$PROMPT_FILE" > "$PEERLOG" 2>&1 &
      ;;
  esac
  local pid=$!
  ACTIVE_PEER_PID="$pid"
  [ "$prev" = 0 ] && set +m
  start_heartbeat
  local start last=-1 lastchg now size
  start="$(date +%s)"; lastchg="$start"
  while kill -0 "$pid" 2>/dev/null; do
    sleep "$POLL_SECS"; now="$(date +%s)"; size="$(wc -c <"$PEERLOG" 2>/dev/null || echo 0)"
    [ "$size" != "$last" ] && { last="$size"; lastchg="$now"; }
    if [ $(( now - lastchg )) -ge "$IDLE_SECS" ]; then
      log "elevated call idle ${IDLE_SECS}s; reaping"; reap "$pid"; break
    fi
    if [ $(( now - start )) -ge "$HARD_SECS" ]; then
      log "elevated call exceeded hard cap ${HARD_SECS}s; reaping"; reap "$pid"; break
    fi
  done
  if wait "$pid" 2>/dev/null; then RUN_SUCCEEDED=true
  else log "elevated call exited non-zero or was reaped"; fi
  reap "$pid" 2>/dev/null || true
  stop_heartbeat
  ACTIVE_PEER_PID=""
}

write_ok_envelope_from_file() {  # <served> <receipt> <output-file>
  local served="$1" receipt="$2" out_file="$3" tmp="${RESULT_PATH}.tmp.$$"
  if jq -n --arg m "$MODEL" --arg s "$served" --arg r "$receipt" --rawfile o "$out_file" \
       '{status:"ok", requested_model:$m, served_model:$s, receipt:$r, output:$o}' \
       > "$tmp" 2>/dev/null; then
    mv -f "$tmp" "$RESULT_PATH"
    log "elevated step complete: requested=$MODEL served=$served receipt=$receipt harness=$HARNESS"
  else
    rm -f "$tmp"
    write_result "$(jq -n --arg m "$MODEL" '{status:"failed", requested_model:$m, evidence:"result envelope build failed"}')"
    log "elevated step: result envelope build failed"
  fi
}

finish_claude() {
  # The stream-json terminal event is the LAST line whose type is "result". Match
  # on it rather than `tail -1`, so a diagnostic written to stderr after the result
  # (an update notice, wrapper output) does not become the "result" we parse.
  EVENT="$(grep -a '"type":"result"' "$PEERLOG" 2>/dev/null | tail -1 || true)"
  PREFIX="$(model_prefix "$MODEL")"
  # jq `keys` is sorted, so keys[0] is not necessarily the served model when
  # modelUsage carries an auxiliary model too; prefer the requested family's key.
  SERVED="$(printf '%s' "$EVENT" | jq -r --arg p "$PREFIX" \
    '(.modelUsage // {} | keys) as $k
     | (if $p != "" then first($k[] | select(startswith($p))) else empty end) // $k[0] // "unverified"' \
    2>/dev/null || printf 'unverified')"
  # Ship "ok" only on a clean success — a terminal event carries .result even when
  # truncated/errored (subtype error_*, is_error true). HAS_OUTPUT is a tiny jq
  # flag, so the plan text is never loaded into a shell variable or an argv.
  SUBTYPE="$(printf '%s' "$EVENT" | jq -r '.subtype // empty' 2>/dev/null || true)"
  IS_ERROR="$(printf '%s' "$EVENT" | jq -r '.is_error // false' 2>/dev/null || printf 'true')"
  HAS_OUTPUT="$(printf '%s' "$EVENT" | jq -r 'if (.result // "") == "" then "no" else "yes" end' 2>/dev/null || printf 'no')"

  if [ "$RUN_SUCCEEDED" = true ] && [ "$HAS_OUTPUT" = "yes" ] \
     && [ "$SUBTYPE" = "success" ] && [ "$IS_ERROR" != "true" ]; then
    RECEIPT="$(classify_receipt "$MODEL" "$SERVED")"
    # Build the envelope by piping the event THROUGH jq, which reads .result
    # internally — never pass the plan text as an argv --arg, which would exceed
    # ARG_MAX for a large Deep plan.
    tmp="${RESULT_PATH}.tmp.$$"
    if printf '%s' "$EVENT" | jq --arg m "$MODEL" --arg s "$SERVED" --arg r "$RECEIPT" \
         '{status:"ok", requested_model:$m, served_model:$s, receipt:$r, output:.result}' \
         > "$tmp" 2>/dev/null; then
      mv -f "$tmp" "$RESULT_PATH"
      log "elevated step complete: requested=$MODEL served=$SERVED receipt=$RECEIPT harness=claude"
    else
      rm -f "$tmp"
      write_result "$(jq -n --arg m "$MODEL" '{status:"failed", requested_model:$m, evidence:"result envelope build failed"}')"
      log "elevated step: result envelope build failed"
    fi
  else
    write_result "$(jq -n --arg m "$MODEL" --arg e "$(bounded_failure_evidence)" \
      '{status:"failed", requested_model:$m, evidence:$e}')"
    log "elevated step failed; wrote failure envelope"
  fi
}

# opencode and opencode2 both emit --format json event streams; parsers stay
# separate so a v1/v2 envelope drift cannot fold the harnesses together.
finish_opencode() {
  local out_file="$SCRATCH_ROOT/opencode-out-$$"
  if [ "$RUN_SUCCEEDED" = true ] \
     && jq -rs '[.[] | select(.type=="text") | (.part.text // empty)] | join("")' "$PEERLOG" > "$out_file" 2>/dev/null \
     && [ -s "$out_file" ]; then
    write_ok_envelope_from_file "unverified" "unverified" "$out_file"
  else
    write_result "$(jq -n --arg m "$MODEL" --arg e "$(bounded_failure_evidence)" \
      '{status:"failed", requested_model:$m, evidence:$e}')"
    log "elevated step failed; wrote failure envelope"
  fi
  rm -f "$out_file"
}

finish_opencode2() {
  local out_file="$SCRATCH_ROOT/opencode2-out-$$"
  if [ "$RUN_SUCCEEDED" = true ] \
     && jq -rs '[.[] | select(.type=="text") | (.part.text // empty)] | join("")' "$PEERLOG" > "$out_file" 2>/dev/null \
     && [ -s "$out_file" ]; then
    write_ok_envelope_from_file "unverified" "unverified" "$out_file"
  else
    write_result "$(jq -n --arg m "$MODEL" --arg e "$(bounded_failure_evidence)" \
      '{status:"failed", requested_model:$m, evidence:$e}')"
    log "elevated step failed; wrote failure envelope"
  fi
  rm -f "$out_file"
}

# --- main -------------------------------------------------------------------
build_cmd "$MODEL" "$HANDOFF_DIR" "$HARNESS"
run_codex_cmd

case "$HARNESS" in
  opencode)  finish_opencode ;;
  opencode2) finish_opencode2 ;;
  *)         finish_claude ;;
esac
rm -f "$PEERLOG"
