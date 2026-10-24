# Stack topology through JJ and GitHub

Do not use a Git-backed stack dispatcher to check out, build, submit, or merge layers. Use native JJ topology and repository-scoped gh API operations as described in `stack-submit.md`. Run JJ from the absolute workspace root and set gh's GIT_DIR from `jj git root` there. See https://docs.jj-vcs.dev/latest/git-experts/ and https://docs.jj-vcs.dev/latest/cli-reference/ .

Resolve a named parent PR by explicit number and `gh pr view <number> --json headRefName,headRefOid,headRepositoryOwner,headRepository,baseRefName,author,state,isDraft`. Verify repository, exact head and bookmark independently; a name alone may be stale or collide. A branch-only parent is only a trunk until a PR is verified. Never move a colliding bookmark to repair a mismatch.

Read the existing stack's explicit PR base/head relationships and verified JJ ancestry. A stored base SHA is not proof of the parent's current tip. Do not infer layer order from unordered API output. Ambiguous topology, unavailable stack support, authorization errors and unrelated histories are distinct residuals, not evidence that the parent is standalone.

Keep managed topology intact. Never link a second unmanaged stack, create an artificial parent, or silently reparent to the top when the requested parent is elsewhere. Landing requires the stack-aware bottom-up lifecycle owned by `ce-babysit-pr`; a single-member merge is not equivalent to landing the stack. If native capabilities cannot preserve that lifecycle, report it blocked rather than invoking a Git-backed bridge.
