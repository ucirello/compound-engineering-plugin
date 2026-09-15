# Workspace Setup

Read this after input triage identifies code work and before any branch move, implementation edit, worker dispatch, or commit. It covers choosing a writable checkout, clarifying the plan, placing the branch, recording what was already in progress before work began, handling a unit that must edit an already-dirty file, and setting up the task list. Return to the main `SKILL.md` flow: the canonical checkout, the branch, the pre-work paths and commits, the exclusions, and the task state.

## Writable Checkout

Repo-local implementation writes require a writable checkout. Before treating the current working directory as the project, confirm it is a jj workspace you can edit (`jj workspace root`). If this session has no writable checkout, but the user named a repository and the harness exposes a remote repo-work surface with a writable checkout, run the implementation work on that surface and treat that checkout as the canonical workspace for verification, commits, and handoff. Otherwise skip repo-local writes and report that no writable checkout is available; do not synthesize file changes from a non-repo scratch directory.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ — read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** — progress lives in jj changes and the task tracker, and legacy `- [ ]` / `- [x]` marks or a `status:` field are not state.

2. **Setup Environment**

   Two things must hold before the first edit: the work lands on a feature branch, and nothing the user did not offer up gets committed or published by this run. Neither is a question for the user. A branch move is a one-command undo, so do it and say so in one line.

   **Bookmark.** Determine the default bookmark of trunk from `jj bookmark list` / remote bookmarks. If that is unavailable, use the host's repository-metadata capability; when the available interface is GitHub CLI, run `GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef`. Otherwise use `main` or `master` when one exists. Read bookmarks on `@` with `jj log -r @ --no-graph -T 'bookmarks'`.

   If you are on the default bookmark, have no bookmark, or cannot tell, create a feature bookmark named from the plan or work description: `jj new <base>` then `jj bookmark create <name>`. When a remote default exists, run `jj git fetch` first. Base the new change on the fetched `main@origin` (or the named default) when `@` has no commits beyond it; base it on `@` when local commits must stay visible to the idempotency check and the shipping check, or when there is no remote. After the bookmark move, run `jj log -r @ --no-graph -T 'bookmarks'` again and treat that result as authoritative. When bookmark safety remains uncertain, use a spare bookmark and never make incremental commits on the real default.

   Otherwise continue on the invoked bookmark without renaming it or asking. Use a jj workspace only when the user asked for one this session (`ce-worktree`), and commit on the default bookmark only when the user explicitly authorized that in this session.

   **Pre-work scope.** Before editing, record `jj status` (the user's in-progress files) and whether `@` carries commits not on the remote default (`jj log -r 'main@origin..@'` or the named default; "unknown" without a remote). Nothing in that set is yours to commit or publish. It rides along on the bookmark move untouched: no stash, no question, no effect on naming. Enforce this without asking the user to choose:
   - Incremental commits describe only work-owned files and are path-limited, so untouched WIP never enters a change; the standalone handoff passes every pre-work file this run did not commit as `exclude:<paths>`, and ships locally via `ce-commit` when pre-existing unpushed commits are on the bookmark (`references/shipping-workflow.md`).
   - A unit that must edit a file that was already dirty is the one case a commit cannot separate. Ask once, at the first commit that would include such a file, and cover every such file in that one question: commit those files with the user's edits included, or leave them uncommitted (an exclusion for the rest of the run, named in the final summary as unshipped). In Return-to-Caller Mode do not ask and do not edit the file — return `status: blocked` naming it, so the user's WIP stays intact and commit-or-stash-and-rerun is a clean recovery.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ — use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent elsewhere), and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
