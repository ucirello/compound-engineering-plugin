---
name: ce-worktree
description: Set up isolated JJ workspaces for fresh work or an existing bookmark, PR, or revision. Use when starting isolated work or isolating an existing ref.
---

# Workspace Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Harnesses may already provide isolation at session start; detect and preserve it first.

**Done when:** the caller is working in a verified isolated workspace — existing or newly created — and its absolute path, registered name, revision, and relevant bookmark/PR have been reported, or a blocker has been reported instead.

**Order of operations: detect existing isolation -> prefer compatible harness-native creation/adoption -> native JJ creation only when the harness supports adoption.** Never create isolation the harness cannot see. Do not fall back to Git worktree commands or bypass permissions.

**Two modes, set by the caller's need:**

- **New work (default).** No ref named — create a fresh working-copy change from a verified trunk/base. This is what `ce-work` and `ce-code-review` use when the user picks the worktree option.
- **Isolate an existing ref.** Resolve the named bookmark, PR head, or revision exactly, then create a working-copy change above that revision. JJ workspaces can share a base; Git's one-branch-one-worktree restriction does not apply. Preserve existing bookmarks and record the correct remote/PR head for subsequent pushes, especially fork PRs. Do not invent or move a PR bookmark merely to satisfy workspace naming.

## Step 0: Detect existing isolation

Start from the harness-provided absolute workspace root, confirm it with `(cd "$workspace_root" && jj root)`, and run every repository operation from that root (never `jj -R`). Compare canonical paths and inspect registration and harness ownership:

```bash
(cd "$workspace_root" && jj workspace list)
(cd "$workspace_root" && jj status)
(cd "$workspace_root" && jj log -r '@ | @-' --no-graph)
(cd "$workspace_root" && jj bookmark list)
```

Match the current canonical path to the registered workspace and the harness's session/run ownership. A workspace name alone (including `default`) does not prove isolation. A Git submodule or linked worktree alone does not prove a usable JJ workspace; if registration or ownership is unclear, report the blocker rather than adopting another checkout.

**Already isolated:** report its existing name and path and work in place. Retain existing names/bookmarks even if nondated or non-colocated; never recreate or rename them to impose new conventions. In existing-ref mode, first verify whether the working-copy revision (or an empty `@` directly above `@-`) already corresponds to the requested head. Do not silently switch dirty/conflicted or unrelated work. A change to a different target requires a safe, authorized decision, not reset/discard or nested isolation.

**Not isolated:** continue below. Keep returned file paths repository-relative; workspace/session paths are absolute.

## Step 1: Prefer compatible harness-native isolation

Inspect available native creation/adoption tools by capability, not another harness's tool names. Before creating, verify that the native path can honor the exact verified base, explicit JJ colocation, the dated name/destination below, and session ownership. Harness-native creation must perform the equivalent of `jj workspace add --colocate --name ... --revision ...` and verify `jj git colocation status` from the resulting root. Unsupported naming or colocation is a compatibility blocker, not permission to use Git or a hidden shell workspace. Do not recreate existing verified isolation to satisfy these new-creation constraints.

## Step 2: Native JJ creation and adoption

Only when Step 0 found no existing isolation and the harness permits shell creation and explicit adoption/session movement. Otherwise use the blocking path below.

