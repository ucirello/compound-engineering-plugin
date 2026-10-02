---
name: ce-worktree
description: Set up isolated JJ workspaces — create a new bookmark for fresh work, or isolate an existing bookmark, PR, or revision. Use when starting isolated work or isolating an existing ref.
---

# Worktree Isolation

Ensure the current work happens in an isolated JJ workspace, without disturbing the user's main checkout. Sessions may already start in an isolated workspace, so the common case is that **isolation already exists**.

**Done when:** the caller is working in an isolated tree — existing or newly created — and its absolute path, workspace name, revision and bookmark have been reported, or a blocker has been reported instead.

**Order of operations: detect existing isolation -> create a JJ workspace only if needed -> move the OpenCode session to it.** Never create a workspace the session cannot see. Use native shell commands, not workspace bridge scripts. See [JJ workspaces](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace), [Git migration guidance](https://docs.jj-vcs.dev/latest/git-experts/), and the [command table](https://docs.jj-vcs.dev/latest/git-command-table/).

**Two modes, set by the caller's need:**

- **New work (default).** No ref named — create fresh work and a meaningful bookmark from a base (trunk). This is what `ce-work` and `ce-code-review` use when the user picks the worktree option.
- **Isolate an existing ref.** The caller names a PR head, bookmark, or revision — create an editable working-copy change above that ref. JJ has no Git one-branch-one-worktree restriction, but concurrent edits or movement of a shared bookmark can still interfere. If that work is already active in another workspace, report its path and prefer using it. Create separate work above the same revision only with caller authorization; do not move its bookmark or rewrite another workspace's active change.

## Step 0: Detect existing isolation

Resolve `jj workspace root` to an absolute physical path, then run all workspace commands with that absolute path as the shell working directory. Inspect `jj workspace list` and the session's startup context to identify the current workspace and the user's primary checkout. Do not compare Git metadata directories: a linked JJ workspace can share one Git backend, and a submodule is not evidence of session isolation.

- **Already isolated:** report the absolute workspace path, name, `@` revision and associated bookmarks, then **work in place**. Never nest another workspace simply because the current one is isolated.
- **Existing-ref mode in an isolated workspace:** first inspect `jj status` and resolve the requested revision. If it is already the current work or the parent of an empty `@`, reuse it. Otherwise use `jj new <target-revision>` here only after confirming existing work will be preserved and the caller authorizes switching; do not abandon, overwrite or silently carry unrelated edits onto another ref.
- **Primary checkout or uncertain isolation:** do not claim isolation based on a path/name heuristic alone. Establish the primary checkout from session context and listed workspaces; if uncertain, report the ambiguity before changing anything.
- **No JJ repository:** report that JJ initialization/import needs authorization. Do not silently fall back to creating a Git worktree.

## Step 1: Create and enter a native JJ workspace

Only when Step 0 found no existing isolation:

1. **Run from the absolute workspace root.** Use `(cd "$workspace_root" && jj ...)`, or set shell `workdir` explicitly. `jj -R` alone never changes cwd; file paths must stay root-relative (for example `src/example.py`, not a path prefixed by a workspace storage directory).
2. Choose a meaningful workspace slug and bookmark from the work description, not an opaque generated name. Base: the configured remote's default bookmark, else local `main`. Resolve it to an unambiguous revision; if unavailable, report the missing base rather than guessing.
3. **Ensure `.worktrees/` and `.tmp/` are ignored before creating anything.** Inspect root `.gitignore`, honoring an existing directory-only `.worktrees/` rule with its trailing slash; add only missing rules. Use `.worktrees/<slug>` for workspace storage. Temporary files, receipts and all fallback/error artifacts belong under this workspace's `.tmp/`; outside a JJ repository use local `.tmp/`. Never use OS-global temporary storage. Do not overwrite an existing destination.
4. Refresh with `jj git fetch --remote <remote>`. This is **non-fatal** — an absent remote or a local-only base is not an abort when the resolved local revision exists. Record the refresh failure and continue with that local ref.
5. Resolve the target, per mode:
   - **New work:** use the resolved remote default bookmark or local base.
   - **Existing bookmark/tag/revision:** resolve the requested ref and inspect existing workspaces for overlapping active work before proceeding.
   - **PR:** from the absolute target workspace root, run repository-scoped GitHub calls with `(cd "$workspace_root" && export GIT_DIR=$(jj git root); gh pr view <n> --json headRefName,headRepository,headRepositoryOwner,isCrossRepository,url)`. Fetch the actual head repository through a JJ remote (including the fork when applicable), resolve its head bookmark, and preserve the PR number, head repository and head bookmark for the later fix/push loop. Do not rely on `FETCH_HEAD`, detached Git checkout, or `gh pr checkout` to establish JJ state. If a temporary remote is needed, use a unique name, record it, and never replace a user's remote; remove only that newly added remote when no longer needed. If the head cannot be resolved, report the blocker rather than isolating the wrong revision.
6. Create with `(cd "$workspace_root" && jj workspace add --name <workspace-name> -r <resolved-target> <absolute-destination>)`. This creates a **new working-copy change above the target**, not an editable checkout of the target itself. For new work, create the chosen bookmark at the new workspace's `@` using `jj bookmark create <bookmark> -r @` from its absolute root. For PR work, retain the head/tracking information and advance the appropriate bookmark only as authorized by the subsequent fix/push workflow; an empty new `@` is not the PR head.
7. Use OpenCode's native `opencode.session_move` with the new absolute directory to make it the session's working directory. Verify the session directory and `jj workspace root` agree, then report the path, workspace name, revision, base and bookmark/PR association. If session movement is unavailable or fails, report the created workspace and navigation blocker; do not pretend the session moved or continue editing the original checkout.

## Failure and cleanup safety

If workspace creation fails with a sandbox or permission error, the requested isolation does not exist. **Do not proceed in the current checkout** — the user chose isolation specifically to avoid it. Report the failure and ask whether to work in the current checkout or stop and resolve the permission issue, using a listed blocking question tool when available. Do not discover tools by invoking a user-facing question. If no such tool exists or a real call fails, present numbered options in chat and wait. Never skip confirmation or retry alternate paths automatically. In a noninteractive run, report the blocker and stop rather than assuming consent.

Track resources created by this invocation. Do not forget/remove existing workspaces, bookmarks, remotes or user files. Cleanup a newly created workspace only after authorization and verification that it contains no work to retain: `jj workspace forget <workspace-name>` from a surviving workspace removes registration, not files; remove only the confirmed invocation-owned directory separately. Never remove the active session directory; move the session to a surviving workspace first. Keep any failure receipt under local `.tmp/`. Do not force cleanup of dirty work or silently delete isolation after a navigation failure.
