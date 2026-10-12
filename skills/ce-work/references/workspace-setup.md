# Workspace Setup

Read this after input triage identifies code work and before any branch move, implementation edit, worker dispatch, or commit. It covers choosing a writable checkout, clarifying the plan, placing the branch, recording what was already in progress before work began, handling a unit that must edit an already-dirty file, and setting up the task list. Return to the main `SKILL.md` flow: the canonical checkout, the branch, the pre-work paths and commits, the exclusions, and the task state.

## Writable Checkout

Repo-local implementation writes require a writable JJ workspace. Confirm its absolute root with `jj workspace root` from the actual target cwd. If this session has no writable workspace but the named repository has a supported remote writable surface, use that as canonical; otherwise report the blocker, never synthesize repository changes from scratch. Run every JJ command from the target absolute root. For repository-scoped `gh`, export `GIT_DIR=$(jj git root)` there first. Temporary artifacts, including failures, belong in local ignored `.tmp/`.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ — read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** — progress lives in JJ changes and the task tracker, and legacy `- [ ]` / `- [x]` marks or a `status:` field are not state.

2. **Setup Environment**

   Two things must hold before the first edit: the work lands on a feature branch, and nothing the user did not offer up gets committed or published by this run. Neither is a question for the user. A branch move is a one-command undo, so do it and say so in one line.

   **Bookmark.** Determine the remote default through repository metadata, such as `(cd "$workspace_root" && export GIT_DIR=$(jj git root) && gh repo view --json defaultBranchRef)`, or verified `main`/`master` remote bookmarks. Inspect `jj bookmark list` and `jj log -r '@ | @-'`: an empty `@` above the invoked feature bookmark is normal, not a detached/default-branch error.

   When no verified invoked feature bookmark exists, create a unique feature bookmark from the task. Fetch the verified remote with `jj git fetch --remote origin`; inspect `jj log -r '<default>@origin..@'`. Base a new empty working change on the remote default only when no local commits/work must remain visible; otherwise preserve the current ancestry and dirty state. Never abandon, reset or overwrite existing work. Create the bookmark on the intended change with `jj bookmark create <name> -r <verified-change>` and verify its target. If safety is uncertain, use a spare bookmark and never advance the real default.

   Otherwise continue on the invoked bookmark without renaming it or asking. User-requested `ce-worktree` creation follows `cross-model-execution.md`'s colocated/date-prefixed naming contract; existing isolation is reused unchanged. Ordinary native worker isolation is harness-owned, and cross-model run-owned isolation follows that reference's separate contract. Commit on the default bookmark only when explicitly authorized this session.

   **Pre-work scope.** Before editing, record `jj status`, `jj diff --summary`, filesystem untracked/ignored inventory and `jj log -r '<default>@origin..@'` (unknown without a verified remote). JJ automatically tracks eligible files, so inspect actual files as well as status. None of this pre-existing work is yours to publish. Preserve it untouched: no stash/discard or naming question. Enforce this without asking the user to choose:
   - Incremental commits stage only work-owned files and are path-limited, so untouched WIP never enters a commit; the standalone handoff passes every pre-work file this run did not commit as `exclude:<paths>`, and ships locally via `ce-commit` when pre-existing unpushed commits are on the branch (`references/shipping-workflow.md`).
   - A unit that must edit a file that was already dirty is the one case a commit cannot separate. Ask once, at the first commit that would include such a file, and cover every such file in that one question: commit those files with the user's edits included, or leave them uncommitted (an exclusion for the rest of the run, named in the final summary as unshipped). In Return-to-Caller Mode do not ask and do not edit the file — return `status: blocked` naming it, so the user's WIP stays intact and commit-or-stash-and-rerun is a clean recovery.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ — use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent elsewhere), and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
