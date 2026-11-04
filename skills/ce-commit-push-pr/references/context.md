# Repository context, bookmarks and PR state

Run JJ with cwd set to the target workspace's absolute root, resolved with `jj workspace root`; `jj -R` is not a cwd substitute. Before every repository-scoped `gh` call export `GIT_DIR=$(jj git root)` there. These rules cover all references and examples. Never invoke the Git executable. See https://docs.jj-vcs.dev/latest/git-command-table/ and https://docs.jj-vcs.dev/latest/cli-reference/ .

Gather `jj status`, `jj diff`, `jj bookmark list`, and `jj git remote list` separately and interpret their exit statuses. Resolve the actual task head, feature bookmark and head repository. Inspect both `@` and `@-`: an empty `@` directly above the pushed commit is normal and does not mean no work or PR. Multiple plausible bookmarks require a decision rather than a guess.

Resolve the default branch with `gh repo view --json defaultBranchRef` and verify its remote bookmark. If unresolved, ask or stop in pipeline mode, never assume `main`. Query only a nonempty branch name:

```bash
gh pr list --head <branch> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner
```

Pass the branch name only, never `<owner>:<branch>`. On forks target the verified base repository with `-R <base-owner>/<repo>`. Only exit-0 `[]` means no PR; non-zero means unknown, requiring auth/connectivity resolution before create. Match head owner/repository and branch, never blindly index 0. Show ambiguous candidates and stop. Record the matching URL/body for composition and apply.

No feature bookmark, or default bookmark with work: derive a non-conflicting feature name without asking again; full-workflow intent authorizes this. Follow `branch-creation.md` for safe base selection. No feature work: report and stop. Reverify head, bookmark, remote, push authority and existing PR immediately before push and create.

Before composing any commit or recommending a title, follow `commit-and-push.md`'s runtime message standards. Project instructions and several full historical subjects AND bodies establish syntax; never assume Conventional Commits.
