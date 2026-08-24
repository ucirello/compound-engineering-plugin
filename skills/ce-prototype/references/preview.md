# Preview helper

Load this when serving a local web prototype. Feedback stays in chat.

This skill ships its own `scripts/light-webserver.js`. Do not import a sibling skill's copy — isolation forbids that.

Use the bundled helper when the current platform can run a bundled skill script. Invoke it via the `SKILL_DIR` anchor: set `SKILL_DIR` to the absolute path of the directory containing the `ce-prototype` `SKILL.md` you loaded (the Bash tool's cwd is the user's project, not the skill dir), and re-set it in the same command on each call since shell vars do not persist between Bash invocations. Do not resolve the helper from the user's project CWD.

Resolve the question directory once, at the start of the run, and reuse the absolute path it prints for every later call. Do not re-derive it per command — the server keys its pidfile and its process match off `--root`, so a start and a stop that resolve differently leave an orphaned server.

`RUN_SLUG` is `<date>-<short-question-slug>` for the run; `QUESTION_SLUG` is `NN-<question-slug>` for the question being built. A run that covers a second related question resolves a second question directory under the same run directory.

Settle durability before you run this block; it claims the run once and there is no second pass. Set `RUN_KEEP="no"` when the user asks not to use the durable root. In a JJ workspace, ensure the workspace-root ignore rules cover `.tmp/` and, for a durable run, `.rocketclaw/` before creating either path. For each missing pattern, offer to append exactly that top-level pattern to the workspace-root `.gitignore`, changing nothing else. If the user declines or an ignore cannot be established safely, stop before writing. Outside JJ, use the current directory's local `.tmp` without changing ignore rules.

```bash
RUN_SLUG="<YYYY-MM-DD>-<run-slug>";
RUN_KEEP="yes";
WORKSPACE_ROOT="$(jj workspace root 2>/dev/null)";
if [ -n "$WORKSPACE_ROOT" ]; then LOCAL_ROOT="$WORKSPACE_ROOT"; else LOCAL_ROOT="$(pwd -P)"; fi;
TMP_ROOT="$LOCAL_ROOT/.tmp";
FALLBACK_ROOT="";
CHECK_TMP="yes";
if [ -n "$WORKSPACE_ROOT" ] && [ "$RUN_KEEP" = yes ]; then ROOT="$WORKSPACE_ROOT/.rocketclaw"; FALLBACK_ROOT="$TMP_ROOT/rocketclaw"; CHECK_TMP="no"; else ROOT="$TMP_ROOT/rocketclaw"; fi;
while :; do
BASE="$ROOT/ce-prototype";
if [ "$CHECK_TMP" = yes ] && [ -L "$TMP_ROOT" ]; then echo "unsafe .tmp symlink: $TMP_ROOT" >&2;
elif [ "$CHECK_TMP" = yes ] && ! (umask 077; mkdir -p "$TMP_ROOT"); then echo "could not create $TMP_ROOT" >&2;
elif [ "$CHECK_TMP" = yes ] && { [ -L "$TMP_ROOT" ] || [ ! -O "$TMP_ROOT" ]; }; then echo ".tmp is not owned by the current user: $TMP_ROOT" >&2;
elif [ "$CHECK_TMP" = yes ] && ! chmod 700 "$TMP_ROOT"; then echo "could not restrict $TMP_ROOT" >&2;
elif [ -L "$ROOT" ]; then echo "unsafe root symlink: $ROOT" >&2;
elif ! (umask 077; mkdir -p "$ROOT"); then echo "could not create $ROOT" >&2;
elif [ ! -O "$ROOT" ]; then echo "root is not owned by the current user: $ROOT" >&2;
elif ! chmod 700 "$ROOT"; then echo "could not restrict $ROOT" >&2;
elif [ -L "$BASE" ]; then echo "unsafe base symlink: $BASE" >&2;
elif ! (umask 077; mkdir -p "$BASE"); then echo "could not create $BASE" >&2;
elif [ ! -O "$BASE" ]; then echo "base is not owned by the current user: $BASE" >&2;
elif ! chmod 700 "$BASE"; then echo "could not restrict $BASE" >&2;
else break; fi;
if [ -z "$FALLBACK_ROOT" ]; then echo "no usable run root" >&2; exit 1; fi;
echo "falling back to $FALLBACK_ROOT" >&2; ROOT="$FALLBACK_ROOT"; FALLBACK_ROOT=""; CHECK_TMP="yes";
done;
RUN_DIR="$BASE/$RUN_SLUG"; n=1;
while ! (umask 077; mkdir "$RUN_DIR") 2>/dev/null; do
if [ ! -e "$RUN_DIR" ]; then echo "could not create $RUN_DIR" >&2; exit 1; fi;
n=$((n+1)); RUN_DIR="$BASE/$RUN_SLUG-$n";
if [ "$n" -gt 99 ]; then echo "could not claim a run directory under $BASE" >&2; exit 1; fi;
done;
chmod 700 "$RUN_DIR" || exit 1;
echo "$RUN_DIR"
```

The symlink and ownership checks cover the selected root and `ce-prototype`, plus `.tmp` and `rocketclaw` on the fallback path, because they survive between runs. `mkdir -p` follows an existing symlink, and `chmod` would otherwise affect its target. An unsafe durable root falls back inside the same workspace; an unsafe fallback stops before writing and never redirects the run to a global location.

