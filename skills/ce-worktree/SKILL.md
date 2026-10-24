---
name: ce-worktree
description: Set up isolated colocated JJ workspaces for fresh work or an existing bookmark, PR, or revision. Use when starting isolated work or isolating an existing ref.
---

# Workspace Isolation

Ensure work happens in an isolated workspace without disturbing the user's primary checkout. **Done when:** the caller is working in verified existing or newly created isolation, its absolute path, registered workspace name, revision and relevant bookmarks have been reported, or a blocker has been reported instead.

**Order: detect existing isolation → prefer harness-native colocated JJ creation → native JJ creation only when no harness primitive exists.** Never create workspace state the harness cannot see. Use the latest JJ, never the Git executable or a Git-only fallback. Reference: https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace and https://docs.jj-vcs.dev/latest/git-command-table/.

All JJ commands must run with their working directory set to the target workspace's absolute root: `(cd "$workspace_root" && jj ...)`; `jj -R` is not a cwd substitute. Keep temporary files, receipts and failure evidence under local `.tmp/`, and ensure `.tmp/` is ignored in `.gitignore` before creation. Do not use global temporary directories.

## Step 0: Detect existing isolation

Resolve the current absolute root with `jj workspace root`, then inspect `jj workspace list`, the current working-copy revision and bookmarks, and harness session/workspace metadata from that root. Determine whether the current workspace is already the caller's isolated session workspace; do not infer isolation merely from the existence of `.git` or from a workspace name. A nested repository is not evidence of linked isolation. If ownership or isolation is ambiguous, report it rather than creating another workspace.

If already isolated, **work in place** and report its verified existing name and path. Do not nest, rename or recreate it to enforce the new naming or colocation rules. Inspect `jj git colocation status` there; report an unmet colocation requirement through the safe decision path below without silently modifying existing isolation. For an existing-ref request, verify the exact target first. Preserve dirty/conflicted or unrelated work; only move a clean workspace to the verified target when authorized, using `jj new <verified-target>` rather than a reset. If already at that target (including an empty `@` directly above it), do not move unnecessarily.

## Step 1: Resolve the mode and stable identity

- **New work (default):** resolve the repository's actual default/trunk bookmark and remote, falling back to a verified local base when appropriate. Refresh the selected remote bookmark with `jj git fetch --remote <verified-remote> --branch <verified-bookmark>`. Fetch failure is non-fatal only if a valid local base is available; disclose stale/local use, never silently substitute an unrelated revision. Resolve and capture the exact base commit before creation.
- **Existing bookmark, tag or revision:** resolve the supplied ref to exactly one verified commit. Preserve the source bookmark's name. JJ permits multiple workspaces based on the same revision; report an existing matching workspace and reuse it when appropriate, rather than imposing Git's one-branch-one-worktree restriction.
- **PR:** from the source root use `GIT_DIR=$(jj git root) gh pr view <number> --json headRefName,headRefOid,headRepository,headRepositoryOwner,isCrossRepository` to verify the head repository, bookmark and exact commit. Fetch that exact source with native JJ remote/fetch operations and verify the resulting commit matches the PR head. Preserve the existing PR/source bookmark and its remote mapping for the fix/push loop, including forks; do not guess `origin`, substitute another ref, or invoke a checkout bridge. If the verified head cannot be retrieved, report a blocker.

For **every newly created workspace**, including a name supplied by a caller:

1. Capture the local creation date **once** as `YYYYMMDD`. Derive a meaningful kebab-case slug from the task, PR or revision: `20261008-fix-email-validation`, `20261008-pr-214`, `20261008-review-efcb657`. Normalize caller-supplied slugs; an already date-prefixed identity must not receive a second prefix. On resume reuse the recorded creation date and identity, not today's date.
2. Use **one identity** for both the registered JJ workspace name and destination directory basename. Keep the caller's existing absolute local `.tmp/` parent layout; the default parent is `<absolute-source-root>/.tmp/workspaces/`. Do not change a required parent layout merely to choose a name.
3. Check **both** registered workspace names and destination paths. On collision with unrelated state, append `-2`, `-3`, etc. to the dated identity, checking both again. Never overwrite, and never use timestamps, PIDs or random identifiers. If a prior attempt already created the recorded workspace, verify its ownership, path, revision and colocation and resume it; do not treat it as a fresh collision.
4. Persist the selected date, identity, absolute source/destination, verified base/head and ownership receipt outside the destination in local `.tmp/` **before creation**. Preserve them across retries, resumes and midnight boundaries. If a race creates unrelated state, stop and reconcile before selecting and recording the next numeric suffix; do not automatically retry a failed operation.

## Step 2: Create and adopt

Prefer the harness's native workspace capability (for example OpenCode's worktree creation and session-move tools) **only when it supports colocated JJ creation, the exact selected name and required destination**. Request and verify these properties, including name = destination basename. Unsupported naming, colocation or placement is a compatibility blocker, not permission to bypass harness ownership or fall back to a Git-only tool. Respect harness cleanup authority.

Only when no native workspace primitive exists and Step 0 found no isolation, create directly from the absolute source root:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Verify the workspace registration, exact absolute path, selected revision, required dated identity and colocation before proceeding. For fresh work retain/create a meaningful task bookmark when the caller needs a publishable bookmark; its name is independent of the workspace identity. Do not rename PR/source bookmarks to match the directory. Move the active harness session to the new workspace using its supported session-adoption operation before working there, and use that absolute root for subsequent commands. Report path, name, revision and bookmarks. A shell `cd` alone does not move a harness session.

## Failure decision path

On creation, verification, permission, sandbox, unsupported naming or session-adoption failure, the requested isolation is not established. Preserve any partial state and receipt and report the specific blocker. Do **not** proceed in the current checkout, retry alternate paths automatically, bypass permissions, or claim success. Ask whether to work in the current checkout or stop to resolve the issue, using the host's listed blocking question capability. If listed but unloaded, use native tool discovery to load it; do not search for another harness's tool name. If no matching tool exists or an actual question call errors, present numbered options in chat and wait. Never skip confirmation.

## Retiring an owned workspace

Completion alone does not authorize cleanup. Respect the caller's cleanup authorization and the harness's lifecycle contract; never manually remove harness-owned state behind its back.

1. Stop workers and other users of the target. Verify the exact registered name, absolute path and run ownership against the receipt; do not remove unrelated, ambiguous or still-referenced state.
2. Inspect tracked changes, conflicts and ignored/untracked content from the target's absolute root. A removal snapshot protects working-copy state, **not ignored files or files left untracked**. Preserve non-disposable content. Prove integration into the intended surviving revision/bookmark when the workflow requires it. Preserve best/archive/recovery bookmarks and needed recovery references; bookmark deletion is a separate decision.
3. Copy required evidence and recovery information outside the target into surviving local `.tmp/` storage and read it back. Leave the target directory and move any active harness session to a verified surviving workspace before removal. If any safeguard cannot be satisfied, retain the workspace and report the blocker.
4. For authorized retirement **and deletion of files**, use JJ's lifecycle from that surviving absolute root:

   ```bash
   (cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")
   ```

   JJ owns colocated metadata cleanup; never run a separate Git cleanup command. Use `jj workspace forget <verified-workspace-name>` **only** when the intended operation is unregistering while preserving files, never as a prelude to directory deletion.
5. Verify **both** deregistration with `jj workspace list` from the surviving root **and** disappearance of the exact directory. A zero exit status is insufficient: file-deletion failures can be warnings. On failure or incomplete cleanup retain remaining state and recovery references, report the blocker, and never force-delete or fall back to Git removal.
