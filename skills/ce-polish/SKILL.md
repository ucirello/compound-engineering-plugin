---
name: ce-polish
description: "Start the dev server, inspect the feature in browser, and iterate on polish."
disable-model-invocation: true
argument-hint: "[PR number, JJ bookmark/revision, or blank for current workspace]"
---

# Polish

Start the dev server, open the feature in a browser, and iterate. You use the feature, say what feels off, and fixes happen.

## Phase 0: Work in the right JJ workspace and revision

1. Require a JJ workspace: resolve its root with `jj workspace root`. Use that root as the project root for every detection script and project-relative path below.
2. Run `jj workspace list`, `jj status`, and `jj bookmark list -r @`. JJ has no current branch: `@` is the current workspace's working-copy revision, and bookmarks are movable labels that may or may not point to it.
3. Resolve the target:
   - With no argument, use `@` in the current workspace.
   - For a JJ bookmark/revision, resolve exactly one revision with `jj log -r 'exactly(<target>, 1)' --no-graph`.
   - For a PR number, read `baseRefName`, `headRefName`, `headRefOid`, and `isCrossRepository` with `GIT_DIR="$(jj git root)" gh pr view <number> --json baseRefName,headRefName,headRefOid,isCrossRepository`; setting `GIT_DIR` this way keeps `gh` working in non-colocated JJ repositories. Require `headRefOid` to be a 40-character hexadecimal object ID. Before using `headRefName`, require a nonempty slash-separated Git branch shape containing only ASCII letters, digits, `.`, `_`, `/`, and `-`: no empty component, component beginning or ending `.`, component ending `.lock`, `..`, or `@{`, and the whole name must not begin `-` or end `/`. Reject invalid metadata rather than interpolating it. Resolve content only with `jj log -r 'exactly(commit_id(<validated-headRefOid>), 1)' --no-graph`; never resolve content from the branch name. If the OID is not present, inspect existing remotes with `jj git remote list`, then fetch with the exact JJ string pattern `jj git fetch --remote "<remote>" --branch "exact:\"<validated-headRefName>\""` and resolve the validated OID again. Do not pass a bare branch name or a glob pattern. Do not use `gh pr checkout` or raw `git` commands. If a cross-repository head is unavailable through any existing remote, stop and ask the user to provide a local JJ revision or workspace; do not add a remote implicitly.
4. Before changing the current workspace, inspect the revisions checked out by `jj workspace list`. If an existing workspace is already at the target or at an empty child of it, continue from that workspace using its path from `jj workspace root --name <workspace>`.
5. Otherwise, if the target is not the current `@`, run `jj status` first. If `@` contains changes, ask before leaving it. Then create a dedicated working-copy change with `jj new <target>`; do not `jj edit` the target, because polish fixes should be a new change rather than a rewrite of the feature revision.
6. Resolve `trunk()` to exactly one revision rather than guessing `main` or `master`. Stop if the selected target is `trunk()`, or if a blank target is an empty `@` directly on `trunk()`; there is no feature to polish.
7. Record the selected target's change ID and Git commit ID with `jj log -r <target> --no-graph -T 'change_id.short() ++ " " ++ commit_id.short() ++ "\n"'`. Git commit IDs are retained only because GitHub identifies PR commits by SHA. To understand the feature scope, use the PR's resolved base remote bookmark for a PR and `trunk()` otherwise, resolve `<base>` with `exactly(fork_point(<comparison-tip> | <target>), 1)`, inspect history with `jj log -r '<base>..<target>'`, and inspect changed paths with `jj diff --from <base> --to <target> --name-only`.

## Phase 1: Start the dev server

The scripts below ship in this skill's `scripts/` directory. The Bash tool's working directory is the user's project, not the skill directory, so a bare `scripts/<name>` path will not resolve — invoke each by the skill's own absolute path. Every runnable block below sets `SKILL_DIR` inline (shell state does not persist between Bash tool calls, so each command must carry it); replace the `<absolute path …>` placeholder with the directory you loaded this `ce-polish` SKILL.md from before running.

### 1.1 Check for `.claude/launch.json`

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

Interpret the detector's complete output grammar before routing:

- For `<type>`, set `PROJECT_TYPE` to that type and `PROJECT_DIR` to the JJ workspace root.
- For `<type>@<relative-dir>`, split at `@`, set `PROJECT_TYPE` to the type, and set `PROJECT_DIR` to that subdirectory under the JJ workspace root.
- For `multiple:<type>@<dir>,...`, show the listed candidates and ask the user which project to run. Set `PROJECT_TYPE` and `PROJECT_DIR` from the selected candidate.
- For bare `multiple`, explain that multiple root signatures matched and ask the user to select the project type and project directory; do not guess.
- For `unknown`, ask how to start the project.

Run the selected recipe's start command with `PROJECT_DIR` as its working directory.

For framework types that need a package manager, run the resolver and substitute the result into the start command:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>"
bash "$SKILL_DIR/scripts/resolve-package-manager.sh" "$PROJECT_DIR"
```

Resolve the port:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>"
bash "$SKILL_DIR/scripts/resolve-port.sh" "$PROJECT_DIR" --type "$PROJECT_TYPE"
```

### 1.3 Start the server

Start the dev server in the background, log output to a temp file. Probe `http://localhost:<port>` for up to 30 seconds. If it doesn't come up, show the last 20 lines of the log and ask the user what to do.

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
- When the user says they're done → run `jj status` and review `jj diff` for the current working-copy change, then invoke `ce-commit` to finalize the fixes and stop. JJ snapshots tracked files automatically; do not stage files or run raw `git` commands.

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
