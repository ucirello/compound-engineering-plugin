---
name: ce-polish
description: "Start the dev server, inspect the feature in browser, and iterate on polish."
disable-model-invocation: true
argument-hint: "[PR number, bookmark name, or blank for current workspace]"
---

# Polish

Start the dev server, open the feature in a browser, and iterate. You use the feature, say what feels off, and fixes happen.

## Phase 0: Get in the right workspace

1. If a PR number or bookmark name was provided, use `ce-worktree` to attach it in an existing or new JJ workspace.
2. If blank, use the current workspace.
3. Resolve the project's protected/default bookmark from the active project instructions and remote metadata shown by `jj bookmark list --all-remotes`; do not infer it from a conventional bookmark name. If those sources do not identify it unambiguously, ask the user rather than guessing.
4. Use `jj bookmark list --all-remotes -r @` to determine which local or remote bookmarks point exactly at the working-copy commit, and use `jj log -r '@ & immutable()'` to check whether that commit is immutable. A bookmark pointing at `@` does not mean the working copy is "on" that bookmark.
5. Before editing, if the resolved protected/default bookmark points at `@`, or if `@` is immutable, run `jj new @` to create a mutable descendant. Otherwise, keep the current working-copy commit so existing unbookmarked work remains intact.

## Phase 1: Start the dev server

The scripts below ship in this skill's `scripts/` directory. The Bash tool's working directory is the user's project, not the skill directory, so a bare `scripts/<name>` path will not resolve — invoke each by the skill's own absolute path. Every runnable block below sets `SKILL_DIR` inline (shell state does not persist between Bash tool calls, so each command must carry it); replace the `<absolute path …>` placeholder with the directory you loaded this `ce-polish` SKILL.md from before running.

### 1.1 Check for `.agents/launch.json`

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>"
bash "$SKILL_DIR/scripts/read-launch-json.sh"
```

If it finds a configuration, use it — the user already told us how to start the project.

### 1.2 Auto-detect (when no launch.json)

Identify the framework:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>"
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
SKILL_DIR="<absolute path of the directory containing this SKILL.md>"
bash "$SKILL_DIR/scripts/resolve-package-manager.sh"
```

Resolve the port:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>"
bash "$SKILL_DIR/scripts/resolve-port.sh" --type <type>
```

### 1.3 Start the server

Resolve the workspace-local temp directory before starting the server:

```bash
WORKSPACE_ROOT="$(jj workspace root 2>/dev/null || pwd)"
TMP_DIR="$WORKSPACE_ROOT/.tmp"
mkdir -p "$TMP_DIR"
```

Start the dev server in the background with output logged under `$TMP_DIR`. Do not use an OS-global temp directory, `$TMPDIR`, `mktemp`, or `tempfile`. Probe `http://localhost:<port>` for up to 30 seconds. If it doesn't come up, show the last 20 lines of the log and ask the user what to do.

### 1.4 Open in browser

Load `references/ide-detection.md` for the env-var probe table. Open the browser using the IDE's mechanism (Claude Code → `open`, Cursor → Cursor browser, VS Code → Simple Browser).

Tell the user:
```
Dev server running on http://localhost:<port>
Browse the feature and tell me what could be better.
```

## Phase 2: Iterate

This is the core loop. The user browses the feature and tells you what to improve. You fix it. Repeat until they're happy.

- When the user describes something to fix → make the change, the dev server hot-reloads
- When the user asks to check something → use a browser-automation capability to screenshot or inspect the page; prefer `agent-browser` if it's installed, otherwise use whatever the host exposes
- When the user says they're done → create a JJ commit for the fixes and stop

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
