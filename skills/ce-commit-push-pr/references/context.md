# Repository context, bookmarks, and PR state

Run every JJ command with cwd set to the target workspace's absolute root, not merely `jj -R`: `(cd "$workspace_root" && jj ...)`. Resolve the root using `jj workspace root`. Every repository-scoped GitHub call uses `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`; additionally use `-R <base-owner>/<repo>` for fork PRs. Inspect each exit status.

Gather `jj status`, `jj diff`, `jj log -r 'ancestors(@, 10)'`, `jj bookmark list`, and `jj git remote list`. Identify the intended bookmark, remote bookmark, exact revision and head repository/owner. JJ has no checked-out branch. An empty `@` directly above the pushed head is normal: inspect `@-` and its bookmarks/PR before deciding there is no work or PR.

Resolve the default through scoped `gh repo view --json defaultBranchRef`; verify its remote bookmark after `jj git fetch --remote <remote>`. Unknown targets stop the run; never guess a base.

Query scoped `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner,headRepository`. Pass only the bookmark name, never `owner:bookmark`; target the base repository on forks. Exit-0 `[]` means none; a non-zero result means unknown (resolve auth/connectivity before creating). Match head owner, repository and bookmark, never index zero blindly; ambiguous matches require a safe stop. Save the matching URL and existing body.

## Step 1: resolve publishing identity

No feature bookmark, or default bookmark with work: derive a non-conflicting feature bookmark from the change and create it at the verified intended revision with `jj bookmark create <name> -r <revision>`. Full shipping intent authorizes this; do not ask again. Never publish directly to the default bookmark. Default bookmark with no work reports and stops. Preserve unrelated bookmarks and work. Read `branch-creation.md` when selecting a new base.

Re-verify bookmark, remote, repository, exact revision and matching PR immediately before pushing or creating. Context is only a snapshot.

## Step 2: conventions

Read project instructions and `commit-and-push.md` before composing a change description. Determine syntax at runtime from several recent subjects AND bodies, not a fixed Conventional Commit default. PR titles follow observed project conventions and describe the complete outcome.
