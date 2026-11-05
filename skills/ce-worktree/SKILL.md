---
name: ce-worktree
description: Set up isolated JJ workspaces for fresh work or an existing bookmark, PR, or revision. Use when starting isolated work or isolating an existing ref.
---

# Worktree Isolation

Ensure work happens in verified isolation without disturbing the user's main checkout. **Detect existing isolation first**, prefer a supported harness-native JJ workspace capability, then use native JJ creation only when the harness can adopt it. Never invoke the Git executable, including through helpers, history or transport fallbacks. Use latest JJ semantics without version checks, upgrade requirements or Git fallbacks.

**Done when:** the caller and active harness session use verified isolation and its absolute path, registered workspace name, revision and relevant bookmarks have been reported, or a blocker has been reported.

**Modes:**
- **New work (default):** create a fresh change above the verified project base. This is the isolation option used by `ce-work` and `ce-code-review`. Create a task bookmark only when required by the caller's workflow.
- **Existing ref:** resolve the caller's bookmark, tag, PR head or revision to an exact commit. JJ workspaces can share a revision; there is no one-branch-one-worktree restriction. Keep PR/source bookmarks and push relationships unchanged. For a PR verify the head repository, remote, bookmark and commit, including fork ownership. Start a working-copy change above that revision, preserving the caller's intended review/fix range.

## Step 0: Detect existing isolation

Resolve the absolute `workspace_root` with `jj workspace root`. Run every subsequent JJ command from that absolute root; `jj -R` does not change the command's working directory.

```bash
(cd "$workspace_root" && jj workspace list)
(cd "$workspace_root" && jj status)
(cd "$workspace_root" && jj git colocation status)
```

Combine registrations with the harness's workspace/session ownership information. Verify current registered name, absolute path, repository identity and whether the caller or harness designated it as isolation. Multiple registrations or colocation alone do not establish isolation. If ownership/isolation is ambiguous, use the safe decision path rather than nesting a workspace.

**Already isolated:** reuse the verified existing name, even if not date-prefixed. Do not rename, recreate or silently change colocation to enforce new-creation rules. Report unmet compatibility requirements safely. For an existing-ref request verify the target before aligning in place. An empty `@` immediately above the exact target is already aligned. Preserve unrelated tracked changes, conflicts and ignored/untracked files; dirty/conflicted state or uncertain targets require a safe decision, never reset/discard.

**Not isolated:** continue below.

## Step 1: Select one stable identity for every new workspace

1. Capture the local date once (`date +%Y%m%d`) and retain it and the chosen identity in the caller's run state. Preserve the selection across retries, resumes and midnight boundaries.
2. Derive a meaningful lowercase kebab-case slug from the task, PR or revision: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Normalize caller-supplied names and separators without double-prefixing a valid `YYYYMMDD-` prefix. Retain an already selected dated identity's date. Reject empty or ambiguous slugs rather than inventing opaque identifiers.
3. Use that **same dated identity** for the registered JJ workspace name and destination directory basename. Preserve the existing absolute destination's local `.tmp/` parent layout. If none is provided, use `<absolute-source-root>/.tmp/workspaces/<identity>`. Ensure `.tmp/` is ignored before creation, preserving existing ignore rules. All temporary artifacts, including errors/fallbacks, belong under local `.tmp/`, never OS-global temporary storage.
4. Check both workspace registrations and destination paths, including dangling directories. For collisions append `-2`, `-3`, etc., rechecking both; never overwrite existing state or use timestamps, PIDs or randomness. On retry/resume reuse the saved identity and existing registration only after verifying the exact run-owned name/path; otherwise report ambiguity or record the next available collision suffix before creation. Workspace naming never renames PR/source bookmarks.

## Step 2: Prefer the harness's native JJ workspace capability

Inspect the available capability and ownership/lifecycle contract. Request colocated JJ creation, the selected dated name, absolute destination and verified base explicitly. Verify the actual resulting name, basename, registration, revision and colocation from its absolute root. A generic Git-worktree tool is not equivalent. Unsupported naming, colocation or session adoption is a compatibility blocker, not permission to silently create a noncompliant workspace or bypass harness ownership. Preserve harness-owned lifecycle authority.

