# Repository context, bookmark, and PR state

Resolve the absolute workspace root with `jj root`. Run commands with cwd set to that absolute root, never `jj -R`. Never invoke the Git executable, including helpers or fallbacks. Native `jj git` and Git-format data are allowed. For every repository-scoped `gh` call set `GIT_DIR=$(jj git root)` in that workspace; use `-R <base-owner>/<repo>` for the verified base repository on forks. Capture each probe's exit status separately.

Inspect `jj status`, `jj diff`, `jj bookmark list --all-remotes`, `jj git remote list`, and exact revision IDs with `jj log`. Resolve the base from task/PR metadata or `gh repo view --json defaultBranchRef`; from the absolute workspace root verify its remote bookmark after `jj git fetch --remote "<verified-remote>" --branch "exact:<verified-base>"`. Substitute verified values without shell evaluation; use the exact branch selector, never a guessed pattern. Never guess a default base. Inspect ignored/untracked content as well as tracked/conflicted work before operations that could affect it.

Identify the intended feature bookmark, exact commit, owner and push remote. An empty `@` directly above the pushed PR head is already aligned: inspect `@-` and its bookmarks before concluding there is no work or PR. An absent bookmark with authorized feature work calls for a new bookmark, not a detached-HEAD operation. Never push the default bookmark directly. Unpushed default-base ancestry requires the decision in `branch-creation.md`; no work means report and stop.

Query `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` only with a nonempty bookmark name. Pass the name only, not owner:name; query the base repository. Only exit-0 `[]` means no PR. Nonzero is unknown: resolve auth/connectivity and stop until known. Match head owner and name, never blindly index 0; ambiguity stops and shows candidates. Preserve the matching URL and authored body.

Probes are snapshots. Reverify exact head commit, bookmark, remote, owner, base repository and PR state immediately before pushing or creating. Unknown push authority or dirty/conflicted/ambiguous alignment is a safe stop; preserve all work, never reset/discard/guess.

Before every message-composition site, including stack layers, archival and PR titles that may become squash messages, follow the full runtime Go/history comparison in `commit-and-push.md`. User/project syntax and observed repository history win; no invented default type/scope/template.

Native JJ documentation: https://docs.jj-vcs.dev/latest/git-experts/ , https://docs.jj-vcs.dev/latest/git-command-table/ , https://docs.jj-vcs.dev/latest/cli-reference/ .
