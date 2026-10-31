---
name: ce-worktree
description: Set up isolated JJ workspaces for fresh work or an existing bookmark, PR, or revision, reusing existing harness isolation.
---

# Workspace Isolation

**Done when:** work runs in verified isolation, with its absolute path, registered name, revision and relevant bookmarks reported; otherwise report a blocker. Detect existing isolation first, then prefer the harness-native lifecycle. No Git executable fallback or workspace bridge scripts.

## 0. Detect and reuse

Resolve the absolute source workspace root with `jj root`. Run every subsequent JJ subprocess with the relevant **absolute workspace root as cwd**: `(cd "$workspace_root" && jj …)`. Do not rely on `jj -R` to change cwd. Inspect `jj workspace list` and harness session/workspace metadata to identify the exact registered name, path and existing isolation ownership. Neither a dated name nor a `.tmp` path alone proves isolation. Ambiguous ownership blocks creation.

**Reuse existing isolation unchanged**, including nonconforming names, paths and colocation. Never rename, relocate, recolocate or nest a new workspace merely to enforce new-workspace conventions. Report actual identity. If an existing-ref request differs from current work, preserve dirty/conflicted state and establish authority for any transition rather than silently switching revisions. JJ allows multiple workspaces at one revision; do not impose Git's one-branch/one-worktree restriction. Never rename existing PR/source bookmarks to match workspace identities.

## 1. Verify the base

- **Fresh work:** resolve the repository's configured trunk/default bookmark, not an assumed branch/remote. When refresh is authorized, use `jj git fetch --remote <verified-remote>` from the absolute source root. Disclose failure; use a local base only when acceptable to the caller.
- **Existing bookmark, PR or revision:** verify the requested target and resolve exactly one full commit ID. For PRs verify repository, PR number, head repository/remote, bookmark and head commit; fetch through JJ and retain the source bookmark for pushing. Do not guess fork destinations or rely on a detached transport placeholder.

Inspect `jj log` and persist the singular full commit ID as `verified_base`; missing or ambiguous resolution blocks creation. Do not inject unchecked caller input as revset syntax. All repository-scoped `gh` operations require the target root and its Git directory, for example:

```bash
(cd "$workspace_root" && export GIT_DIR="$(jj git root)" && gh pr view "$pr_number" --json headRefName,headRefOid,headRepository)
```

## 2. Choose one stable new identity

These requirements apply to **every new workspace**, including callers such as `ce-work` and `ce-code-review`:

1. Capture the local date once as `YYYYMMDD`. Derive a meaningful lowercase kebab slug from task, PR or revision: `fix-email-validation`, `pr-214`, `review-efcb657`. Normalize caller names by stripping an existing valid `YYYYMMDD-` prefix before slug normalization, avoiding double prefixes. On resume retain the persisted date/identity, even across midnight. Reject empty/unsafe slugs and traversal; never use timestamp, PID or random identities.
2. The registered name and destination basename must be **identical**, e.g. `20261008-fix-email-validation`. Use an existing local `.tmp` parent under the source root, or establish that parent with authority. Verify ignore configuration and JJ status without a Git executable. Never use global temporary storage. Canonicalize the parent and require the absolute destination to stay inside it.
3. Check **both** all registered workspace names and filesystem destinations, including dangling symlinks. On collision append `-2`, `-3`, etc. to the entire identity until both are free. Do not overwrite/remove collisions or reuse unrelated registrations.
4. Before creation persist date, selected identity, absolute source/destination, exact base and run/session ownership in a receipt under source-local `.tmp` **outside the destination**. Reuse it on retries/resumes. A concurrent collision may require the next suffix: update the receipt first without recapturing the date. If the receipt matches an already created and verified owned workspace, reuse it unchanged. Partial/mismatched state requires investigation, not automatic deletion or another workspace.

## 3. Honor the harness lifecycle

Inspect actual native tool contracts. Native creation takes precedence only when it can satisfy the required JJ operation, exact name/destination, verified base, colocation and session visibility. A tool accepting only a name or creating an opaque Git worktree does not prove these capabilities. If a mandatory native lifecycle cannot supply them, report a **safe blocker**; do not bypass it with hidden shell-created isolation.

Only when the harness supports shell-created JJ workspaces with native session adoption, use this equivalent native workflow:

```bash
(cd "$source_root" && jj workspace add --colocate --name "$identity" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
(cd "$absolute_destination" && jj workspace list)
(cd "$absolute_destination" && jj log --no-graph -r @ -n 1)
```

Verify colocation in the **resulting absolute root**, exact registration/path, and the working-copy parent at the verified base (creation normally creates a new working-copy change above it). Native tool creation needs the same verification; do not assume `--colocate` occurred. Adopt the workspace using the harness-native session move capability, e.g. OpenCode `session_move(directory=absolute_destination)`, and verify the session cwd before edits.

Failure of creation, verification or adoption means isolation is incomplete. Do not proceed in the original workspace or automatically try alternate paths. Preserve the receipt and report command outcome, registration/directory existence and any partial state. Use an available blocking question capability to offer resolving isolation versus explicitly authorizing work in place; otherwise present numbered options in chat and wait. Never force-delete partial directories. No version detection, installation or Git fallback.

## 4. Report and hand off

Report reused-versus-created, absolute root, registered identity, verified base/current change, preserved PR/source bookmarks, colocation verification (or unchanged legacy status), receipt path and session adoption. Callers must retain the chosen identity across retries and cleanup. Completion alone is not cleanup permission.

## 5. Separately authorized cleanup

Destructive cleanup uses `jj workspace remove VERIFIED_NAME` from a **surviving absolute root**. `jj workspace forget` merely unregisters while retaining files; never combine it with filesystem deletion as a cleanup substitute.

Before removal, satisfy every gate:

1. Verify explicit cleanup authority, run ownership, exact registered name/canonical path and receipt. Never delete unrelated, non-disposable, still-referenced or ambiguous content. Check other sessions/workspaces and stop/join workers. Completion alone supplies no authority.
2. Inspect tracked changes, conflicts, **ignored and untracked files separately**, including `.tmp` artifacts. Use `jj status`, `jj diff`, tracked-file listings and a filesystem inventory compared against tracked paths/ignore rules. `jj file list` alone does not enumerate ignored data. Snapshot protection does not protect ignored/untracked files. Uncertain inventory or ownership blocks removal. Verify required integration into the intended surviving revision/bookmark; worker completion is not integration evidence.
3. Preserve recovery bookmarks/references for relevant revisions and operation IDs. Copy the receipt, exact identity/path/base/head, status/conflict reports, integration proof, inventories and required ignored/untracked data to durable local `.tmp` storage **outside the target**. Read evidence back and verify copied data before proceeding. Keep bookmarks needed for recovery.
4. Leave the target, move the harness session to the surviving workspace using its native lifecycle, and verify its absolute cwd. Ensure no process/session still depends on the target. If native removal is mandatory, verify it implements the JJ removal contract; inability is a blocker, not permission to bypass it.
5. Execute `(cd "$surviving_root" && jj workspace remove "$verified_name")`. Inspect exit status **and warnings**. Verify the exact registration is absent **and the directory is gone**. Warning, failure, lingering registration or remaining directory means incomplete cleanup: retain receipt/recovery state and report remaining state and blocker. No force-delete fallback or destructive retry, even after apparent command success.

References: [JJ for Git experts](https://docs.jj-vcs.dev/latest/git-experts/), [command table](https://docs.jj-vcs.dev/latest/git-command-table/), [CLI reference](https://docs.jj-vcs.dev/latest/cli-reference/), [workspace commands](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace).
