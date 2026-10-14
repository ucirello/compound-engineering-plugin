# Stack CLI boundaries for JJ-managed layers

Read `gh stack <command> --help` as authoritative before relying on its semantics. Run all repository `gh` calls from the target absolute root with exported `GIT_DIR=$(jj git root)`. JJ owns revisions, bookmarks, ancestry and working-copy state; do not use Git-oriented `gh stack checkout`, `init`, `add`, `top` or `submit` to mutate them.

Use `gh stack view --json` only as metadata when available; its reported base is a recorded parent SHA, not necessarily the parent's latest tip. Do not infer order from array ordering or an undocumented top field. Verify every layer's immediate parent and exact head with JJ and PR metadata.

For external JJ-managed layers, `gh stack link` is GitHub-only, not local tracking. Use it only when its actual help and repository capability support the desired relationship; never assume it creates local managed-stack state or makes subsequent local submit/view/merge discover layers. If the required topology or landing capability cannot be verified, return a residual rather than falsely claiming a managed stack.

`gh pr view <n> --json headRefName,headRefOid,author,headRepositoryOwner` identifies a parent only after matching repository/owner and exact commit. A name alone may be stale or collide. Fetch verified remote bookmarks with JJ; use GitHub API metadata when refs are unavailable, and stop construction if the required exact parent is unreachable.

Never use `gh pr merge` on a managed stack member. Landing belongs to `ce-babysit-pr` under explicit `posture:stack-land` with verified manager support, or the user. Permission, missing CLI, unavailable repository capability, authentication failure and ambiguous topology are distinct residuals, not an excuse to guess or retry denied actions.
