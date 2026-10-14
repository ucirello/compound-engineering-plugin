# Workspace Setup

Read this after input triage identifies code work and before any branch move, implementation edit, worker dispatch, or commit. It covers choosing a writable checkout, clarifying the plan, placing the branch, recording what was already in progress before work began, handling a unit that must edit an already-dirty file, and setting up the task list. Return to the main `SKILL.md` flow: the canonical checkout, the branch, the pre-work paths and commits, the exclusions, and the task state.

## Writable Checkout

Repo-local implementation writes require a writable JJ workspace. Confirm its absolute root with `jj workspace root` before treating it as the project. If the harness supplies a writable remote repo-work surface, use that verified JJ workspace as canonical; otherwise report that no writable workspace is available, without synthesizing edits in non-repo scratch storage. Run every JJ command from the target absolute root; repository-scoped GitHub calls use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Store all temporary/error/recovery files under local ignored `.tmp/`.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ — read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** — progress lives in git commits and the task tracker, and legacy `- [ ]` / `- [x]` marks or a `status:` field are not state.

2. **Setup Environment**

   Two things must hold before the first edit: the work lands on a feature branch, and nothing the user did not offer up gets committed or published by this run. Neither is a question for the user. A branch move is a one-command undo, so do it and say so in one line.

   **Bookmark.** Resolve the remote default with repository metadata (`GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef` from the absolute root), otherwise verify an existing `main` or `master` bookmark. Inspect `jj log -r '@ | @-'` and `jj bookmark list` to resolve the work bookmark and empty working-copy parent; do not invent a current Git branch.

   If only the default bookmark is selected, none is selected, or placement is uncertain, create a task-derived feature bookmark without moving the default. Fetch with `jj git fetch --remote origin --bookmark <verified-default>` when a remote exists. Verify the remote revision and local ancestry with `jj log` before choosing the base; preserve local unpublished changes and unrelated working-copy edits rather than reset/rebase them away. Record the resulting exact revision and feature bookmark and verify with `jj bookmark list`. Unknown target or dirty-state movement enters the safe decision path.

   Otherwise continue on the invoked bookmark without renaming or asking. Detect/reuse existing isolation first. Use `ce-worktree` only when requested for the session or when the selected isolated engine contract authorizes it; follow cross-model-execution.md's colocated creation, dated identity, stable collision/retry names, absolute destinations and colocation verification. Preserve harness lifecycle ownership and existing workspace names/bookmarks. Unsupported required capabilities block safely. Record changes on the default bookmark only with explicit session authorization.

   **Pre-work scope.** Before editing, record `jj status`, `jj diff --summary`, untracked/ignored inventory, and `jj log -r '<verified-default>@origin..@'` for unpublished changes (unknown without a remote). Nothing pre-existing is yours to commit or publish. Preserve it without stash, reset, discard or redundant questions. Enforce this without asking the user to choose:
   - Incremental JJ commits are path-limited to work-owned files, so untouched WIP never enters a change; the standalone handoff passes every pre-work file this run did not commit as `exclude:<paths>`, and ships locally via `ce-commit` when pre-existing unpublished changes exist (`references/shipping-workflow.md`).
   - A unit that must edit a file that was already dirty is the one case a commit cannot separate. Ask once, at the first commit that would include such a file, and cover every such file in that one question: commit those files with the user's edits included, or leave them uncommitted (an exclusion for the rest of the run, named in the final summary as unshipped). In Return-to-Caller Mode do not ask and do not edit the file — return `status: blocked` naming it, so the user's WIP stays intact and commit-or-stash-and-rerun is a clean recovery.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ — use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent elsewhere), and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
