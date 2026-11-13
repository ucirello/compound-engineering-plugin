---
name: ce-worktree
description: Set up isolated colocated JJ workspaces for fresh work or an existing bookmark, PR, or revision. Use when starting isolated work or isolating an existing ref.
---

# Worktree Isolation

Ensure work happens in an isolated JJ workspace without disturbing the user's primary checkout. **Detect existing isolation first → prefer supported harness-native creation → use native JJ only when the harness supports adopting it.** Never create invisible workspace state.

**Done when:** the caller's active session is working in verified isolation and its absolute path, registered workspace name, revision, and relevant bookmarks have been reported, or a blocker has been reported instead.

Use the latest JJ, never the Git executable (including read-only commands or transport). See [JJ workspaces](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace), [Git experts](https://docs.jj-vcs.dev/latest/git-experts/), and the [command table](https://docs.jj-vcs.dev/latest/git-command-table/). Run every JJ command with its working directory set to the target workspace's **absolute root**, not merely with `-R`.

## Step 0: Detect existing isolation

Resolve the current absolute root with `jj workspace root`, then from that root inspect `jj workspace list`, the current workspace identity, revision and bookmarks, and the harness's session/worktree metadata. Confirm the current path's registration and whether the harness already owns an isolated workspace; a workspace name alone is not proof of isolation. Do not mistake a nested repository or submodule for linked isolation.

If already isolated, **reuse its verified existing name and path**, even if its name lacks a date prefix. Do not rename, recreate, nest another workspace, or change colocation merely to enforce new-creation rules. Inspect `jj git colocation status` from that absolute root and report any unmet compatibility requirement through the safe decision path below.

For an existing-ref request, verify whether the current revision already matches the requested target. Before any authorized `jj edit` or `jj new` to align it, inspect tracked changes, conflicts and ignored/untracked files and preserve unrelated work. An ambiguous target or unsafe alignment is a blocker, not permission to discard state. Report relevant bookmarks unchanged.

## Step 1: Resolve the exact revision and stable identity

- **New work:** resolve the task's intended base from repository instructions and the actual remote/default bookmark configuration. A permitted `jj git fetch --remote "<verified-remote>"` may refresh it. A fetch failure can use an explicitly verified local base for fresh work, disclosing staleness; never silently substitute a ref. Resolve the base to an exact commit ID before creating.
- **Existing bookmark, revision, or PR:** resolve that exact target to a commit ID. For a PR verify its head repository, remote, source bookmark and head commit, including fork identity; fetch that exact head with native JJ when needed and verify it matches. Preserve source/PR bookmark names and push tracking rather than renaming them to the workspace identity. If the exact ref cannot be obtained, stop. JJ workspaces can share a revision; do not import a one-branch-one-worktree restriction.
- Repository-scoped PR queries run from the absolute target root, for example `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view "<number>" --json headRefName,headRefOid,headRepository)`. Do not use checkout commands that invoke Git.

For **new creation only**, capture the local creation date once as `YYYYMMDD` (for example `date +%Y%m%d`) and derive a meaningful kebab-case slug from the task, PR or revision. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Normalize caller-provided names too: lowercase, replace separators/punctuation with hyphens, collapse/trim hyphens, and remove an existing leading `YYYYMMDD-` before applying the once-selected date. Reject an empty or meaningless slug rather than use a random name. On a recorded retry/resume, reuse the previously selected dated identity instead of capturing a new date or prefixing it again.

Use **one identity** as both the registered workspace name and destination basename. Keep the existing absolute local `.tmp/` parent layout supplied by the caller; otherwise use `"$workspace_root/.tmp/workspaces"`. Ensure `.tmp/` is ignored in `.gitignore` before creation, inspecting the applicable ignore rules locally without Git. Keep all receipts and temporary/error files under local `.tmp/`.

Check both registered workspace names and destination filesystem entries (including dangling symlinks). On collision append `-2`, `-3`, etc. to the dated slug and check again; never overwrite or use timestamps, PIDs or random identifiers as substitutes. Persist the selected identity, date, exact revision, absolute parent/path, and ownership/adoption information in a local `.tmp/` run receipt before creation, so retries and midnight do not change them. On resume inspect existing registration/path against that receipt: reuse verified completed creation; ambiguous or partial state is a blocker, not another collision to skip silently.

## Step 2: Create through the supported lifecycle and adopt

Prefer the harness's native worktree/workspace primitive **only if** it supports colocated JJ creation, the required dated name and absolute destination, exact verified revision, and native session adoption/ownership. Request these explicitly and verify all results. A Git-only primitive or unsupported naming/colocation is a compatibility blocker; do not bypass its lifecycle by creating behind its back.

Only when no native creation primitive applies **and** the harness explicitly supports adopting a manually created JJ workspace, create from the source workspace's absolute root:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base_commit" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

The harness-native creation path must likewise use `jj workspace add --colocate` through its supported capability, not configuration-dependent defaults. Verify from the created absolute root that colocation is active; verify the exact registered name/path, destination basename, and the working-copy parent against the captured commit (workspace creation starts a new change at that revision). Verify no source/PR bookmark was renamed. Adopt/move the active harness session using its supported session capability before beginning work, and record lifecycle ownership. A successful shell command alone is not successful session adoption.

## Blocked isolation

If creation, naming, colocation, revision verification, adoption, sandbox access or permission fails, the requested isolation is not established. Preserve remaining state and report the precise blocker. Do **not** proceed in the current checkout, mutate existing isolation, force permissions, use another harness, or retry alternative paths automatically.

Ask whether to work in the current checkout or stop and resolve the blocker, using the host's listed blocking question capability. Presence in the tool list is proof it exists; never call a user-facing question tool merely to discover it. Load a listed-but-unloaded capability through supported discovery. Only when no such capability exists or a real call errors, present numbered options in chat and wait. Never skip confirmation.

## Retirement and unregister-only operations

Completion alone does not authorize deleting a user's workspace. Honor explicit cleanup authorization and the harness owner's lifecycle contract; use its supported JJ removal capability for harness-owned workspaces, not a behind-the-back removal.

Before retiring a disposable run-owned workspace:

1. Stop and await all workers; ensure no other worker/session still references it. Leave the target directory and move every active harness session to a surviving workspace using supported adoption.
2. From the surviving absolute root, verify the exact registered name, absolute path, receipt/run ownership and cleanup authorization. Inspect tracked changes, conflicts, and ignored/untracked content in the target before leaving it. Never remove unrelated, ambiguously owned, still-referenced or non-disposable content.
3. Prove integration when the calling workflow requires it. Preserve best/archive/recovery bookmarks and any needed references. Copy required evidence and recovery instructions outside the target (under a surviving workspace's local `.tmp/`) and read it back before removal. Removal snapshots working-copy state, but ignored files and files left untracked are not protected by that snapshot; preserve them separately or stop.
4. For authorized deletion, run `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")` through the supported lifecycle. JJ owns colocated metadata cleanup. Do not combine `workspace forget` with directory deletion or invoke a separate Git cleanup.
5. Verify **both** deregistration with `jj workspace list` from the surviving absolute root and directory disappearance. A successful exit is insufficient: deletion failures can be warnings. On failure or incomplete cleanup retain remaining state and report the blocker; never force-delete or fall back to Git removal.

Use `(cd "$surviving_workspace_root" && jj workspace forget "$verified_workspace_name")` **only** for an explicitly intended unregister-only operation that retains files, with the same ownership/session/authorization checks. State clearly that files remain. Bookmark deletion is a separate, separately authorized operation; never delete needed PR/source, best/archive or recovery bookmarks as part of workspace cleanup.
