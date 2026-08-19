# `gh stack` Semantics Used Here

Verified against `gh stack version 0.1.0`. Live `gh stack <command> --help` is authoritative. This reference covers only GitHub stack-manager behavior; Jujutsu remains the owner of local changes, descriptions, bookmarks, fetches, rebases, and pushes.

## Interoperability Boundary

`gh stack` reads and may update the colocated Git view. Before a metadata operation, export Jujutsu bookmarks with `jj git export`. After an operation that changes checkout or stack metadata, import with `jj git import`, then verify `jj status`, bookmark targets, and the working-copy change before continuing. If the workspace is not colocated or the manager cannot represent the Jujutsu bookmark topology without rewriting it, stop with a residual.

## Parent Classification

```bash
gh stack checkout "<parent-pr-number>"
```

Resolve a parent by PR number when available. A bare branch name resolves local manager state only. Branch on exit code, not stderr text.

| Exit | Meaning | Action |
|---|---|---|
| 0 | Parent is in a stack and checkout changed | Import and verify its bookmark/change identity |
| 2 | Parent is standalone | Keep the original Jujutsu change selected |
| 5 | Invalid arguments | Correct against live help |
| 6 | Disambiguation required | Stop and identify the intended stack |
| 9 | Stacks unavailable | Report and stop |

`gh stack view --json` returns `trunk`, `currentBranch`, and branch records containing name, head, base, current/merged/rebase flags, and PR metadata. `base` is the parent commit last known to the manager, not necessarily the current parent tip. Do not infer ordering beyond what the manager documents.

## Building and Submitting

```bash
gh stack init --base "<trunk>" "<bookmark>"...
gh stack add "<bookmark>"
gh stack submit --auto --open
```

`init` processes names bottom-to-top and adopts exported bookmarks that already exist. `add` must run from the top manager branch; exit 5 is a topology decision, not permission to run `gh stack top`. `submit --auto` avoids title prompts; `--open` creates ready PRs and can mark existing drafts ready.

Do not use `gh stack link`: it creates GitHub-only links with no local manager topology. Do not use `gh pr merge` for a managed member; landing belongs to `gh stack merge`. Avoid bare manager commands that open a TUI or prompt.
