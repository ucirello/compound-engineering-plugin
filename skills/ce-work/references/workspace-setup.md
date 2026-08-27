# Workspace Setup

Read this after input triage identifies code work and before any revision move, implementation edit, worker dispatch, or change description. It returns the canonical Jujutsu workspace, working-copy change and revision, relevant bookmark and remote bookmark, pre-work paths and local revisions, exclusions, and task state to the kernel.

## Writable Workspace

Repo-local writes require a writable Jujutsu workspace. Confirm with `jj workspace root`, `jj workspace root`, and `jj status`. Ensure `.tmp/` is ignored before any controller or isolated-workspace state is created there. Outside Jujutsu, report that repository state is unavailable rather than initializing or substituting another VCS. A remote work surface is eligible only when it provides a writable Jujutsu workspace that can remain canonical for verification and handoff.

## Prepare

1. Read `references/work-intake.md` for a plan-backed run. Do not edit the plan body during execution; progress lives in Jujutsu changes and the task tracker.
2. Establish a feature change. Discover the default bookmark from tracked remote bookmarks and repository metadata, fetch with `jj git fetch --remote <remote>` when available, and inspect the current stack with `jj log -r '<default>@<remote>..@'`. If `@` is the default or immutable revision, start a mutable working-copy change with `jj new <base-revset>`. Preserve local ancestor changes by using `@` as the base when they belong to this work. Do not move the default bookmark.
3. Record pre-work scope before editing: `jj status`, `jj diff --name-only -r @`, the current change ID and commit ID from `jj log -r @`, and local revisions not on the remote default using the revset `<default>@<remote>..@`. An unavailable remote makes the unpublished-revision result unknown.

Nothing in the recorded pre-work paths belongs to this run unless the user offered it. Keep unit changes separate with filesets and revision structure: create a child with `jj new` before implementation, or split owned paths with `jj split <filesets>` and leave excluded paths in their original change. If implementation must modify a path already changed at intake, ask once in standalone mode whether the combined path change may be included. In Return-to-Caller Mode, leave it untouched and return blocked.

Use `ce-worktree` only when isolated workspace behavior was requested. Multiple Jujutsu workspaces may share bookmarks; isolation is defined by distinct working-copy changes and workspace roots.

4. Create a task list when triage did not create one and the route is not trivial. Use the host's available task capability without depending on a particular provider name.
