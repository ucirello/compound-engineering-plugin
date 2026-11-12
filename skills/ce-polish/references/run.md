# Prepare the live polish loop

This reference owns checkout safety, server startup, reachability, and browser handoff. It does not own the user's iterative polish decisions.

## Resolve the workspace

Resolve and retain the absolute target JJ workspace root; run every JJ command with its shell working directory set to that root, not with `-R` as a substitute. If the user named a PR or branch, first inspect `jj workspace list` and bookmarks to locate whether its revision is already owned by a workspace. Enter and adopt that existing workspace through the harness lifecycle when supported; if it cannot, report the blocker and stop. Only use the harness's revision-switching capability in the current workspace when no other workspace owns the target. With no argument, stay in the current workspace. Repository-scoped `gh` calls must run from the verified root with `GIT_DIR=$(jj git root)` in their environment; never invoke the Git executable.

Verify the requested feature bookmark and its exact revision against the PR/source and remote evidence; an empty working-copy revision immediately above the verified feature head is valid, not a detached-branch failure. Never edit the default bookmark's line. Report and stop when a safe feature workspace cannot be reached or identity is uncertain; preserve conflicts, unrelated tracked changes, ignored and untracked files. Do not create another workspace behind the harness or move uncommitted user changes. If authorized isolation is needed, route through `ce-worktree` and its naming, ownership, explicit `jj workspace add --colocate`, and created-root `jj git colocation status` checks; unsupported harness lifecycle is a compatibility blocker, not permission to bypass it.

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

Inspect the chosen port and select exactly one intended server instance before handoff. Reuse a process already serving that port only when evidence identifies it as the intended project server. Only when no intended instance is selected may the resolved command be launched in the background with the project's working directory and environment; that process becomes the selected instance. Keep its process or session handle, and write its output under a directory created with `mktemp -d "$PROJECT_ROOT/.tmp/rocketclaw/polish-XXXXXX"`, where `PROJECT_ROOT` is the verified absolute workspace root. Before creation, reject symlinked `.tmp` or `rocketclaw` directories, create them with private permissions, and verify ownership and writability; fail safely without an OS-temp fallback.

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
