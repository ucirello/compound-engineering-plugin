---
name: ce-polish
description: "Start the dev server, inspect the feature in a browser, and iterate on the user-visible result."
disable-model-invocation: true
argument-hint: "[PR number, bookmark/change, or blank for the current working copy]"
---

# Browser Iteration

Start the dev server, open the feature in a browser, and iterate with the user until the requested experience is accepted. Finish with the changes committed in the selected `jj` working copy, or report the blocker that prevents that result.

## Phase 0: Select the working copy

If a PR number was provided, preserve the GitHub/`gh` workflow for resolving its head and select the corresponding `jj` change or bookmark. If a bookmark or change was provided, select it directly, reusing an existing `jj` workspace when one already owns that working copy. With no argument, use the current working-copy change. Do not iterate directly on the immutable trunk change; stop and ask for direction if the requested target cannot be selected safely.

## Phase 1: Start the dev server

The scripts below ship in this skill's `scripts/` directory. The shell tool's working directory is the user's project, not the skill directory, so a bare `scripts/<name>` path will not resolve. Invoke each by the skill's own absolute path. Every runnable block sets `SKILL_DIR` inline because shell state does not persist between calls; replace the placeholder with the directory from which this `ce-polish` route was loaded.

### 1.1 Check for `.claude/launch.json`

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/read-launch-json.sh"
```

If it finds a configuration, use it — the user already told us how to start the project.

### 1.2 Auto-detect when no launch configuration exists

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

Start the dev server in the background. Put its log under `<jj workspace root>/.tmp/`; if the workspace root cannot be resolved, use `$PWD/.tmp/`. Create the selected local directory before use and do not write runtime files to a global temporary directory. Probe `http://localhost:<port>` for up to 30 seconds. If it does not come up, show the last 20 lines of the log and ask the user what to do.

### 1.4 Open in browser

Load `references/ide-detection.md` for the env-var probe table. Open the browser using the IDE's mechanism (Claude Code → `open`, Cursor → Cursor browser, VS Code → Simple Browser).

Tell the user:
```
Dev server running on http://localhost:<port>
Browse the feature and tell me what could be better.
```

## Phase 2: Iterate

The user browses the feature and directs the improvements. Make each in-scope change and use the running server to verify it until the user accepts the result.

- When the user describes something to fix, make the change and let the dev server reload it.
- When the user asks to check something, use a browser-automation capability to screenshot or inspect the page; prefer `agent-browser` if it is installed, otherwise use whatever the host exposes.
- When the user accepts the result, commit the fixes with `jj` and stop. Local project commit-message conventions take precedence. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Treat the Go guidance as guidance rather than fixed syntax, and do not impose a fixed message format when local conventions differ.

Do not introduce a separate checklist or handoff artifact.

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
