---
name: ce-worktree
description: Set up isolated colocated JJ workspaces for fresh work or an existing bookmark, PR, or revision.
---

# Worktree Isolation

Ensure work happens in isolation without disturbing the user's main checkout. **Detect existing isolation first; prefer supported native creation/adoption; never fall back to Git.** Done when the caller is working in verified isolation and its absolute path, name, revision and relevant bookmarks are reported, or a blocker is reported.

Use native JJ, not workspace bridge scripts or the Git executable. References: [workspaces](https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace), [Git experts](https://docs.jj-vcs.dev/latest/git-experts/), [command mapping](https://docs.jj-vcs.dev/latest/git-command-table/).

**Modes:** New work creates a fresh working-copy change at a verified base; create a task bookmark only if the caller needs one. Existing-ref mode resolves the exact requested bookmark, tag, PR head or commit. Preserve PR/source bookmarks and push tracking. JJ permits multiple workspaces based on one revision; the Git one-branch-one-worktree restriction does not apply.

## Step 0: Detect existing isolation

Resolve the current absolute root with `jj workspace root`; run every subsequent JJ command with that workspace's absolute root as cwd: `(cd "$workspace_root" && jj ...)`. Inspect `jj workspace list` and harness session metadata to establish the current registered name, absolute path, isolation and lifecycle owner. Git directory shape is not evidence of isolation.

If the session already has isolation, **reuse it in place under its existing name**, even if it predates the naming rules. Verify registration and `(cd "$workspace_root" && jj git colocation status)`. Do not rename, recreate or silently modify existing isolation to enforce naming or colocation. Unmet requirements follow the compatibility-blocker decision path below. For an existing-ref request, verify its current base; changing it requires caller authority, clean/conflict-free state and preserved unrelated tracked, ignored and untracked work. Never discard work or nest isolation merely to switch refs.

## Step 1: Resolve base and stable identity

Only continue if no existing isolation was found.

1. Record the **absolute source workspace root** and resolve a verified immutable base commit ID. For fresh work, use the configured/default remote bookmark or explicit local base; do not guess `main`. Refresh the chosen remote with `jj git fetch --remote <remote>` from the source root when appropriate. A refresh failure may permit the verified local base with reported staleness; never substitute another ref for an explicit target.
2. For a PR, verify its head repository, source bookmark and exact commit through repository-scoped `gh`. From the source absolute root, `export GIT_DIR=$(jj git root)` before the `gh` sequence. Fetch the verified source using `jj git fetch`, resolve and compare its commit ID to the PR head. Stop if unavailable; preserve fork/source push identity for the caller's fix loop. Do not use `gh pr checkout` as a bridge.
3. Capture the local creation date **once**, as `YYYYMMDD`. Derive a meaningful lowercase kebab-case slug from the task, PR or revision: `fix-email-validation`, `pr-214`, `review-efcb657`. Normalize a caller's leading `YYYYMMDD-` by removing it before applying the captured date, avoiding double-prefixes. Reject empty/unsafe slugs, separators, `.` and `..`; no timestamp, PID or random substitute.
4. Use one identity, e.g. `20261008-fix-email-validation`, for **both workspace name and directory basename**. Use an absolute owned destination under the source's local `.tmp/`, e.g. `$workspace_root/.tmp/workspaces/$workspace_name`. Ensure `.tmp/` is ignored in `.gitignore` before creation, inspecting applicable rules locally without Git and preserving existing entries.
5. Check **both registrations and filesystem destinations**, including files and symlinks, for collisions. Append `-2`, `-3`, etc.; never overwrite or adopt unrelated state. Record the selected identity, date, base ID, source root, destination and ownership outside the prospective target. Preserve that selection across retries, resumes and midnight boundaries. On resume verify and reuse matching owned state; a conflicting occupant is a blocker, not permission to silently select another identity.

## Step 2: Create and adopt isolation

Prefer a harness-supported **colocated JJ** workspace capability, requesting the exact selected identity, absolute destination and verified base. Verify actual results. A primitive unable to honor naming/colocation is a compatibility blocker, not permission to bypass ownership or use a Git-only tool.

With no native creation tool, shell creation is allowed only when the harness supports explicit adoption/session movement and the caller authorizes that route. Never create phantom isolation the harness cannot see. From the source absolute root:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_destination")
(cd "$absolute_destination" && jj git colocation status)
```

Verify exact registration name/path, base and colocation. Adopt/move the harness session through its supported interface (for example OpenCode `session_move` with the absolute destination), then set shell/tool cwd to that absolute root. A shell `cd` alone does not move the session. Report path, identity, base and bookmarks; retain ownership/lifecycle records.

If creation, colocation, naming, adoption or permissions fail, preserve remaining state and report precisely what exists. Do not proceed in the original checkout or bypass the failure. Use the host's listed blocking question capability to offer “work in the current checkout” versus “stop and resolve isolation.” If none is available or its actual call errors, present numbered options in chat and wait. Do not call a question tool merely to discover whether it exists. Never skip confirmation or retry through a Git fallback.

## Retire isolation safely

Completion alone does not authorize deleting a user's workspace. Respect caller cleanup authorization and harness lifecycle authority; uncertainty blocks cleanup. For authorized run-owned disposable isolation:

1. Stop and await all workers. Verify the **exact registered name, resolved absolute path, run ownership, cleanup authority and absence of live references**. Prove integration into the intended surviving revision when required. Preserve best/archive/recovery bookmarks separately.
2. From the target absolute root inspect tracked changes, conflicts, ignored and untracked files. JJ snapshots do not protect ignored/untracked content. Unrelated, ambiguous or nondisposable content blocks deletion until safely preserved/resolved. Copy required evidence, recovery references/commit IDs and records outside the target, under a surviving workspace's local `.tmp/` or appropriate durable storage. **Read back and verify those copies** before removal.
3. Move active harness sessions to a surviving workspace through the supported native interface and leave the target in all shell/tool working directories. Respect harness-owned removal authority; if it cannot support the required JJ lifecycle operation, stop rather than bypass it.
4. From the surviving workspace's **absolute root**, run `(cd "$surviving_workspace_root" && jj workspace remove "$verified_workspace_name")`. Colocated metadata belongs to JJ's lifecycle, not separate Git cleanup. `jj workspace forget` is only for explicitly authorized unregister-and-preserve-files behavior, never a precursor to directory deletion.
5. Verify **both** deregistration using `jj workspace list` from the surviving root and disappearance of the exact directory, including any remaining symlink. A successful exit is insufficient because deletion failures can be warnings. On failure or incomplete cleanup, retain remaining state and report the blocker; never force-delete or fall back to Git. Bookmark deletion is separate, requires its own authority and must preserve best/archive/recovery and still-needed PR/source references.
