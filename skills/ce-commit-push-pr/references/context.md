# Repository context, bookmarks, and PR state

Run every JJ operation with cwd set to the target workspace's absolute root, obtained with `jj workspace root`. Never invoke Git directly. See https://docs.jj-vcs.dev/latest/git-command-table/ and https://docs.jj-vcs.dev/latest/cli-reference/ . Probe exit statuses individually; failures are unknown state, not empty results.

For every repository-scoped gh invocation, use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`, including all examples in these references. In argv-based execution, first obtain `jj git root` with that cwd, then set GIT_DIR in the gh process environment. Do not leak repository environment to unrelated repositories.

Gather `jj status`, `jj diff`, `jj bookmark list`, `jj git remote list`, and recent full descriptions with `jj log --no-graph -r '::<verified-history-head>' -n 10 -T 'description ++ "\n"'`. Resolve the actual task's history head, not an assumed default bookmark. Identify the intended local bookmark and its tracked remote target; JJ does not have a checked-out branch. An empty `@` above the verified pushed head is already aligned: inspect `@-` and its bookmarks and PR before deciding there is no work.

Resolve the default branch using `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`; verify the corresponding remote bookmark after `jj git fetch --remote <remote> --branch <base>`. If unresolved, stop or ask; never guess a base.

## Step 1: resolve bookmark and PR state

- No feature bookmark, or default bookmark with work: create a collision-free meaningful feature bookmark automatically. Workflow intent authorizes this; never ask whether to branch. Follow `branch-creation.md` for default-base decisions.
- Default bookmark with no local or unpublished work: report and stop.
- Existing feature bookmark: verify its exact target, remote, and push authority and continue.

Query `gh pr list -R <base-owner/repo> --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner`. Pass the branch name only, never owner:branch. Skip an unresolved/empty head filter. Exit-0 `[]` alone means no PR; nonzero means unknown (resolve authentication/connectivity before creating). Match both head owner/repository and name, not index zero; ambiguous candidates require a safe stop. Record the matching URL and body for composition and handoff.

Snapshots are not authority: reverify bookmark, remote, repository, exact commit and PR immediately before pushing or creating. Preserve unrelated tracked, ignored, and untracked work. Dirty/conflicted state, uncertain targets, denied tools, and unknown push authority use the safe decision path, never reset/discard.

## Step 2: conventions

Read `commit-and-push.md`'s complete message standard before composing any change description or title intended to become one. Project instructions and observed full JJ descriptions determine syntax at runtime, not a fixed Conventional Commit default.
