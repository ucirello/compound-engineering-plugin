# Repository context, bookmark, and PR state

Resolve the target workspace's absolute root with `jj workspace root`; run every subsequent JJ command from that root, using shell `(cd "$workspace_root" && jj ...)` or subprocess `cwd=workspace_root`. File lists are repository-relative. For every repository-scoped GitHub command, obtain and export `GIT_DIR=$(jj git root)` in that same workspace before running `gh`; explicit `-R <base-owner>/<repo>` selects the base repository for fork PR queries. Read each command's exit status; failure is not absence.

Gather `jj status`, `jj diff`, `jj bookmark list`, `jj git remote list`, and `jj log -r '@ | @-'`. Resolve the actual feature bookmark, head repository, remote, and commit, not a Git checkout branch. `@` can be an empty working-copy change directly above the pushed PR head: inspect `@-` and its bookmarks/remote/PR before concluding no PR exists. Multiple bookmarks require verified selection, not a guess.

Read recent commit subjects AND bodies from the read-only backend: `(cd "$workspace_root" && GIT_DIR=$(jj git root) git log -10 --format=%B)`. Apply the runtime composition standards in `references/commit-and-push.md`.

Resolve the default bookmark from `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`, verifying its remote bookmark after fetch. Do not silently guess an unresolvable base. Query `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` only with a verified nonempty bookmark name. Pass the name alone, never `<owner>:<bookmark>` (that silently returns `[]`). Match both head owner and bookmark; do not blindly take index 0. Ambiguous matches stop with candidates. Exit-0 `[]` means none; nonzero means unknown auth/connectivity/tool state and blocks creation until resolved.

No feature bookmark, or work on the default bookmark, authorizes creation of a nonconflicting feature bookmark without another approval under the full workflow. Default bookmark with no work reports and stops. Follow `references/branch-creation.md`; preserve existing user bookmarks. Re-verify bookmark, remote, exact commit and PR presence immediately before push/create: collected context is only a snapshot.

Project instructions and observed repository history determine commit and PR-title syntax. No fixed Conventional Commit fallback is imposed.
