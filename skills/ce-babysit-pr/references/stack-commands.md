# Managed-stack native JJ recipes

Use these recipes only with fresh positively confirmed managed membership (`manager_status == "confirmed"`). Topology alone is never membership. Read manager order through repository-scoped `gh api` GraphQL stack metadata, not a local Git-based stack manager (including its view, checkout, rebase, push, merge or sync commands). Unavailable metadata is a classification/compatibility residual, not permission to invent membership. Preserve snapshot null/schema-unavailable/default-branch versus auth/transport/error distinctions.

Run every JJ command with cwd set to the target workspace's **absolute root**; shell examples use `(cd "$workspace_root" && jj ...)`. Run repository-scoped `gh api` there with `GIT_DIR=$(jj git root)` exported. Use actual verified head repositories, bookmarks and tracking remotes, never an assumed origin. Use non-interactive commands and exact quoted revsets/string patterns, not interpolated untrusted shell. All receipts/baselines belong under that workspace's ignored `.tmp/`. Before composing a squash description follow `references/change-descriptions.md`.

## Baseline and topology proof

Before a delegate may push, save the fresh ordered open target/dependents, PR head/base repositories and refs, remote OIDs fetched with `(cd "$workspace_root" && jj git fetch --remote "<verified-remote>")`, local bookmark OIDs, exact parent boundaries and commit sets for every layer, plus the JJ operation ID. Retain recoverable references to the old commits. Require clean, conflict-free state and unambiguous bookmarks matching these remote heads. An empty `@` immediately above the verified target is aligned. Missing/ambiguous refs or unrelated work are a true pre-delegate stop: no tick or watcher re-arm; report a resumable residual.

Prove each layer's exclusive range from its recorded parent head to its own head, and that the chain is linear with no outside descendants, merges, shared bookmarks, other workspaces' work or unrelated commits in the rewrite set. Record full commit IDs (not a mutable revset alone). Native JJ may already have rebased descendants when the delegate rewrote the target: reconcile stable change IDs, old/new parent boundaries and diffs before deciding what remains. Never rebase a propagated change twice. A genuine topology mismatch is a residual; do not adopt/import/change stack structure.

## After an authorized active-head push

Freshly revalidate metadata, membership, clean state and the delegate-reported pushed SHA. Fetch and require both target bookmark and remote head to equal it; the target itself is excluded from maintenance. For each open dependent in bottom-up manager order, map its recorded exclusive commit set to the current local commits. If already propagated correctly, verify it rather than rebase again. Otherwise rebase **only that exact set**, retaining its internal edges:

```bash
(cd "$workspace_root" && jj rebase --revisions '<verified-exclusive-commit-set>' --onto '<verified-new-parent-head>')
```

`--revisions` preserves dependencies inside the selected set; it can also reparent descendants left behind, so prove the complete affected closure is authorized before running it. Do not use default branch/source selection or trunk rebasing. Recheck target unchanged, each dependent's expected diff, ancestry and bookmark after every operation. Move an existing bookmark only to its verified rewritten tip with `jj bookmark set --revision '<verified-tip>' '<exact-bookmark>'` from the absolute workspace root. Do not create unrelated bookmarks, use `--allow-conflicts`, bypass immutability or discard work. On conflict stop publication, preserve operation/recovery IDs and report needs-human; do not blindly undo/restore concurrent operations. A narrowly verified reversal of solely this operation requires no concurrent work and preservation of all recovery evidence; otherwise leave it recoverable.

Before each push, fetch and compare the dependent remote to the **saved baseline OID**, not merely the latest fetched value. If it moved to the expected new tip, record progress; any other movement is a race residual. Then push only the verified bookmark:

```bash
(cd "$workspace_root" && jj git push --remote '<verified-tracking-remote>' --bookmark 'exact:<verified-bookmark>')
```

