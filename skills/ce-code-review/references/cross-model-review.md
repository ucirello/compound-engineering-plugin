# External Adversarial Pass

Runs the adversarial review through an independent provider CLI in a separate read-only process. The external actor gets the same `references/personas/adversarial-reviewer.md` brief, returns the same `findings-schema.json` shape, and folds into Stage 5 as reviewer `adversarial-external`; agreement with the in-process `adversarial` persona promotes the finding.

All invocation detail lives in **`scripts/cross-model-adversarial-review.sh`**. This reference decides whether to run it, which available provider to use, and how to fold the result in. The pass is non-blocking: a missing output file is simply "no external pass," never a failure.

## Gates — run only when all hold

1. `adversarial-reviewer` was selected in Stage 3 (reuse that diff gate — don't run a costly external CLI on a trivial diff).
2. Scope is `local-aligned` or standalone — the workspace IS the reviewed head. Skip in `pr-remote` / `bookmark-remote`: the peer reviews local `@`, which is not the PR/bookmark head.

## Step 1 — Identify host and peer (runtime self-id, no build-time)

```bash
if [ -n "${CURSOR_AGENT:-}${CURSOR_CONVERSATION_ID:-}" ]; then XHOST=cursor; XPEER=codex
elif [ "${CLAUDECODE:-}" = "1" ]; then XHOST=claude; XPEER=codex
elif [ -n "${CODEX_SANDBOX:-}${CODEX_SANDBOX_NETWORK_DISABLED:-}${CODEX_SESSION_ID:-}${CODEX_THREAD_ID:-}${CODEX_CI:-}" ]; then XHOST=codex; XPEER=claude
else XHOST=unknown; XPEER=""; fi
echo "EXTERNAL_REVIEW_HOST: $XHOST  PROVIDER: ${XPEER:-none}"
```

Cursor and Claude prefer **codex** as the peer (a guaranteed different model family); Codex prefers **claude**. There is no single canonical marker Codex sets across surfaces (CLI, web, CI), and `shell_environment_policy`/IDE inheritance can strip env vars, so check the union above. Do **not** use the *other* CLI's home (e.g. `CODEX_HOME`) — it leaks into a Claude session. `unknown` → skip the pass silently. The script also re-validates the peer it is handed, so a wrong/missing peer fails safe.

## Step 2 — Announce in default mode

- Default mode: surface a prominent standalone line that an independent external pass will run, without naming or attributing its provider, model, or host.
- Provider unavailable: one quiet line that the external pass was skipped and why. Never an error.
- `mode:agent`: emit no prose.

## Step 3 — Run the bundled script (launch it in parallel with the persona reviewers)

The script is a CLI shell-out, not a subagent, so it doesn't consume the subagent concurrency budget. **Launch it as a background shell process in the same Stage 4 dispatch wave as the persona reviewers** so its runtime overlaps theirs, then collect before Stage 5.

Invoke it via the skill-dir anchor — set `SKILL_DIR` to the absolute directory of **this** skill's `SKILL.md` (the one you read to run ce-code-review), because the Bash tool's CWD is the user's project, not the skill dir, on every host:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-code-review SKILL.md you read>"
bash "$SKILL_DIR/scripts/cross-model-adversarial-review.sh" "<peer>" "<base-ref>" "<run-dir>"
```

- `<peer>` = `XPEER` from Step 1 (`codex` or `claude`).
- `<base-ref>` = the Stage 1 `BASE` (the diff base the peer reviews via `jj diff --from <base-ref> --git`).
- `<run-dir>` = the Stage 4 workspace-local run dir (`$(jj workspace root)/.tmp/rocketclaw/code-review/<run-id>/`, or `$PWD/.tmp/rocketclaw/code-review/<run-id>/` outside a JJ repo). The script writes `adversarial-external.json` there.

Set the Bash tool `timeout` to `660000` (11 min) — the script self-bounds (provider idle-timeout, default-180s stall with reasoning forced on for liveness; hard backstop `EXTERNAL_REVIEW_HARD_SECS`, default 600s) and exits cleanly. If the harness can't background a shell command, run it inline before awaiting the reviewers; correctness is unaffected, only wall-clock. The script needs no prompt or schema passed in — it reads the persona brief and `findings-schema.json` itself from the skill dir.

## Step 4 — Fold into Stage 5

- Read `<run-dir>/adversarial-external.json`. If present, treat it as one reviewer return with `reviewer: adversarial-external`, exactly like a persona artifact.
- **No file**: the pass simply did not run. Note "external pass: not run" in Coverage in default mode; stay silent in `mode:agent`.
- Empty `findings`: note "external pass: no additional issues" in Coverage.
- A finding sharing a dedup fingerprint with the in-process `adversarial` persona promotes by one anchor step because it was independently reproduced.

## What the script does (for maintainers — you don't invoke this directly)

`scripts/cross-model-adversarial-review.sh <peer> <base-ref> <run-dir>`:
- Self-locates the persona + schema via `BASH_SOURCE` (works from any CWD); derives the repo root from `jj workspace root`.
- Composes the provider prompt from the canonical persona brief and a JSON-only contract. Provider-specific flags preserve read-only operation. After capture, the script forces `reviewer = adversarial-external` so it remains distinct from the in-process reviewer.
- Codex peer: `codex exec - -s read-only -o <out>` at high reasoning effort. No `--output-schema` (Codex strict mode rejects the permissive draft-07 schema); the full schema embedded in the prompt is its only contract, which produces complete schema-shaped findings (verified). The `-o` write is done by the codex CLI *outside* the model's sandbox, so it succeeds under `-s read-only` (verified); if it ever fails to materialize, the script recovers the same JSON from codex's captured stdout (belt-and-suspenders, no data lost).
- Claude peer: `claude -p --permission-mode dontAsk --disallowedTools Edit Write NotebookEdit --json-schema … --output-format json` (disallowed tools passed as separate variadic args, not one quoted string), captured from stdout (it can't write a file under those permissions), parsed via `.structured_output` with a `.result` fallback.
- Read-only differs by peer: codex `-s read-only` is a hard sandbox; claude `dontAsk` denies `Edit`/`Write`/`NotebookEdit`/`Bash` plus `mcp__*` (a user's pre-approved MCP write/deploy tools would otherwise run under `dontAsk`) and `Task` (a subagent would bypass the deny list) — so it can't mutate via shell, MCP, or a spawned subagent even under broad user allow-rules (deny overrides allow) — and reviews the embedded diff with read-only file access. Non-blocking everywhere: any gap → log + exit 0, no output file.
- Timeouts kill the whole process group so no orphaned provider call outlives the script. Streaming execution uses a watchdog with `EXTERNAL_REVIEW_IDLE_SECS` and `EXTERNAL_REVIEW_HARD_SECS`; single-shot execution uses the hard cap. Provider-specific flags and process handling remain in the script.
