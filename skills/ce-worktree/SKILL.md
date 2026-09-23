---
name: ce-worktree
description: Set up isolated JJ workspaces for fresh work or an existing bookmark, PR, or revision. Use when starting isolated work or isolating an existing ref.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main workspace. Harness-created isolation often already exists.

**Done when:** the caller is working in an isolated workspace, existing or newly created, and its absolute path, workspace name, change ID, and relevant bookmark have been reported, or a blocker has been reported instead.

**Order: detect existing isolation -> prefer a native JJ workspace tool -> fall back to public JJ commands.** Never create a workspace the harness cannot access.

**Two modes, set by the caller's need:**

- **New work (default).** No ref named: create a fresh change from trunk and choose a meaningful bookmark name from the work description. This is what `ce-work` and `ce-code-review` use when the user picks isolation.
- **Isolate an existing ref.** The caller names a PR head, bookmark, tag, or revision. Preserve that target and its publishing destination. Do not edit another workspace's working-copy change; report its registered path instead. Only when a separate tree is essential, create a child of that revision without moving its bookmark.

## Step 0: Detect existing isolation

Discover the absolute root with `jj workspace root`. This initial discovery may run in the current directory; every later JJ subprocess must have its cwd set to the absolute workspace root it operates on. Do not substitute `-R` for cwd, inspect `.jj` or `.git` internals, or infer membership from filesystem identity.

Run the bundled read-only inspector. Fill `SKILL_DIR` with the absolute directory containing this file:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
python3 "$SKILL_DIR/scripts/workspace-info.py" --workspace-root "<absolute workspace root>"
```

The inspector uses `jj workspace list` and `jj workspace root --name NAME` to identify registered roots. By default `default` is the main workspace. If it has been renamed, supply `--main-workspace <name>` only when the project's conventions or user establish that name; otherwise report the ambiguity and stop.

- **Current root is the main root:** continue to Step 1.
- **Current root belongs to another registered workspace:** isolation already exists. Report it and work in place, without nesting a workspace. For an existing-ref request, apply Step 2's target checks before changing the current workspace. Preserve existing work by creating a new child change when switching targets; edit a target directly only if the current change is empty, the target is mutable, and no other workspace owns it.
- **Discovery fails or membership is ambiguous:** report the blocker. Do not infer a normal checkout from failure and create isolation blindly.

## Step 1: Prefer the harness's native JJ workspace tool

Use a native isolation tool only if it creates and registers a JJ workspace and makes that root accessible to the harness. A Git-only worktree primitive is not a JJ workspace tool. Before either creation route, apply Step 2's name, destination, target-resolution, ownership, and mutability checks, including the PR-target checks when applicable. The native tool must preserve the resolved target and publishing destination. Verify the result through the inspector before continuing.

For **OpenCode V2**, a native workspace-create capability follows the same rule. `session_move` changes a session's directory; it does not create a workspace. When only that capability is available, use Step 2 and then move the current session to the returned absolute root. Continue using explicit subprocess cwd for the remainder of this turn. Other harnesses must likewise enter or attach to the new root before declaring isolation ready.

## Step 2: JJ fallback

Create a workspace only when Step 0 found the main workspace and no suitable native tool exists. When already isolated, use the target checks here but switch in place instead of adding a workspace.

1. Choose a meaningful workspace name and bookmark name. Check existing names with the inspector and `jj bookmark list`. Do not overwrite a workspace or move an existing bookmark to force new-work setup. Report its existing location instead.
2. Keep the destination under the main workspace's `.tmp/workspaces/<name>`. Before creating it, ensure the main root's `.gitignore` has an effective `.tmp/` rule, including the trailing slash; add it when needed. Read this normal project file, not repository internals. Avoid later negations that would undo the rule. Do not stage the edit: JJ snapshots working-copy changes. Keep any additional scratch artifacts under the active workspace root's `.tmp/` as well.
3. Refresh the relevant remote using `jj git fetch`. Failure is non-fatal when a usable local target exists; report the failure and use that local revision. For new work, resolve `trunk()`; if it resolves to `root()`, use the local `main` bookmark if available, otherwise report a missing base. Resolve every selected target to a single commit ID before creation.
4. For an existing target, inspect `jj log -r <target> --no-graph -T 'working_copies.map(|w| w.name()).join("\n")'` and resolve each returned name with `jj workspace root --name <name>`. An already-owned target is reported rather than edited elsewhere. If its registered root is unavailable, report that blocker rather than forgetting the workspace. Inspect `immutable` and `empty` through `jj log` before selecting direct editing versus a new child; do not bypass immutability.
5. Create the workspace from the resolved target:

   ```bash
   jj workspace add --name <name> -r <resolved-target-commit-id> "<absolute main root>/.tmp/workspaces/<name>"
   ```

   `-r` sets the parent of a new working-copy change; it does not check out the target itself. Resolve the new root with `jj workspace root --name <name>`, then set all subsequent subprocess cwd to that root. For an unowned mutable existing target, `jj edit <resolved-target-commit-id>` attaches directly. For immutable or already-owned targets, keep the new child. For new work, `jj bookmark create <name> -r @` creates its bookmark. Do not compose a change description during isolation setup.
6. Re-run the inspector from the resulting root, enter it in the harness, and report the path, workspace name, change ID, and bookmark. Before any later publication, the publishing skill must move the intended bookmark to the actual work tip: `@-` when `@` is an empty child, otherwise the reviewed non-empty change. Creating a child does not advance bookmarks automatically.

### PR targets

Run GitHub commands in the absolute workspace root with command-scoped `GIT_DIR` obtained from `jj git root`. A failed root lookup must prevent the GitHub command from running:

```bash
JJ_GIT_DIR=$(jj git root) && GIT_DIR="$JJ_GIT_DIR" gh pr view <number> --json headRefName,headRefOid,headRepository,headRepositoryOwner,isCrossRepository
```

Identify the actual head repository and head bookmark from that metadata. Use `jj git remote list` to find its remote; add a distinct remote with `jj git remote add <remote> <head-repository-url>` when necessary, preserving existing remote URLs. Fetch it with `jj git fetch --remote <remote> --branch <headRefName>` and verify `<headRefName>@<remote>` resolves to the reported `headRefOid`. A fetch failure without that exact local revision is a blocker. Do not use a pull-ref refspec or a Git checkout command.

Apply the same target-ownership and mutability checks above. Preserve the actual head bookmark name and remote as the publishing destination, including for forks. Track it with `jj bookmark track <headRefName> --remote <remote>` only when this does not conflict with an unrelated local bookmark; report a collision instead of repointing it. A synthetic `pr-<number>` workspace name is fine, but it is not a substitute push destination. This skill does not push.

### Isolation failure

If creation fails with a sandbox or permission error, the requested isolation does not exist. Do not proceed in the current workspace. Report the failure and ask whether to work in the current workspace or stop and resolve permissions, using the host's listed blocking question capability. If listed but unloaded, discover and load it by capability. If none is listed or the call errors, present numbered options in chat and wait. Never skip confirmation or automatically retry alternative paths. A created workspace that the harness cannot enter is likewise a blocker; report its path without automatically deleting it.
