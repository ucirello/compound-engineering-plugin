# Workspace Setup

Read this after input triage identifies code work and before any branch move, implementation edit, worker dispatch, or commit. It covers choosing a writable checkout, clarifying the plan, placing the branch, recording what was already in progress before work began, handling a unit that must edit an already-dirty file, and setting up the task list. Return to the main `SKILL.md` flow: the canonical checkout, the branch, the pre-work paths and commits, the exclusions, and the task state.

## Writable Checkout

Repo-local implementation writes require a writable JJ workspace. Before treating the current working directory as the project, confirm it is a JJ workspace you can edit. If this session has no writable workspace, but the user named a repository and the harness exposes a remote repo-work surface with a writable JJ workspace, run the implementation work on that surface and treat that workspace as canonical for verification, commits, and handoff. Otherwise skip repo-local writes and report that no writable workspace is available; do not synthesize file changes from a non-repo scratch directory.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ — read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** — progress lives in JJ changes and the task tracker, and legacy `- [ ]` / `- [x]` marks or a `status:` field are not state.

2. **Setup Environment**

   Two things must hold before the first edit: the work lands on a feature branch, and nothing the user did not offer up gets committed or published by this run. Neither is a question for the user. A branch move is a one-command undo, so do it and say so in one line.

   **Bookmark.** Run all JJ commands with cwd equal to the verified absolute target workspace root. Determine the remote default from `jj bookmark list --all-remotes` and repository metadata; for repository-scoped GitHub commands set `GIT_DIR=$(jj git root)` in that root before `gh repo view --json defaultBranchRef`. Otherwise use `main` or `master` only when verified. Inspect bookmarks and exact working-copy/parent revisions with `jj log`; an empty `@` above a bookmarked task head is not detached work. Record the verified task-history head explicitly.

   If you are on the default bookmark or cannot identify a safe task bookmark, create a feature bookmark named from the plan or work description. Fetch the verified remote using `jj git fetch --remote origin` when available. Base new work on the fetched default only when no local task commits or user work would be lost; otherwise preserve the verified local head and all dirt. Verify the new bookmark and exact base using `jj bookmark list` and `jj log`. Unknown branch safety never authorizes rewriting the real default. Use `jj new <verified-base>` only after protecting and preserving existing work.

   Otherwise continue on the invoked branch without renaming it or asking. Use a worktree only when the user asked for one this session (`ce-worktree`) or when `references/multi-pr-delivery.md` builds a PR group in its own checkout or session, and commit on the default branch only when the user explicitly authorized that in this session.

   **Pre-work scope.** Before editing, record `jj status`, `jj diff --summary`, conflicts and a separate ignored/untracked inventory, plus full descriptions for `jj log -r '<verified-default>@origin..<verified-task-head>'`; use "unknown" without a verified remote. Nothing in that set is yours to commit or publish. It stays untouched: no stash, no question, no effect on naming. Snapshots do not protect ignored/untracked data. Enforce this without asking the user to choose:
   - Incremental commits stage only work-owned files and are path-limited, so untouched WIP never enters a commit; the standalone handoff passes every pre-work file this run did not commit as `exclude:<paths>`, and ships locally via `ce-commit` when pre-existing unpushed commits are on the branch (`references/shipping-workflow.md`).
   - A unit that must edit a file that was already dirty is the one case a commit cannot separate. Ask once, at the first commit that would include such a file, and cover every such file in that one question: commit those files with the user's edits included, or leave them uncommitted (an exclusion for the rest of the run, named in the final summary as unshipped). In Return-to-Caller Mode do not ask and do not edit the file — return `status: blocked` naming it, so the user's WIP stays intact and commit-or-stash-and-rerun is a clean recovery.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ — use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent elsewhere), and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
