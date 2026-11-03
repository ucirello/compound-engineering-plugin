# Workspace Setup

Read this after input triage identifies code work and before any branch move, implementation edit, worker dispatch, or commit. It covers choosing a writable checkout, clarifying the plan, placing the branch, recording what was already in progress before work began, handling a unit that must edit an already-dirty file, and setting up the task list. Return to the main `SKILL.md` flow: the canonical checkout, the branch, the pre-work paths and commits, the exclusions, and the task state.

## Writable Checkout

Repo-local implementation writes require a writable checkout. Before treating the current working directory as the project, confirm it is a git checkout you can edit. If this session has no writable checkout, but the user named a repository and the harness exposes a remote repo-work surface with a writable checkout, run the implementation work on that surface and treat that checkout as the canonical workspace for verification, commits, and handoff. Otherwise skip repo-local writes and report that no writable checkout is available; do not synthesize file changes from a non-repo scratch directory.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ — read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** — progress lives in git commits and the task tracker, and legacy `- [ ]` / `- [x]` marks or a `status:` field are not state.

2. **Setup Environment**

   Two things must hold before the first edit: the work lands on a feature branch, and nothing the user did not offer up gets committed or published by this run. Neither is a question for the user. A branch move is a one-command undo, so do it and say so in one line.

   **Bookmark.** Resolve the absolute workspace root with `jj root`, then run every JJ command from that absolute cwd. Determine the remote default using `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef)` or verified repository metadata; never guess a history anchor. Inspect `jj bookmark list` and `jj log -r '@ | @-'` for current identity, including an empty working copy above a bookmarked parent.

   If on the default bookmark or identity is uncertain, create a task bookmark only after verifying the base. Fetch the exact remote bookmark with `jj git fetch --remote origin --bookmark <verified-default>`. Compare `jj log -r '<verified-remote-default>..<verified-local-head>'`: base new work on the fetched default only when no local commits must remain visible; otherwise preserve the verified local head and its ancestry. Do not silently substitute another ref. Create with `jj bookmark create <task-bookmark> -r <verified-base>` and make a new working-copy change there only when existing user work is preserved. Re-read bookmark targets and full commit IDs. Uncertain identity blocks mutation, not permission bypass.

   Otherwise continue on the invoked branch without renaming it or asking. Use a worktree only when the user asked for one this session (`ce-worktree`) or when `references/multi-pr-delivery.md` builds a PR group in its own checkout or session, and commit on the default branch only when the user explicitly authorized that in this session.

   **Pre-work scope.** Before editing, record `jj status`, `jj diff --summary`, `jj file list`, conflicts, and ignored/untracked filesystem inventory without changing ignore rules. Record exact current/parent commit IDs and `jj log -r '<verified-remote-default>..<verified-local-head>'` (unknown without verified remote identity). Nothing already present is yours to commit or publish. Preserve it without stash/reset or changing the named source bookmark. Enforce this without asking the user to choose:
   - Incremental commits stage only work-owned files and are path-limited, so untouched WIP never enters a commit; the standalone handoff passes every pre-work file this run did not commit as `exclude:<paths>`, and ships locally via `ce-commit` when pre-existing unpushed commits are on the branch (`references/shipping-workflow.md`).
   - A unit that must edit a file that was already dirty is the one case a commit cannot separate. Ask once, at the first commit that would include such a file, and cover every such file in that one question: commit those files with the user's edits included, or leave them uncommitted (an exclusion for the rest of the run, named in the final summary as unshipped). In Return-to-Caller Mode do not ask and do not edit the file — return `status: blocked` naming it, so the user's WIP stays intact and commit-or-stash-and-rerun is a clean recovery.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ — use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent elsewhere), and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
