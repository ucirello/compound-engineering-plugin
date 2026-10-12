# GitHub stack semantics for JJ-managed layers

JJ owns local changes, bookmarks, topology and workspace state. Do not run `gh stack checkout`, `init`, `add`, `top`, or `submit`: those operate on Git checkout/index state rather than JJ's working copy. Use `references/stack-submit.md` for equivalent native construction and publication.

Run all JJ commands from the target workspace's absolute root. Export `GIT_DIR=$(jj git root)` in that root before repository-scoped `gh`; select the base repo explicitly for forks. `gh stack <command> --help` is authoritative for supported GitHub-only operations. Missing stack support is a required-intent blocker or soft-intent residual, never proof of a standalone parent.

`gh pr view <parent> --json headRefName,headRefOid,author,baseRefName,headRepositoryOwner` identifies a parent. A name alone is insufficient: verify repository and exact commit, and stop on stale/colliding bookmarks instead of resetting them. Resolve parent PR numbers preferentially; branch-only parents have no proven PR ownership and can serve only as an untouched trunk.

GitHub-only `gh stack link` is appropriate for JJ-managed branches if supported by this repository: unlike local Git stack construction it does not create local tracking. Do not claim `gh stack view` or `submit` now manages those JJ layers. Verify the explicit ordered PR chain with each PR's actual base/head metadata; unsupported stack linking remains a disclosed coverage residual.

Never land a managed stack with `gh pr merge`. Landing belongs to `ce-babysit-pr` under explicit `posture:stack-land` or to the user, using the supported stack landing path. This reference grants no merge authorization.

JJ sources: https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/cli-reference/ .
