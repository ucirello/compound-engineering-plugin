# Preview helper

Load this when serving a local web prototype. Isolated web runs start the helper with annotation on; `references/annotation-loop.md` owns the wait loop and when chat is the fallback.

This skill ships its own `scripts/light-webserver.js`. Do not import a sibling skill's copy — isolation forbids that.

Use the bundled helper through OpenCode's shell tool when it can run bundled skill scripts. Invoke it via the `SKILL_DIR` anchor: set `SKILL_DIR` to the absolute path of the directory containing the `ce-prototype` `SKILL.md` you loaded (the shell's cwd is the user's project, not the skill dir), and re-set it in the same command on each call since shell vars do not persist between invocations. Do not resolve the helper from the user's project CWD.

Resolve the question directory once, at the start of the run, and reuse the absolute path it prints for every later call. Do not re-derive it per command — the server keys its pidfile and its process match off `--root`, so a start and a stop that resolve differently leave an orphaned server.

`RUN_SLUG` is `<date>-<short-question-slug>` for the run; `QUESTION_SLUG` is `NN-<question-slug>` for the question being built. A run that covers a second related question resolves a second question directory under the same run directory.

Settle durability before you run this block. In the absolute project directory, resolve the JJ root with `(cd "$project_dir" && jj workspace root)`. Use that absolute root as `RUN_PARENT`; use the absolute local project directory only when there is no JJ workspace. Don't treat an unreadable or broken workspace as no workspace. See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).

In JJ, verify ignore coverage before marking either destination usable. Evaluate the effective ignore rules for the directory itself, including negations, using local ignore-pattern matching or inspection of the applicable rules; an explicit, effective `/.context/` or `/.tmp/` in the root `.gitignore` covers the corresponding directory. Also check that no paths there are already tracked with `(cd "$workspace_root" && jj --ignore-working-copy file list .context .tmp)`; this lists tracked paths, not ignore matches. Do not assume an empty listing alone proves the directory is ignored. If coverage is uncertain or the check fails, don't mark that destination usable.

Set `CONTEXT_OK=yes` only in JJ when `.context/` is covered and the user wants a durable run. If ignore coverage is missing, first offer to append `/.context/` to the workspace-root `.gitignore`, only with approval, preserving existing content; then verify coverage again. Don't offer this edit for a run that needs the temporary root regardless. Set `TEMP_OK=yes` if `.tmp/` is confirmed ignored and untracked in JJ, or if working outside JJ and local `.tmp/` is permitted by the project. If local temporary storage is needed but `.tmp/` needs an ignore rule, offer to append `/.tmp/` only with approval and verify again. If no authorized safe destination remains, report the blocker, rather than writing to OS-global storage or a tracked path. An ignored `.tmp/` is still physically in the workspace: if the user forbids workspace writes entirely, don't use it.

```bash
RUN_SLUG="<YYYY-MM-DD>-<run-slug>";
RUN_PARENT="<absolute verified workspace or local project root>";
CONTEXT_OK="<yes or no>";
TEMP_OK="<yes or no>";
safe_dir() {
  [ ! -L "$1" ] &&
    { [ -d "$1" ] || (umask 077; mkdir "$1") || [ -d "$1" ]; } &&
    [ ! -L "$1" ] && [ -d "$1" ] && [ -O "$1" ] && [ -w "$1" ]
}
BASE="$RUN_PARENT/.context/ce-prototype";
if [ "$CONTEXT_OK" = yes ] &&
   safe_dir "$RUN_PARENT/.context" && safe_dir "$BASE" && chmod 700 "$BASE"; then
  :
else
  ROOT="$RUN_PARENT/.tmp";
  BASE="$ROOT/rocketclaw/ce-prototype";
  if [ "$TEMP_OK" != yes ] || ! safe_dir "$ROOT" ||
     ! safe_dir "$ROOT/rocketclaw" || ! safe_dir "$BASE" || ! chmod 700 "$BASE"; then
    echo "no usable run root" >&2; exit 1;
  fi;
  echo "using local temporary storage: $BASE" >&2;
fi;
RUN_DIR="$BASE/$RUN_SLUG"; n=1;
while ! (umask 077; mkdir "$RUN_DIR") 2>/dev/null; do
if [ ! -e "$RUN_DIR" ]; then echo "could not create $RUN_DIR" >&2; exit 1; fi;
n=$((n+1)); RUN_DIR="$BASE/$RUN_SLUG-$n";
if [ "$n" -gt 99 ]; then echo "could not claim a run directory under $BASE" >&2; exit 1; fi;
done;
chmod 700 "$RUN_DIR" || exit 1;
echo "$RUN_DIR"
```

The block checks symlinks and ownership at each directory below the verified parent before descending. It restricts the prototype base and run directory without changing permissions on shared `.context/` or `.tmp/`. If the durable path is unsafe it tries the verified local fallback; if the fallback has not yet been authorized or verified, resolve that before retrying. Never widen permissions to make either path work.

Creating the directory is how it is claimed — never test whether the name is free and then write, which two runs starting together both pass. There is no rejoin: this block runs once per invocation, so a second question never re-derives the run directory and can neither split into a suffixed sibling nor adopt a finished run's directory.

