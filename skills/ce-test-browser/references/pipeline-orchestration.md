# Pipeline-Mode Server Orchestration

Read and follow this file only when invoked with `mode:pipeline` by an automated runner. It overrides visibility prompts, free-port selection, and dev-server startup. It does not change browser-driver selection. In pipeline mode you run unattended — never block on a question.

## 1. No visibility question

Unattended execution does not mean hidden execution. Do not ask a visibility question:

- When a host-native integrated browser is selected, keep its normal integrated surface visible and non-blocking so the user can watch progress without interrupting the run. Do not repeatedly steal focus.
- When the fallback `agent-browser` driver is selected, run it headless without passing `--headed`.

## 2. Claim a free port and start the server

Multiple agents may run on the same machine, so never assume the resolved port is free: `scripts/resolve-port.sh --free` in this skill's directory resolves the port and scans upward to the first port with no listener, printing it alone on stdout.

Run the whole thing as **one** command. Shell variables do not survive between separate Bash calls, so the port resolution, the free scan, and the startup all happen inside this block — it seeds `PORT` by capturing the script's output, not from anything an earlier step printed. Add the explicit port as a second argument when the user gave `--port N` or your in-context project instructions state the dev-server port.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PORT=$(bash "$SKILL_DIR/scripts/resolve-port.sh" --free);   # append the explicit port as a further argument when you have one
echo "Using dev server port: $PORT"

WORKSPACE_ROOT="$(jj workspace root 2>/dev/null || pwd -P)"
TMP_ROOT="$WORKSPACE_ROOT/.tmp"
if [ -L "$TMP_ROOT" ]; then echo "unsafe scratch parent symlink: $TMP_ROOT" >&2; exit 1; fi
(umask 077; mkdir -p "$TMP_ROOT") || exit 1
if [ -L "$TMP_ROOT" ] || [ ! -O "$TMP_ROOT" ]; then echo "scratch parent is not owned by the current user: $TMP_ROOT" >&2; exit 1; fi
chmod 700 "$TMP_ROOT" || exit 1
SCRATCH_ROOT="$TMP_ROOT/ce-test-browser"
if [ -L "$SCRATCH_ROOT" ]; then echo "unsafe scratch root symlink: $SCRATCH_ROOT" >&2; exit 1; fi
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1
if [ -L "$SCRATCH_ROOT" ] || [ ! -O "$SCRATCH_ROOT" ]; then echo "scratch root is not owned by the current user: $SCRATCH_ROOT" >&2; exit 1; fi
chmod 700 "$SCRATCH_ROOT" || exit 1
RUN_DIR=""
for ATTEMPT in $(seq 1 100); do
  CANDIDATE="$SCRATCH_ROOT/run-$(date +%Y%m%d%H%M%S)-$$-${RANDOM}"
  if (umask 077; mkdir "$CANDIDATE"); then RUN_DIR="$CANDIDATE"; break; fi
done
if [ -z "$RUN_DIR" ]; then echo "could not reserve unique browser-test scratch" >&2; exit 1; fi
LOG_PATH="$RUN_DIR/dev-server.log"
echo "Using browser-test scratch: $RUN_DIR"

# start in the background (the scan guarantees this port is free), then wait up to 30s
echo "Starting dev server on port ${PORT}..."
if [ -f "bin/dev" ]; then
  PORT=${PORT} bin/dev > "$LOG_PATH" 2>&1 &
elif [ -f "bin/rails" ]; then
  bin/rails server -p ${PORT} > "$LOG_PATH" 2>&1 &
elif [ -f "package.json" ]; then
  PORT=${PORT} npm run dev > "$LOG_PATH" 2>&1 &
fi
for i in $(seq 1 30); do
  lsof -i ":${PORT}" -sTCP:LISTEN -t >/dev/null 2>&1 && break
  sleep 1
done
if ! lsof -i ":${PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Server did not start in 30s. Last output:"
  tail -20 "$LOG_PATH" 2>/dev/null
  exit 1
fi
```

The scan may land on a different port than the resolved one, and shell variables do not survive into later shell calls. Note the literal port and scratch path this block echoes. Use that port in every subsequent selected-driver navigation and keep all transient pipeline artifacts under that scratch path. Then return to the "Test Each Affected Page" step, navigate to `http://localhost:<N>`, inspect the rendered state, and test each route.
