# Workspace Setup

Read this after input triage identifies code work and before changing the working-copy change, editing, dispatching, or finalizing a change. It owns writable JJ workspace selection, plan clarification, bookmark placement, pre-work inventory, modified-path collision handling, and task-list setup. Return the canonical workspace, working-copy change, bookmark, pre-work paths and changes, exclusions, and task state to the kernel.

## Writable Workspace

Repo-local implementation writes require a writable JJ workspace. Before treating the current directory as the project, require `jj workspace root` to resolve and confirm the workspace is writable. If this session has no writable workspace, but the user named a repository and the harness exposes a remote repo-work surface with one, run there and treat it as canonical for verification, JJ changes, bookmarks, and handoff. Otherwise skip repo-local writes and report that no writable JJ workspace is available; do not synthesize repository changes from scratch space.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ - read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** - progress lives in JJ changes and the task tracker, and legacy checklist marks or a `status:` field are not state.

2. **Setup Environment**

   Two things must hold before the first edit: the work has its own mutable JJ change and publishable bookmark, and nothing the user did not offer enters a described or published change. Creating a new change is locally reversible, so do it and report it in one line.

   **Change and bookmark.** Resolve the repository's integration base with `trunk()`. Use `gh repo view --json defaultBranchRef` only when GitHub metadata is needed to name the eventual bookmark. Read the current working-copy change and its parents with `jj log -r '@ | @-'`; read local and remote bookmark targets with `jj bookmark list --all-remotes`.

   If `@` is the same commit as `trunk()`, create a child with `jj new trunk()` before editing. If `@` already contains or descends from user work, preserve that mutable stack and create a new child with `jj new @`. Otherwise continue in the existing empty mutable change. Re-read `jj log -r '@ | @-'` after mutation and treat it as authoritative.

   Create or move a feature bookmark only when publication needs one, using `jj bookmark set <runtime-derived-name> -r <final-change>`. Never use a bookmark as the workspace selector. Continue on an invoked mutable stack without rewriting existing bookmarks. Use an additional JJ workspace only when isolation requires one or the user requested one through the functional `ce-worktree` route. Describe work directly on `trunk()` only when the user explicitly authorized that in this session.

   **Pre-work scope.** Before editing, record `jj diff --summary -r @` and `jj log -r 'trunk()..@'`. Nothing already present in that working-copy change or mutable stack is yours to publish. Do not stash, abandon, or rewrite it. Enforce ownership with filesets:

   - Finalize each unit with explicit work-owned filesets, using `jj commit <filesets>` or `jj split <filesets>` as local syntax requires, so unrelated paths stay in the succeeding working-copy change. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Runtime conventions win; apply compatible Go guidance to message quality, clarity, and structure, and impose no fixed message shape. The standalone handoff passes every starting path this run did not finalize as `exclude:<paths>`.
   - If a unit must edit a path already modified in the starting change, standalone mode asks once whether the combined path belongs in the unit or remains excluded. Return-to-Caller Mode does not ask or edit it; return `status: blocked` with the path and a recovery direction that preserves the existing change.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ - use the platform's task-tracking capability when available and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