Creating the directory is how it is claimed — never test whether the name is free and then write, which two runs starting together both pass. There is no rejoin: this block runs once per invocation, so a second question never re-derives the run directory and can neither split into a suffixed sibling nor adopt a finished run's directory.

Then, once per question, create that question's directory under the run directory the block above printed:

```bash
RUN_DIR="<absolute run directory the resolution block printed>";
QUESTION_SLUG="<NN>-<question-slug>";
if [ -L "$RUN_DIR" ] || [ ! -O "$RUN_DIR" ]; then echo "unsafe run directory: $RUN_DIR" >&2; exit 1; fi;
PROTO_DIR="$RUN_DIR/$QUESTION_SLUG"; (umask 077; mkdir -p "$PROTO_DIR") || exit 1; chmod 700 "$PROTO_DIR" || exit 1;
echo "$PROTO_DIR"
```

Start (detached), with `PROTO_DIR` set to the absolute path the resolution printed:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PROTO_DIR="<absolute question directory the resolution block printed>";
if [ -L "$PROTO_DIR" ] || [ ! -O "$PROTO_DIR" ]; then echo "unsafe run directory: $PROTO_DIR" >&2; exit 1; fi;
node "$SKILL_DIR/scripts/light-webserver.js" start --root "$PROTO_DIR"
```

The server takes `--root` on trust — it resolves the path and creates it, and checks nothing — so each call re-checks the directory it is about to hand over. The path arrives here by transcription across separate shell invocations, and a mistyped or stale one would otherwise be written to unverified.

Append `--foreground` to that `start` command for foreground mode. Status and stop take the same anchor and the same `PROTO_DIR` — and because neither persists between Bash invocations, each must re-set both in its own call rather than reuse the `start` block's values:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PROTO_DIR="<absolute question directory the resolution block printed>";
if [ -L "$PROTO_DIR" ] || [ ! -O "$PROTO_DIR" ]; then echo "unsafe run directory: $PROTO_DIR" >&2; exit 1; fi;
node "$SKILL_DIR/scripts/light-webserver.js" status --root "$PROTO_DIR"
# stop: the same command with `stop` in place of `status` (re-set both again)
```

If `SKILL_DIR` cannot be resolved to a concrete skill directory, do not guess from the project CWD. Stop and report that the preview cannot start; do not settle the question in chat instead.

The helper creates `screens/` and `state/`, serves the newest `.html` file in `screens/` at `/`, writes `state/display-info.json`, and exposes `/version` so the browser can poll for screen changes. Every other URL is read from the matching nested path under `screens/`, so a screen keeps the asset layout it was copied from. Put referenced assets under `screens/` at those paths, or inline them as data URIs. Anything resolving outside `screens/` is refused.

Before handing over the URL, look at the rendered screen — a screenshot where the platform has one, otherwise measure the laid-out result in the DOM. A 200 on every asset is not that check: an image that loads correctly at the wrong size passes it, as does a script that leaves the page inert. Check each variant at rest, not just the page — one bug in shared scaffolding reads as several bad designs. Drive an interaction only when its behavior is invisible at rest, which is also the case where telling them to try something you have not tried is a claim you made up. Measurement lies by default — computed styles read mid-transition, scroll events coalesce — so read after things settle, and suspect the instrument before you conclude the page is broken. You are done when they could judge the idea, not when the code is correct. If you have no way to see the rendered result, say so when you hand over the URL rather than implying it was checked.

The browser reloads only when the newest screen changes; it must not continually reload on a timer. `/version` polling does not count as activity. Detached servers monitor the owning harness process when it can be resolved, and all servers exit after an idle timeout. The helper has no browser-to-agent event path. Interactive HTML is allowed.

Write screens under:

```text
<workspace-root>/.rocketclaw/ce-prototype/<run-id>/
  decisions.md               # run capsule for the next skill; not a plan
  01-<question-slug>/
    screens/
      001-<variant>.html
      <asset-path>            # assets at the paths the screen references
    state/
      display-info.json
  02-<question-slug>/         # only when the run covers a second related question
    screens/
    state/
```

The in-workspace fallback starts at `<workspace-root>/.tmp/rocketclaw/ce-prototype/`; outside JJ, it starts at `<current-directory>/.tmp/rocketclaw/ce-prototype/`. The capsule sits at the run directory and names each question directory; `--root` is always a question directory, never the run directory.

## Launch mode by platform

The server is the same everywhere; only the launch mode changes.

- **Claude Code / Claude desktop app:** detached `start` is the default path. If the app opens localhost URLs, show the returned URL and continue.
- **Codex CLI / Codex app:** if detached processes are reaped or the URL dies after the tool call, use `start --foreground` through the platform's long-running/background terminal mechanism.
- **Plain terminal UI:** print the returned URL for the user to open manually.
- **Remote or containerized sessions:** if `localhost` is not reachable from the user's browser, start with `--host 0.0.0.0` and tell the user which host/port to open. That serves the run directory to anything that can reach the port, with no auth — do it only on a network the user trusts, and say so when you hand over the URL.

If the helper path is unavailable or the platform cannot display a local URL cleanly, stop and report that. Do not settle the question in chat instead — a question that needs a real artifact to be decided is not answered by talking about it.