Then, once per question, create that question's directory under the run directory the block above printed:

```bash
RUN_DIR="<absolute run directory the resolution block printed>";
QUESTION_SLUG="<NN>-<question-slug>";
if [ -L "$RUN_DIR" ] || [ ! -O "$RUN_DIR" ]; then echo "unsafe run directory: $RUN_DIR" >&2; exit 1; fi;
PROTO_DIR="$RUN_DIR/$QUESTION_SLUG";
[ ! -L "$PROTO_DIR" ] && (umask 077; mkdir -p "$PROTO_DIR") &&
  [ ! -L "$PROTO_DIR" ] && [ -d "$PROTO_DIR" ] && [ -O "$PROTO_DIR" ] &&
  chmod 700 "$PROTO_DIR" || exit 1;
echo "$PROTO_DIR"
```

Start (detached), with `PROTO_DIR` set to the absolute path the resolution printed:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PROTO_DIR="<absolute question directory the resolution block printed>";
if [ -L "$PROTO_DIR" ] || [ ! -O "$PROTO_DIR" ]; then echo "unsafe run directory: $PROTO_DIR" >&2; exit 1; fi;
node "$SKILL_DIR/scripts/light-webserver.js" start --root "$PROTO_DIR" --annotate
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

The helper creates `screens/` and `state/`, serves the newest `.html` file in `screens/` at `/`, writes `state/display-info.json`, and exposes `/version` so a default (annotate-off) browser can poll for screen changes. Isolated web starts pass `--annotate`: the printed URL is the origin (no token in it), the overlay is added at serve time to every HTML document the browser navigates to under `screens/` (a script fetching an HTML partial gets it raw), and disk screens stay agent-clean. Visiting that origin sets a session cookie so the overlay can reach wait, annotation, and events; those routes stay token-gated. Do not print the token to the explorer. A prototype may use `?token=` or other query state of its own. Every other path is read from `screens/` at that same path — `/img/blot.webp` serves `screens/img/blot.webp` — so a screen keeps whatever asset layout it was copied from, nesting included. Put the assets the screen references under `screens/` at the paths it asks for, or inline them as data URIs. Anything resolving outside `screens/` is refused.

Before handing over the URL, look at the rendered screen — a screenshot where the platform has one, otherwise measure the laid-out result in the DOM. A 200 on every asset is not that check: an image that loads correctly at the wrong size passes it, as does a script that leaves the page inert. Check each variant at rest, not just the page — one bug in shared scaffolding reads as several bad designs. Drive an interaction only when its behavior is invisible at rest, which is also the case where telling them to try something you have not tried is a claim you made up. Measurement lies by default — computed styles read mid-transition, scroll events coalesce — so read after things settle, and suspect the instrument before you conclude the page is broken. You are done when they could judge the idea, not when the code is correct. If you have no way to see the rendered result, say so when you hand over the URL rather than implying it was checked.

A default start reloads only when the newest screen changes; it must not continually reload on a timer. Annotate-on pushes each change under `screens/` — the screen or an asset it links — over a stream, and the page reloads. Pins for notes the agent has not applied yet survive the reload; a pin leaves the page once its note is applied, and every pin clears when the session ends. `/version` polling and an open tab do not count as activity, so an abandoned tab cannot keep the server alive; an annotation POST and a running `wait` do, so a session with an agent waiting on it does not idle out. Detached servers monitor the owning harness process when it can be resolved, and all servers exit after an idle timeout. Interactive HTML is allowed.

Write screens under:

```text
<repo>/.context/ce-prototype/<YYYY-MM-DD>-<run-slug>/
  decisions.md               # run capsule for the next skill; not a plan
  01-<question-slug>/
    screens/
      001-<variant>.html
      img/blot.webp          # any assets the screen references, at the paths it uses
      world/cast/pip.webp
    state/
      display-info.json
  02-<question-slug>/         # only when the run covers a second related question
    screens/
    state/
```

The fallback root takes the same shape under `<workspace-or-local-project>/.tmp/rocketclaw/ce-prototype/`. The capsule sits at the run directory and names each question directory; `--root` is always a question directory, never the run directory.

## Handoff

Pick the browser that will load the prototype — one surface. Hand it the origin it will actually request. The helper prints `http://localhost:<port>`. Use that when that browser is on this machine. When it is not, start with `--host 0.0.0.0` and hand the explorer the helper's returned URL with only the host rewritten to one they can reach. Rewrite only the host. Do not also hand localhost. Visiting that origin sets the session cookie. Wait talks the bind address with the file token. Do not print the token. Binding every interface serves the run directory to anything that can reach the port; annotation and wait routes stay token-gated — do it only on a network the user trusts, and say so when you hand over the URL.

Keep the server alive the way this host actually does. Detached `start` is the default. If this host reaps detached processes or the URL dies after the tool call, append `--foreground` through its long-running terminal.

If the helper path is unavailable or the platform cannot display a local URL cleanly, stop and report that. Do not settle the question in chat instead — a question that needs a real artifact to be decided is not answered by talking about it.
