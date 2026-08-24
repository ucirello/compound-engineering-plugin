# Prepare the live polish loop

This reference owns workspace safety, server startup, reachability, and browser handoff. It does not own the user's iterative polish decisions.

## Resolve the workspace

If the user named a PR or bookmark, resolve its target revision while preserving `gh` and GitHub as the PR interface. In a non-colocated Jujutsu workspace, point `gh` at the backing repository reported by `jj git root`. First use `jj workspace list` to locate whether that revision is already the working-copy revision of a workspace. Enter that existing workspace when the harness can; if it cannot, report the blocker and stop. Only edit the target revision in the current workspace when no other workspace owns it. With no argument, stay at the current working-copy revision.

Confirm the resulting working-copy revision is not the revision targeted by the repository's default bookmark. Jujutsu has no active-bookmark concept, so do not infer safety from bookmark presence. Report and stop when a safe feature workspace cannot be reached; do not create another workspace behind the harness or rewrite, abandon, or move the user's existing changes.

## Resolve the start command

The commands below execute scripts bundled with this skill. For every self-contained shell call, set `SKILL_DIR` to the absolute directory containing the loaded `ce-polish` `SKILL.md`; shell state does not carry between calls.

First inspect the workspace-root launch configuration:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
bash "$SKILL_DIR/scripts/read-launch-json.sh"
```

Resolve one startup tuple: command, working directory, environment, and port. A selected launch configuration supplies every usable fact it declares: `runtimeExecutable` plus optional `runtimeArgs` form the command, `cwd` defaults to the workspace root, `env` augments the inherited environment, and `port` must be numeric. Preserve those facts while resolving only what remains unknown. When all four facts are usable, the tuple is complete: skip classification, recipe loading, package-manager resolution, and port resolution, then continue to startup. Ambiguous declarations remain in disambiguation: show their names, ask the user to choose, and rerun with that name. Any operational failure or unresolved tuple fact blocks startup and must be reported.

Run project classification only when an unresolved command or port requires a project type. Classify the selected working directory when a launch configuration supplied one; otherwise classify the workspace root. Omit the path argument for the workspace root:

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

Startup may proceed only when the tuple has a usable command, working directory, environment, and numeric port. If a classifier, recipe, or resolver fails operationally or leaves its required fact unknown, report that blocker; do not substitute a plausible value. After supported auto-detection supplies a missing fact, offer once to save the completed tuple as `.workspace/launch.json`; write it only when the user accepts, after reading `references/launch-json-schema.md` and any recipe used.

## Start and hand off

Inspect the chosen port and select exactly one intended server instance before handoff. Reuse a process already serving that port only when evidence identifies it as the intended project server. Only when no intended instance is selected may the resolved command be launched in the background with the project's working directory and environment; that process becomes the selected instance. Keep its process or session handle. Write its output under the artifact directory named by the project's active conventions; when none is defined, create a unique run directory under `<workspace-root>/.tmp/local`, where `<workspace-root>` is reported by `jj root`. The output path must remain inside the workspace root and outside `.jj/` and `.git/`; otherwise report the blocker instead of choosing an OS-temp path.

An occupied port that cannot be attributed to the intended project server remains an unresolved collision. Ask the user whether to stop that process, choose another port, or stop this run; never kill it or launch past it.

Resolve the selected instance's actual URL before handoff. The resolved port seeds `http://localhost:<port>` as the default candidate, but server output or a user correction replaces that candidate when it identifies a different URL. Attribute successful reachability at the resolved actual URL to the selected instance by probing for up to 30 seconds; a response from another process is not success.

- **Reachable:** use the browser-opening capability already exposed by the active harness with the verified actual URL. If it has none or the handoff fails, print that URL; browser handoff is a convenience, not a gate.
- **Not reachable:** show diagnostics derived from the selected instance. Include the last 20 log lines only when this run launched it and owns those logs. Ask whether to correct the server URL or start configuration, or stop.

Do not continue into the polish loop unless reachability is attributed to the selected instance.

Tell the user exactly:

```text
Go to <verified-actual-url> and tell me what could be better.
```
