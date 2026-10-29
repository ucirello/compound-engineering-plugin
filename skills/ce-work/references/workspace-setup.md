# Workspace Setup

Read this after input triage identifies code work and before any branch move, implementation edit, worker dispatch, or commit. It covers choosing a writable checkout, clarifying the plan, placing the branch, recording what was already in progress before work began, handling a unit that must edit an already-dirty file, and setting up the task list. Return to the main `SKILL.md` flow: the canonical checkout, the branch, the pre-work paths and commits, the exclusions, and the task state.

## Writable Checkout

Repo-local implementation writes require a writable JJ workspace. Before treating the current directory as the project, resolve and verify its absolute `jj workspace root`. If this session has no writable workspace, but the user named a repository and the harness exposes a writable JJ repo-work surface, use that surface as the canonical root for verification, commits and handoff. Otherwise report that no writable workspace is available; do not synthesize changes from a non-repository scratch directory. Set every JJ command's cwd to that absolute root. Follow the isolated lifecycle contract in `cross-model-execution.md` whenever isolation is selected; it preserves existing isolation, explicit colocated creation/status checks, naming, ownership and safe removal.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ — read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** — progress lives in JJ commits and the task tracker, and legacy `- [ ]` / `- [x]` marks or a `status:` field are not state.

2. **Setup Environment**

   Two things must hold before the first edit: the work lands on a feature branch, and nothing the user did not offer up gets committed or published by this run. Neither is a question for the user. A branch move is a one-command undo, so do it and say so in one line.

   **Bookmark.** Resolve the absolute workspace root with `jj workspace root`; run every JJ command with cwd set to that root. Determine the remote default from repository metadata, using `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef)` on GitHub. Inspect `jj bookmark list` and the exact current change rather than assuming a current branch.

   If the target is the default bookmark or uncertain, create a feature bookmark named from the task. Fetch the verified remote with `jj git fetch --remote <remote>`, inspect the exact default remote bookmark and local ancestry, and preserve local commits and dirty state. Base new work on the fetched default only when there are no local commits to preserve; otherwise retain the verified current history. Verify the resulting bookmark target. Never move the real default without explicit authorization or discard unrelated work to align a base.

   Otherwise continue on the invoked branch without renaming it or asking. Use a worktree only when the user asked for one this session (`ce-worktree`), and commit on the default branch only when the user explicitly authorized that in this session.

   **Pre-work scope.** Before editing, record `jj status`, `jj diff --summary`, a local filesystem inventory of ignored/untracked content, and `jj log` for the verified remote-default-to-current range (unknown without a remote). Nothing pre-existing is yours to commit or publish. Preserve it without stash/discard. All scratch belongs under local `.tmp/`. Enforce this without asking the user to choose:
   - Incremental commits stage only work-owned files and are path-limited, so untouched WIP never enters a commit; the standalone handoff passes every pre-work file this run did not commit as `exclude:<paths>`, and ships locally via `ce-commit` when pre-existing unpushed commits are on the branch (`references/shipping-workflow.md`).
   - A unit that must edit a file that was already dirty is the one case a commit cannot separate. Ask once, at the first commit that would include such a file, and cover every such file in that one question: commit those files with the user's edits included, or leave them uncommitted (an exclusion for the rest of the run, named in the final summary as unshipped). In Return-to-Caller Mode do not ask and do not edit the file — return `status: blocked` naming it, so the user's WIP stays intact and commit-or-stash-and-rerun is a clean recovery.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ — use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent elsewhere), and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
