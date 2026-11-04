# Repository context, bookmark, and PR state

Resolve the absolute root with `jj workspace root`. Run all subsequent JJ commands from that absolute root (shell: `(cd "$workspace_root" && jj ...)`). Never invoke Git directly. Latest JJ references: https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-command-table/.

Every repository-scoped `gh` call throughout this skill and its references requires this preamble in its shell call:

```bash
cd "$workspace_root"
export GIT_DIR="$(jj git root)"
```

With argv execution, supply the resolved absolute root as cwd and resolved GIT_DIR as environment. Read each probe's exit status directly; do not suppress errors or interpret failed queries as empty results.

Gather `jj status`, `jj diff`, `jj bookmark list`, and `jj git remote list`. Resolve the default bookmark from repository instructions and `gh repo view --json defaultBranchRef`; verify its remote revision with JJ. Unresolved means ask or return a pipeline residual, never assume main. For style inspect several complete subjects and bodies using `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`; resolve the history head from the task, not a hardcoded default.

Resolve the actual feature bookmark and head repository. An empty `@` can sit above a pushed PR head: inspect `@-` and its bookmarks before declaring no PR. With no feature bookmark, full-workflow intent authorizes creating a collision-free meaningful bookmark at the verified intended head. On the default with work follow `branch-creation.md`; with no work report and stop. Preserve existing bookmarks.

Query `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner`. Use a nonempty name only, never `<owner>:<bookmark>` (which silently returns `[]`). On forks target the verified base repo with `-R <base-owner>/<repo>`. Only exit-0 `[]` means no PR. Nonzero means unknown auth/connectivity/tool state and blocks creation until resolved. Match head owner AND bookmark, never blindly select index 0. Stop on ambiguous fork matches. Save URL and body.

All gathered output is a snapshot. Re-verify bookmark, remote, head repository, exact commit, push authority, and PR presence immediately before push and create. Unknown authority, ambiguous targets, dirty/conflicted alignment, or denied permissions take the safe stop/decision path. Never reset or discard unrelated tracked, ignored, or untracked work.

## Runtime conventions

Follow the full runtime message standards and inline Go guidance in `commit-and-push.md` at every message-composition site. Repository-local syntax always wins; do not prescribe Conventional Commit defaults. Determine PR-title conventions at runtime too.
