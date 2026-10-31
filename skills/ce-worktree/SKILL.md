---
name: ce-worktree
description: Set up isolated colocated JJ workspaces for fresh work or an existing bookmark, PR, or revision. Use when starting isolated work or isolating an existing ref.
---

# Worktree Isolation

Ensure the current work happens in an isolated workspace, without disturbing the user's main checkout. Harnesses may already provide isolation, so **detect and reuse it first**. Use latest native JJ only; never invoke Git directly or use a Git fallback. See the [JJ workspace reference](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace) and [Git command table](https://docs.jj-vcs.dev/latest/git-command-table/).

**Done when:** the caller is working in an isolated workspace — existing or newly created — and its absolute path, registered name, revision and applicable bookmarks have been reported, or a blocker has been reported instead.

**Order of operations: detect existing isolation -> prefer a compatible harness-native workspace tool -> native JJ creation only when the harness can adopt it.** Never create a workspace the harness cannot see.

**Two modes, set by the caller's need:**

- **New work (default).** No ref named — start a fresh change from the verified base (trunk). This is what `ce-work` and `ce-code-review` use when the user picks the worktree option. Create a meaningful task bookmark only when needed by the caller's workflow.
- **Isolate an existing ref.** Resolve the caller's PR head, bookmark, tag or commit to one verified revision. Preserve existing PR/source bookmark names and tracking. JJ permits multiple workspaces at a revision; do not import Git's one-branch-one-worktree restriction. Prefer an already-owned suitable workspace rather than duplicating isolation. Never move a shared source bookmark merely to isolate it.

## Step 0: Detect existing isolation

Obtain the absolute source root with `jj workspace root`, then run all further JJ commands with that absolute root as their working directory (shell `(cd "$workspace_root" && jj ...)`, or subprocess `cwd=workspace_root`). Do not use `jj -R` as a substitute for setting cwd or strip prefixes from returned file paths.

```bash
(cd "$workspace_root" && jj workspace list)
(cd "$workspace_root" && jj git colocation status)
```

Use JJ registration information together with the harness's workspace/session metadata to verify the current registered workspace name, resolved absolute path, ownership and whether it is already isolated. A directory name or colocation alone is not proof of isolation; if ambiguous, stop and ask rather than creating nested state.

**Already isolated:** report and work in place, preserving its existing name even if undated. Do not rename, recreate, or change its colocation merely to enforce new-creation requirements. For an existing-ref request, verify the current revision first; transition only with appropriate authority and clean/conflict-free state, preserving unrelated work. Otherwise report the mismatch for the caller's decision. An unmet required colocation capability is a safe compatibility blocker, not permission to rebuild existing isolation.

## Step 1: Prefer the harness's native worktree tool

Use a harness-native workspace primitive when it supports explicit colocated JJ creation at the verified base and the dated identity below. Request and verify those properties; a generic Git-only worktree primitive is not compatible. Preserve its ownership and lifecycle contract. If required naming or colocation cannot be supported, report a compatibility blocker rather than silently choosing another name or bypassing the harness.

## Step 2: Native JJ creation and adoption

Only when Step 0 found no existing isolation and no compatible native tool exists, and the harness can adopt a manually created JJ workspace. Otherwise stop through the safe decision path below.

1. **Verify the base.** For fresh work inspect the configured remote/default bookmark, refreshing with `jj git fetch --remote <verified-remote>` when available. A refresh failure may use an explicitly verified local base, with the stale/local-only fact reported; never invent a trunk or substitute a different existing-ref target. Resolve exactly one revision before creation. For a PR, use repository-scoped `gh` from the absolute target root with `GIT_DIR=$(jj git root)` to verify repository, fork/head remote, source bookmark and exact head commit; retrieve that exact head using native JJ fetch and verify it locally. Do not use `gh pr checkout` as a workspace bridge. Missing or ambiguous requested refs block creation.
2. **Select one stable dated identity.** Capture local `YYYYMMDD` once (for example `date +%Y%m%d`) when selecting a new workspace. Derive a meaningful kebab-case slug from the task, PR or revision: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Normalize caller-supplied names without double-prefixing; an already selected dated identity is retained on retry/resume, including across midnight. Do not rename PR/source bookmarks to match it.
3. **Keep storage local and ignored.** Preserve the caller's existing absolute local `.tmp/` parent layout; otherwise use `<absolute-source-root>/.tmp/workspaces/`. Ensure `.tmp/` is covered by the source root's `.gitignore` (add the narrow rule if absent). All temporary, error and fallback files also stay under local `.tmp/`, never OS-global temporary storage.
4. **Check collisions.** Check both JJ workspace registrations and filesystem destinations, including ignored content and symlinks. The registered workspace name and destination basename MUST be the same dated identity. If either is occupied by unrelated state, choose `-2`, `-3`, etc.; never overwrite. Preserve the selected identity and destination in the caller's run state so retries reuse verified run-owned state rather than creating duplicates. No PIDs, random values or timestamp substitutes.
5. **Create explicitly from the absolute source root:**

   ```bash
   (cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_owned_destination")
   (cd "$absolute_owned_destination" && jj git colocation status)
   ```

   Verify the registration, absolute path, selected name and base relationship as well as colocation. JJ creates a fresh working-copy change on the supplied base; preserve the exact source revision and bookmark identity for later integration/push tracking. Do not silently replace the selected base.
6. **Adopt before working.** Move the active harness session using its supported session/workspace adoption capability, then set shell/subprocess cwd to the new absolute root. If adoption fails, report the created state and blocker without doing work in the original checkout or deleting it behind the harness. Report path, workspace name, base/current revision and applicable bookmarks.

If creation, verification or adoption fails with a capability, sandbox or permission error, requested isolation is not ready. **Do not proceed in the current checkout.** Report the actual failure and any retained state, then ask whether to work in the current checkout or stop and resolve the blocker. Use the host's listed blocking question capability; if listed but unloaded, discover that capability, not another host's tool name. If no such tool exists or an actual call errors, present numbered options in chat and wait. Never bypass denial or retry alternate paths automatically.

## Retirement (only when authorized)

Completion alone does not authorize deleting a workspace. Respect explicit cleanup authority and harness ownership/lifecycle. Before destructive retirement:

1. Stop workers; leave the target and move every active session to a surviving workspace.
2. From the surviving absolute root, verify the target's exact JJ registered name, absolute path and run ownership. Prove integration where the caller requires it; preserve needed best/archive/recovery bookmarks separately.
3. Copy required evidence outside the target (under a surviving workspace's local `.tmp/`) and read it back. Inspect tracked changes and conflicts with JJ from the target absolute root, and inspect ignored/untracked files locally: JJ's removal snapshot does not protect ignored or untracked content. Stop for unrelated, ambiguous, still-referenced or non-disposable data.
4. From the surviving absolute root, run `jj workspace remove <verified-workspace-name>`. JJ owns colocated metadata cleanup. Use `jj workspace forget` ONLY for explicitly requested unregister-only behavior that preserves files, never followed by directory deletion.
5. Verify both deregistration and directory disappearance. A zero exit can still include directory-removal warnings. On any failure or retained directory, preserve remaining state and report the blocker; never force-delete or use a Git/manual deletion fallback. Bookmark deletion is a separate authorized decision, not part of workspace removal.
