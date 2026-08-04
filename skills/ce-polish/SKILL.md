---
name: ce-polish
description: "Start the dev server, inspect the feature in browser, and iterate on polish."
disable-model-invocation: true
argument-hint: "[PR number, bookmark name, or blank for current workspace]"
---

# Polish

Start the dev server, open the feature in a browser, and iterate. You use the feature, say what feels off, and fixes happen.

## Phase 0: Get in the right workspace

1. If a PR number was provided, use `gh pr view <number> --json headRefName` to resolve its GitHub head name, then use `ce-worktree` to attach that bookmark in an existing or new JJ workspace. Preserve all other PR review and GitHub operations through `gh`.
2. If a bookmark name was provided, use `ce-worktree` to attach it in an existing or new JJ workspace. When remote synchronization is needed, inspect configured remotes with `jj git remote list`, select the project-defined remote, and run `jj git fetch --remote <remote>` before attaching; do not guess the remote.
3. If blank, keep the current JJ workspace and working-copy commit, including any unbookmarked changes already present.
4. Resolve the project's protected/default bookmark from the active project instructions and remote bookmarks shown by `jj bookmark list --all-remotes`. If those sources do not identify it unambiguously, ask rather than assuming a conventional name.
5. Inspect exact local and remote pointers with `jj log -r '@ & (bookmarks() | remote_bookmarks())'`, cross-check their names with `jj bookmark list --all-remotes`, and inspect immutability with `jj log -r '@ & immutable()'`. A bookmark pointing at `@` does not mean the workspace is "on" that bookmark.
6. Before editing, if the protected/default bookmark points at `@`, or if `@` is immutable, create a mutable descendant with `jj new @`. Otherwise preserve the current working-copy commit.

## Phase 1: Start the dev server

The scripts below ship in this skill's `scripts/` directory. The Bash tool's working directory is the user's project, not the skill directory, so a bare `scripts/<name>` path will not resolve — invoke each by the skill's own absolute path. Every runnable block below sets `SKILL_DIR` inline (shell state does not persist between Bash tool calls, so each command must carry it); replace the `<absolute path …>` placeholder with the directory you loaded this `ce-polish` SKILL.md from before running.

### 1.1 Check for `.rocketclaw/launch.json`

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/read-launch-json.sh"
```

If it finds a configuration, use it — the user already told us how to start the project.

### 1.2 Auto-detect (when no launch.json)

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

Resolve `WORKSPACE_ROOT` with `jj workspace root`, falling back to the current directory, create `$WORKSPACE_ROOT/.tmp/rocketclaw/ce-polish`, and make one unique per-run directory beneath it. Start the dev server in the background with output logged only under that directory. Probe `http://localhost:<port>` for up to 30 seconds. If it doesn't come up, show the last 20 lines of the log and ask the user what to do.

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
- When the user says they're done, inspect the complete working-copy change with `jj status` and `jj diff`. Preserve unrelated pre-existing changes and ask before splitting them if the intended boundary is ambiguous. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Preserve every semantic content requirement stated by this site while adapting syntax to runtime conventions. The mandated sentence's `git log` wording is not an operational command; inspect history with `jj log`. The project's active instructions and change-description syntax inferred at runtime from `jj log` always win. Apply compatible Go guidance only for quality, clarity, and structure. Do not impose any fixed prefix, type, scope, subject, body, layout, template, or example. Set the description with `jj describe -m <description-composed-from-runtime-conventions>`, then run `jj new` so the completed change is left as a described parent and the workspace is ready for new work. Do not add creator, model, provider, tool, or runtime attribution to the JJ description. Do not create, move, or push a bookmark unless the user asks. When publication is requested, resolve the specific bookmark and an explicit writable remote from the project's active instructions, `jj log`, `jj bookmark list --all-remotes`, and `jj git remote list`; ask if either is ambiguous. Move that bookmark to the completed change with `jj bookmark set <bookmark> -r @-`, verify its target, and publish only that bookmark with `jj git push --remote <remote> --bookmark <bookmark>`, while preserving GitHub operations through `gh`.

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
