# Repository context and PR state

Resolve `workspace_root` using `jj root` to the absolute target workspace. Every JJ command runs with that absolute cwd, never merely -R. Every repository-scoped gh invocation in this skill and its references, including probes, help, retries and stack commands, MUST use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`. Never invoke the Git executable, including through helpers.

Gather `jj status`, `jj diff`, `jj bookmark list --all-remotes`, `jj git remote list`, and `jj log`. Resolve actual work revision, intended bookmark, remote, head owner, and base repository. An empty working revision directly above a pushed head is normal: inspect `@-`, its bookmarks and PR before concluding none exists. Ambiguous bookmarks require a safe decision.

Resolve default branch via scoped `gh repo view --json defaultBranchRef`, then fetch and verify that exact remote bookmark with `jj git fetch --remote <remote> --branch <base>`. Never guess main or substitute another ref. Failed metadata/authentication/ref resolution is unknown, not absence.

Query scoped `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner`. Pass a nonempty name only, not owner:name; target the base repo with -R for forks. Only exit-0 [] means no open PR. Match head owner AND bookmark, never blindly index zero. Preserve URL and body. Re-verify repository/bookmark/remote/exact revision/PR before push or create.

Full workflow intent authorizes a feature bookmark when none exists or work is on default; read branch-creation.md. Default without unpublished work stops. Project instructions and several recent full subjects AND bodies determine syntax; no fixed conventional-commit fallback. Read commit-and-push.md before every composition, including archival and stack layers.
