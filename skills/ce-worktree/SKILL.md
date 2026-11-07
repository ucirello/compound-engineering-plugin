---
name: ce-worktree
description: Set up isolated JJ workspaces for fresh work or an existing bookmark, PR, or revision.
---

# Workspace Isolation

Ensure the current work happens in isolation without disturbing the user's primary checkout. **Done when:** the active harness session is working in verified isolation and its absolute path, registered name, revision and relevant bookmarks are reported, or a blocker is reported.

**Order:** detect existing isolation → prefer compatible harness-native creation → explicit JJ creation only with supported harness adoption. Never create a workspace the harness cannot see. Never invoke the Git executable or use a Git-only fallback. See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace), [Git command mapping](https://docs.jj-vcs.dev/latest/git-command-table/) and [Git experts guide](https://docs.jj-vcs.dev/latest/git-experts/).

## Step 0: Detect existing isolation

Resolve the absolute current root with `jj workspace root`. Run subsequent JJ commands with cwd set to that absolute root, never `jj -R`. Inspect `(cd "$workspace_root" && jj workspace list)` and the harness's workspace/session ownership metadata. Establish whether this registered absolute path is already designated isolated by the harness or caller. Multiple registrations alone do not prove the current primary checkout is isolated; ambiguous ownership is a blocker.

**Reuse existing verified isolation under its existing name unchanged**, even if not dated or colocated. Do not rename, recreate or modify it merely to enforce new-creation rules. Report its root, name, revision and bookmarks and work in place; never nest a workspace. For an existing-ref request, verify the exact target and current state before aligning in place. Preserve unrelated tracked, ignored and untracked work. Dirty/conflicted state, uncertain targets or denied permissions require the safe decision path below, never reset or discard.

## Step 1: Resolve the mode and exact base

- **New work (default):** derive an identity from the task. Resolve the actual project default/trunk bookmark and remote from task instructions and repository configuration; do not assume `main` or a remote name. Refresh using native `jj git fetch` where appropriate and authorized. An unavailable remote is non-fatal only if a local base is verified and the task allows it; disclose the stale/local base. Start fresh work from that verified base and preserve the task's intended bookmark/push route.
- **Existing bookmark, tag or revision:** resolve the exact requested ref to a verified revision. Workspace names and bookmarks are separate; do not rename the source bookmark or impose Git's one-branch-one-worktree rule. Still detect existing isolation and concurrent ownership before creating anything.
- **PR:** verify the PR repository, head repository, source bookmark, remote and exact head revision, including forks. Repository-scoped GitHub CLI requires `GIT_DIR=$(jj git root)` in the target absolute workspace, for example `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view <number> --json number,headRefName,headRefOid,headRepository,headRepositoryOwner)`. Fetch/resolve that exact head using native `jj git` transport. Preserve the PR/source bookmark and fork-safe push tracking; do not manufacture a dated PR bookmark or orphan the fix loop on an anonymous fetched head. Unknown exact heads or push routes are blockers.

Record the verified base/revision and source identity; do not silently substitute them during retries or resumes.

## Step 2: Select one stable dated identity

For **every new workspace**, including caller-selected names:

1. Capture local creation date **once** with `date +%Y%m%d`. Persist it and the selected identity in caller run state under the source workspace's local `.tmp/` before creation. Consult existing state first and preserve the identity across retries, resumes and midnight boundaries.
2. Derive a meaningful lowercase kebab-case slug from the task, PR or revision. Normalize caller names by removing an existing leading `YYYYMMDD-` before applying the captured date; never double-prefix. On resume reuse the recorded name unchanged. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Never substitute timestamps, PIDs, random identifiers or opaque slugs.
3. Use the **same identity** for JJ workspace name and destination basename. Preserve the caller's approved absolute local `.tmp/` parent layout, e.g. `<absolute-source-root>/.tmp/workspaces/20261008-pr-214`. Verify parent containment and ownership and ensure `.tmp/` is ignored before creation using local configuration inspection and JJ status, never a Git ignore command. All temporary/error/recovery storage belongs under local `.tmp/`, never OS temporary storage.
4. Check **both workspace registrations and filesystem destinations**, including symlinks. On collision choose `-2`, `-3`, etc. for both name and basename; never overwrite unrelated state. Persist the final selection. A retry may reuse created state only after verifying the exact registration, path and run ownership; otherwise report the collision or record the next available suffix before creation. Never create another workspace merely because midnight passed.

## Step 3: Create and adopt through the harness

Prefer the harness-native workspace capability only when it supports explicit colocated JJ creation, the exact required dated name/destination, the verified base and session adoption. Request these explicitly and verify the result. A name-only primitive or Git-only worktree tool is insufficient. Unsupported naming or colocation is a **compatibility blocker**, not permission to bypass harness ownership or silently accept another name.

When no native creation primitive exists, shell-driven JJ is allowed only if the harness supports adopting/tracking the external workspace and this route is authorized. From the source absolute root:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$selected_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$new_workspace_root" && jj git colocation status)
```

Verify `$new_workspace_root` is the created absolute root. Inspect registration and revision from that root: name must equal `$selected_name` and the destination basename, base must match, and colocation status must confirm colocation. Defaults are not evidence. Adopt with the harness-supported session move/navigation capability (OpenCode's `opencode.session_move` when available), then verify the active session directory. Changing shell cwd alone does not move the session. Report actual remaining state if creation, verification or adoption fails; do not claim isolation exists.

If sandboxing, permissions, incompatible capabilities or adoption block isolation, **do not proceed in the original checkout**. Use the host's available blocking question capability to offer “work in the current checkout” versus “stop and resolve isolation.” Match actual listed capabilities, loading listed-but-unloaded tools through supported discovery; never probe another host's tool names. If none exists or the real question call fails, present numbered options in chat and wait. Never automatically retry alternate paths or evade a denial. Higher policy and lifecycle constraints remain binding.

## Retirement and preserve-files unregistering

Completion alone does **not** authorize deletion. Require explicit cleanup authority and respect the harness-owned lifecycle; do not directly remove harness-owned state without its supported authority.

Before destructive retirement:

1. Stop all workers/processes using the target. Identify a surviving workspace's absolute root, leave the target in shells, move any active harness session to the survivor and verify that move.
2. Verify the exact registered name, absolute path and run ownership against recorded identity. Never remove unrelated, ambiguously owned, still-referenced or non-disposable content. Prove integration when required by the caller and retain best/archive/recovery bookmarks and other recovery references.
3. Inspect tracked changes, conflicts, ignored and untracked content. Removal snapshots do **not** protect ignored/untracked files. Preserve needed work and copy required evidence, reports, receipts and logs outside the target, under a survivor's local `.tmp/` where appropriate; **read back** the copies to verify completeness. Unresolved ownership, authorization, integration, evidence or disposability blocks removal.
4. From the surviving absolute root run `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")`. JJ owns colocated metadata cleanup; never perform separate Git cleanup.
5. Verify **both deregistration and directory disappearance**. Success exit alone is insufficient because deletion failures may be warnings. Preserve remaining state and report failure/incomplete cleanup; never force-delete files or fall back to Git removal. Bookmark deletion is separately authorized; preserve needed best/archive/recovery references.

Use `(cd "$surviving_workspace_root" && jj workspace forget "$verified_workspace_name")` **only** for explicitly intended unregistering while preserving files. Never follow it with directory deletion or present it as destructive retirement.
