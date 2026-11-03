---
name: ce-worktree
description: Set up isolated, colocated JJ workspaces for new work or an existing bookmark, PR, or revision while respecting harness ownership and lifecycle.
---

# Workspace Isolation

Ensure the task runs in a verified isolated JJ workspace without disturbing the user's main checkout. Detect existing isolation before creating anything.

**Done when:** report the absolute root, registered workspace name, verified base/head, relevant bookmarks and ownership/lifecycle, or a blocker. Never silently continue in the original checkout after isolation fails.

## 1. Detect and preserve existing isolation

Resolve the absolute root with `jj root`, then run all subsequent JJ commands with that absolute workspace as shell cwd (not merely `-R`). Inspect `jj workspace list`, current revision/bookmarks and harness session/workspace metadata. Registration alone does not prove task isolation or ownership: distinguish the user's primary workspace from harness-created task isolation and reconcile canonical paths and names.

Reuse existing verified isolation with its **exact name and path unchanged**. Do not rename, recreate, nest another workspace or impose the new-workspace date convention. Preserve harness ownership and cleanup policy. If the requested ref differs, inspect tracked changes, conflicts, ignored/untracked files and active workers before any move; never overwrite work. Obtain applicable authorization or report a safe decision/blocker if reuse cannot satisfy the request.

## 2. Verify lifecycle support and the exact base

Prefer native harness lifecycle only when it supports **JJ, explicit colocation, the requested name and destination**, and the verification below. A Git-only worktree tool is incompatible; a tool's presence does not prove these capabilities. If the harness requires native lifecycle management, unsupported requirements are a **compatibility blocker**, not permission to bypass it. Shell creation is allowed only when the harness explicitly supports adopting/managing the workspace or explicitly leaves lifecycle to the caller. Never create invisible workspace state.

- **New work:** resolve the caller's base or repository-configured default remote bookmark to one exact commit. Never assume `main` or substitute a different ref. Fetch the selected remote/bookmark with `jj git fetch` when appropriate; disclose failure and use verified local data only if the caller's contract allows it.
- **Existing bookmark/tag/revision:** resolve the exact requested target and preserve source bookmark names. JJ does not impose Git's one-branch-one-worktree restriction. Do not invent that restriction or move shared bookmarks implicitly.
- **PR:** inspect the actual PR repository, head repository, head ref and head commit. Fetch through JJ using the verified remote/ref and verify that exact commit. Preserve the PR source bookmark and fork-aware push destination; never substitute a same-named base-repository bookmark. Unresolvable exact targets are blockers.

Repository-scoped GitHub operations use the absolute target cwd and JJ backing directory:

```bash
(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view "$pr_number" --json headRefName,headRefOid,headRepository,headRepositoryOwner)
```

No direct Git executable, including transport, ignore checks or cleanup. Do not use `gh pr checkout` as a hidden Git workspace operation.

## 3. Persist a new workspace identity

Applies **only to newly created workspaces**:

1. Capture local calendar date once with `date +%Y%m%d`. Persist date, task identity, selected name, absolute destination and verified base in a task-owned receipt outside the candidate, under the surviving workspace's absolute `.tmp/`. Resume/retry reads the receipt, including across midnight. No global temporary directory, PID, random suffix or time-of-day naming.
2. Derive a meaningful lowercase kebab-case task/PR/revision slug, such as `repair-login`, `pr-123`, or `review-<verified-short-revision>`. Normalize caller spaces/punctuation, collapse and trim separators, reject empty/path-traversal names, and strip an existing leading `YYYYMMDD-` date prefix before applying the captured date. Never double-prefix caller names or use unrelated opaque identifiers.
3. Start with `YYYYMMDD-meaningful-slug`. Select an absolute task-owned destination beneath the surviving workspace's `.tmp/`, for example `.tmp/workspaces/<name>`. **Name equals destination basename.** Inspect repository ignore rules and JJ ignored/tracked status; arrange an authorized `.tmp/` ignore rule if needed. Do not silently alter unrelated ignore configuration or track nested workspace contents.
4. Check **both** registered names/canonical paths and filesystem entries, including dangling symlinks. Collisions append `-2`, `-3`, etc.; never overwrite/adopt unrelated content. Persist the selected identity before creation. Retry reuses it when receipt plus registration/path prove this run created it; otherwise retain the captured date and deterministic collision sequence. Partial/ambiguous creation requires recovery, not deletion or randomized naming.

## 4. Create, verify and hand off

Use compatible native lifecycle providing these explicit semantics, or this command only under the lifecycle permission established above:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Require colocation status to confirm enabled colocation, not merely successful exit. Verify the created absolute `jj root`, registered name/path and exact base (normally the new empty working-copy change's parent). Record actual working-copy change/commit and relevant bookmarks. Keep receipt and error evidence outside the candidate. Failed verification is not successful isolation and does not authorize task edits there.

Move the harness session to the verified root with its supported session-move capability when required; verify subsequent commands run there. A single shell's cwd change is not a harness session move. Report root, name, base/head, bookmark/push mapping, receipt and lifecycle owner. Workspace names are not source bookmark names: do not rename bookmarks to match dated workspaces.

On permission, sandbox, lifecycle or creation failure, retain evidence and report that requested isolation does not exist. Offer resolving the blocker, explicitly authorizing in-place work, or stopping, using an available blocking-question capability. If unavailable or failed, present choices and wait. No automatic alternate paths or restriction bypass.

## 5. Authorized retirement

Task completion is **not deletion authorization**. Harness-owned cleanup must follow supported lifecycle with equivalent JJ semantics and safeguards; unsupported cleanup is a blocker. For caller-owned retirement:

1. Verify explicit disposal authorization, scope, registered name/canonical path, run receipt and ownership. Never remove the primary/surviving root or unrelated/ambiguous content. Identify and stop/join workers; ensure no session, worker, integration process or other task still depends on the target.
2. Verify required integration against the intended revision. Preserve best/archive/recovery refs and exact commit IDs. Copy required evidence, receipts, logs, artifacts and recovery instructions outside the target into surviving storage and **read them back**. Keep source revisions reachable. Empty working-copy state is not evidence of integration.
3. Inspect tracked changes, conflicts, ignored and untracked content explicitly, including nested repositories/workspaces. Removal snapshots do not protect ignored/untracked files. Preserve necessary material outside and verify it; obtain authorization for disposable remainder. Unknown, unrelated, referenced or non-disposable content must survive. Uncertain ownership, integration, references, preservation or authorization means retain and report.
4. Move every affected harness session out first using supported lifecycle. Run removal from a verified **surviving absolute root**, rechecking registered identity immediately beforehand:

   ```bash
   (cd "$surviving_root" && jj workspace remove "$verified_name")
   ```

5. Verify **both** deregistration of name/path using `jj workspace list` from the survivor and absence of the target directory (including symlink entries). Report both results separately. Failure/partial cleanup retains remaining content and evidence for recovery: no force deletion, recursive filesystem removal or Git fallback. Never retire with `jj workspace forget` plus filesystem deletion. `forget` is only for explicitly requested unregister-and-preserve-files behavior.

Bookmark cleanup requires separate authorization. Preserve best, archive, integration and recovery refs regardless of workspace retirement.
