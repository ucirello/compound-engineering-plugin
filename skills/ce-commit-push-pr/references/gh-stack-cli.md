# GitHub stack semantics for JJ-managed changes

The installed `gh stack <command> --help` is authoritative; inspect it before relying on flags or exit codes. Report differences. No separate gh-stack skill package is required.

JJ owns local changes, bookmarks, and pushes. Configure every `gh` process with `GIT_DIR` from `jj git root`, obtained in the absolute workspace root. Do not run gh-stack checkout/init/add/navigation/rebase/submit commands: they manage a Git working tree and local tracking that a JJ-managed stack does not have.

## Linking published PRs

```bash
gh stack link --base <bottom-base> <bottom-pr-url> <next-pr-url> ...
```

Arguments are bottom-to-top. Explicit PR URLs avoid ambiguity with numeric branch or stack identifiers and avoid implicit branch pushes. Branch arguments automatically push and may create PRs; do not use them. Create PRs with `gh pr create` after JJ pushes, with explicit immediate-parent bases, then link their URLs.

`link` creates or extends GitHub stack membership, preserving existing members. It does not create local gh-stack tracking. Thus `gh stack view --json` cannot prove remote membership or order, and absence there never proves a parent is standalone. Use a supported read-only GitHub API to verify remote topology; if unavailable, report a residual instead of reconstructing local tracking or guessing.

`--open` marks new **and existing** PRs ready; omit it whenever any existing draft lacks author authorization to open. Check draft state after linking. Always provide explicit arguments; bare commands can prompt or open a TUI.

## Resolving a parent

`gh pr view <url> --json headRefName,headRefOid,author,baseRefName,state` identifies the PR head. Confirm its repository and fetched JJ revision match, not merely its branch name. Never reset an unrelated or stale same-named bookmark. A branch-only parent without proven ownership serves as a trunk, not an adopted PR layer. A named parent in an existing stack must be the top before append; never silently move above some other layer.

## Landing

Never use `gh pr merge` for a stack member. `ce-babysit-pr` owns stack landing and must use the installed supported remote-stack interface. Do not assume `gh stack merge` can see a `link`-created stack through local tracking; missing support is a typed residual, not permission to check out or rebuild the stack.
