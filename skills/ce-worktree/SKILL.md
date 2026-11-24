---
name: ce-worktree
description: Set up isolated colocated Jujutsu workspaces for fresh work or an existing bookmark, tag, PR, or commit. Use when starting isolated work or isolating an existing ref.
---

# Workspace Isolation

Ensure the work happens in an isolated workspace without disturbing the user's primary checkout. The harness may already have provided isolation.

**Done when:** the caller is working in an adopted, verified colocated JJ workspace and has its absolute path, registered name, base commit, applicable bookmark or PR, and lifecycle owner; otherwise report the blocker.

**Order: detect existing isolation → prefer the harness's supported colocated JJ workspace capability → use native JJ and adopt it into the session only where the harness allows it.** Never create a workspace the harness cannot see. See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace), [Git command table](https://docs.jj-vcs.dev/latest/git-command-table/), and [JJ for Git experts](https://docs.jj-vcs.dev/latest/git-experts/). Do not run the Git executable.

**Two modes, set by the caller's need:**

- **New work (default).** No ref named — start a fresh change on the verified trunk base and use a new task bookmark. This is what `ce-work` and `ce-code-review` use when the user picks workspace isolation.
- **Isolate an existing ref.** The caller names a bookmark, tag, PR head, or commit — start from that exact commit. If another workspace is already working at that ref, report its path and offer to work there if authorized. If a clean separate tree is essential, use a fresh child change of the verified commit; never edit the same change in both workspaces or move the source bookmark just to isolate it.

## Step 0: Detect existing isolation

Identify the absolute current root with `jj workspace root`, then run subsequent JJ commands from the relevant absolute workspace root. From the current root, inspect the registrations with `jj workspace list -T 'if(current_workspace, "* ", "  ") ++ name ++ "\t" ++ root ++ "\n"'`. Match the current entry and canonical path against the harness's reported workspace and known primary checkout. A workspace linked to the shared JJ repository (its `.jj/repo` is a pointer file rather than the main repository directory) is evidence of a secondary JJ workspace; a name other than `default` or a `.git` pointer alone is not proof. Treat ambiguous isolation or an existing harness workspace without a verified JJ registration as a blocker.

If already isolated, verify colocation with `jj git colocation status` from that root and **reuse the existing registered name**, even if undated. Do not nest another workspace, rename it, enable colocation in place, or recreate it to enforce these requirements. If it is incompatible, use the blocker path below. For an existing-ref request, verify the target as in Step 1. If the workspace is not already at it or on an empty child of it, use `jj new "$verified_base"` there only after verifying that changing the baseline is authorized and will not disturb ongoing, conflicted, ignored, or untracked work. For edits, also start a child if `@` is the source commit itself. Otherwise stop for a decision if the needed change of baseline is unsafe or unauthorized.

## Step 1: Verify the base and select one new identity

- **Fresh work:** Prefer the verified remote default branch (usually `origin`), then the local counterpart or `main` when no remote default is known. Inspect configured remotes and `trunk()` rather than guessing the default. Refresh the selected branch with `jj git fetch --remote "$base_remote" --branch "$base_branch"` when authorized. Missing remote or failed refresh is non-fatal only if the intended local base verifies; disclose use of a local base instead of claiming it is current.
- **Existing bookmark, tag, or commit:** Resolve that exact ref to one full commit ID; disambiguate explicitly and do not use a nearby ref as a substitute.
- **PR:** From the absolute repository workspace root, verify the head repository, branch, and advertised head OID with `GIT_DIR=$(jj git root) gh pr view "$pr" --repo "$base_repository" --json headRefOid,headRefName,headRepository,headRepositoryOwner,isCrossRepository,url` using the verified base repository (proceed only if `jj git root` succeeds). If the exact head commit isn't present, fetch the head branch with `jj git fetch --remote "$head_remote" --branch "$head_branch"` from a remote verified to match the head repository, not necessarily `origin`. For a fork with no matching remote, add a uniquely named remote with `jj git remote add "$head_remote" "$verified_head_url"` only if authorized; never repoint an existing remote. If an exact PR-head ref is already mapped by the repository's fetch configuration, JJ may fetch it via the verified base remote instead. Require the fetched or already present commit to match the advertised OID exactly; otherwise stop. For an authorized fix/push workflow, record the exact fork/remote and head branch for publication. Reuse an existing PR bookmark only after verifying its association and position, or create a new noncolliding local PR bookmark at the verified head if needed. Do not move or rename existing PR/source bookmarks during isolation.
- For any mode, require the resulting base to resolve unambiguously in `jj log --no-graph -r "$candidate" -T 'commit_id ++ "\n"'`. Record that full commit ID as `verified_base`.

For **new** workspace creation only:

