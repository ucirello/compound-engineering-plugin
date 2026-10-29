---
name: ce-worktree
description: Set up isolated colocated JJ workspaces for fresh work or an existing bookmark, PR, or revision. Detect and reuse existing isolation first.
---

# Workspace Isolation

Ensure work happens in isolation without disturbing the user's primary checkout. **Done when:** the caller is working in verified existing or new isolation and its absolute path, registered name, revision and relevant bookmarks have been reported, or a blocker has been reported instead.

**Order: detect existing isolation -> prefer a capable harness-native workspace tool -> native JJ creation only when no harness workspace primitive exists and the harness can adopt the result.** Never create a workspace the harness cannot see. Assume latest JJ; never invoke the Git executable or a Git fallback. See [JJ workspaces](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace), [Git experts](https://docs.jj-vcs.dev/latest/git-experts/) and [command table](https://docs.jj-vcs.dev/latest/git-command-table/).

## Step 0: Detect and reuse existing isolation

Resolve the source workspace's absolute root with `jj workspace root`. Run every JJ command with its target workspace's absolute root as cwd, including when initially called from a subdirectory. Inspect `jj workspace list` and the harness's current session/workspace ownership information; identify the exact current registered name and absolute path. A name, `.git` file or workspace count alone does not prove isolation. If ownership or isolation is ambiguous, use the safe decision path below.

If isolation already exists, **reuse its existing name and path**, even if the name is not date-prefixed or it is not colocated. Do not rename, recreate, nest a workspace or change colocation merely to enforce new-creation requirements. Report unmet compatibility requirements. Preserve existing PR/source bookmarks.

For an existing-ref request, verify the exact target before aligning existing isolation. An empty `@` directly above the requested head already represents that head. Do not discard unrelated tracked, ignored or untracked work or conflicts. Unsafe alignment or uncertain targets require the safe decision path, not nested isolation.

## Step 1: Resolve the base and stable identity

Two modes:

- **New work:** resolve the repository's actual default remote bookmark/trunk and verify its revision. Refresh the verified remote using `jj git fetch` where appropriate. An absent remote, fetch failure or local-only repository is not automatically fatal: use a verified local base only if it satisfies caller intent, disclosing the limitation. Never silently substitute another revision.
- **Existing ref:** resolve the exact bookmark, tag, revision or PR head. Use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view <number> ...)` for PR metadata; verify head repository, remote, bookmark and commit, including forks. Retrieve the exact head with native `jj git fetch` as needed. Never invoke `gh pr checkout` or direct Git. Preserve source/PR bookmark names and push association. JJ does not require Git's one-branch-one-worktree restriction or a detached checkout workaround.

Capture the **local creation date once** as `YYYYMMDD`. Record it with the intended task/ref, verified base, absolute parent and selected identity in caller/session state outside a disposable target. Preserve the selected identity across retries, resumes and midnight boundaries. Before retrying a failed attempt, inspect whether it already created the exact run-owned workspace; do not recalculate dates or suffixes merely because a command errored.

Derive a meaningful lowercase kebab-case slug from the task, PR or revision. Normalize supplied names: strip an existing leading date prefix before applying the captured date and normalize separators without double-prefixing. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. A recorded identity being resumed stays unchanged. Do not use timestamps, PIDs or random identifiers.

Use **one identity for the JJ workspace name and destination directory basename**. Preserve the existing local `.tmp/` parent layout, resolved absolutely, for example `<absolute-source-root>/.tmp/workspaces/<identity>`. Ensure `.tmp/` is ignored before creation: inspect ignore rules and add `.tmp/` to `.gitignore` when needed without invoking Git or altering unrelated rules. All scratch, fallback and error artifacts belong under local `.tmp/` too.

Check both `jj workspace list` registrations and filesystem destinations, including symlinks, for collisions. Reuse only an exact verified workspace owned by this run. Otherwise append `-2`, `-3`, etc. to the dated slug, checking both namespaces and recording the final identity before creation. Never overwrite or adopt unrelated state. The workspace identity is not an instruction to rename source bookmarks.

## Step 2: Prefer harness-native creation

If a native workspace primitive exists, inspect its actual explicit-naming, placement, colocated-JJ and lifecycle capabilities. Request the exact selected dated identity, absolute destination and verified base with explicit colocation. Verify the resulting name, matching destination basename, revision and ownership rather than trusting tool success. Use supported OpenCode workspace/session tools and move/adopt the active session into the resulting absolute root.

An available primitive unable to honor naming, colocation, placement or session ownership is a **compatibility blocker**, not permission to bypass it with shell creation, accept a noncompliant name or alter harness-owned state. A tool exposing only a `name` argument does not prove colocation or placement support. Existing isolation remains governed by Step 0, not these new-creation requirements.

## Step 3: Native JJ creation without a harness primitive

Only if Step 0 found no isolation, no native workspace primitive exists, and the harness can adopt the result, create from the source workspace's **absolute root** using the recorded identity/destination and verified revision:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

For **every** creation path, including harness-native creation, verify colocation from the created workspace's absolute root with `jj git colocation status`; do not rely on configuration defaults. Verify registry name/path, matching basename, working-copy base and intended bookmarks. Adopt/move the harness session before working; shell `cd` alone does not move a session. Report absolute path, registered identity, base/current revision, relevant bookmarks and colocation. Never proceed in the source checkout when requested isolation failed.

## Safe decision path

On permission errors, unsupported capabilities, uncertain ownership/ref, dirty alignment or incomplete creation, retain state and report the precise blocker. Do not reset, discard, retry alternate paths, bypass permissions or fall back to Git. Ask whether to work in the current checkout or stop and resolve isolation, using the host's blocking question tool already in the current tool list (match by capability, not another host's tool name). If listed but unloaded, load it through host discovery. Only if unavailable or an actual call errors, present numbered options in chat and wait. Never silently waive the caller's isolation choice.

## Retirement and unregister-only operations

Creation or task completion does **not** authorize deleting a user's workspace. Respect caller cleanup authorization and harness-owned lifecycle authority. For authorized retirement of an exact run-owned disposable workspace:

1. Stop all workers, monitors and processes using it. Identify active sessions/references; move any active harness session to a verified surviving workspace and leave the target directory before removal. Never remove still-referenced state.
2. From the surviving workspace's absolute root, verify the exact registered target name, absolute path and run ownership. Reject unrelated or ambiguous targets. Prove integration into the intended destination where required; preserve best/archive/recovery bookmarks and references still needed.
3. Inspect target tracked changes, conflicts, ignored and untracked files, including `.tmp/` content. Preserve recovery revision references. Copy required evidence, receipts and recovery information outside the target and **read back the copies** before removal. The removal snapshot protects tracked working-copy state, not ignored files or files left untracked. Preserve non-disposable or uncertain content and stop rather than assume safety.
4. Only after those checks and authorization, remove from the surviving absolute workspace root:

   ```bash
   (cd "$surviving_workspace_root" && jj workspace remove "$verified_owned_workspace_name")
   ```

5. Verify **both deregistration and exact target directory disappearance**. Successful exit alone is insufficient because deletion failures can be warnings. On failure or incomplete cleanup, retain remaining state and report the blocker. Never force-delete, separately clean Git metadata or fall back to Git removal. Bookmark deletion is separate and must preserve needed source/recovery references.

Use `jj workspace forget <verified-name>` **only** for explicitly intended unregister-only behavior preserving files. Never follow it with directory deletion or use it as a retirement shortcut. Apply ownership, session and reference safeguards to unregistering as well.
