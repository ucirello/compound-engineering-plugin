# Workspace Setup

Read this after input triage identifies code work and before any bookmark move, implementation edit, worker dispatch, or change description. It owns writable-workspace selection, plan clarification, bookmark placement, pre-work inventory, changed-file collision handling, and task-list setup. Return the canonical workspace, bookmark, pre-work paths and changes, exclusions, and task state to the kernel.

## Writable Workspace

Repository-local writes require a writable Jujutsu workspace. Require `jj workspace root` to resolve before treating the current directory as the project. If this session has no writable local workspace but the user named a repository and the harness exposes a remote repo-work surface with one, run there and treat it as canonical for verification, changes, and handoff. Otherwise report that no writable workspace is available; never synthesize repository changes from unrelated scratch space.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ - read `references/work-intake.md` for read sizing, plan extraction, and question gates. The plan is a decision artifact, not an execution script. Do not edit its body during execution; progress lives in Jujutsu changes and the task tracker, not checkbox or `status:` fields.

2. **Set Up the Environment**

   Before the first edit, the work must have its own mutable change and nothing the user did not offer may be described or published. Creating and moving local changes is recoverable through Jujutsu's operation log, so perform the safe local setup and report it in one line.

   **Bookmark and base.** Resolve the default base with `trunk()`; if it does not resolve, stop workspace setup and report the blocker. Query `tracked_remote_bookmarks() & trunk()` and `remote_bookmarks() & trunk()` explicitly for remote targets, then use `jj bookmark list --all-remotes -r 'trunk()'` to reconcile their names. Treat a remote bookmark as the default only when the tracked query and listing identify one target and one name for it. If the target or name is absent or ambiguous, keep `trunk()` as the base but leave the default bookmark and remote unresolved; do not guess either name. Jujutsu has no active bookmark.

   If `@` is the `trunk()` change, immutable, or ambiguous, fetch the uniquely resolved remote when one exists, then create a mutable working-copy change with `jj new 'trunk()'`. When `@` already contains user work that this run must exclude, preserve it as a sibling and move this workspace to a fresh change based on `@-` with `jj new @-`; never make excluded work an ancestor of the publication range. Preserve an existing local descendant as the base only when the user offered it for this run. Create or move a feature bookmark only for publication with `jj bookmark set <dynamic-name> -r <change>`; bookmarks do not advance automatically. Re-read `jj status`, `jj log -r 'remote_bookmarks()..@'`, the explicit remote target queries, and `jj bookmark list --all-remotes` after setup. When placement remains uncertain, create a separate change and do not move any tracked remote bookmark.

   Otherwise continue from the invoked change without renaming bookmarks or asking. Use another workspace only when the user asked for one this session (`ce-worktree`), and move the default bookmark only when the user explicitly authorized that in this session.

   **Pre-work scope.** Before editing, record `jj status`, the paths from `jj diff --name-only`, the current change id, and local-only history from `jj log -r 'remote_bookmarks()..@'` (`unknown` without a remote). Nothing in that set is yours to describe or publish. Preserve excluded work in its own sibling change before implementation. A later path collision is separated with `jj split` or `jj squash` only after the user decides whether their edits belong. The standalone handoff passes every excluded path as `exclude:<paths>` and uses `ce-commit` when local-only changes must remain unpublished. Return-to-Caller Mode does not edit a colliding file and returns `status: blocked` with the recovery path.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ - use the platform's task-tracking capability when available and follow `references/work-intake.md` for derivation, naming, and ordering. If none exists, continue without simulating a task list in chat.
