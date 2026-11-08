# Workspace Setup

Read this after input triage identifies code work and before any branch move, implementation edit, worker dispatch, or commit. It covers choosing a writable checkout, clarifying the plan, placing the branch, recording what was already in progress before work began, handling a unit that must edit an already-dirty file, and setting up the task list. Return to the main `SKILL.md` flow: the canonical checkout, the branch, the pre-work paths and commits, the exclusions, and the task state.

## Writable Checkout

Repo-local writes require a writable JJ workspace. Resolve its absolute root with `jj workspace root`; run every subsequent JJ command with cwd at that root, not `-R` alone. If only a harness remote repo-work surface offers the requested writable JJ workspace, use it as canonical; otherwise report no writable workspace and do not synthesize changes in non-repo scratch. Repository GitHub commands run as `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`; never directly execute Git.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ — read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** — progress lives in git commits and the task tracker, and legacy `- [ ]` / `- [x]` marks or a `status:` field are not state.

2. **Setup Environment**

   Two things must hold before the first edit: the work lands on a feature branch, and nothing the user did not offer up gets committed or published by this run. Neither is a question for the user. A branch move is a one-command undo, so do it and say so in one line.

   **Bookmark.** Determine the remote default from repository metadata (`GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef` from the absolute root), or verified existing `main`/`master` when metadata is unavailable. Inspect bookmarks at the actual task head with `jj bookmark list` and `jj log`; JJ does not have a current Git branch, and an empty `@` above the task head is not a new source branch.

   If the task bookmark is default or uncertain, create a feature bookmark named from the task with `jj bookmark create <name> -r <verified-task-head>`. Fetch the verified remote default with `jj git fetch --remote origin --branch <default>` when applicable. Base new work on the exact fetched default only if no local commits or working-copy changes would be lost; preserve local history at the verified task head otherwise. Reinspect bookmark targets after mutation. Unknown base/dirty state selects preservation and a safe decision, not discard/reset. Never advance the default without explicit authorization.

   Otherwise continue on the invoked bookmark unchanged. Use isolation only when requested (`ce-worktree`), required by multi-PR delivery, or the selected engine's bounded isolation contract. Reuse existing isolation first. New caller-selected names follow `YYYYMMDD-meaningful-kebab-slug`, captured once and persisted, normalized without double prefixes; name equals absolute local `.tmp/` destination basename with checked registration/path collisions suffixed `-2`, `-3`. Require `jj workspace add --colocate`, verify `jj git colocation status` in the destination and exact base, and respect harness adoption/lifecycle authority. Unsupported naming/colocation blocks; existing names and PR/source bookmarks remain unchanged. Retirement safeguards and `jj workspace remove` are in `cross-model-execution.md` and apply to all caller-owned cleanup; never forget-and-delete.

   **Pre-work scope.** Before editing, record `jj status`, `jj diff --summary`, actual untracked/ignored files and exact task head; inspect `jj log -r '<verified-remote-default>..<verified-task-head>'` for pre-existing local commits (unknown without verified remote). None are yours to commit/publish. Preserve them without stash/discard. Enforce this without asking the user to choose:
   - Incremental commits stage only work-owned files and are path-limited, so untouched WIP never enters a commit; the standalone handoff passes every pre-work file this run did not commit as `exclude:<paths>`, and ships locally via `ce-commit` when pre-existing unpushed commits are on the branch (`references/shipping-workflow.md`).
   - A unit that must edit a file that was already dirty is the one case a commit cannot separate. Ask once, at the first commit that would include such a file, and cover every such file in that one question: commit those files with the user's edits included, or leave them uncommitted (an exclusion for the rest of the run, named in the final summary as unshipped). In Return-to-Caller Mode do not ask and do not edit the file — return `status: blocked` naming it, so the user's WIP stays intact and commit-or-stash-and-rerun is a clean recovery.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ — use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent elsewhere), and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