1. Use `YYYYMMDD-<meaningful-kebab-case-slug>`. Record the local creation date once (`date +%Y%m%d`). Derive a meaningful lowercase kebab-case slug from the task, PR, or revision, e.g. `20261008-fix-email-validation`, `20261008-pr-214`, or `20261008-review-efcb657`. Normalize caller-supplied names by stripping any leading `YYYYMMDD-` before slug normalization (for example, `20261008-Fix/Email Validation` yields `fix-email-validation`). Prefix the recorded local date once. A caller's verified receipt from the same run, not a free-form supplied date, controls retries and resumes.
2. Use the **same dated name** as both the JJ name and the destination basename. Keep the caller's designated absolute parent under the source root's ignored `.tmp/`; default to `<source-root>/.tmp/workspace/` if none was designated. Verify `.tmp/` is ignored, respecting directory-only ignore rules; if needed add `.tmp/` to the root `.gitignore` only if authorized. Keep temporary and failure artifacts under local `.tmp/`, outside the destination if needed after cleanup.
3. Check `jj workspace list` for the exact registration and the filesystem for the exact path (including a dangling symlink). Do not write through a symlink or into a parent that resolves outside the designated local `.tmp/`. For collisions belonging to other work, try `-2`, `-3`, etc., checking both again. Record the chosen date, name, absolute path, verified base, and intended lifecycle owner in the run's local receipt outside the destination before attempting creation. Reuse that identity across retries, resumes, and midnight; inspect partial creation and verify ownership before resuming. Do not pick a new identity to bypass a failed creation or adopt an unrelated existing path. No timestamps, PIDs, or random naming substitutes.

## Step 2: Create, verify, and adopt

Prefer the harness's native workspace capability when it supports colocated JJ creation with the verified base, required name and local destination, and manages adoption and cleanup. Pass the chosen identity and verify the returned result; unsupported colocation, naming, or adoption is a compatibility blocker, not permission to bypass the lifecycle or create a differently named workspace.

Where the harness does not own creation but supports explicitly adopting a JJ workspace, create it from the source root:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$destination")
```

If the source has sparse patterns and the isolated task requires a full tree, explicitly request `--sparse-patterns full` for inline creation. For either creation route, verify the registration and absolute path from the source (`jj workspace list`, `jj workspace root --name "$name"`). From the destination, verify the current registration and check colocation and the new working copy:

```bash
(cd "$destination" && jj git colocation status)
(cd "$destination" && jj log --no-graph -r '@-' -T 'commit_id ++ "\n"')
```

Require colocation status to affirm colocation and `@-` to be the single verified base; check `jj status` for unexpected working-copy state. For fresh work, create a new task bookmark on `@` from the destination (`jj bookmark create "$task_bookmark" --revision @`), using the workspace name by default or an authorized task bookmark name. Verify that it is unused or belongs to this run on resume; never overwrite a bookmark. The workspace name does not rename any source ref.

If the native operation did not already adopt the workspace, adopt it through the harness's supported session operation (for example, OpenCode `opencode.session.move` with the absolute `directory` when available). Verify the session root after adoption takes effect. A shell `cd` alone does not adopt the workspace. Record verified creation and adoption, with the actual lifecycle owner, in the receipt. Report the verified name, path, base, and applicable bookmark/PR before beginning work. If creation, verification, or adoption fails, preserve partial state and report what exists; do not continue in the primary checkout automatically.

## Retire an authorized run-owned workspace

Completion is not authorization to delete. Never remove inherited, unrelated, ambiguously owned, still-referenced, or non-disposable workspaces. For harness-owned workspaces, use only the harness's supported cleanup lifecycle and verify the outcome; do not remove them behind the harness's back.

1. Stop the workspace's workers and writers. Verify the exact name and canonical path against the run receipt and current JJ registration (`jj workspace root --name "$verified_name"` from a surviving root). Check authorization and prove integration to the intended destination when the caller requires it.
2. From the target root, inspect `jj status`, tracked diffs and conflicts. Compare a filesystem inventory (including hidden paths) with `jj file list` to check ignored files and anything left untracked. The removal snapshot does not preserve those files. Preserve recoverable changes with verified recovery references outside the workspace lifecycle; copy and read back required evidence and any non-disposable files outside the destination. If anything cannot be accounted for or recovered, retain the workspace.
3. Leave the destination in both shell and harness. Move any active harness session to a surviving workspace and verify adoption before deleting. For an authorized run-owned workspace whose lifecycle is not harness-managed, run:

   ```bash
   (cd "$surviving_root" && jj workspace remove "$verified_name")
   ```

4. Verify both deregistration from the surviving root and disappearance of the recorded absolute path. A successful command can still warn that deletion failed. On failure or partial cleanup, retain remaining state and report the exact blocker; do not force-delete or use a Git fallback. JJ manages colocated metadata. Use `jj workspace forget` only for a separately authorized unregister-only operation that intentionally preserves files. Bookmark cleanup is separate; preserve PR/source, best, archive, recovery, and other still-needed bookmarks.

## Blocker decision

If isolation is unavailable, incompatible, denied, or fails verification, report the failure and wait for the caller's decision. For an interactive user, offer options such as “work in the current checkout” versus “stop and resolve the issue” using the host's blocking question tool if available. Discover a listed but unloaded question capability through that host's tool discovery; if none is listed or the actual call errors, present numbered options in chat and wait. Do not automatically retry a denied action, create a workspace by another route, or proceed without isolation.
