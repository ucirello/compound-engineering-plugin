# Workspace Setup

Read this after input triage identifies code work and before any branch move, implementation edit, worker dispatch, or commit. It covers choosing a writable checkout, clarifying the plan, placing the branch, recording what was already in progress before work began, handling a unit that must edit an already-dirty file, and setting up the task list. Return to the main `SKILL.md` flow: the canonical checkout, the branch, the pre-work paths and commits, the exclusions, and the task state.

## Writable Checkout

Repo-local implementation writes require a writable JJ workspace. Resolve its absolute root with `jj workspace root` and set cwd to that root for every JJ command. If this session has no writable checkout, but the user named a repository and the harness exposes a writable repo-work surface, use that as canonical for verification and handoff. Otherwise report the blocker; do not synthesize changes from non-repository scratch.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ — read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** — progress lives in JJ changes and the task tracker, and legacy `- [ ]` / `- [x]` marks or a `status:` field are not state.

2. **Setup Environment**

   Before editing, establish a feature bookmark and preserve everything the user did not offer for committing or publication. Do not move unrelated changes or bookmarks.

   **Bookmark.** Determine the remote default through repository metadata: `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef)`. Verify the exact remote bookmark with `jj bookmark list` and inspect `jj log` for the current task's bookmark and ancestry; never guess ambiguous targets.

   If the task lacks a safe feature bookmark, select a meaningful unused name and create it at the verified task revision with `jj bookmark create <name> -r <verified-task-revision>`. Fetch the exact verified remote with `jj git fetch --remote <remote>` when needed. Preserve local commits beyond the remote default and all dirty state; do not rebase or discard them merely to select a base. Re-read bookmark and ancestry after creation. Never commit onto the real default without explicit authorization.

   Otherwise continue on the invoked feature bookmark unchanged. Use isolation only when requested (`ce-worktree`), required by multi-PR delivery, or required by the selected isolated engine. Apply detect-isolation-first, explicit colocation, dated identity, session adoption and safe removal rules in `references/cross-model-execution.md`; existing isolation is reused under its verified name.

   **Pre-work scope.** Before editing, record `jj status`, `jj diff --summary`, conflicts and a local filesystem inventory of ignored/untracked content. Inspect the verified remote-default-to-task range with `jj log -r '<verified-default>..<verified-task-head>'`; record unknown without a verified remote. Nothing in that pre-work set is yours to commit or publish. Preserve it untouched: no stash or discard. Enforce this without asking the user to choose:
   - Incremental commits stage only work-owned files and are path-limited, so untouched WIP never enters a commit; the standalone handoff passes every pre-work file this run did not commit as `exclude:<paths>`, and ships locally via `ce-commit` when pre-existing unpushed commits are on the branch (`references/shipping-workflow.md`).
   - A unit that must edit a file that was already dirty is the one case a commit cannot separate. Ask once, at the first commit that would include such a file, and cover every such file in that one question: commit those files with the user's edits included, or leave them uncommitted (an exclusion for the rest of the run, named in the final summary as unshipped). In Return-to-Caller Mode do not ask and do not edit the file — return `status: blocked` naming it, so the user's WIP stays intact and commit-or-stash-and-rerun is a clean recovery.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ — use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent elsewhere), and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
