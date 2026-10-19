---
name: ce-worktree
description: Set up isolated colocated Jujutsu workspaces for fresh work or an existing bookmark, PR, or revision. Reuse existing isolation before creating a workspace.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace without disturbing the user's primary workspace. Coding harnesses may already provide isolation; **detect it first**.

**Done when:** the caller is working in verified isolation — existing or newly created — and its absolute path, registered workspace name, revision, and relevant bookmark have been reported, or a blocker has been reported instead.

**Order:** detect existing isolation -> prefer supported harness-native colocated JJ creation -> explicit JJ creation only when the harness can adopt it. Never create a workspace the harness cannot see or manage. Use [JJ workspace documentation](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace), the [Git migration guide](https://docs.jj-vcs.dev/latest/git-experts/), and [command table](https://docs.jj-vcs.dev/latest/git-command-table/). No Git-only worktree fallback or permission workaround.

**Two modes, set by the caller's need:**

- **New work (default):** create a new working-copy change based on the verified trunk revision. A JJ workspace name is not a bookmark; do not invent or rename source bookmarks to match it.
- **Isolate an existing ref:** resolve the requested bookmark, PR head, or revision to an exact verified commit. Preserve existing PR/source bookmark names and push tracking. JJ workspaces can reference the same revision; Git's one-branch-one-worktree restriction does not apply. Do not move a shared bookmark merely to create isolation.

## Step 0: Detect existing isolation

Resolve `workspace_root` to the current workspace's absolute root using `jj workspace root`. Run every workspace-scoped command from that absolute root, for example `(cd "$workspace_root" && jj workspace list)`; `jj -R` alone does not set the working directory. File lists must remain workspace-relative (`src/example.py`), not prefixed with a `.tmp/.../workspace/` path.

Inspect the registered workspace names and absolute paths, the current revision and bookmarks, and the harness's session/workspace metadata. A workspace under a temporary directory is not by itself proof of ownership or isolation. If no JJ repository is available, report a compatibility blocker rather than initialize or convert the user's repository silently.

If the current workspace is already isolated, **work in place** under its verified existing name. Report its root, name, revision, bookmarks, and colocation status from `(cd "$workspace_root" && jj git colocation status)`. Do not rename, recreate, or silently change an existing workspace to enforce the new-creation naming or colocation rules. If existing isolation cannot meet a required capability, use the safe decision path below. For an existing-ref request, verify whether the current revision (including an empty working-copy change directly above the requested commit) already satisfies it. Only align a clean workspace when authorized; preserve unrelated tracked, ignored, and untracked work, and stop on conflicts or an ambiguous target. Never nest another workspace merely because the current directory is already isolated.

## Step 1: Select a stable identity and verified base

Only create when Step 0 found no suitable existing isolation and the caller requires isolation.

1. Capture the **local creation date once**, e.g. `creation_date=$(date +%Y%m%d)`. Select and record a single identity `YYYYMMDD-<meaningful-kebab-case-slug>` before creating anything. Derive the slug from the task, PR, or revision: `20261008-fix-email-validation`, `20261008-pr-214`, or `20261008-review-efcb657`. Normalize a caller-supplied name into meaningful lowercase kebab case; strip an existing leading date prefix before applying the captured date, rather than double-prefixing. On a retry or resume, reuse the previously recorded selected identity and creation date, even across midnight; do not regenerate them from the current date.
2. Use that **same identity** as the JJ workspace name and destination directory basename. Preserve the caller's approved local `.tmp/` parent layout; by default use the source workspace's absolute `$workspace_root/.tmp/workspaces/$workspace_name`. Resolve the parent to an absolute owned path. No timestamps, PIDs, random naming substitutes, OS-global temporary directories, or relative destinations.
3. Inspect `(cd "$workspace_root" && jj workspace list)` and the destination, including existing files, directories, and symlinks. For an occupied registration or destination that is not this verified resumable run, append `-2`, `-3`, etc. to the identity in **both** places until both are available. Never overwrite, adopt unrelated state, or reuse a path merely because its registration is absent. Record the final identity and absolute destination outside the new directory. Recheck before creation; if a race creates a collision, preserve the occupied state and select the next suffix, recording the replacement identity. Other retries retain the selection.
4. Ensure the source root's `.gitignore` contains `.tmp/` and that local `.tmp/` content is ignored before creation. Do not write temporary artifacts outside local `.tmp/`, including fallback/error paths. Preserve unrelated ignore rules.
5. Resolve the base to a verified revision. For new work, identify the configured remote's actual default bookmark (otherwise a verified local trunk such as `main`); do not guess a remote or unresolved revision. Refresh with `(cd "$workspace_root" && jj git fetch --remote "<verified-remote>")` when appropriate. A missing remote, offline fetch, or local-only base is non-fatal if the local base is verifiable; report the fallback and its staleness. For existing refs, resolve that exact ref instead. For a PR, verify the head repository, remote, source bookmark, and commit before selecting the base; preserve the PR's original source bookmark and push destination, including forks. Run repository-scoped GitHub calls as `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view <number> ...)`. If a PR ref needs importing, use the documented JJ fetch/ref mapping for that verified remote; never guess its head from the PR number alone.

## Step 2: Prefer harness-native workspace creation

When the harness provides a native workspace primitive, use its supported **colocated JJ workspace** capability and lifecycle contract. Request the selected date-prefixed name, exact verified base, and absolute local `.tmp/` destination. The workspace name and directory basename must match the recorded identity. Verify the returned registration, absolute root, name, base, and `(cd "$created_workspace_root" && jj git colocation status)`; do not assume native creation defaults provide colocation.

Unsupported required naming, colocation, placement, or session adoption is a compatibility blocker, not permission to create a noncompliant or Git-only workspace behind the harness. Do not bypass native ownership with a manual creation or removal tool. Reuse already-existing isolation under its existing identity as described above.

## Step 3: Explicit JJ creation and session adoption

Only when no suitable native creation capability exists, Step 0 found no existing isolation, and the harness supports adopting an explicitly created JJ workspace:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
(cd "$absolute_owned_destination" && jj workspace list)
```

Verify the registered name equals the destination basename, the root equals the selected absolute destination, and the revision is based on the verified target. Adopt the workspace using the harness's supported session move/adoption capability before working there; merely changing a shell's directory does not move the active session. Subsequent commands must use this workspace's absolute root as their working directory. Report the path, dated workspace name, target revision, bookmarks, verified colocation, and adoption status. Do not claim isolation is ready before all checks pass.

## Failure and safe decision path

If creation, verification, adoption, permissions, or required harness capabilities fail, the requested usable isolation does not exist. Preserve any partially created state and report its exact registration/path and blocker. Do **not** proceed in the user's current workspace or retry alternate paths automatically. Ask whether to work in the current workspace or stop and resolve the blocker, using the host's blocking question capability already in the tool list. Presence in the current list proves availability; do not invoke a user-facing question to discover tools. If listed but unloaded, load that capability using the host's discovery primitive rather than guessing another host's tool name. Only if no such tool exists or an actual call errors, present numbered choices in chat and wait. Never reset, discard, force-create, or bypass permissions.

## Retiring a workspace (only when authorized)

Completion alone does not authorize deleting a user's workspace. Respect the harness's lifecycle authority; harness-owned workspaces must be retired through its supported JJ lifecycle, not an out-of-band command.

Before any authorized removal:

1. Stop workers and processes using the target. Leave its directory, and move any active harness session to a verified surviving workspace before deleting the target.
2. Verify the exact registered workspace name, absolute path, and run ownership against the recorded identity. Do not remove unrelated, ambiguously owned, still-referenced, or non-disposable content.
3. Inspect tracked changes, conflicts, and ignored/untracked files from the target's absolute root. Prove integration when the calling workflow requires it. Preserve recovery references and copy required evidence outside the target directory into a surviving workspace's local `.tmp/`; read it back before removal. Removal snapshots working-copy state, but that does **not** protect ignored files or files left untracked. Preserve those separately or stop.
4. From a surviving workspace's absolute root, use `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")` to unregister the run-owned workspace **and delete its files**. Colocated Git metadata belongs to JJ's lifecycle: no separate Git cleanup. Reserve `jj workspace forget` exclusively for an explicitly intended unregister-only operation that preserves the files.
5. Verify both deregistration with `jj workspace list` from the surviving root and disappearance of the exact target directory (including a leftover symlink). A successful exit is insufficient: directory-deletion failures may be warnings. On failed or incomplete cleanup, preserve remaining state and report the blocker; never force-delete or fall back to Git removal.

Bookmark deletion is a separate operation requiring its own authority. Preserve best/archive/recovery bookmarks and any references still needed by the user or workflow.
