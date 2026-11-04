---
name: ce-worktree
description: Set up isolated colocated JJ workspaces for new work or an existing bookmark, PR, or revision, reusing verified isolation when available.
---

# Workspace Isolation

Ensure work happens in an isolated workspace without disturbing the user's primary checkout. **Done when:** the active harness session owns or has adopted verified isolation and its absolute path, JJ workspace name, exact starting revision, and relevant bookmarks have been reported; otherwise report a blocker.

**Order: detect existing isolation → prefer a compatible harness-native tool → explicitly authorized native JJ creation.** Never create a workspace invisible to the harness. Never invoke the Git executable or workspace bridge scripts.

## 0. Detect and reuse isolation

Resolve the current root with `jj root` from the current absolute working directory. Use that resolved absolute path as `workspace_root`. Every subsequent JJ command must run with the target absolute workspace as its actual working directory, not merely with `-R`:

```bash
(cd "$workspace_root" && jj workspace list)
(cd "$workspace_root" && jj git colocation status)
(cd "$workspace_root" && jj log --no-graph -r @ -T 'commit_id ++ "\n" ++ bookmarks ++ "\n"')
```

Compare the resolved root and registered workspace path with the harness inventory and session ownership. A non-default name alone is not proof of isolation. Verify registered name/path, colocation, and ownership; distinguish a primary checkout or unrelated workspace from run-owned isolation. Insufficient evidence is a blocker.

If already isolated, **reuse it without renaming, recreating, or modifying it**, even if its name predates this convention. If a requested existing ref differs from its current revision, report the mismatch and ask for a safe decision, rather than switching or discarding work. Never nest workspaces on repeated calls.

## 1. Resolve the source and stable identity

- **New work:** resolve the project's actual configured default/trunk bookmark to one exact commit ID; do not assume `main` or a remote name. An authorized `jj git fetch --remote <verified-remote>` may refresh it. Fetch failure may permit a verified local base with disclosed staleness; ambiguity blocks creation.
- **Existing bookmark/tag/revision:** resolve the exact supplied reference to one commit ID. Never substitute trunk or a different range on failure.
- **PR:** discover the repository, actual head repository/branch, and exact head commit. Repository-scoped `gh` must receive `GIT_DIR` captured with `(cd "$workspace_root" && jj git root)` and run from that same absolute root. Fetch the verified source using native `jj git fetch`, resolve it, and verify it matches the requested PR head. Preserve source/PR bookmarks and push-tracking information, including fork ownership; never invent a replacement branch or move a source bookmark to isolate it.

JJ workspaces may share a starting revision; do not impose Git's one-branch-one-worktree restriction. Capture the exact base/head before creation and verify it afterward. Isolation does not authorize pushing or moving bookmarks.

For **new** workspaces, capture local `date +%Y%m%d` **once** per creation request. Persist the captured date and chosen identity in durable caller run state outside the prospective target under the existing absolute local `.tmp` layout. Reuse them across retries, resumes, and midnight. Derive a meaningful kebab-case slug from the task, PR, or revision. Normalize a supplied name by stripping an existing leading `YYYYMMDD-` before applying the captured date; never double-prefix. No timestamp, PID, or random substitute.

Use `YYYYMMDD-meaningful-kebab-case-slug` as **both** the JJ workspace name and destination basename under the repository's existing absolute `.tmp` workspace layout. Check registered names **and** filesystem destinations, including symlinks. For unrelated collisions append `-2`, `-3`, etc. to both. Reuse a candidate only when exact name/path/run ownership and source evidence verify it belongs to this request; never overwrite or delete it. Persist the selected candidate so retries do not create duplicates.

For a creation date of October 8, 2026, fresh work might be `20261008-fix-email-validation`, PR 214 `20261008-pr-214`, and revision efcb657 `20261008-review-efcb657`. A supplied `20261008-pr-214` is not double-prefixed; a collision selects `20261008-pr-214-2` for both name and destination basename. A retry or resume after midnight keeps the persisted identity rather than capturing a new date. Existing PR/source bookmarks are unchanged.

## 2. Prefer compatible harness-native creation

Discover actual host capabilities. In OpenCode, use native workspace/worktree creation and session adoption only if documented capabilities support the requested dated name, absolute destination, exact revision, and explicit JJ colocation. Availability alone does not prove these guarantees. Verify all of them afterward, including `jj git colocation status` **from the created absolute root**.

If a native tool cannot guarantee these requirements, do not invoke it and then repair, rename, or silently replace its workspace. Explain the incompatibility and obtain a safe decision: authorized native JJ creation with supported harness registration/adoption, working in the current checkout, or stopping. Respect host lifecycle and permissions. A workspace bridge or another harness's dispatcher is not a fallback.

## 3. Native JJ creation, only when authorized

Proceed only if no isolation exists, the source and identity are verified, local `.tmp` is ignored by project policy, and the harness can register/adopt the result. Missing ignore coverage requires authorization before modifying ignore configuration. All temporary artifacts, including failure evidence, belong under the absolute local `.tmp`, never system temporary directories.

```bash
# Paths are absolute; identity and source were captured and verified above.
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$exact_source_commit" "$destination")
(cd "$destination" && jj git colocation status)
(cd "$destination" && jj workspace list)
(cd "$destination" && jj log --no-graph -r '@-' -T 'commit_id ++ "\n"')
```

Verify the new working-copy change's parent is the exact source, registered name/path match, and colocation is enabled. Then register/adopt through the supported harness lifecycle; in OpenCode, move the current session to the verified destination when supported. Only then work there. Report absolute path, dated name, exact source, working-copy identity, relevant bookmarks, and adoption outcome. Failed verification/adoption is a blocker; retain and report partial creation for recovery.

For sandbox, permission, capability, or reference failures, stop. Use the actual host's blocking question capability if present; otherwise present options in chat and wait. Never automatically retry alternate paths or proceed in the primary checkout when isolation was requested.

## Cleanup is separately authorized

Completion is not deletion authority. Cleanup requires all safeguards below:

1. Stop workers; verify no live session/process still references the target. Verify exact registered name, resolved path, and durable run ownership. Unrelated, ambiguous, still referenced, or non-disposable workspaces are ineligible.
2. Verify required integration and recovery references. Retain archive, best-result, source/PR, and recovery bookmarks. Bookmark cleanup is separate.
3. Inspect tracked changes and conflicts with JJ from the target absolute root. Separately inventory ignored/untracked files, including `.tmp`: snapshotting does not protect them. Copy required evidence and recoverable content outside the target to surviving local `.tmp` storage and read it back before deletion. Unknown content blocks cleanup.
4. Leave the target and adopt a verified surviving absolute workspace in the harness **first**. Confirm host lifecycle and permissions allow removal. Only then, from the surviving root:

   ```bash
   (cd "$surviving_workspace_root" && jj workspace remove "$verified_run_owned_name")
   (cd "$surviving_workspace_root" && jj workspace list)
   ```

5. Verify **both** deregistration and directory disappearance. Warnings, remaining directories, or failed checks mean incomplete cleanup: retain/report state and recovery evidence. Never force-delete, use Git fallback, or forget plus delete. `jj workspace forget` is only for explicitly requested unregister-only preservation, not cleanup.

No live destructive operation is part of setting up or validating this skill.
