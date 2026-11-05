# Workspace Setup

Read this after input triage identifies code work and before any branch move, implementation edit, worker dispatch, or commit. It covers choosing a writable checkout, clarifying the plan, placing the branch, recording what was already in progress before work began, handling a unit that must edit an already-dirty file, and setting up the task list. Return to the main `SKILL.md` flow: the canonical checkout, the branch, the pre-work paths and commits, the exclusions, and the task state.

## Writable Checkout

Repo-local implementation writes require a writable JJ workspace. Before treating the current directory as the project, resolve its absolute root with `jj workspace root` and confirm it is editable. Run every JJ command with that absolute root as cwd, never merely `jj -R`. If this session has no writable workspace, but the user named a repository and the harness exposes a writable JJ repo-work surface, use that surface as canonical. Otherwise skip repo-local writes and report the missing capability; do not synthesize changes in non-repo scratch. Never invoke Git directly; use https://docs.jj-vcs.dev/latest/git-command-table/ and https://docs.jj-vcs.dev/latest/cli-reference/ . Temporary files stay beneath local `.tmp/`.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ — read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** — progress lives in JJ commits and the task tracker, and legacy `- [ ]` / `- [x]` marks or a `status:` field are not state.

2. **Setup Environment**

   Two things must hold before the first edit: the work lands on a feature branch, and nothing the user did not offer up gets committed or published by this run. Neither is a question for the user. A branch move is a one-command undo, so do it and say so in one line.

   **Bookmark.** Resolve the default bookmark using repository metadata; for GitHub run `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef)`. Otherwise verify an existing `main` or `master`, never guess. Inspect `jj bookmark list` and the actual working-copy revision from the absolute workspace root. JJ may have an empty `@` above the intended head; inspect `@-` too.

   If the intended bookmark is default, absent, or uncertain, create a task feature bookmark at the verified current task head using `jj bookmark create <feature> -r <verified-head>`. When a remote default exists, first run `jj git fetch --remote origin --branch <verified-default>` from the absolute workspace root, inspect ancestry with `jj log`, and preserve local commits and all working-copy changes. Do not move user work to a guessed base. Re-read bookmark targets; never advance the default without this session's authorization. If the head/base remains uncertain, stop with the concrete ambiguity rather than resetting.

   Otherwise continue on the invoked branch without renaming it or asking. Use a worktree only when the user asked for one this session (`ce-worktree`) or when `references/multi-pr-delivery.md` builds a PR group in its own checkout or session, and commit on the default branch only when the user explicitly authorized that in this session.

   **Pre-work scope.** Before editing, from the absolute root record `jj status`, `jj diff --summary`, conflicts, and a local filesystem inventory of ignored/untracked content, and inspect `jj log -r '<verified-remote-default>..<verified-task-head>'` for pre-existing unpushed commits (unknown without a verified remote). Nothing in that set is yours to commit or publish. Preserve it without stash, discard or reset. Enforce this without asking the user to choose:
   - Incremental commits stage only work-owned files and are path-limited, so untouched WIP never enters a commit; the standalone handoff passes every pre-work file this run did not commit as `exclude:<paths>`, and ships locally via `ce-commit` when pre-existing unpushed commits are on the branch (`references/shipping-workflow.md`).
   - A unit that must edit a file that was already dirty is the one case a commit cannot separate. Ask once, at the first commit that would include such a file, and cover every such file in that one question: commit those files with the user's edits included, or leave them uncommitted (an exclusion for the rest of the run, named in the final summary as unshipped). In Return-to-Caller Mode do not ask and do not edit the file — return `status: blocked` naming it, so the user's WIP stays intact and commit-or-stash-and-rerun is a clean recovery.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ — use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent elsewhere), and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
