# Workspace Setup

Read this after input triage identifies code work and before any bookmark move, implementation edit, worker dispatch, or accepted change. It owns writable-workspace selection, plan clarification, change/bookmark placement, pre-work inventory, collision handling, and task-list setup. Return the canonical workspace, working-copy change, bookmark, pre-work paths and changes, exclusions, and task state to the kernel.

## Writable Workspace

Repo-local implementation writes require a writable JJ workspace. Before treating the current directory as the project, require `jj workspace root` to resolve and verify that root is writable. If this session has no writable workspace but the user named a repository and the harness exposes a writable remote repo-work surface, initialize or use a colocated JJ workspace there and treat it as canonical for verification, accepted changes, bookmarks, and handoff. Otherwise skip repo-local writes and report that no writable JJ workspace is available; do not synthesize file changes elsewhere.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ — read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** — progress lives in JJ changes and the task tracker, and legacy `- [ ]` / `- [x]` marks or a `status:` field are not state.

2. **Setup Environment**

   Two things must hold before the first edit: work has its own mutable change and local bookmark away from `trunk()`, and nothing the user did not offer gets folded into that change or published. These are reversible JJ operations recorded in `jj op log`, so establish them and report the result in one line.

   **Change and bookmark.** Resolve and retain `<remote>` from explicit repository configuration when present, otherwise by matching the host's repository identity to the configured JJ remotes. Run `jj git fetch --remote <remote>` when network access is within authority, then resolve the immutable base with `trunk()`. If `trunk()` cannot resolve exactly one revision, use the host's repository metadata to identify the remote default bookmark, track it with `jj bookmark track <name> --remote=<remote>`, fetch, and resolve `<name>@<remote>`; block rather than guessing when no unique base or applicable remote exists. There is no current bookmark in JJ: inspect `@`, its parents, and bookmarks separately with revsets.

   If `@` is the trunk revision or immutable, create a new empty working-copy change with `jj new trunk()`. If `@` already contains mutable work for this request, continue it; if it contains unrelated work, create a sibling workspace/change rather than rebasing or editing that work. Create or set a feature bookmark named from local conventions with `jj bookmark set <name> -r @-` after the first accepted change, not on the empty working-copy change. Resolve bookmark conflicts before publishing; `jj status` and `jj bookmark list` expose them.

   Otherwise continue the invoked mutable change without renaming its bookmark or asking. Use an additional JJ workspace only when isolation is requested or required; do not create a second linked-checkout mechanism. Rewrite `trunk()` only when the user explicitly authorized it in this session.

   **Pre-work scope.** Before editing, record the current operation from `jj op log`, the working-copy change/commit IDs from `jj log -r @`, changed paths from `jj diff -r @ --name-only`, conflicts from `jj log -r '@ & conflicts()'`, and unpublished local changes from `jj log -r 'remote_bookmarks(remote=<remote>)..@'` when `<remote>` resolves. Nothing the user did not offer is yours to fold into an accepted change or publish. Preserve unrelated work as its own change or workspace; do not translate it through a staging or shelving workflow. Return the retained `<remote>` to shipping.
   - Incremental integration uses explicit filesets with `jj split` or `jj squash`, so untouched pre-work paths remain in their original change. The standalone handoff passes every excluded pre-work path and every unpublished pre-work change ID to shipping.
   - If one file contains both user work and required unit work, ask once in standalone mode whether to include the combined file or leave the unit blocked. In Return-to-Caller Mode do not edit it; return `status: blocked` with the path and recovery action. Never use `jj restore` to discard user content.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ — use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent elsewhere), and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
