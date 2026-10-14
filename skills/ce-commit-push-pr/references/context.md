# Repository context, bookmark, and PR state

Resolve the absolute root with `jj workspace root`. Every JJ command must run with that target root as cwd, not merely `jj -R`. Scope every repository GitHub CLI call there with `GIT_DIR=$(jj git root)`, for example `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr list --head "<bookmark>" --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner)`.

Gather individual probes: `jj status`, `jj diff`, `jj log`, `jj bookmark list`, `jj git remote list`. Interpret failures, never suppress them. Resolve the default through `gh repo view --json defaultBranchRef` and verify its remote bookmark; unresolved targets require a question or pipeline residual, not a guessed base.

JJ has no required current branch. Resolve the intended feature bookmark from revision and remote relationships. An empty `@` above a pushed commit is normal: inspect `@-`, its bookmarks, remote branch and associated PR before deciding there is no PR or work. Full workflow authorizes a non-conflicting feature bookmark when needed without another branch-creation approval. Default bookmark with work follows `branch-creation.md`; default with no work reports and stops.

Only exit-0 `[]` against the base repository means no open PR. Failed queries mean unknown and block creation until auth/connectivity is resolved. Never query empty `--head`; use bookmark name alone, not `owner:bookmark`. Forks target the base with `-R`. Match head repository owner and bookmark, never blindly select index zero; uncertain or multiple matches stop with candidates. Keep matching URL/body for preservation.

Snapshots are hints: re-verify bookmark, remote, head repository/commit, authority and PR state before each external write. Message style comes from project instructions and several recent complete messages, with compatible Go guidance in `commit-and-push.md`; no fixed Conventional Commit default applies.
