# Repository context, bookmark, and PR state

Read the [JJ command table](https://docs.jj-vcs.dev/latest/git-command-table/) and [bookmark semantics](https://docs.jj-vcs.dev/latest/bookmarks/). Use JJ, never the Git executable. Run JJ from the target workspace's absolute root (resolve it with `jj workspace root`, then use the tool's working-directory field; `-R` does not change directories). Run repository-scoped `gh` from that root with `GIT_DIR=$(jj git root)`. In an argv-oriented runner obtain `jj git root` separately, require success and a nonempty path, then set `GIT_DIR` in the `gh` call's environment. Do not substitute a guessed `.git` path. These rules also apply to all examples and fallbacks in the references.

## Step 1: Gather facts and resolve the feature bookmark

Run probes separately and inspect their exit statuses. Treat output as a snapshot; re-verify before publication or PR creation.

| Probe | Resolve |
| --- | --- |
| `jj status`, `jj diff --summary` | Working-copy change, parents, current changes and conflicts; also inspect ignored/untracked filesystem paths separately before a tree-changing operation. |
| `jj log -r '@ \| @-'` | Full IDs for `@` and its parents; an empty `@` directly above a single parent commonly means the parent is the actual head. |
| `jj bookmark list -r '@ \| @-' --all-remotes` | Candidate local and tracked remote bookmarks. With no exact candidate, inspect history for the intended compatible feature ancestor; do not guess from distance or default remote. |
| `jj git remote list` | Verify the repository identities, hosts and candidate remotes for base and head independently. |
| `gh repo view -R <base-repo> --json defaultBranchRef --jq '.defaultBranchRef.name'` | Authoritative default branch for the base repo. If unavailable, resolve `trunk()` only when it is verified to represent the intended remote default; otherwise ask, or stop in pipeline mode. Never assume `main`. |
| `gh pr list -R <base-repo> --head <branch> --state open --json number,url,title,body,state,isDraft,headRefName,headRefOid,headRepository,headRepositoryOwner` | Open PR candidates for the feature bookmark. Exit 0 with `[]` means none; non-zero is unknown. |

Always pass the branch name only to `--head`; `<owner>:<branch>` can return a false empty list, and an empty branch drops the filter. Query the base repository even when pushing to a fork. Match the head **repository**, owner, and branch, not index 0; fail closed on ambiguity or incomplete identity. Record the URL, body, and exact head OID. Resolve unknown auth/connectivity before acting; do not equate a failed probe with absence.

- **Feature bookmark** — continue if the intended bookmark, its exact target, the head repository, and the remote are unambiguous. For new commits above an existing bookmark, prove the bookmark is an ancestor and the entire additional range belongs to this publication. Do not choose between competing bookmarks by convention.
- **Default bookmark with work** — create a feature bookmark using `references/branch-creation.md`; never push the default directly.
- **No feature bookmark** — if authorized work exists on an unbookmarked change or series, create a non-colliding feature bookmark at its intended committed tip, as described in `references/commit-and-push.md`. Full workflow intent authorizes naming the work; don't ask just whether to create the bookmark.
- **Default without feature work** — report and stop. An empty `@` above a published feature tip does not mean this case applies: inspect `@-` and resolve its PR.

## Step 2: Conventions

Resolve the workspace and exact task history anchor, then follow `references/commit-and-push.md` for all commit composition. PR-only title and body conventions are in `references/pr-description-writing.md`.
