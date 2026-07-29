---
name: ce-polish
description: "Start the dev server, inspect the feature in a browser, and iterate on RocketClaw polish."
disable-model-invocation: true
argument-hint: "[PR number, bookmark name, or blank for current change]"
---

# RocketClaw Polish

Start the dev server, open the feature in a browser, and iterate. The user tries the feature and says what feels off; apply the fixes.

## Phase 0: Select the right Jujutsu change

Before any repository-scoped `gh` operation, resolve `<repo>` in `[HOST/]OWNER/REPO` form from the applicable GitHub remote reported by `jj git remote list`; if multiple remotes remain plausible, stop rather than guessing. Preserve the host for GitHub Enterprise. Use `gh repo view <repo>` for repository inspection and pass `-R <repo>` to every `gh pr` and other repository-scoped command that supports it. If a call needs local repository context instead of accepting `-R`, run that same call as `GIT_DIR="$(jj git root)" gh ...`; do not export `GIT_DIR` for later calls.

1. Run `jj workspace root`, `jj status`, `jj diff`, and `jj log -r '@ | ancestors(@, 5)'` to establish the workspace, working-copy change, and nearby history. Use `jj workspace list` to detect another workspace already editing the requested revision.
2. If a PR number was provided, use `gh pr view <pr-number> -R <repo> --json headRefName` to resolve its bookmark, then run `jj git fetch --remote <remote>` and inspect it with `jj bookmark list <bookmark> --all-remotes`. Track it with `jj bookmark track <bookmark>@<remote>` when continued synchronization is wanted.
3. If a bookmark was provided, inspect it with `jj bookmark list <bookmark> --all-remotes`; fetch with `jj git fetch --remote <remote>` first when the remote state may be stale.
4. Jujutsu has no active or checked-out bookmark. If the requested revision is not already `@`, first preserve any current work, then use `jj new <bookmark-or-revision>` to create the RocketClaw polish change on top of it. If no argument was provided, continue the current non-empty change or use `jj new <base-revision>` when `@` is the trunk bookmark target.
5. Do not put RocketClaw polish edits directly in the trunk bookmark target. Confirm the selected base and working-copy change with `jj status` and `jj log -r '@ | parents(@)'` before continuing.

## Phase 1: Start the dev server

The scripts below ship in this skill's `scripts/` directory. The Bash tool's working directory is the user's project, not the skill directory, so a bare `scripts/<name>` path will not resolve — invoke each by the skill's own absolute path. Every runnable block below sets `SKILL_DIR` inline (shell state does not persist between Bash tool calls, so each command must carry it); replace the `<absolute path …>` placeholder with the directory you loaded this `ce-polish` SKILL.md from before running.

### 1.1 Check for `.rocketclaw/launch.json`

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/read-launch-json.sh"
```

If it finds a configuration, use it; the user has already specified how to start the project.

### 1.2 Auto-detect (when no launch.json)

The project's active instructions and observed scripts and configuration take precedence. Treat the recipes and stubs as fallback examples, not fixed syntax or templates.

Identify the framework:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/detect-project-type.sh"
```

Route by type to the matching recipe reference for start command and port defaults:

| Type | Recipe |
|------|--------|
| `rails` | `references/dev-server-rails.md` |
| `next` | `references/dev-server-next.md` |
| `vite` | `references/dev-server-vite.md` |
| `nuxt` | `references/dev-server-nuxt.md` |
| `astro` | `references/dev-server-astro.md` |
| `remix` | `references/dev-server-remix.md` |
| `sveltekit` | `references/dev-server-sveltekit.md` |
| `procfile` | `references/dev-server-procfile.md` |
| `unknown` | Ask the user how to start the project |

For framework types that need a package manager, run the resolver and substitute the result into the start command:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/resolve-package-manager.sh"
```

Resolve the port:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/resolve-port.sh" --type <type>
```

### 1.3 Start the server

Create workspace-local runtime storage before starting the server. Resolve the root with `jj workspace root`; if that fails, use the current directory so the fallback remains local `.tmp`. Reject symlinks at either managed path, apply a private umask, create `.tmp/rocketclaw-polish`, and keep the server log and any socket there. Never use a global temporary location.

```bash
WORKSPACE_ROOT=$(jj workspace root 2>/dev/null)
if [ -z "$WORKSPACE_ROOT" ]; then WORKSPACE_ROOT="$PWD"; fi
TMP_ROOT="$WORKSPACE_ROOT/.tmp"
if [ -L "$TMP_ROOT" ]; then printf '%s\n' "ERROR: refusing symlinked runtime directory: $TMP_ROOT" >&2; exit 1; fi
umask 077
RUN_DIR="$TMP_ROOT/rocketclaw-polish"
if [ -L "$RUN_DIR" ]; then printf '%s\n' "ERROR: refusing symlinked runtime directory: $RUN_DIR" >&2; exit 1; fi
mkdir -p "$RUN_DIR"
chmod 700 "$TMP_ROOT" "$RUN_DIR"
```

Start the dev server in the background and write output to `$RUN_DIR/dev-server.log`. Probe `http://localhost:<port>` for up to 30 seconds. If it does not come up, show the last 20 lines of that log and ask the user what to do.

### 1.4 Open in browser

Load `references/ide-detection.md` for the environment probe table. Open the browser using the available host mechanism.

Tell the user:
```
Dev server running on http://localhost:<port>
Browse the feature and tell me what could be better.
```

## Phase 2: Iterate

This is the core loop. The user browses the feature and says what to improve. Apply each fix and repeat until the user is happy.

- When the user describes something to fix → make the change, the dev server hot-reloads
- When the user asks to check something → use a browser-automation capability to screenshot or inspect the page; prefer `agent-browser` if it's installed, otherwise use whatever the host exposes
- When the user says they are done, inspect the final shape with `jj status`, `jj diff`, and `jj log`. Use `jj split`, `jj squash`, or `jj rebase` only when needed to leave coherent changes in the intended order.
- At the single change-description site, follow the repository-local instructions and observed message and command syntax first. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Use `jj describe` with the locally observed syntax; only when no local syntax is established, use `jj describe -r <revision> -m "<message derived from repository conventions and the actual diff>"`. Then use `jj new` to start a fresh change.
- If a bookmark should identify the finalized revision, use `jj bookmark set <bookmark> -r <revision>`. Do not push unless the user requested it; when requested, use `jj git push --bookmark <bookmark>` and use `gh` for PR operations.

No checklist. No envelope. Just conversation.

## References

Reference files (loaded on demand):
- `references/launch-json-schema.md` — launch.json schema + per-framework stubs
- `references/ide-detection.md` — host IDE detection and browser-handoff
- `references/dev-server-detection.md` — port resolution documentation
- `references/dev-server-rails.md` — Rails dev-server defaults
- `references/dev-server-next.md` — Next.js dev-server defaults
- `references/dev-server-vite.md` — Vite dev-server defaults
- `references/dev-server-nuxt.md` — Nuxt dev-server defaults
- `references/dev-server-astro.md` — Astro dev-server defaults
- `references/dev-server-remix.md` — Remix dev-server defaults
- `references/dev-server-sveltekit.md` — SvelteKit dev-server defaults
- `references/dev-server-procfile.md` — Procfile-based dev-server defaults

Scripts (invoked via `bash "$SKILL_DIR/scripts/<name>"` — see Phase 1 for `SKILL_DIR`):
- `scripts/read-launch-json.sh` — launch.json reader
- `scripts/detect-project-type.sh` — project-type classifier
- `scripts/resolve-package-manager.sh` — lockfile-based package-manager resolver
- `scripts/resolve-port.sh` — port resolution cascade
