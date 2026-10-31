# Managed-stack API and native JJ recipes

Load this file when the active run uses a confirmed managed stack (`manager_status == "confirmed"`). Use `gh stack` only for proven GitHub API discovery/link/merge operations, never for local rebase, push, checkout or sync. If an API route is missing, exits unavailable (e.g. code 9), or cannot operate without a Git-backed local mutation, surface an incomplete stack residual; never invent membership from topology or claim that route completed.

Always non-interactive. Run every command from the current target workspace's verified absolute root (`cd "$workspace_root" || exit 1`), and export `GIT_DIR="$(jj git root)"` there for every repository-scoped `gh` sequence. Prefer JSON probes and exact names. Resolve each layer's actual head repository, named remote and bookmark independently; never assume all layers use `origin` or even the same remote. No direct Git executable or Git-backed local extension mutation is allowed.

## After an owned push on the active layer (dependents exist)

1. **Capture a recoverable transaction before the delegate pushes.** Save under the workspace's `.tmp/rocketclaw/` the confirmed manager order, PR/link IDs, base/head repository and ref identities, exact local and freshly fetched remote-bookmark OIDs for target and all open dependents, parent boundary for each layer's exclusive commit set, workspace tip and current JJ operation ID. Create uniquely run-owned recovery bookmarks at every old tip, and read back the evidence. Prove ordinary push authority and clean, non-conflicted tracked state; inspect ignored/untracked content and preserve unrelated work. Dirty state or unconfirmed membership stops the invocation before the delegate/watch. Keep recovery bookmarks outside the set to push.
2. **Revalidate after the target push.** Retain the delegate-reported pushed target OID. Fresh API view must prove identical ordered PR/link/head identities; fetch the exact layer bookmarks with `jj git fetch --remote "<layer-remote>" --branch "exact:<layer-bookmark>"`. The target's local bookmark and remote OID must equal the reported pushed OID, and each dependent's local/remote OIDs must still equal its baseline. Do not replace the recorded lease with newly observed concurrent work. An empty `@` above the verified target is aligned. No dependents means no cascade.
3. **Rewrite only the verified dependent suffix in JJ.** From recorded old parent boundaries, enumerate the first open dependent's exclusive commits and all subsequent open dependent layers in manager order. Prove the connected linear revision set contains exactly those commits: no target, trunk, landed-prefix commits, unrelated branch, recovery ref content, or unowned descendants that JJ would also rewrite. If topology, missing commits, immutability or automatic descendant effects cannot be bounded, stop with a precise incomplete residual; never bypass immutable protection. Record stable change IDs and old per-layer tips. Then from the absolute root run:

   ```bash
   jj rebase --revision "<verified-dependent-suffix-revset>" --onto "<exact-pushed-target-oid>"
   ```

   This moves only the suffix roots onto the unchanged target, preserving internal layer order; it does not rebase the target onto trunk. JJ can move bookmarks with rewritten changes, so recovery bookmarks alone are not immutable pins: retain the captured operation ID/full old OIDs and evidence outside the rewritten set, then re-anchor only run-owned recovery bookmarks to their recorded original commit OIDs with `jj bookmark set "<owned-recovery-bookmark>" --revision "<recorded-old-commit-oid>" --allow-backwards` and read them back before any push. Never re-anchor user refs. Resolve each dependent's new tip from its recorded change identity and validate the old/new exclusive patches, parent boundaries, and final diffs. Update only that layer's existing bookmark with `jj bookmark set "<layer-bookmark>" --revision "<validated-new-layer-tip>"`; preserve PR names, head repositories, manager membership and link identities. Record every owned operation ID; once subsequent bookkeeping operations exist, the rewrite alone is no longer the latest operation and cannot be blindly undone.
