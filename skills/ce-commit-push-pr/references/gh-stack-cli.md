# Stack capability boundary

Do not use Git-backed stack checkout/init/add/submit helpers: they may invoke the Git executable internally. Stack construction uses native JJ revisions/bookmarks and explicit GitHub PR metadata, as defined in `stack-submit.md`. Repository `gh` calls run from the absolute workspace root with `GIT_DIR=$(jj git root)`.

Do not guess stack order from an unordered API array. Verify each exact parent/head relation and preserve existing drafts. Never use a standalone `gh pr merge` to land a managed stack; hand off explicit stack-land intent to `ce-babysit-pr`, and report a capability blocker if its authorized native landing route is unavailable.
