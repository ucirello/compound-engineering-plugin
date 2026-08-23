# Workspace Setup

Read this after input triage identifies code work and before any Jujutsu graph move, implementation edit, worker dispatch, or finalized change. It owns writable-workspace selection, plan clarification, feature-change placement, pre-work inventory, dirty-path collision handling, and task-list setup. Return the canonical workspace, working-copy change, bookmark context, pre-work paths and unpublished changes, exclusions, and task state to the kernel.

## Writable Workspace

Repository writes require a writable Jujutsu workspace. Confirm `jj workspace root` succeeds and the workspace can be edited before treating the current directory as canonical. If the user named a repository and the harness exposes a remote work surface, use it only when it provides such a workspace. Otherwise perform no repository writes and report that no writable Jujutsu workspace is available.

## Prepare The Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ - read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script. Do not edit the plan body during execution; progress lives in task state and described Jujutsu changes, and legacy checkboxes or status fields are not execution state.

2. **Establish Jujutsu State**

   Before the first edit, preserve work the user did not offer and establish a dedicated feature change:

   1. Run `jj status` and inspect `jj diff --summary` to record existing workspace changes.
   2. Inspect local and remote bookmarks with `jj bookmark list --all-remotes`. Determine the default publishing bookmark from active project conventions and remote state; Jujutsu has no active bookmark, so never infer one from `@`.
   3. Use the configured Jujutsu remote-fetch capability only when current remote state is required. Use the remote bookmark as parent only when the working-copy ancestry contains no local changes beyond it; otherwise preserve current ancestry.
   4. If `@` contains unrelated work, create a new child with `jj new @`. If `@` is empty and already a dedicated child, continue there. Do not move a bookmark merely to begin work.
   5. Record pre-work paths and unpublished changes. Do not rewrite, abandon, describe, publish, or compose them into this run.

   A task that must modify a path already changed before the run is the one case logical-change separation cannot protect automatically. Ask once in standalone interactive mode whether that existing work may be included or must remain excluded. In Return-to-Caller Mode, do not ask or edit the path; return `status: blocked` with the path and recovery direction.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ - use the platform's task-tracking capability when available and follow `references/work-intake.md` for derivation, naming, dependencies, and verification. If no task capability exists, continue without simulating a task list in chat.