4. **Conflict rollback / safe stop.** Do not push any conflicted or unvalidated layer. Inspect the exact operation's effects. Only after verifying with `jj op log` that the rewrite's captured operation ID is still the latest exclusively run-owned operation in this workspace, no remote push occurred and no unrelated/concurrent work intervened may `jj undo` roll back that one local operation; verify old tips and clean state afterward. Do not repeat undo or use a cross-workspace override. Otherwise retain the conflicted state and recovery refs, stop and report how to recover without discard. Never reset, abandon unrelated changes, auto-resolve a semantic choice, or layer another attempt over an interrupted transaction.
5. **Push explicit layers with baseline leases.** Recheck exact target OID, link/order identities and all layer leases before the first push. For each dependent, bottom-to-top, verify JJ's expected remote-bookmark OID still equals its recorded baseline and push only its validated bookmark:

   ```bash
   jj git push --remote "<layer-remote>" --bookmark "<layer-bookmark>"
   ```

   JJ's remote-bookmark compare-and-swap is the lease; do not refetch and blindly push an old rewrite after rejection. Never use a blanket/all-bookmarks push. Treat the sequence as potentially non-atomic. After success, rejection or interruption, fetch and independently re-probe every layer: compare remote/local OIDs with baseline and expected new tips, verify the target is still exactly the reported pushed OID, and confirm managed order/links. Record already-updated layers as progress, name the first rejected/divergent layer, retain old/new recovery refs, and return a recoverable residual for the remainder. Do not undo already-pushed progress, overwrite concurrent work, restart the budget, or claim stack readiness without this proof. Resume from a freshly reconciled baseline only after the cause is resolved.

## Discover order / next open layer

```bash
gh stack view --json
```

## Land one prefix (only under `posture:stack-land`)

Merge the **bottom-most open settled** PR — `gh stack merge <PR>` merges the full stack prefix through that PR atomically. Never merge an upstack active PR while downstack PRs remain open when single-prefix landing is intended.

```bash
gh stack merge <BOTTOM_MOST_OPEN_SETTLED_PR> --yes --squash
```

Re-probe the landed PR before advancing: on merge-queue bases the CLI may succeed after enqueue while the PR stays OPEN — keep watching or return a queued residual until `pr_state` is `MERGED`. Only then treat the just-merged PR as a **layer transition** (stop watcher, re-probe, continue next open non-draft needing work with posture restated) — not a run-level Terminal stop for this babysit invocation.

**Native post-land synchronization.** Capture the same per-layer baseline/recovery evidence before landing. After actual `MERGED`, resolve and fetch the exact new base bookmark/OID and the API's landed-prefix identities (a squash commit is not the old layer tip). Verify the new base includes the landed result. Reconcile the remaining open manager order and existing PR/link/base-ref identities through API-only view/link operations where required; never recreate PRs, silently alter dependency structure or guess a relink. If the API cannot prove/update the required managed linkage, stop with an incomplete residual. Apply the native suffix transaction above with destination = that verified new base OID and suffix = only the remaining open layers' exclusive commits after the recorded old landed-prefix boundary. Exclude all landed-prefix patches to avoid replaying a squash-merged change; missing/ambiguous boundaries stop the transaction. Maintain per-layer leases, target/new-base OID invariants, clean-work safeguards, rollback restrictions and non-atomic reprobe evidence. There is no extra trunk rebase or local bookmark deletion. Only when actual merge, API linkage, JJ topology and all intended remote tips are verified is land+synchronization complete; otherwise report the queued/partial/incomplete residual and do not advance or return pipeline success.

For post-land synchronization, the invariant differs deliberately from post-push propagation: the API-proven new base OID stays fixed during the suffix transaction; remaining layers may move only from their recorded old OIDs to validated new tips. Preserve the landed target's old OID in recovery evidence rather than requiring its remote bookmark to survive an API-confirmed branch deletion. A missing remaining open-layer head, unexpected base movement, or a deletion not explained by the confirmed merge is a blocker, not permission to guess. Revalidate this distinction on every reprobe.

## Forbidden on managed stack members

```bash
gh pr merge …
```

Use `gh stack merge` only. Under `posture:target` and `posture:stack-ready`, print the exact merge command when reporting ready-as-next; do not execute it.
