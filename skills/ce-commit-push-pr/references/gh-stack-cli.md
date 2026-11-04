# Stack metadata and JJ-native execution

Do not invoke `gh stack`: its checkout, construction, submission, and merge routes manage Git branches/workspaces. Use `stack-submit.md` for native JJ topology and transport, and repository-scoped `gh pr` API operations for GitHub metadata. This restriction does not forbid Git-format data or `jj git`.

Resolve a parent PR with `gh pr view <number> --json headRefName,headRefOid,headRepositoryOwner,baseRefName,author,url,state,isDraft`. Verify repository owner AND ref AND exact commit. Fetch the exact required bookmark through `jj git fetch`; if unavailable, retrieve the exact PR ref using supported JJ fetch selection, or report the exact-ref blocker. Never silently substitute a similarly named bookmark.

Stack topology comes from verified JJ ancestry and explicit PR bases, not ordering guessed from API arrays. Ambiguous/shared parents, unavailable stack functionality, stale local refs, and unproven heads are residuals. Do not move the work to a different parent to make construction succeed. Preserve existing drafts unless opening them was explicitly authorized.

Never merge stack members independently with `gh pr merge`. Hand stack landing to `ce-babysit-pr` under explicit `posture:stack-land`; if its native stack landing contract cannot be fulfilled, report a blocker rather than invoke a Git-backed extension.
