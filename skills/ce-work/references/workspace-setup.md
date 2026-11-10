# Workspace Setup

Read after code triage, before edits or dispatch. Resolve a writable JJ root with `jj root`, then run repository commands with cwd set to that absolute root, never `-R` as a cwd substitute. If no writable target exists, report a blocker; do not synthesize repository edits in scratch. For repository-scoped GitHub CLI, export `GIT_DIR=$(jj git root)` in that root before `gh` commands. Never launch Git directly.

## Prepare work

Read the plan through `work-intake.md`; clarify missing boundaries before implementing. The plan body is not execution state. Record `jj status`, `jj diff`, working-copy/parent commit and change ids, bookmarks, conflicts, and filesystem untracked/ignored inventory before edits. Determine the actual remote/default via JJ remotes/bookmarks and repository metadata, not hardcoded names. Fetch with `jj git fetch` only when needed and authorized. Compare verified history against that remote/default; unknown means unknown. Existing user changes and unpublished commits never become implicitly owned or published.

Reuse an existing feature bookmark without renaming it. Otherwise create a meaningful task bookmark on the verified intended revision with `jj bookmark create`; preserve local ancestry. An empty `@` above a verified head is not a detached/default-branch failure. Inspect `@-` and bookmarks before deciding. Keep commits path-limited to unit-owned changes. Ask once before including edits to an already-dirty file; return-to-caller mode instead blocks without editing that file. Unoffered files and commits remain exclusions in the shipping handoff. No stash, reset, discard or generic undo.

Use native task tracking if available; otherwise do not simulate it in chat.

## Isolation creation

First inspect `jj workspace list`, the absolute root, and native harness metadata. Reuse existing suitable isolation with its original name/bookmarks and preserve harness ownership. Ordinary synchronous units use the active workspace; native-managed workers retain native ownership. An explicit `ce-worktree` request or PR-group isolation may create an owned JJ workspace; model choice alone does not require one.

For creation, read the current `ce-worktree` guide and command help. Verify supported harness adoption, navigation and lifecycle management before creation; unavailable support is a compatibility blocker. Capture local `YYYYMMDD` once, derive a meaningful task/PR/revision slug, normalize any existing date prefix exactly once, and use identical `YYYYMMDD-<slug>` identity for registration and destination basename. Put the absolute owned destination under `<surviving-root>/.tmp/workspaces/`. Check BOTH registered names/paths and disk; suffix `-2`, `-3` on collisions. Persist selection for stable retries; no PID/random naming. Verify the intended base to a unique immutable revision before creation. Run from the surviving absolute root:

```sh
jj workspace add --colocate --name "$workspace_name" --revision "$verified_base" "$absolute_destination"
```

Then set cwd to the new absolute destination and run `jj git colocation status`; verify registration, path, base and colocation. Adopt the destination through supported native session navigation or an explicit authorized handoff, and verify worker cwd before editing or dispatch. Unsupported naming/colocation/adoption semantics are compatibility blockers, not permission for a Git fallback or silently non-colocated workspace. Never rename existing isolation or PR/source bookmarks to match new naming rules.

## Guarded removal

Removal is a separate authorized operation, not automatic disposal of output. Stop all workers and move any active session to a surviving absolute workspace first. Require exact verified name/path, task ownership and explicit cleanup authorization; never remove native-owned isolation through a manual bridge. Copy integration receipts, immutable recovery refs, logs and required artifacts outside the target and read them back. Prove integrated/abandoned output is recoverable. Inspect tracked changes, conflicts, ignored AND untracked files, including hidden files and symlinks. A JJ snapshot protects neither ignored nor untracked content. Any unpreserved material, ownership/path uncertainty, running worker, missing authorization, or failed evidence copy blocks cleanup.

From the surviving absolute root run `jj workspace remove "$verified_name"` only after every guard passes. Check command status, registration absent, and exact directory gone. Warnings or surviving files mean incomplete cleanup and a blocker: preserve evidence, never force-delete or use Git. `jj workspace forget` only unregisters and preserves files; it is not removal or successful cleanup. Interrupted removal resumes by reconciling both registration and disk, never by guessing or broad deletion.
