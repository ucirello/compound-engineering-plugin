# Workspace Setup

Read this after input triage identifies code work and before any bookmark move, implementation edit, worker dispatch, or commit. It covers choosing a writable workspace, clarifying the plan, placing the bookmark, recording what was already in progress before work began, handling a unit that must edit an already-dirty file, and setting up the task list. Return to the main `SKILL.md` flow: the canonical workspace, the bookmark, the pre-work paths and changes, the exclusions, and the task state.

## Writable Checkout

Repo-local implementation writes require a writable workspace. Before treating the current working directory as the project, confirm `jj workspace root` succeeds and you can edit that workspace. If this session has no writable workspace, but the user named a repository and the harness exposes a remote repo-work surface with a writable workspace, run the implementation work on that surface and treat that workspace as canonical for verification, commits, and handoff. Otherwise skip repo-local writes and report that no writable workspace is available; do not synthesize file changes from a non-repo scratch directory.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ — read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** — progress lives in jj changes and the task tracker, and legacy `- [ ]` / `- [x]` marks or a `status:` field are not state.

2. **Setup Environment**

   Two things must hold before the first edit: the work lands on a feature bookmark, and nothing the user did not offer up gets committed or published by this run. Neither is a question for the user. A bookmark move is a one-command undo, so do it and say so in one line.

   **Bookmark.** Set cwd to the absolute root reported by `jj workspace root` for every JJ command. Determine the remote default through repository metadata; when the available interface is GitHub CLI, run `GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef` in that workspace. Corroborate it with `jj bookmark list`; remote names are the form JJ prints (often `main@origin`). Without metadata, use `main` or `master` only when one exists unambiguously. Read local bookmarks at `@`; if `@` is empty and has no bookmark, inspect `@-` before deciding that this work has no bookmark. Multiple candidates are ambiguous, never a reason to pick the first.

   If you are on the default bookmark, have no bookmark, or cannot tell, create a feature bookmark named from the plan or work description. When a remote default exists, run `jj git fetch` first. Base the new bookmark on the fetched remote bookmark when `@` has no changes beyond it; base it on `@` when local changes must stay visible to the idempotency check and the shipping check, or when there is no remote. After the bookmark move, read the current bookmark again and treat that result as authoritative. When bookmark safety remains uncertain, use a spare bookmark and never make incremental commits on the real default.

   Otherwise continue on the invoked bookmark without renaming it or asking. Use a linked workspace only when the user asked for one this session (`ce-worktree`), and commit on the default bookmark only when the user explicitly authorized that in this session.

   **Pre-work scope.** Before editing, record `jj diff --name-only` and `jj status` (the user's in-progress files) and whether `@` carries changes not on the remote default bookmark (`jj log -r 'remote_bookmark..@' --no-graph`; "unknown" without a remote). Nothing in that set is yours to commit or publish. It rides along on the bookmark move untouched: no stash, no question, no effect on naming. Enforce this without asking the user to choose:
   - Incremental commits name only work-owned files, so untouched WIP never enters a change; the standalone handoff passes every pre-work file this run did not commit as `exclude:<paths>`, and ships locally via `ce-commit` when pre-existing unpushed changes are on the bookmark (`references/shipping-workflow.md`).
   - A unit that must edit a file that was already dirty is the one case a commit cannot separate. Ask once, at the first commit that would include such a file, and cover every such file in that one question: commit those files with the user's edits included, or leave them uncommitted (an exclusion for the rest of the run, named in the final summary as unshipped). In Return-to-Caller Mode do not ask and do not edit the file — return `status: blocked` naming it, so the user's WIP stays intact and commit-or-stash-and-rerun is a clean recovery.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ — use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent elsewhere), and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