1. **Verify base:** inspect bookmarks/remotes and resolve one exact revision. Prefer the actual remote default/trunk, otherwise a verified local base; do not assume `main` exists. Refresh with `(cd "$workspace_root" && jj git fetch --remote "<verified-remote>")` when appropriate. Fetch failure is non-fatal only if the local base remains verified and acceptable; disclose staleness. For PRs, query head repository, remote, bookmark, and commit with `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view <number> --json headRefName,headRefOid,headRepository,headRepositoryOwner)`, fetch the verified head through JJ, and confirm the exact commit is available. Never substitute a guessed PR base or use `gh pr checkout` as a Git bridge.
2. **Capture local creation date once** as `YYYYMMDD`, before naming, and retain it with the chosen identity across retries/resume/midnight. Derive a meaningful kebab-case slug from the task, PR number, or revision: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Normalize caller-supplied names too: lowercase, replace unsafe separators/punctuation with hyphens, collapse/trim hyphens, and reject an empty meaningless slug. Strip a supplied leading date before applying the captured date so it is not double-prefixed; an already recorded retry identity retains its original date. These are workspace identities, not prescribed bookmark names.
3. **Use a local owned parent:** select an absolute destination below the source workspace's `.tmp/rocketclaw/workspaces/`, confirm the parent is ignored by inspecting ignore rules and `jj status`, and obtain authorization for any necessary ignore-rule edit before creation. Never use global `/tmp`, `TMPDIR`, random/PID/timestamp suffixes, or initialize a JJ repository in local `.tmp`. The registered workspace name and destination basename must be identical. Check both `jj workspace list` and filesystem entries (including dangling symlinks); append `-2`, `-3`, etc. for collisions. Do not reuse an existing path unless registration and run ownership prove it is this exact resumed operation. Recheck before creation; a race is a collision, never an overwrite.
4. **Create explicitly** from the surviving absolute source root:

   ```bash
   (cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_owned_destination")
   (cd "$absolute_owned_destination" && jj git colocation status)
   (cd "$absolute_owned_destination" && jj workspace list)
   (cd "$absolute_owned_destination" && jj status)
   ```

   Verify actual colocation, exact name/path registration, and base revision; do not infer success from directory existence. Preserve partial state and report a blocker if verification fails.
5. **Adopt before work:** move the OpenCode session using its native session-move capability when available and authorized, then set `workspace_root` to the new absolute root. A shell `cd` alone does not move the active session. Verify the harness now owns/tracks that destination; if adoption is unsupported, stop without editing there or deleting partial state. Report identity, path, base, bookmark/PR mapping, and receipt of adoption.

## Blocked isolation

If creation/adoption fails or the native tool cannot satisfy the constraints, requested isolation is not established. Do **not** proceed in the current checkout: the user chose isolation specifically to avoid it. Report the failure and ask whether to work in the current checkout or stop and resolve the compatibility/permission issue, using a listed blocking question capability. If listed but unloaded, use the host's discovery primitive; never probe another host's tool name. If no matching tool exists or a real question call fails, present numbered options in chat and wait. Do not retry denied operations, alternative paths, or Git bridges automatically.

## Owned workspace retirement (only when explicitly authorized)

Completion is not deletion permission. Respect the harness's lifecycle and existing authorization; do not remove main, unrelated, unclear, still-referenced, or nondisposable workspaces.

1. Stop workers using the target, leave its directory, and move any active session to a verified surviving absolute root. Confirm no active session/worker still references it. Verify exact registered name, canonical path, run ownership, and disposal authorization.
2. Inspect target tracked changes, conflicts, ignored and untracked files. Snapshotting does **not** protect ignored/untracked content. Preserve necessary recovery bookmarks and copy evidence/recovery files outside the target to owned local storage under the surviving workspace's `.tmp`; read back copies. When retirement depends on integration, prove the exact changes are integrated in the verified destination/remote; do not treat a completed task or closed PR alone as proof.
3. From the surviving root only, run `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")`. This snapshots and deletes workspace files; the main workspace cannot be removed. Bookmark deletion is a separate authorized operation; preserve recovery/archive/best references.
4. Verify both deregistration with `jj workspace list` from the survivor **and** disappearance of the target directory. Warnings or remaining files mean incomplete cleanup. Preserve remaining state and report a blocker; never force-remove files or use Git cleanup.

`jj workspace forget` is **unregister-only**, preserving files, and is appropriate only for an explicitly authorized unregister operation. Never describe it as destructive retirement or successful directory cleanup.

JJ reference: https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace and https://docs.jj-vcs.dev/latest/git-experts/ . All repository-scoped `gh` calls require `GIT_DIR=$(jj git root)` obtained from their target absolute workspace root; all JJ operations use that root as cwd.
