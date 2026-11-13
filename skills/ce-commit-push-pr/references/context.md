# Repository context, bookmarks, and PR state

Resolve the absolute target root with `jj workspace root`. Run every subsequent JJ command with that absolute root as its working directory. Never invoke the Git executable, including history, transport, or fallback paths. Use the latest JJ; authoritative command documentation is https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-command-table/.

For **every repository-scoped gh call in this skill and its references**, use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`, or obtain the value there and supply it in the command environment with the same absolute cwd. This includes stack metadata, fallback, browser-link, authentication, and error-recovery calls. Preserve exit statuses; do not suppress failures. All temporary files and error captures belong under `$workspace_root/.tmp/`; ensure `.tmp/` is ignored.

Gather `jj status`, `jj diff`, `jj bookmark list`, `jj git remote list`, and the actual task head's full descriptions as required by `commit-and-push.md`. There is no current Git branch in JJ: resolve the intended bookmark and exact commit from task intent, local/remote bookmarks, and PR metadata. An empty `@` directly above the published head is already aligned; inspect `@-` before concluding there is no PR.

Resolve the default branch through repository instructions and `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`, then verify its remote bookmark. Do not guess a base. Unknown or ambiguous targets stop the consequential action.

For a nonempty confirmed head bookmark query `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner`. Empty head names must never reach this query. On a fork, target the base repository with `-R <base-owner>/<repo>` and pass the branch name only, not `owner:branch`. Only exit-0 `[]` means no open PR; any nonzero exit means unknown, not none. Resolve authentication/connectivity before create.

Match results by verified head repository owner AND head bookmark; never blindly select index zero. Preserve the matching URL and body. Ambiguity requires the safe decision path, not a guessed PR.

An unbookmarked change, or work on the default bookmark, automatically gets a nonconflicting feature bookmark derived from the work; full shipping intent already authorizes this. Use `branch-creation.md` for default-base decisions. No work on the default reports and stops. Reverify bookmark, repository, remote, exact head and PR state immediately before push or create: gathered context is only a snapshot.

## Conventions

Read project instructions and compare several full recent descriptions at the actual verified task history head, following `commit-and-push.md`. Repository-local message syntax wins. Do not impose a Conventional Commit default or infer syntax from the Go example. PR titles also follow the project's actual conventions.