## Step 3: Native JJ creation with harness adoption

Only when there is no existing isolation and no supported native creation tool, and the harness permits creation/adoption without bypassing its lifecycle:

1. From the absolute source root inspect configured remotes and the actual project trunk/default bookmark. Refresh with `jj git fetch --remote <verified-remote>` when appropriate. A refresh failure is non-fatal only when the intended local base exists and stale/local use is acceptable to the caller; disclose it. Never silently substitute a different ref for an unavailable requested ref. Resolve the selected base to one exact commit using `jj log`, retaining the caller's actual base/head range rather than hardcoding `main`.
2. For PRs resolve the exact head using repository-scoped `gh` and retrieve the verified source with native JJ. Preserve bookmark/push associations; if the exact ref cannot be retrieved, report that diagnostic instead of fetching a substitute. From the target absolute root supply `GIT_DIR` through JJ: `(cd "$workspace_root" && export GIT_DIR=$(jj git root) && gh pr view <verified-pr>)`. This does not authorize direct Git execution.
3. Create and verify explicitly colocated isolation:

   ```bash
   (cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_destination")
   (cd "$absolute_destination" && jj git colocation status)
   (cd "$absolute_destination" && jj workspace list)
   (cd "$absolute_destination" && jj status)
   ```

4. Verify colocation, exact registered name/path, matching dated basename and working-copy parent equal to the verified base. Adopt the absolute destination through the harness's supported session-move capability (OpenCode: `opencode.session_move`) before working. A shell `cd` alone does not move the session. If adoption or verification fails preserve state and report the blocker, not success.
5. Report absolute path, name, revision, bookmarks and lifecycle authority. Run subsequent commands from the created absolute root, keeping file lists repository-relative, not prefixed by the workspace storage path.

## Safe decision path

If permissions, isolation, ownership, naming, colocation or adoption fail, requested isolation is not ready. **Do not proceed in the current checkout.** Report the specific blocker and ask whether to work in the current checkout or stop and resolve it, using the host's blocking question tool already in its tool list (match by capability). Presence in that list proves availability; never call a question tool to discover whether it exists. If listed but unloaded, use the host's tool-discovery capability. Only if no matching tool is listed or an actual question call errors, present numbered options in chat and wait. Never bypass a denial or retry alternative paths automatically.

## Retiring a workspace

Completion alone does not authorize deletion. Respect existing cleanup authorization and harness-owned lifecycle authority. Retire only an exactly verified, run-owned, disposable workspace:

1. Stop workers and other users first. Leave the target and move active harness sessions to a surviving workspace; verify adoption before removing the directory.
2. From the surviving workspace's absolute root verify the exact registered target name, absolute path and run ownership. Refuse unrelated, ambiguous, still-referenced or non-disposable content. Prove integration into the intended destination when required by the workflow. Preserve best/archive/recovery bookmarks and any references still needed; bookmark deletion is a separate decision.
3. Inspect tracked changes, conflicts, ignored files and untracked content from the target's absolute root. Removal snapshots working-copy state, but ignored and left-untracked files are not protected by that snapshot. Preserve required recovery references; copy required evidence outside the target (for example to the surviving workspace's ignored `.tmp/` run directory) and **read it back** before removal. Obtain required authorization for remaining disposable content; uncertainty blocks removal.
4. Through the permitted lifecycle authority, run `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")`. JJ manages colocated metadata, with no separate Git cleanup.
5. Verify **both** deregistration using `jj workspace list` from the surviving root and disappearance of the exact directory. Successful exit alone is insufficient because deletion failures can be warnings. On failure or incomplete cleanup retain remaining state and report the blocker. Never force-delete or fall back to Git removal.

Use `jj workspace forget` **only** for an explicitly intended unregister-only operation preserving files, never as deletion preparation.

Native references: https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace ; https://docs.jj-vcs.dev/latest/git-experts/ ; https://docs.jj-vcs.dev/latest/git-command-table/ .
