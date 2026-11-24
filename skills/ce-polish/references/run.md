# Prepare the live polish loop

This reference owns workspace safety, server startup, reachability, and browser handoff. It does not own the user's iterative polish decisions.

## Resolve the workspace

1. Find the current absolute root with `jj workspace root`. Run subsequent JJ commands from the absolute root of the workspace they target, not with `jj -R` from elsewhere. Identify existing harness isolation and inspect `jj workspace list -T 'name ++ " " ++ target.commit_id() ++ " " ++ root ++ "\n"'`, `jj bookmark list --all-remotes`, and the relevant ancestry with `jj log`. A normal JJ working-copy change `@` can be empty and sit just above the feature bookmark at `@-`; check both before concluding there is no feature context. With no argument, stay in this workspace and establish its feature bookmark or PR context from the evidence.
2. For a branch argument, resolve a unique bookmark and commit. For a PR number, verify the PR's head repository, branch, and exact head OID, and match them to a JJ bookmark/remote using `jj git remote list`; do not mistake a same-named branch in another repository for its head. For example, from the absolute source root, with the PR's base repository verified:

   ```bash
   (cd "$workspace_root" &&
     GIT_DIR=$(jj git root) && export GIT_DIR &&
     gh pr view "$pr_number" --repo "$base_repo" \
       --json headRefName,headRefOid,headRepository,headRepositoryOwner,isCrossRepository)
   ```

   If necessary and allowed, fetch only the verified branch from its matching configured remote with `jj git fetch --remote "exact:$remote" --branch "exact:$branch"` from that root, then verify it against the PR OID. Stop if the head cannot be verified. Establish the repository's default branch from project or remote evidence, not a guessed name. Do not polish the default branch, a tag, or an arbitrary commit without verified feature context.
3. For a named target, compare the registered workspace tips (including their feature ancestry and the empty-working-copy case) and harness ownership records before switching anything. If the target already has a workspace, use it under its existing name. If switching is needed and allowed, move the OpenCode session to its verified absolute path with `opencode.session.move`; after the move takes effect, verify the selected root, target context, and `jj git colocation status` from there. Stop if the harness cannot adopt it, multiple workspaces plausibly own the target, or existing isolation is incompatible. Do not rename, recreate, or change the colocation of existing isolation.
4. If staying in the current workspace, first verify existing isolation with `jj git colocation status` from its absolute root and stop if incompatible; do not change it. Only when no other workspace owns a verified named target and the current workspace is safe to switch, start a working-copy change over that exact feature revision with `(cd "$workspace_root" && jj new "$verified_base")`. Skip the switch if already in the verified feature context. Check `jj status`, the working-copy diff and conflicts, and local ignored or untracked files before switching; if any user work could be displaced or overwritten, stop. Recheck the resulting feature context. Do not rewrite the target commit, move PR/source bookmarks, create or retire a workspace, or bypass harness ownership. Report and stop whenever a safe feature workspace cannot be reached.

See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace) and [command table](https://docs.jj-vcs.dev/latest/git-command-table/).

## Resolve the start command

Run the bundled helpers from the selected absolute workspace root (`workspace_root`); pass the classified project path explicitly when it differs. For every self-contained shell call, set `SKILL_DIR` to the absolute directory containing the loaded `ce-polish` `SKILL.md`; shell state does not carry between calls.

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

Inspect the chosen port and select exactly one intended server instance before handoff. Reuse a process already serving that port only when evidence identifies it as the intended project server. Only when no intended instance is selected may the resolved command be launched in the background with the project's working directory and environment; that process becomes the selected instance. Keep its process or session handle, and write its output under a private run directory created as described in `references/live-start.md`, "Run directory and endpoint". Use `LOG_ROOT` and `ce-polish-server-XXXXXX` in place of `LIVE_ROOT` and `ce-polish-live-XXXXXX`; do not start the live endpoint for traditional polish.

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
