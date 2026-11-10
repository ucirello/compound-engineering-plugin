# Repository context, bookmarks, and PR state

Resolve `workspace_root` with `jj root`, then run every repository command with that absolute root as cwd. Never use a repository flag as a cwd substitute. Before repository-scoped `gh`, export `GIT_DIR=$(jj git root)` from that workspace. Never invoke the underlying Git executable, even for read-only probes or fallback.

Gather separate probes and preserve exit status: `jj status`, `jj diff`, `jj bookmark list --all-remotes`, `jj git remote list`, and `jj log --no-graph -r '@ | @-'`. Resolve the publishing bookmark and head from actual graph and remote state. Empty `@` above the verified PR head is aligned, not new work. Dirty, conflicted, divergent, ambiguous, or unauthorized heads require a safe stop without discarding work.

Resolve base repository and default bookmark through `gh repo view --json nameWithOwner,defaultBranchRef`; verify against the selected JJ remote. Never guess a default name. Fetch with `jj git fetch --remote <verified-remote> --bookmark <base>` and verify the fetched revision. No feature bookmark plus actual work takes `branch-creation.md`; no work reports and stops. Preserve existing PR/source bookmark names.

For a nonempty verified head bookmark, query `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner`. On forks target the base repository with gh's `--repo`; pass only the bookmark name to `--head`, never owner:name. Only exit-0 `[]` means no PR; errors mean unknown and block creation. Select by both head owner and bookmark, never index zero. Stop on ambiguity. An absent bookmark must not become an unfiltered query.

Reverify workspace, bookmark target, remote, permission, and PR state before push/create. Prior output is a snapshot.

## Step 2: conventions

Read `commit-and-push.md`'s runtime composition contract before any commit or PR title, including archival and stack commits. Active project instructions and several recent full messages determine syntax; Go is guidance, not a fixed conventional-commit default. Preserve semantic intent: when conventional types apply, repairs are fixes rather than new capabilities. Never invent a breaking-change marker.
