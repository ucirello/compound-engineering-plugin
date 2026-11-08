# Repository context, bookmarks, and PR state

Resolve the absolute root with `jj workspace root`. Every JJ command must have that root as cwd, never `-R` alone. Run probes separately and inspect their exit statuses. Every repository-scoped `gh` command throughout this skill and all references must run at that root with `GIT_DIR=$(jj git root)`: `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Never invoke the Git executable. See https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/cli-reference/ .

Gather `jj status`, `jj diff`, `jj bookmark list`, and `jj git remote list`. Resolve the actual task history head and examine full recent descriptions as required by `references/commit-and-push.md`. Resolve the base repository default using `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`, then fetch and verify that exact bookmark. If unresolved, ask instead of guessing main.

JJ has no current branch. Identify the intended feature bookmark from the task commit, remote, and PR. An empty `@` may be immediately above the published head: inspect `@-`, its bookmarks, remote and PR before declaring no work or PR. Without a feature bookmark, automatically create a unique one at the verified task head; full workflow intent authorizes this. Default-bookmark work uses `references/branch-creation.md`; no feature work means report and stop. Multiple plausible bookmarks require a decision, not an arbitrary selection.

Query `gh pr list --head <branch> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` only with a nonempty verified bookmark name. Use its name only, never `<owner>:<branch>` which silently returns no results. For forks, target the base repository with `-R <base-owner>/<repo>` where necessary. Only exit-0 `[]` means no open PR; nonzero means unknown tool/auth/connectivity state and blocks creation until resolved.

Match both head owner and bookmark, never blindly select index 0. Preserve the matching URL and body; ambiguous repository/owner matches require a safe stop with candidates. Probes are snapshots: re-verify bookmark, exact commit, remote, head repository and existing PR immediately before push and create.

## Conventions

Read the complete message standards in `references/commit-and-push.md` before composing any change description. Repository instructions and several recent full subjects/bodies determine runtime syntax; this skill imposes no Conventional Commit default. PR titles likewise follow repository conventions and the outcome-focused description reference.
