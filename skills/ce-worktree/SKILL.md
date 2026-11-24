---
name: ce-worktree
description: Set up isolated, colocated JJ workspaces. Use when starting isolated work from trunk or working separately on an existing bookmark, PR, or revision.
---

# Worktree Isolation

**Done when:** the session is in verified isolation and the caller has its absolute path, registered JJ name, and bookmark or exact revision. Report a blocker instead of disturbing the main checkout. If called by another skill, return control in the same session.

Use [native JJ workspace operations](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace), never the Git executable. Discover the root with `jj workspace root`, resolve it to an absolute path, and run all subsequent JJ commands from the absolute root of the workspace they target.

## Detect existing isolation first

Correlate the current root with the harness's isolation state and JJ registrations:

```bash
(cd "$workspace_root" && jj --ignore-working-copy workspace list -T 'name ++ "\t" ++ if(root, root, "<unknown>") ++ "\t" ++ current_workspace ++ "\n"')
```

A linked JJ workspace has a `.jj/repo` pointer file rather than the primary workspace's `.jj/repo` directory. The harness may also provide a separate repository. A non-default name or `.git` file alone is not proof of isolation. Verify JJ identity and `jj git colocation status` from the isolated workspace's absolute root; if either is unverified, use the blocker path. Reuse its verified name even if undated; never nest, rename, recreate, or silently change colocation.

For fresh work, stay in verified existing isolation. For an explicit target, resolve it below first. `@` at that commit or an empty `@` directly above it is already aligned. Otherwise, use `jj new "$verified_base"` only if inspection shows it will not displace tracked, conflicted, ignored, or untracked work and the workspace owner permits it. If uncertain, stop rather than nesting isolation.

## Resolve the revision

- **Fresh work (default):** Use verified trunk for new isolation. Refresh the default bookmark of the verified default remote with `jj git fetch`. If there is no remote or refresh fails, use the corresponding verified local trunk and tell the caller. Create a meaningful work bookmark in the new workspace without moving an existing one.
- **Existing bookmark, tag, or commit:** Resolve the requested ref unambiguously to one commit ID. When positive evidence shows a requested bookmark is already in use in another workspace, report that path instead of attaching a second writer. Let the caller decide whether to use that workspace or, if separate isolation is essential and otherwise allowed, work from the same commit without moving the in-use bookmark.
- **PR:** Resolve the exact head repository, head branch, and head commit in the verified base repository. For repository-scoped `gh`, set `GIT_DIR` with `jj git root` from that repository's absolute JJ workspace:

  ```bash
  (cd "$workspace_root" && GIT_DIR="$(jj git root)" && export GIT_DIR && gh pr view "$pr_number" --repo "$verified_base_repo" --json headRefOid,headRefName,headRepository,headRepositoryOwner)
  ```

  If necessary, fetch the exact branch from a named JJ remote verified against the head repository, using `jj git fetch --remote "exact:$head_remote" --branch "exact:$head_branch"`. For a fork, use its own verified remote; add it only within the caller's authority and never repoint an existing remote. If the fetched head differs from the verified PR head, stop rather than substituting it. Keep or create a local PR work bookmark so follow-up work stays reachable (`pr-214`, for example). Preserve existing PR and source bookmarks; never retarget an unrelated bookmark. Carry the verified head repository, branch, and commit forward so later updates can target the right PR. Isolation does not authorize a push.

Use the verified commit ID as `verified_base`; never pass an unresolved name or a multi-commit revset to workspace creation. A new work bookmark can be created at the verified workspace's `@` using `jj bookmark create --revision @ "$work_bookmark"`, from that workspace's absolute root. Reuse a bookmark on resume only if it is verified as belonging to the same work.

## Create only when there is no existing isolation

Capture the local creation date once. Derive a meaningful slug from the task, PR, revision, or caller-supplied name. Strip any existing `YYYYMMDD-` prefix before applying the captured date to a new name. Lowercase the slug and collapse runs of separators and other non-alphanumeric characters to a single hyphen; trim edge hyphens. Use ASCII kebab case and require a meaningful, nonempty slug. Examples: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. A name already selected for this run is not fresh input: preserve it across retries, resumes, and midnight.

Use the same dated identity for the registered JJ workspace name and destination basename under the source workspace's local `.tmp/` (native fallback: `$workspace_root/.tmp/workspace/$name`). Verify the parent resolves within local `.tmp/`, is ignored, and has no tracked files. Add a missing `/.tmp/` rule to the root `.gitignore` only when authorized; otherwise report the blocker. Check JJ registrations and filesystem entries, including symlinks. If the initial name is taken, select the first free suffix (`-2`, `-3`, etc.). Carry the date, name, destination, and base in the run's resume state, storing any receipt under the source workspace's `.tmp/`, outside the destination. Reconcile partial creation against that state and run ownership. If the selected identity is now occupied by something else, report the conflict; do not rename, overwrite, or reuse it.

Prefer native harness creation for JJ. Request colocated isolation from the verified base at the selected name and destination. If the harness owns creation but cannot satisfy those requirements, report a compatibility blocker.

If native JJ creation is absent and the harness permits direct creation and adoption, use:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$absolute_owned_destination")
```

For either creation path, verify the registered name and root, ensure the basename matches and the new working-copy change is based on `verified_base`, and verify colocation from the new workspace:

```bash
(cd "$absolute_owned_destination" && jj git colocation status)
```

Adopt the verified workspace through the harness's supported session move if the creation tool did not already adopt it (in OpenCode, `opencode.session.move` when available). Verify the active session root after the move takes effect and before proceeding. A `cd` in one shell call does not switch the harness session.

## Blockers

If isolation, alignment, or adoption is blocked by compatibility, permission, sandboxing, or uncertain state, leave remaining state intact and report the failed check and affected path. Do not retry through another mechanism or start the work in the current checkout. In an interactive session, offer the safe choices (for example, explicitly accept work here or stop to resolve isolation) through the host's blocking question capability. Discover or load that capability through the host if listed but unloaded; do not probe by asking a question. If unavailable or a real call errors, present numbered choices in chat and wait. In a non-interactive run, return the blocker without asking or proceeding.

## Authorized retirement

Completion does not authorize cleanup. When retirement is separately authorized, read [the JJ retirement safeguards](references/retirement.md) before making any cleanup changes.
