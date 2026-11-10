# Remote stack semantics with JJ

Do not invoke checkout/init/add/submit operations from a branch-switching stack CLI: those delegate local repository management outside JJ. Keep topology in JJ revisions and bookmarks and manage remote PR relationships through explicit gh PR operations.

Run from the absolute target workspace root with exported `GIT_DIR=$(jj git root)`. Inspect PR metadata using `gh pr view <ref> --json number,url,state,isDraft,baseRefName,headRefName,headRefOid,author,headRepositoryOwner`. Resolve exact owner and head, not just a possibly stale same-name local bookmark. Fetch through JJ's documented remote/bookmark facilities; use the API diff/commits fallback for unreachable PR-only refs, never a direct Git fetch.

If repository-supported remote stacking cannot represent the requested topology without a local Git manager, stop with a compatibility residual instead of changing tools silently. Never flatten required stack intent. Never individually merge a managed stack member: landing stays with the authorized stack-aware babysit workflow and must stop if no compatible landing mechanism exists.
