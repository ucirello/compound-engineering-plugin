# Prepare the live polish loop

This reference owns JJ workspace safety, Git-provider interoperability, server startup, reachability, and browser handoff. It does not own the user's iterative polish decisions.

## Resolve the workspace

Require a JJ workspace and resolve its root with `jj workspace root`. Jujutsu has working-copy changes and bookmarks, not a current branch, detached HEAD mode, an index, or a stash. Use JJ for every repository mutation. Read-only Git commands remain valid in a colocated repository when an operational provider needs them, and Git Bash remains a supported shell, but do not substitute a mutating Git command for a JJ operation.

If the user named a GitHub PR, use `gh` to obtain its head repository, head bookmark, and head commit ID. In a non-colocated Git-backed workspace, obtain the backing repository with `jj git root` and expose that path to `gh` as `GIT_DIR`. Fetch the head through `jj git fetch` from a configured remote that matches the head repository; when none exists, use `jj git remote` to add a uniquely named remote for that provider repository before fetching, and remove only that temporary remote after the selected revision is anchored by the new working-copy change. Do not use `gh pr checkout`. For another provider, use its available interface for the same metadata and keep all fetch/import operations in `jj git`. If authentication, provider metadata, remote identity, or the fetched head cannot be established exactly, report the blocker and stop.

Resolve a supplied bookmark, change ID, commit ID, or revset to exactly one revision with `jj log -r`; fetched bookmarks may require their `<bookmark>@<remote>` name. With no argument, select `@`. Inspect `jj workspace list` before changing the current workspace. If a listed workspace's working-copy revision is the selection or contains it in the workspace's unambiguous active mutable stack, enter that workspace when the available filesystem capability permits it; otherwise report the workspace path and stop rather than attaching a second workspace to the same work.

When the selected revision is not already the current workspace's `@`, preserve any existing current work: proceed only when `@` is empty and conflict-free, then start a new working-copy change with `jj new <selected-revision>`. Never use `jj edit` merely to emulate branch checkout because edits would rewrite the selected revision. Confirm the resulting `@` is mutable, conflict-free, and not `trunk()` itself. A selection at `trunk()` is safe only because `jj new` creates a mutable child. If any revset is ambiguous, a workspace is stale, or moving to the target would overwrite or strand work, report the evidence and stop. Do not create, forget, or delete a workspace implicitly.

## Resolve the start command

The commands below execute scripts bundled with this skill. For every self-contained shell call, set `SKILL_DIR` to the absolute directory containing the loaded `ce-polish` `SKILL.md`; shell state does not carry between calls.

First inspect the workspace-root launch configuration:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/read-launch-json.sh"
```

Resolve one startup tuple: command, working directory, environment, and port. A selected launch configuration supplies every usable fact it declares: `runtimeExecutable` plus optional `runtimeArgs` form the command, `cwd` defaults to the workspace root, `env` augments the inherited environment, and `port` must be numeric. Preserve those facts while resolving only what remains unknown. When all four facts are usable, the tuple is complete: skip classification, recipe loading, package-manager resolution, and port resolution, then continue to startup. Ambiguous declarations remain in disambiguation: show their names, ask the user to choose, and rerun with that name. Any operational failure or unresolved tuple fact blocks startup and must be reported.

Run project classification only when an unresolved command or port requires a project type. Classify the selected working directory when a launch configuration supplied one; otherwise classify the workspace root. Pass that resolved project root explicitly:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/detect-project-type.sh" "<project-root>"
```

`<type>` means the classification root; `<type>@<relative-dir>` means that directory under the classification root. Ask the user to choose when the output is `multiple` or `multiple:...`. For `unknown`, ask only for the unresolved tuple facts and do not guess.

Read `references/dev-server-<base-type>.md` only when the command remains unresolved after a supported classification. If that recipe requires a package-manager executable to complete the command, resolve it in the classified project root rather than guessing:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/resolve-package-manager.sh" "<project-root>"
```

Run the port resolver only while the port remains unresolved, using the detected type without replacing a selected command, working directory, or environment:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/resolve-port.sh" "<project-root>" --type <base-type>
```

Startup may proceed only when the tuple has a usable command, working directory, environment, and numeric port. If a classifier, recipe, or resolver fails operationally or leaves its required fact unknown, report that blocker; do not substitute a plausible value. After supported auto-detection supplies a missing fact, offer once to save the completed tuple as `.claude/launch.json`; write it only when the user accepts, after reading `references/launch-json-schema.md` and any recipe used.

## Start and hand off

Inspect the chosen port and select exactly one intended server instance before handoff. Reuse a process already serving that port only when evidence identifies it as the intended project server. Only when no intended instance is selected may the resolved command be launched in the background with the project's working directory and environment; that process becomes the selected instance. Keep its process or session handle. Write its output only beneath an ignored, non-symlinked `.tmp/rocketclaw/polish/<unique-run>/` directory at the root returned by `jj workspace root`; outside JJ, use the current local workspace's `.tmp/rocketclaw/polish/<unique-run>/`. Reject a `.tmp` path not owned by the effective user, create directories with mode `0700`, atomically reserve a unique log file with mode `0600`, and retry on collision. Never use an operating-system or global temporary directory.

An occupied port that cannot be attributed to the intended project server remains an unresolved collision. Ask the user whether to stop that process, choose another port, or stop this run; never kill it or launch past it.

Resolve the selected instance's actual URL before handoff. The resolved port seeds `http://localhost:<port>` as the default candidate, but server output or a user correction replaces that candidate when it identifies a different URL. Attribute successful reachability at the resolved actual URL to the selected instance by probing for up to 30 seconds; a response from another process is not success.

- **Reachable:** use an available browser-opening capability with the verified actual URL. If none exists or the handoff fails, print that URL; browser handoff is a convenience, not a gate.
- **Not reachable:** show diagnostics derived from the selected instance. Include the last 20 log lines only when this run launched it and owns those logs. Ask whether to correct the server URL or start configuration, or stop.

Do not continue into the polish loop unless reachability is attributed to the selected instance.

Tell the user:

```text
Dev server running on <verified-actual-url>
Browse the feature and tell me what could be better.
```
