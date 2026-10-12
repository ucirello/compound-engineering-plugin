# Prepare the live polish loop

This reference owns checkout safety, server startup, reachability, and browser handoff. It does not own the user's iterative polish decisions.

## Resolve the workspace

Resolve the current absolute root with `jj workspace root`. Run every JJ command from the target workspace's absolute root, for example `(cd "$workspace_root" && jj status)`; `jj -R` is not a working-directory substitute. Consult https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace and https://docs.jj-vcs.dev/latest/git-experts/ for native workspace and bookmark semantics. For repository-scoped GitHub calls use `(cd "$workspace_root" && export GIT_DIR=$(jj git root) && gh ...)`.

If the user named a PR or branch, resolve its exact revision and bookmark, then inspect `jj workspace list` and the registered workspaces to locate any existing workspace on that target (including an empty `@` directly above it). Enter that existing workspace and move the active harness session there using its supported capability; if it cannot, report the blocker and stop. Reuse existing isolation under its verified name without renaming, recreating, or silently changing its colocation. Only use the harness's JJ revision-switch capability in the current workspace when no other workspace owns the target and unrelated tracked, ignored, and untracked work is preserved. With no argument, stay in the current workspace.

Confirm the resulting feature revision is associated with the intended non-default bookmark, not the repository's default bookmark; JJ's working-copy change need not itself carry a bookmark. Report and stop when a safe feature workspace cannot be reached; do not create another workspace behind the harness or move unrelated user changes. This workflow does not create or remove workspaces. Any separately authorized isolated setup must follow `ce-worktree`'s explicit `jj workspace add --colocate`, destination-root `jj git colocation status`, stable `YYYYMMDD-<meaningful-kebab-case-slug>` identity matching the local `.tmp/` destination basename, collision suffixes, and harness ownership rules; incompatible harness capabilities are blockers, not a Git fallback. Retirement belongs to the authorized workspace owner under `ce-worktree`'s safe JJ-owned `workspace remove` lifecycle, not this polish loop.

## Resolve the start command

The commands below execute scripts bundled with this skill. For every self-contained shell call, set `SKILL_DIR` to the absolute directory containing the loaded `ce-polish` `SKILL.md`; shell state does not carry between calls.

First inspect the repo-root launch configuration:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/read-launch-json.sh"
```

Resolve one startup tuple: command, working directory, environment, and port. A selected launch configuration supplies every usable fact it declares: `runtimeExecutable` plus optional `runtimeArgs` form the command, `cwd` defaults to the repository root, `env` augments the inherited environment, and `port` must be numeric. Preserve those facts while resolving only what remains unknown. When all four facts are usable, the tuple is complete: skip classification, recipe loading, package-manager resolution, and port resolution, then continue to startup. Ambiguous declarations remain in disambiguation: show their names, ask the user to choose, and rerun with that name. Any operational failure or unresolved tuple fact blocks startup and must be reported.

Run project classification only when an unresolved command or port requires a project type. Classify the selected working directory when a launch configuration supplied one; otherwise classify the repository root. Omit the path argument for the repository root:

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

Inspect the chosen port and select exactly one intended server instance before handoff. Reuse a process already serving that port only when evidence identifies it as the intended project server. Only when no intended instance is selected may the resolved command be launched in the background with the project's working directory and environment; that process becomes the selected instance. Keep its process or session handle, and write its output under a directory created with `mktemp -d "$workspace_root/.tmp/polish-XXXXXX"`. First ensure the workspace-local `.tmp/` parent exists, is owned and writable, is not a symlink, and is ignored; do not fall back to OS-global temporary storage on failure.

An occupied port that cannot be attributed to the intended project server remains an unresolved collision. Ask the user whether to stop that process, choose another port, or stop this run; never kill it or launch past it.

Resolve the selected instance's actual URL before handoff. The resolved port seeds `http://localhost:<port>` as the default candidate, but server output or a user correction replaces that candidate when it identifies a different URL. Attribute successful reachability at the resolved actual URL to the selected instance by probing for up to 30 seconds; a response from another process is not success.

- **Reachable:** use the browser-opening capability already exposed by the active harness with the verified actual URL. If it has none or the handoff fails, print that URL; browser handoff is a convenience, not a gate.
- **Not reachable:** show diagnostics derived from the selected instance. Include the last 20 log lines only when this run launched it and owns those logs. Ask whether to correct the server URL or start configuration, or stop.

Do not continue into the polish loop unless reachability is attributed to the selected instance.

Tell the user:

```text
Dev server running on <verified-actual-url>
Browse the feature and tell me what could be better.
```