JJ's push checks that remote refs still match its fetched expectations (lease safety). Do not fetch-and-retry a rejection without comparing the original baseline: that would accept someone else's update. Do not assume atomic multi-ref publication. After success **or** rejection fetch/re-probe every baseline open dependent and target, comparing old and expected new OIDs. Already-published dependents are observed progress; report the first rejected/divergent layer and exact recoverable retry boundary. Do not roll back successful remote updates or claim ready while any dependent is stranded. Independent review/CI streams may continue, but not another mutation conflicting with unresolved maintenance.

## Align/transition to a layer

Resolve its PR through fresh manager metadata, then follow `references/setup.md`'s exact head repository/bookmark/remote verification and clean JJ alignment. Do not check out through a local Git-based manager. Empty `@` above the verified PR head already qualifies. Preserve existing isolation under its existing name; no reset or discard. If new isolation is needed, follow `ce-worktree`: capture local YYYYMMDD once, normalize meaningful task/PR/revision/caller slug without double prefix, same stable dated name and destination basename under local `.tmp/`, check registrations and disk, suffix collisions -2/-3, and create with `jj workspace add --colocate` from the source absolute root at the verified revision. Verify `jj git colocation status` in the new absolute root and adopt the harness session using its native lifecycle. Unsupported naming/colocation is a safe blocker, not permission to alter existing isolation.

Cleanup is separately authorized: stop workers, move the active session to a surviving workspace, verify exact registration/path/run ownership, inspect tracked/conflicted/ignored/untracked work, prove required integration, preserve recovery references and copy/read back evidence outside the destination. From the surviving absolute root use `jj workspace remove <verified-name>` only for disposable run-owned files; verify deregistration **and** directory disappearance. Warnings/incomplete cleanup are blockers, never force-delete. `jj workspace forget` is unregister-only when preserving files. Preserve harness ownership and unrelated bookmarks.

## Land the bottom-most settled prefix endpoint (`posture:stack-land` only)

Freshly prove no open downstack PR remains before this single-layer land, and recheck settle/pipeline gates, exact expected head SHA, base and manager order. Merge through the GitHub API, not a Git-backed local manager or `gh pr merge`:

```bash
(cd "$workspace_root" && GIT_DIR=$(jj git root) gh api --method PUT 'repos/<verified-owner>/<verified-repo>/pulls/<bottom-most-open-settled-PR>/merge' -f merge_method=squash -f sha='<verified-head-SHA>')
```

Inspect the response and re-probe PR state; command success alone is not merge success. If repository policy requires a merge queue, use its supported GitHub GraphQL `enqueuePullRequest` mutation with the verified PR node ID and expectedHeadOid, and wait for actual MERGED. Never bypass policy. A queued OPEN PR remains active (or a pipeline queued residual), never a successful land/transition. Unsupported/denied API or queue behavior is a recoverable residual, not a fallback to a local manager.

Only after actual MERGED, fetch the actual base and remaining heads, refresh metadata, and propagate the surviving layers with the same exact-set topology/lease checks above, replacing the old landed-head boundary with the verified new base tip. This is the native equivalent of post-land sync; do not replay the landed layer's commits or rebase unrelated trunk history. Revalidate/update the immediate surviving PR's base via repository-scoped `gh api` only when manager metadata proves that required post-land transition and its current base still matches the recorded old one; verify afterward. Preserve manager ordering/metadata via supported GitHub API if required; inability to complete that synchronization is a stack residual, not readiness. Never sync after failed/queued merge. Re-probe every changed head/base before continuing with the same invocation budget/posture; this run's own actual merge is a layer transition, external MERGED/CLOSED remains Terminal.

Under `target`/`stack-ready`, show the exact verified API merge command when reporting ready-as-next but do not execute it. Merge, post-land synchronization and upstack maintenance remain caller-owned, never delegated. These recipes are verified against `jj rebase --help` (exact revision sets retain internal dependencies) and `jj git push --help` (explicit bookmarks and fetched-ref lease checks); see https://docs.jj-vcs.dev/latest/cli-reference/ and https://docs.jj-vcs.dev/latest/bookmarks/#pushing-bookmarks-safety-checks .
