# Repository context, bookmark, and PR state

Resolve the absolute target workspace root with `jj workspace root`. Run every JJ command from that absolute root (shell `cd` or subprocess `cwd`), not merely with `-R`. Every repository-scoped `gh` call in this skill and all references must run from that root with the exported context below:

```bash
cd "$workspace_root"
export GIT_DIR=$(jj git root)
```

Keep probes separate and interpret exit statuses; never suppress errors or invoke Git directly. See https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/git-command-table/.

Gather `jj status`, `jj diff --git`, `jj bookmark list --all-remotes`, and `jj git remote list`. Resolve the actual work head and intended feature bookmark. If `@` is empty, inspect `@-` and its bookmarks, remote, and PR before deciding there is no work. Ambiguous bookmarks or repository ownership require a safe stop.

Resolve the remote default using scoped `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`, project instructions, and verified remote bookmarks. If unresolved, ask; pipeline mode reports a blocker. Never assume a default branch.

Query `gh pr list --head <branch> --state open --json number,url,title,body,state,isDraft,headRefName,headRefOid,headRepositoryOwner` only after resolving a nonempty bookmark name. Pass the branch name alone, not `<owner>:<branch>`. On forks target the base repository with `-R <base-owner>/<repo>`. Exit-0 `[]` means no open PR; errors mean unknown, never none. Match head owner, bookmark and exact commit; never blindly select index 0. Stop and show ambiguous candidates. Preserve the matching URL and body.

## Step 1: Resolve the feature bookmark

Unbookmarked work automatically gets a meaningful collision-free feature bookmark at the verified work head with `jj bookmark create <branch-name> -r <verified-work-head>`. The full workflow authorizes this; do not ask again. Default-bookmark work follows `branch-creation.md`, never pushes the default directly. No work on the default reports and stops. Existing feature bookmarks continue without renaming.

Re-verify repository, bookmark, remote, commit and PR immediately before each push or create. Context is a snapshot, not authority.

## Step 2: Conventions

Before composing messages or titles that become messages, follow the complete runtime standards in `commit-and-push.md`: read the full Go guide and several full subjects and bodies at the verified relevant history head. Project instructions and observed local syntax always win; never impose a Conventional Commit default.
