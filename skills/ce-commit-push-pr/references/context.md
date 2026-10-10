# Repository context, bookmarks, and PR state

Run probes from the target absolute workspace root and export `GIT_DIR` obtained there from `jj git root` for all repository-scoped `gh`. Preserve repo-relative paths. Interpret exit status directly; do not suppress failures.

| Probe | Purpose / failure handling |
| --- | --- |
| `jj workspace root` | Absolute root; outside JJ report and stop |
| `jj status`, `jj diff` | Changes/conflicts; preserve unrelated work |
| `jj bookmark list`, `jj log -r '@ | @-'` | Intended local/remote bookmark and exact tip; empty `@` over pushed head is normal |
| `GIT_DIR=$(jj git root) git log -10 --format=%B` | Read-only backend history: compare several subjects AND bodies before composition |
| `jj git remote list` | Verified base/head repositories and remotes |
| `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` | Resolve default base; if unavailable inspect verified remote bookmarks, otherwise ask/report residual, never guess |
| `gh pr list --head <bookmark> --state open --json number,url,title,body,state,isDraft,headRefName,headRepositoryOwner` | Only query verified nonempty head name; exit 0 `[]` means none, failure means unknown |

On forks target the base repo with `-R <base-owner>/<repo>`; pass only the head bookmark name, not `<owner>:<bookmark>` (which can return a misleading empty array). An empty `--head` drops filtering; skip until resolved. Match confirmed head owner/repository and bookmark, never index 0 blindly. Multiple plausible candidates require a safe stop with their URLs. Preserve URL/body for application.

Snapshots are hints: immediately before pushing or creating, re-verify root, remote, bookmark, exact commit, and PR presence. Unknown auth/connectivity/permission is not evidence of no PR or push authority.

## Feature identity

Full shipping intent authorizes a collision-free feature bookmark when none exists. On the default bookmark with work, follow `branch-creation.md`; no extra routine branching approval. Default with no work reports and stops. Never move default/unrelated bookmarks to publish. Multiple plausible feature bookmarks require a decision.

Before concluding there is no PR because `@` is empty, inspect `@-`, its bookmarks, remote head and PR. Continue eligible babysitting. An empty `@` directly above the exact verified pushed head is already aligned.

## Runtime conventions

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards.

Before composing, validating, or recommending messages/titles, read `commit-and-push.md`, the full https://go.dev/wiki/CommitMessage, and recent complete subjects AND bodies. Compare several for prefix/package, case, tense, separation, wrapping, and issue placement. Repository instructions and history always win syntax differences; no history means project/user instructions plus compatible Go guidance, not invented precedent.
