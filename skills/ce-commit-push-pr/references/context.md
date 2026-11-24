# Workspace, bookmark, and PR state

Resolve the absolute workspace root with `jj workspace root`. Stop if there is no JJ workspace. Run every later JJ command from that absolute root, not from the launch directory or with `jj -R` as a substitute. See the [JJ command reference](https://docs.jj-vcs.dev/latest/cli-reference/) and [bookmark guide](https://docs.jj-vcs.dev/latest/bookmarks/).

Run probes separately and inspect each exit status. Every repository-scoped `gh` call in this skill (including references, rechecks, and recovery) uses this scope:

```bash
(cd "$workspace_root" && repo_git_dir="$(jj git root)" && export GIT_DIR="$repo_git_dir" && gh …)
```

With an argv shell interface, resolve `jj git root` separately and pass that value in the `gh` environment with the same absolute CWD. Use the verified host and base repository on PR queries (`-R <host>/<owner>/<repo>` or the full PR URL as supported; explicit host and repository path for `gh api`). Do not assume the PR base and push remote are the same repository.

## Step 1: Resolve bookmark and PR state

Run `jj status` and `jj diff --summary -r @`; check for conflicts. Inspect `jj log --no-graph -r '@ | parents(@)'` and `jj bookmark list --all-remotes`. A JJ bookmark isn't automatically the current branch: identify the intended bookmark from the invocation or from the verified feature lineage and its tracking bookmark. An empty `@` directly above the head is normal; inspect its parent before deciding there is no branch, no push, or no PR. An ordinary nonempty `@` above the feature bookmark is pending work; don't publish it until its owned paths are committed. Stop on competing plausible targets, divergent bookmarks, multiple unexplained parents or unrelated work in the candidate history. Do not select the closest bookmark by name alone.

Use `jj git remote list` to verify the push and base remotes against their repository identities. Resolve the default branch from project context or scoped `gh repo view -R <base-repo> --json defaultBranchRef --jq '.defaultBranchRef.name'`; verify its matching remote bookmark before using it. When necessary, check the candidate defaults `main`, `master`, and `develop` on that verified base remote. If the target is still unproven, ask only where a user can resolve it; pipeline reports a blocker. Never push the default branch.

For a known head bookmark, run scoped `gh pr list -R <base-repo> --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner`. Pass the branch name only: an empty name drops the filter, and `<owner>:<branch>` silently returns `[]`. Verify the full head repository, branch, and SHA for a candidate via `gh pr view <url>` or the corresponding PR API. Do not pick index zero when different forks share the branch name. An exit-0 `[]` on the base repo is "no open PR"; a nonzero exit is unknown, not permission to create. If the query returns other heads only, require positive verification that none matches the intended repo and branch before creating. When given an explicit PR ref, resolve that exact PR directly instead of discovering it from the workspace.

Description modes do not create or move bookmarks. Full mode automatically creates a collision-free feature bookmark when the only bookmark is the default and there is work, or when there is unpublished work on an unbookmarked change. Default-branch work follows `references/branch-creation.md`; for otherwise unbookmarked work verify the exact parent/lineage before naming it in Step 3. If there is no feature work, report and stop. Immediately before any push or PR create, re-verify the current JJ revision, local and remote bookmarks, PR target and open-PR state; a probe is only a snapshot.

## Step 2: Conventions

Use the commit guidance in `references/commit-and-push.md` at every message-composition site. PR titles have their own policy in `references/pr-description-writing.md`; the PR content range is never a substitute for the recent-history style sample, or vice versa.
