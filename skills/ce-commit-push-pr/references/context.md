# Repository context, bookmarks, and PR state

Resolve the absolute workspace root with `jj workspace root` from the known absolute target directory. Every subsequent JJ subprocess uses that absolute root as cwd, including `jj git root`: shell `(cd "$workspace_root" && jj ...)`, or a tool's explicit cwd. No direct Git executable calls. See https://docs.jj-vcs.dev/latest/git-experts/, https://docs.jj-vcs.dev/latest/git-command-table/, https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/cli-reference/#jj-workspace.

Gather `jj status`, `jj diff`, `jj bookmark list`, and `jj git remote list` from that root. Resolve the intended feature bookmark, remote, head repository and exact committed head; JJ has no checked-out branch. An empty `@` directly above the verified PR head is already aligned. Inspect `@-` and its bookmarks/remote/eligible PR rather than treating an empty `@` as no work.

Every repository-scoped gh operation in this skill and ALL references runs from this root with `GIT_DIR` obtained there: `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh <arguments>)`. This preamble applies to every abbreviated gh example, including stack metadata, browse, auth and PR calls. Read exit status directly; errors are never empty results.

Resolve the default bookmark from verified remote metadata and `gh repo view --json defaultBranchRef`; unknown base means ask or return a pipeline residual, not guess. A head without a suitable feature bookmark, or the default bookmark with work, creates a feature bookmark through `references/branch-creation.md` without asking whether to branch. Default bookmark with no work reports and stops. Do not rename existing PR/source bookmarks.

Query `gh pr list --head <feature-bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRefOid,headRepositoryOwner` against the base repository (`-R <base-owner>/<repo>` for forks). Pass only the bookmark name, never owner:name or an empty name. Only exit-0 `[]` means no PR; nonzero means unknown authentication/connectivity/capability and blocks creation. Match owner AND bookmark, then verify the exact head commit. Never blindly take index 0; ambiguity stops with candidates. Capture the URL and body for preservation. Re-verify repository, bookmark, remote, commit and PR immediately before each push/create/edit/handoff; snapshots are not authority.

## Conventions

Before composing or validating a message, follow the full runtime standards and verbatim source guidance in `references/commit-and-push.md`. Repository instructions and several full historical subjects/bodies determine syntax, not a fixed Conventional Commit default. PR titles follow observed project conventions and outcome scope.
