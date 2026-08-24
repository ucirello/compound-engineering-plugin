# `gh stack` provider semantics and JJ interop

`gh stack` uses Git branch terminology and mutates the colocated Git view. It is allowed only when `jj git colocation status` confirms colocation. Before each `gh stack` mutation, ensure every participating JJ bookmark is exported with `jj git export`. Afterward, run `jj git import`, inspect bookmark and change movement, and use `jj edit <change>` only when the intended workspace change is proven. Stop on divergence or an unexpected provider branch.

`gh stack <command> --help` is authoritative for the installed provider extension. Preserve provider exit codes and report a detected version mismatch rather than compensating with Git commands.

## Classify and inspect

```bash
gh stack checkout "<parent-pr-number>"
gh stack view --json
```

Resolve a parent by PR number when available; a bare provider branch name can resolve only local stack state. Branch on exit status, never stderr text. Exit 0 means the parent was selected; 2 means standalone; 5 means invalid invocation or wrong stack position as documented by the subcommand; 6 requires disambiguation; 9 means unavailable for the repository. Import after a successful checkout before making JJ decisions.

The JSON includes trunk, current provider branch, and branch entries with head/base/PR state. `base` is the provider's remembered parent commit, not necessarily the current parent tip. Do not infer undocumented ordering or stack top from array order.

Resolve a PR head with `gh pr view <n> --json headRefName,headRefOid,author`. Materialize it for `gh stack` by creating or moving the same-named JJ bookmark to the proven commit, export it, and stop if an existing bookmark or exported branch points elsewhere. If normal JJ remote fetch cannot obtain the commit, use the provider API fallback and import; never use a direct Git fetch workflow.

## Build and submit

```bash
gh stack init --base "<trunk>" "<provider-branch>"...
gh stack add "<provider-branch>"
gh stack submit --auto --open
```

`init` processes provider branches bottom to top and selects the last. Existing exported bookmarks are adopted; missing provider branches may be created by the extension and must be imported and reconciled to JJ bookmarks immediately. `add` must run from the provider's top branch; exit 5 is a topology decision, not permission to run `gh stack top` and reparent work. `--auto` avoids title prompts. `--open` creates ready PRs and can ready existing drafts, so use it only under the draft gate in `stack-submit.md`.

Never use `gh stack link`; it creates provider-only state that is not managed by the local stack. Never use `gh pr merge` for a managed member; landing belongs to `gh stack merge`. Never invoke a stack command without the arguments or noninteractive flags needed to avoid its TUI.
