# Pipeline-Mode Server Orchestration

Read and follow this file only when invoked with `mode:pipeline` (LFG or another automated runner). It overrides visibility prompts, free-port selection, and dev-server startup. It does not change browser-driver selection. In pipeline mode you run unattended — never block on a question.

The run's report, either the summary or the preflight blocker that stopped testing, is the last thing this skill writes. It ends this skill, not the turn. The caller runs in this same session, and its next step follows the report.

## 1. No visibility question

Unattended execution does not mean hidden execution. Do not ask a visibility question:

- When a host-native integrated browser is selected, keep its normal integrated surface visible and non-blocking so the user can watch progress without interrupting the run. Do not repeatedly steal focus.
- When the fallback `agent-browser` driver is selected, run it headless without passing `--headed`.

## 2. Claim a free port and start the server

Multiple agents may run on the same machine, so never assume the resolved port is free: `scripts/resolve-port.sh --free` in this skill's directory resolves the port and scans upward to the first port with no listener, printing it alone on stdout.

Run the whole thing as **one** command. Shell variables do not survive between separate Bash calls, so the port resolution, the free scan, and the startup all happen inside this block — it seeds `PORT` by capturing the script's output, not from anything an earlier step printed. Add the explicit port as a second argument when the user gave `--port N` or your in-context project instructions state the dev-server port.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
workspace_root="<verified absolute target workspace root>"
cd "$workspace_root" || exit 1
mkdir -p "$workspace_root/.tmp" || exit 1
export TMPDIR="$workspace_root/.tmp"
PORT=$(bash "$SKILL_DIR/scripts/resolve-port.sh" --free) || exit 1 # append the explicit port as a further argument when you have one
SERVER_LOG=$(mktemp "$workspace_root/.tmp/browser-server-${PORT}.XXXXXX") || exit 1
echo "Using dev server port: $PORT"

# Start in the background, then wait up to 30s. Another process can race the scan.
echo "Starting dev server on port ${PORT}..."
if [ -f "bin/dev" ]; then
  PORT=${PORT} bin/dev > "$SERVER_LOG" 2>&1 &
elif [ -f "bin/rails" ]; then
  bin/rails server -p ${PORT} > "$SERVER_LOG" 2>&1 &
elif [ -f "package.json" ]; then
  PORT=${PORT} npm run dev > "$SERVER_LOG" 2>&1 &
else
  echo "No supported dev-server entrypoint; preflight blocked. Log: $SERVER_LOG"
  exit 1
fi
SERVER_PID=$!
echo "Owned server PID: $SERVER_PID; log: $SERVER_LOG"
for i in $(seq 1 30); do
  lsof -i ":${PORT}" -sTCP:LISTEN -t >/dev/null 2>&1 && break
  sleep 1
done
if ! lsof -i ":${PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Server did not start in 30s. Last output:"
  tail -20 "$SERVER_LOG" 2>/dev/null
  exit 1
fi
```

Record the server PID and absolute log path in run evidence. Verify startup output and root response belong to this server, not a process that raced the port scan; an exited child or port collision is a preflight blocker, not a passing startup. At completion or failure, stop only the verified process owned by this run (and its verified children), never an unrelated listener. Preserve logs and screenshots under the target workspace's absolute `.tmp/`, including failure evidence; do not use global temporary directories.

The scan may land on a different port than the resolved one, and `$PORT` does not survive into later shell calls. Note the number this block echoes ("Using dev server port: N") and use that literal port in every subsequent selected-driver navigation — do not rely on `${PORT}` carrying over. Then return to the "Test Each Affected Page" step, navigate to `http://localhost:<N>`, inspect the rendered state, and test each route.
