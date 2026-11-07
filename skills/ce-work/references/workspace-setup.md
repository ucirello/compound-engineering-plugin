# Workspace Setup

Read before implementation writes or dispatch. Verify a writable JJ workspace with `jj root`, then run every JJ and repository-scoped command with cwd set to that absolute root (never `jj -R`, never the Git executable). Native `jj git` and `jj diff --git` are permitted. See https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/cli-reference/ . If no writable workspace exists, report the limitation rather than synthesize edits in scratch.

Read the plan via work-intake.md; clarify unresolved scope before building. Do not use plan body checkboxes as execution state. Record task progress in JJ revisions, receipts and the task tracker.

## Base, bookmark and pre-work scope

Inspect `jj status`, `jj diff`, `jj bookmark list --all-remotes` and the relevant exact revision history. Inventory ignored and untracked files separately; snapshots do not protect them. Record existing dirty paths, conflicts and pre-existing unpublished commits. They are not owned or publishable by this run. Never reset, discard or stash them implicitly. Resolve the default from repository metadata, not a guessed hardcoded main. For GitHub CLI use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh repo view --json defaultBranchRef)` and apply that environment to every repository-scoped gh call. Fetch with native `jj git fetch` only within authorization. Preserve local and PR/source bookmarks and exact base evidence.

Reuse an existing feature bookmark and verified isolation unchanged. If the current change is on the default, create a task bookmark on a verified safe revision, keeping pre-existing local work visible and excluded from publication. Unknown/dirty/conflicted base alignment is a safe stop, never a discard. Incremental revisions contain only owned paths; pass all untouched or leave-uncommitted pre-work paths as shipping exclusions. Pre-existing unpublished commits select local-only ce-commit unless separately authorized. If a unit must touch an already-dirty file, ask once before including the user's edits; return-to-caller must instead block before editing it.

## Isolation

Ordinary synchronous work stays in the active workspace. Detect existing isolation first and respect harness lifecycle ownership; never recreate/rename it merely for naming or colocation. Use ce-worktree only when requested or required for independent concurrent work/group sessions. New names, including caller-selected names, are `YYYYMMDD-meaningful-kebab-slug`: capture local date once, retain across retries/resume/midnight, derive slug from task/PR/revision, normalize without double date prefix, and use exactly the destination basename. Example: `20261008-pr-214`. Check both registrations and destinations; deterministic collisions append `-2`, `-3`, never timestamps, PIDs or random suffixes.

Use an absolute run-owned destination under the verified workspace's `.tmp/rocketclaw/` parent and a verified exact base:

```sh
(cd "$workspace_root" && jj workspace add --colocate --name "<name>" --revision "<verified-base>" "<absolute-owned-destination>")
(cd "$new_workspace_root" && jj git colocation status)
```

Adopt the new root in the active session before writes. Harness-native isolation must support explicit colocation, required naming and verified base; unsupported capability is a compatibility blocker, not permission to bypass ownership.

## Guarded cleanup

Completion is not deletion authorization. Stop workers, leave the target and move the active harness session to a surviving absolute root first. Verify exact registration/name/path, run ownership and explicit disposal authority. Prove integration when required, retain recovery/best/archive bookmarks, and copy then read back needed receipts outside the target. Inspect tracked/conflicted/ignored/untracked content. Never delete unrelated, ambiguous, referenced or non-disposable work. Respect harness cleanup authority.

Only after all evidence and safety checks, use `(cd "$surviving_workspace_root" && jj workspace remove "<verified-name>")`. `forget` is unregister-preserve-files only, never a prelude to filesystem deletion. Verify deregistration AND directory disappearance; warnings or partial failure require preserving/reporting state, never force deletion or Git cleanup. Bookmark deletion is separately authorized.

Create the task list through native tracking when available; otherwise proceed without simulating one in chat.
