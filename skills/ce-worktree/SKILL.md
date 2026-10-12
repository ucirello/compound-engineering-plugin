---
name: ce-worktree
description: Set up isolated colocated JJ workspaces — start fresh work from a verified base, or isolate an existing bookmark, PR, or revision. Use when starting isolated work or isolating an existing ref.
---

# Worktree Isolation

Ensure the current work happens in an isolated JJ workspace, without disturbing the user's main workspace. Coding harnesses may already provide isolation, so the common case is that **isolation already exists**.

**Done when:** the caller is working in an isolated workspace — existing or newly created — and its absolute path, registered workspace name, revision and applicable bookmarks have been reported, or a blocker has been reported instead.

**Order of operations: detect existing isolation -> prefer a supported harness-native colocated JJ workspace capability -> use native JJ with supported session adoption.** Never create a workspace the harness cannot see. No Git-only workspace fallback or permission workaround is allowed.

**Two modes, set by the caller's need:**

- **New work (default).** No ref named — start a fresh working-copy change from a verified base (trunk), with a new task bookmark when the caller needs one. This is what `ce-work` and `ce-code-review` use when the user picks the worktree option.
- **Isolate an existing ref.** The caller names a PR head, bookmark, tag, or revision — start a fresh working-copy change above that exact verified revision without moving or renaming its source bookmarks. JJ permits multiple workspaces based on the same revision; there is no Git one-branch-one-worktree rule. Preserve the PR's verified head repository, remote and bookmark for any later fix/push workflow; the workspace identity is not a replacement PR branch.

## Step 0: Detect existing isolation

Resolve the current workspace's absolute root and inspect its JJ registration together with the harness's session/workspace ownership metadata. Run every JJ command with its actual working directory set to that absolute root; `jj -R` alone does not change cwd. Do not infer isolation from a `.git` file, a relative path, a workspace's name, or mere membership in a JJ repository.

```bash
jj workspace root    # resolve this result to an absolute root
(cd "$workspace_root" && jj workspace list)
(cd "$workspace_root" && jj git colocation status)
```

- **Verified existing isolation:** report its path, registered name, revision and bookmarks, then **work in place**. Preserve its existing name even if it is not date-prefixed. Do not rename, recreate, nest another workspace, or silently change its colocation merely to satisfy new-creation rules. If its state cannot meet a required capability, report the compatibility blocker through the safe decision path below.
- **No existing isolation:** continue to Step 1.
- **Ambiguous ownership/isolation or no JJ repository:** stop and resolve the blocker; do not initialize or convert the user's repository behind their back.

In existing-ref mode, first verify the requested target and current state. An empty `@` immediately above that exact target is already aligned. Otherwise only align clean, conflict-free, disposable state using `jj new <verified-target>` from the workspace root, within the caller's authority. Preserve unrelated tracked, ignored and untracked work; dirty/conflicted state or an uncertain target requires a safe stop/decision, not a reset or discard.

## Shared creation contract: one stable dated identity

Before either creation route, capture the **local** creation date once as `YYYYMMDD`, derive a meaningful kebab-case slug from the task, PR or revision, and record the selected identity in the caller's resumable run state outside the destination. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`.

Normalize caller-supplied names: lowercase, replace separators/punctuation with hyphens, collapse/trim hyphens, and require a meaningful non-empty slug. Recognize an existing `YYYYMMDD-` prefix rather than double-prefixing it. On a fresh request, use the captured local date plus that name's slug; on a verified retry/resume, reuse the recorded complete identity and destination unchanged, including across midnight. Do not replace names with timestamps, PIDs or random identifiers.

Use **the same identity** for the JJ workspace name and destination directory basename. Preserve the caller's existing workspace-local `.tmp/` parent layout; absent one, use `<absolute-source-root>/.tmp/workspaces/<identity>`. Check both registered workspace names and all destination filesystem entries. On collision with unrelated state, append `-2`, `-3`, etc. to both name and basename and record the selected result before creation. Never overwrite. For retries, verify registration, absolute path, run ownership and intended base before reusing already-created state; conflicting partial state is a blocker, not permission to choose a different name silently.

Ensure `.tmp/` is ignored before creation, honoring existing directory-only ignore rules; narrowly add `.tmp/` to `.gitignore` if necessary. All temporary artifacts, including error and fallback files, remain under the source workspace's local `.tmp/`, never OS-global temporary storage.

## Step 1: Prefer the harness's native JJ workspace capability

If the harness provides workspace isolation, use its supported **colocated JJ** capability, requesting the shared contract's exact dated name, matching destination basename and verified base. Verify the registered name, absolute path, revision and `jj git colocation status` from the resulting absolute root before proceeding. Respect its session adoption and lifecycle authority. Unsupported required naming or colocation is a compatibility blocker, not permission to bypass the tool, use Git-only isolation or create unmanaged state.

