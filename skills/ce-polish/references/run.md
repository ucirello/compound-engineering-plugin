# Prepare the live polish loop

This reference owns workspace safety, server startup, reachability, and browser handoff. It does not own the user's iterative polish decisions.

## Resolve the workspace

Discover the current absolute root with `jj workspace root`. After discovery, run JJ in the relevant workspace's absolute root, e.g. `(cd "$workspace_root" && jj workspace list)`. With no argument, stay in the current workspace and verify its feature line.

If the user named a PR or branch, resolve it to a verified feature bookmark and exact revision. For a PR, inspect the head branch, repository and commit with `(cd "$workspace_root" && GIT_DIR="$(jj git root)" && export GIT_DIR && gh pr view "$pr" --json headRefName,headRefOid,headRepository,headRepositoryOwner,isCrossRepository)`. Match those facts to the JJ bookmark and its remote; if a fetch is needed and authorized, use `jj git fetch` from the verified absolute root for the exact verified remote and bookmark, then verify the commit again. Do not guess a fork or substitute a stale or unrelated revision. Inspect existing JJ workspace registrations and their working-copy revisions first, including empty working copies immediately above the target. If another workspace owns the target, verify its registered name and absolute path and adopt it with `opencode.session.move` (use the new directory only after the session move takes effect). Check its colocation state with `jj git colocation status` from the adopted root; keep its existing name and do not modify it to enforce colocation. If the tool or lifecycle does not permit adoption, or a required workspace capability is unmet, stop and report the blocker.

Only when no other workspace owns the target may you switch the current workspace. Verify there are no unrelated edits, conflicts, or ignored/untracked content at risk before changing revisions. For an editable local feature change use `(cd "$workspace_root" && jj edit "$verified_revision")`; for an immutable feature tip use `(cd "$workspace_root" && jj new "$verified_revision")`. An empty `@` directly above the verified tip is already on the feature line. Recheck `@`, its parents and bookmarks with `jj log` and confirm the feature line is tied to the intended bookmark and is not the repository's default branch. Stop on ambiguity, unsafe state, or denied permissions. Do not create, rename, or remove workspaces, move bookmarks, or move uncommitted user changes as part of workspace selection. See the [JJ workspace documentation](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).

## Resolve the start command

The commands below execute scripts bundled with this skill. For every self-contained shell call, set `SKILL_DIR` to the absolute directory containing the loaded `ce-polish` `SKILL.md` and `workspace_root` to the verified absolute workspace root; shell state does not carry between calls.

First inspect the repo-root launch configuration:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
(cd "$workspace_root" && bash "$SKILL_DIR/scripts/read-launch-json.sh")
```

Resolve one startup tuple: command, working directory, environment, and port. A selected launch configuration supplies every usable fact it declares: `runtimeExecutable` plus optional `runtimeArgs` form the command, `cwd` defaults to the repository root, `env` augments the inherited environment, and `port` must be numeric. Preserve those facts while resolving only what remains unknown. When all four facts are usable, the tuple is complete: skip classification, recipe loading, package-manager resolution, and port resolution, then continue to startup. Ambiguous declarations remain in disambiguation: show their names, ask the user to choose, and rerun with that name. Any operational failure or unresolved tuple fact blocks startup and must be reported.

Run project classification only when an unresolved command or port requires a project type. Classify the selected working directory when a launch configuration supplied one; otherwise classify the repository root. Omit the path argument for the repository root:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
(cd "$workspace_root" && bash "$SKILL_DIR/scripts/detect-project-type.sh" "<absolute project root>")
```

`<type>` means the classification root; `<type>@<relative-dir>` means that directory under the classification root. Ask the user to choose when the output is `multiple` or `multiple:...`. For `unknown`, ask only for the unresolved tuple facts and do not guess.

Read `references/dev-server-<base-type>.md` only when the command remains unresolved after a supported classification. If that recipe requires a package-manager executable to complete the command, resolve it in the classified project root rather than guessing:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
(cd "$workspace_root" && bash "$SKILL_DIR/scripts/resolve-package-manager.sh" "<absolute project root>")
```

Run the port resolver only while the port remains unresolved, using the detected type without replacing a selected command, working directory, or environment:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>";
(cd "$workspace_root" && bash "$SKILL_DIR/scripts/resolve-port.sh" "<absolute project root>" --type <base-type>)
```

Startup may proceed only when the tuple has a usable command, working directory, environment, and numeric port. If a classifier, recipe, or resolver fails operationally or leaves its required fact unknown, report that blocker; do not substitute a plausible value. After supported auto-detection supplies a missing fact, offer once to save the completed tuple as `.claude/launch.json`; write it only when the user accepts, after reading `references/launch-json-schema.md` and any recipe used.

## Start and hand off

Inspect the chosen port and select exactly one intended server instance before handoff. Reuse a process already serving that port only when evidence identifies it as the intended project server. Only when no intended instance is selected may the resolved command be launched in the background with the project's working directory and environment; that process becomes the selected instance. Keep its process or session handle, and write its output under a directory created with `mktemp -d "$scratch_root/ce-polish-XXXXXX"` after preparing the local scratch root below.

For server logs and live-mode state, verify the workspace `.gitignore` covers `/.tmp/` and that `.tmp/` is not tracked; do not write run data where it could be committed. If these checks fail, report the blocker. Use this preamble with the verified absolute `workspace_root`, including when a live session reuses a server and has no new server logs:

```bash
tmp_root="$workspace_root/.tmp"
scratch_root="$tmp_root/rocketclaw"
for dir in "$tmp_root" "$scratch_root"; do
  if ! { [ ! -L "$dir" ] && (umask 077; mkdir -p "$dir") &&
         [ ! -L "$dir" ] && [ -d "$dir" ] && [ -O "$dir" ] &&
         [ -w "$dir" ] && [ -x "$dir" ]; }; then
    echo "unsafe local scratch directory: $dir" >&2
    exit 1
  fi
done
chmod 700 "$scratch_root" || exit 1
```

Use no OS-global fallback if local scratch preparation fails; stop and report the failure.

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
