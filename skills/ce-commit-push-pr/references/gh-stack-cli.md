# GitHub stack compatibility with JJ-managed layers

Use `gh stack <command> --help` as authoritative for installed version behavior; `gh stack help <command>` is not equivalent. Run every repository-scoped `gh` command from the absolute JJ workspace root with `GIT_DIR=$(jj git root)` exported. Git-backed checkout/init/add/submit commands are not the workspace manager here: use JJ bookmarks and native publication in `stack-submit.md`.

## Classifying a parent without checkout

Resolve a parent PR by number with `gh pr view <number> --json headRefName,headRefOid,author,baseRefName,url,state`. A branch-only parent can be classified locally but cannot establish PR authorship. Inspect `gh stack view --json` when supported without checkout; do not parse stderr as topology. A read failure is unknown, not standalone. Disambiguation, unavailable stacks, invalid arguments, or missing parent evidence are residuals rather than guessed topology.

`gh stack view --json` reports `trunk`, `currentBranch`, and `branches[]` with name, head, base, isCurrent, isMerged, needsRebase, and PR metadata. `base` is the last known contained parent SHA, not its current tip. There is no documented branch ordering or top field: derive ordering from verified JJ ancestry and PR bases, never array order. A Git currentBranch may be absent in JJ; do not create a fake checkout to make this field appear.

For interpreting existing CLI receipts only, version 0.1.0 classified a parent with exit 0 (in a stack), 2 (standalone), 5 (invalid arguments), 6 (disambiguation required), or 9 (stacked PRs unavailable). Do not run its checkout command to obtain these receipts in a JJ workspace. Follow installed help if codes differ and report the difference. In JJ-native classification, require equivalent positive metadata evidence; absence or a failed probe is never standalone. The old `add` exit 5 meant not at top; that remains a topology residual, not permission to select another parent.

Resolve the parent by exact `headRefOid`, not name alone: names can be stale, absent, or collide. Fetch the parent bookmark through `jj git fetch`, verify its commit ID against PR metadata, and use API evidence or stop if the exact SHA cannot be reached. Never reset a colliding bookmark or move unrelated work. Prefer the current remote tip unless latest parent work is verified local-only, in which case use that exact local tip.

## GitHub-managed external layers

`gh stack link` is GitHub-only and is intended for external managers including JJ. Check its installed help and explicit repository availability before using it to register externally managed parent/child PRs. It creates no local tracking: later local `gh stack submit/view/merge` must not be assumed to see those layers. If required server topology or landing cannot be verified, return a hard residual rather than pretending the stack is managed. Do not silently replace required stack intent with independent PRs.

## Never

- Run interactive/TUI stack commands without explicit arguments.
- Use `gh stack checkout`, `init`, `add`, or `top` to move a JJ workspace or choose a different parent.
- Treat an unknown parent as standalone or reorder layers from undocumented JSON ordering.
- Use `gh pr merge` to land a managed stack member. Landing belongs to `ce-babysit-pr` under `posture:stack-land` or the user, through a verified server-compatible stack merge route; unavailable routes are residuals.