## Step 2: Native JJ creation and session adoption

Only when no native isolation capability exists, Step 0 found no existing isolation, and the harness supports adopting the resulting directory:

1. From the source's absolute root, identify the base: the verified remote default bookmark, otherwise a verified local default such as `main`. Refresh with `jj git fetch --remote <verified-remote> --branch <verified-bookmark>` when available. A missing remote or failed refresh is non-fatal only if a usable local base is verified; disclose that it may be stale. Never guess an unresolved base.
2. For an existing bookmark, tag or revision, resolve the exact intended revision. For a PR, use repository-scoped GitHub metadata to verify the head repository (including forks), head bookmark, remote and commit; fetch that verified head with JJ and check the fetched revision matches the PR. Do not use `gh pr checkout`, a detached `FETCH_HEAD`, or move a source bookmark to arrange isolation. Repository-scoped calls must run as `(cd "$workspace_root" && export GIT_DIR=$(jj git root) && gh ...)`.
3. Apply the shared naming/collision contract, then create explicitly colocated isolation:

   ```bash
   (cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_owned_destination")
   (cd "$absolute_owned_destination" && jj git colocation status)
   (cd "$absolute_owned_destination" && jj workspace list)
   (cd "$absolute_owned_destination" && jj status)
   ```

4. Verify the exact registered name/path, matching destination basename, colocation and working-copy parent against the selected base. For fresh work only, create a new task bookmark if the caller requires one, without changing existing source/PR bookmarks. Existing-ref mode retains the verified push destination for the later authorized fix workflow.
5. Move the active OpenCode session to the absolute destination using its supported session-directory capability (such as `opencode.session_move`). A shell `cd` alone is not session adoption. Set subsequent tool cwd to that root; file paths should be `src/example.py`, not `.tmp/.../src/example.py`. Report the workspace identity, path, revision, bookmarks, colocation and adoption result.

### Safe decision path

If creation, verification or adoption fails, or naming/colocation is unsupported, requested isolation is not established. Do **not** proceed in the current workspace: the user chose isolation specifically to avoid it. Preserve partial state and report the precise blocker. Ask whether to work in the current workspace or stop and resolve the issue, using the host's blocking question tool already in the current tool list (match by capability, not a host-specific name). Presence in the list proves availability; never call a question tool merely to discover it. If listed but unloaded, use the host's tool-discovery capability to load it. Only if absent or a real question call errors, present numbered options in chat and wait. Never skip confirmation, automatically retry alternative paths, force cleanup, or bypass denied permissions.

## Retirement: JJ owns removal

Completion alone does not authorize deletion. Respect the caller's cleanup authorization and the harness's lifecycle authority; a harness-owned workspace is retired through its supported JJ lifecycle, not behind its back.

Before removing a run-owned disposable workspace:

1. Stop its workers. Verify the exact registered workspace name, absolute destination and run ownership from a surviving workspace's absolute root. Refuse unrelated, ambiguous, still-referenced or non-disposable targets.
2. Inspect tracked changes, conflicts, ignored and untracked content from the target's absolute root. JJ removal snapshots working-copy state, but ignored files and files left untracked are **not** protected by that snapshot. Preserve all required content; unknown content blocks deletion.
3. Prove integration when the caller's workflow requires it. Preserve recovery revision IDs and best/archive/recovery bookmarks. Copy all required receipts, evidence and recovery material outside the target, and read them back there before removal; a path inside the target is not preserved evidence.
4. Leave the target directory and move any active harness session to a verified surviving workspace before its directory is removed. Confirm workers/sessions no longer depend on it.
5. Only with the required authorization, remove through JJ from the surviving root:

   ```bash
   (cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
   (cd "$surviving_workspace_root" && jj workspace list)
   ```

6. Verify **both** deregistration and disappearance of the exact absolute directory. Success exit alone is insufficient: directory deletion failures may be warnings. On failure or incomplete cleanup, preserve remaining state and report the blocker; never force-delete, fall back to Git removal, or separately clean colocated Git metadata.

Use `jj workspace forget <verified-workspace-name>` **only** for explicitly authorized unregister-only operations that preserve all files, never followed by directory deletion. Bookmark deletion is a separate authorized action; preserve best/archive/recovery bookmarks and all still-needed references.

Native command semantics: [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace), [Git command table](https://docs.jj-vcs.dev/latest/git-command-table/), and [JJ for Git experts](https://docs.jj-vcs.dev/latest/git-experts/). No helper bridge scripts or cross-harness dispatch are needed for this workflow.
