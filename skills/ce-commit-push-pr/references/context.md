# Repository, bookmark, and PR context

Resolve the absolute target `workspace_root` using `jj workspace root`. Every JJ command, including probes, runs with that absolute root as cwd: `(cd "$workspace_root" && jj ...)`. Never invoke the Git executable. For every repository-scoped gh command, obtain `git_dir` with `(cd "$workspace_root" && jj git root)` and pass `GIT_DIR="$git_dir"` in its environment. Run commands separately and interpret each exit status; failed authentication or connectivity means unknown, never absence.

Gather `jj status`, `jj diff --git`, `jj bookmark list --all-remotes`, `jj git remote list`, and exact commit IDs for `@` and `@-`. A bookmark is not an implicit current branch. Explicitly select the intended publishing bookmark, remote and repository; preserve other bookmarks. If `@` is empty above an exact PR head, inspect `@-`'s bookmarks, remote branch and associated PR before claiming no work or no PR. This is already aligned when repository, bookmark, remote and commit all match.

Resolve the default branch from `gh repo view --json defaultBranchRef`; verify its remote bookmark after `jj git fetch --remote <remote> --branch <base>`. Never guess a default or substitute another ref on failure. With no feature bookmark and work to publish, create a unique task-derived bookmark at the verified intended commit with `jj bookmark create <bookmark> -r <verified-commit>`; workflow authorization already permits this. Default-branch publication is unsupported. With no work, report and stop.

Query `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner`. Never query an empty head; pass the branch name only, not owner:branch. On forks explicitly target the base repository with `-R`. Only an exit-0 `[]` proves absence. Match head owner AND bookmark, never blindly select index 0; ambiguous candidates require a safe stop. Retain the exact URL and body. Re-verify repository, bookmark, remote, commit and PR immediately before push/create.

## Message and title conventions

Read the full https://go.dev/wiki/CommitMessage guide, then compare several recent full subjects AND bodies from the actual relevant verified runtime history head:

```bash
(cd "$workspace_root" && jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"')
```

Analyze prefix/package, case and tense, subject/body separation, wrapping and issue placement. Project instructions and observed history syntax always win; apply compatible Go quality guidance. Without history use project/user instructions and Go guidance, never invented precedent. Read the SOURCE GUIDANCE in `commit-and-push.md` before composing or validating any message or title. No fixed conventional-commit syntax or fallback is prescribed.
