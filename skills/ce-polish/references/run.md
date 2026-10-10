# Prepare the live polish loop

This reference owns checkout safety, server startup, reachability, and browser handoff. It does not own the user's iterative polish decisions.

## Resolve the workspace

Resolve the absolute `workspace_root` first, using `(cd "<absolute current directory>" && jj workspace root)` for discovery. Run subsequent JJ commands from that absolute root, never with `jj -R`; returned file paths remain repository-relative. If the user named a PR or bookmark, verify its repository, remote, bookmark, and exact revision. Repository-scoped GitHub calls use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Inspect `(cd "$workspace_root" && jj workspace list)` and the registered workspaces' revisions to locate an existing workspace for the target. Adopt that existing workspace through OpenCode's native session-move capability when available; if adoption cannot be done safely, report the blocker and stop. Preserve its verified existing name, even if nondated, and do not recreate or rename it to impose colocation. Only when no other workspace owns the target may the harness's native workspace adoption/switch capability use the current workspace; use native JJ revision selection, such as `(cd "$workspace_root" && jj new "<verified-target>")`, only when the current workspace is clean and unconflicted and switching preserves unrelated tracked, ignored, and untracked work. With no argument, stay in the current workspace.

Confirm the resulting change belongs to the intended feature bookmark, not the repository's default bookmark or an ambiguous/unassociated target. An empty `@` immediately above the verified feature head is acceptable. Report and stop when a safe feature workspace cannot be reached; do not create another workspace behind the harness or move uncommitted user changes. This workflow does not create or retire workspaces. JJ operation guidance: https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace .

## Resolve the start command

The commands below execute scripts bundled with this skill. For every self-contained shell call, set `SKILL_DIR` to the absolute directory containing the loaded `ce-polish` `SKILL.md` and run the helper from the resolved absolute `workspace_root` (for example, `(cd "$workspace_root" && bash "$SKILL_DIR/scripts/read-launch-json.sh")`); shell state does not carry between calls. Helpers discover the JJ root from their absolute current directory, and explicit project paths stay scoped to the selected project.

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

Inspect the chosen port and select exactly one intended server instance before handoff. Reuse a process already serving that port only when evidence identifies it as the intended project server. Only when no intended instance is selected may the resolved command be launched in the background with the project's working directory and environment; that process becomes the selected instance. Keep its process or session handle, and write its output under a directory created with `mktemp -d "$workspace_root/.tmp/polish-XXXXXX"` after safely creating the workspace-local `.tmp` parent and confirming it is ignored. Never fall back to global temporary storage.

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
