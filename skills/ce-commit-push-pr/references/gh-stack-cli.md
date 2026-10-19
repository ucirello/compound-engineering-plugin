# JJ-managed stack semantics

Use JJ dependencies and bookmarks for local stacks. Do not invoke Git-checkout-based `gh stack init`, `add`, `checkout`, `top`, or `submit` to mutate a JJ workspace. Resolve metadata through scoped `gh` with `GIT_DIR=$(jj git root)` from the absolute workspace root. Consult installed `gh stack <command> --help` for required remote stack operations; never assume an extension is available.

Resolve parents by PR number where available and verify base/head repository, owner, `headRefName`, and `headRefOid` against fetched JJ revisions. Names alone do not identify fork heads. Unknown/conflicting identities are residuals, never reasons to move unrelated bookmarks.

Remote stack linking does not establish local topology or authorize rewriting. Preserve existing manager contracts; if required operations cannot safely coexist with JJ, report the compatibility blocker instead of silently converting the stack. Never use `gh pr merge` on managed members. Landing stays with `ce-babysit-pr` under explicit stack-land intent and the verified manager's supported landing operation.
