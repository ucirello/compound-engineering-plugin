# Workspace Setup

Read this after input triage identifies code work and before any branch move, implementation edit, worker dispatch, or commit. It covers choosing a writable checkout, clarifying the plan, placing the branch, recording what was already in progress before work began, handling a unit that must edit an already-dirty file, and setting up the task list. Return to the main `SKILL.md` flow: the canonical checkout, the branch, the pre-work paths and commits, the exclusions, and the task state.

## Writable Checkout

Repo-local implementation writes require a writable JJ workspace. Resolve its absolute root with `jj workspace root` before treating it as canonical. Run every subsequent JJ command with that absolute root as its working directory, for example `(cd "$workspace_root" && jj status)`, including commands in workers and verification. If only a supported remote writable JJ surface exists, use its verified absolute root; otherwise report blocked rather than synthesize changes in non-repository scratch.

## Isolated execution and retirement

Detect existing isolation first and reuse its verified name and path without renaming or recreation, even when its name is not dated. Respect harness session adoption and lifecycle ownership. For new isolated execution, capture local `YYYYMMDD` once, normalize the task/PR/revision/caller slug without double-prefixing, and retain the selected identity across retries, resumes and midnight. Use `YYYYMMDD-<meaningful-kebab-case-slug>` as both workspace name and destination basename beneath the existing absolute local `.tmp/` parent. Check `jj workspace list` and destination collisions; append `-2`, `-3`, etc. Never use PID/random/timestamp identities; preserve PR/source bookmarks. Request these guarantees from harness-owned isolation; unsupported required colocation/naming is a safe blocker, not a Git fallback. Caller-owned creation from the source absolute root is explicitly:

```bash
(cd "$workspace_root" && jj workspace add --colocate --name "$dated_name" --revision "$verified_base" "$absolute_owned_destination")
(cd "$absolute_owned_destination" && jj git colocation status)
```

Verify exact base commit and colocation before worker edits, and execute the worker's checks from that same created absolute root. Do not trust a default-branch copy to contain dirty dependencies. See https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace.

Retirement requires explicit cleanup authority and harness lifecycle permission, not mere completion. Stop workers; move active sessions to a surviving workspace; prove exact registered name/path/run ownership and integration. Preserve recovery bookmarks and copy/read back required evidence outside the target. Inspect tracked changes/conflicts AND ignored/untracked files; JJ's snapshot does not protect the latter. Never remove ambiguous, still-referenced, unrelated or non-disposable data. From the surviving absolute root run `jj workspace remove <verified-workspace-name>`, then verify deregistration AND directory disappearance. Warnings or failure preserve remaining state and report a blocker; no force/manual/Git deletion fallback. Use `workspace forget` only to unregister while preserving files. Keep bookmark deletion separate and retain necessary recovery/archive references.

## Prepare the Work

1. **Read Plan and Clarify** _(skip for a bare prompt)_ — read `references/work-intake.md` for how to size the read, what to pull from the plan, and when to stop and ask. Treat the plan as a decision artifact, not an execution script: ask anything unclear before implementing rather than after. **Do not edit the plan body during execution** — progress lives in JJ changes and the task tracker, and legacy `- [ ]` / `- [x]` marks or a `status:` field are not state.

2. **Setup Environment**

   Two things must hold before the first edit: the work lands on a feature branch, and nothing the user did not offer up gets committed or published by this run. Neither is a question for the user. A branch move is a one-command undo, so do it and say so in one line.

   **Bookmark.** Determine the verified remote default via repository metadata. For GitHub CLI, run `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef)`; all repository-scoped `gh` commands, including tracker/PR followups, require this context. Otherwise inspect existing `main`/`master` remote bookmarks, without guessing an absent default. Read `jj bookmark list` and exact `@`/`@-` identities: JJ has no implicit current branch, and an empty `@` above the intended head is normal.

   If no safe feature bookmark is established, create one with `jj bookmark create <feature> -r <verified-head>`. When authorized and a remote default exists, fetch with `jj git fetch --remote origin --branch <default>`. Choose the verified fetched `<default>@origin` only when no local commits would be lost; otherwise retain the verified local head and its visible work. Never move dirty work onto another base, guess an ambiguous target, or rewrite the real default. Re-read bookmark and commit identities after selection; preserve already-invoked feature bookmarks unchanged.

   Otherwise continue on the invoked branch without renaming it or asking. Use a worktree only when the user asked for one this session (`ce-worktree`) or when `references/multi-pr-delivery.md` builds a PR group in its own checkout or session, and commit on the default branch only when the user explicitly authorized that in this session.

   **Pre-work scope.** Before editing, record `jj status`, `jj diff --summary`, local untracked/ignored filesystem inventory, and `jj log -r '<verified-default>@origin..<verified-head>'` for pre-existing local commits (unknown without a verified remote). Nothing in that inventory is yours to commit/publish. Preserve it without stash/reset. Enforce this without asking the user to choose:
   - Incremental commits stage only work-owned files and are path-limited, so untouched WIP never enters a commit; the standalone handoff passes every pre-work file this run did not commit as `exclude:<paths>`, and ships locally via `ce-commit` when pre-existing unpushed commits are on the branch (`references/shipping-workflow.md`).
   - A unit that must edit a file that was already dirty is the one case a commit cannot separate. Ask once, at the first commit that would include such a file, and cover every such file in that one question: commit those files with the user's edits included, or leave them uncommitted (an exclusion for the rest of the run, named in the final summary as unshipped). In Return-to-Caller Mode do not ask and do not edit the file — return `status: blocked` naming it, so the user's WIP stays intact and commit-or-stash-and-rerun is a clean recovery.

3. **Create Task List** _(skip if triage already built one or routed as Trivial)_ — use the platform's task-tracking capability when available (`TaskCreate`/`TaskUpdate`/`TaskList` in Claude Code, `update_plan` in Codex, or the equivalent elsewhere), and follow `references/work-intake.md` for how tasks are derived, named, and ordered. If no such capability exists, continue without simulating a task list in chat.
