# Native JJ stack recipes and handoff receipt

All JJ commands run at the absolute target workspace root. Export `GIT_DIR=$(jj git root)` there for repository `gh`; store receipts/body files under local `.tmp/rocketclaw/`. `stack.md` owns authority, graph verification, conflict recovery and partial-publication rules. No `gh stack` checkout/init/add/rebase/push/sync/submit routes.

## Explicit native topology

Materialize the complete caller-supplied graph as JSON, preserving exact PR/source bookmarks and ownership. This is a schema example, not inferred topology:

```json
{
  "kind": "native-jj",
  "explicit": true,
  "trunk": "main",
  "base_oid": "<verified-full-base-oid>",
  "entries": [
    {
      "url": "https://<host>/<base-owner>/<base-repo>/pull/<N>",
      "name": "<head-bookmark>",
      "remote": "<verified-head-remote>",
      "head_repository": "<host>/<head-owner>/<head-repo>",
      "head": "<verified-full-head-oid>",
      "base_ref_name": "<immediate-parent-bookmark-or-trunk>",
      "parent_head": "<captured-full-immediate-parent-oid>"
    }
  ]
}
```

List every layer bottom-to-top; PR numbers are repository-scoped, URLs and head repositories are mandatory. `parent_head` captures the boundary of the owned layer before propagation; the next entry's base name must equal the previous bookmark. Retain before/after receipts and recovery bookmarks for each maintenance transaction. A caller's handoff does not waive live verification or grant land authority. Existing externally managed stacks retain their original ownership instead of being relabeled `native-jj`.

```bash
cd "$workspace_root" || exit 1
export GIT_DIR=$(jj git root)
export BABYSIT_TOPOLOGY_FILE="$workspace_root/.tmp/rocketclaw/<run>/topology.json"
jj git fetch --remote <verified-head-remote> --branch 'exact:<head-bookmark>'
jj log --no-graph -r '<verified-parent-oid> & ::<verified-head-oid>' -T commit_id
```

Export the same absolute topology-file path in every later shell call; shell state does not persist. The helper also persists `pr_chain.topology_file` in the state journal and recovers that path on session/shell resumption, before fetching; a previously native-owned journal with missing/malformed ownership evidence stops instead of silently degrading to external/manual discovery. New layer state directories still require the explicit exported path. Fetch all exact heads and verify them against API data before polling. Missing/stale evidence is `probe-error`, never absent. Retain and reconcile recovery receipts across layer transitions and retries.

## Clean alignment and scoped propagation

```bash
jj new <verified-head-commit>
jj rebase -r '<exact-owned-layer-revset>' -d <verified-new-parent>
jj bookmark set <owned-layer-bookmark> -r <verified-rewritten-tip>
jj git push --remote <verified-head-remote> --bookmark <owned-layer-bookmark>
```

Alignment is only after the clean-state gate in `setup.md`; empty `@` above that head is already aligned. Rebase is caller-owned authorized upstack maintenance only, never the target fixer's scope. Capture old/new heads and parent boundaries first. Preserve intent, coverage and all unrelated revisions; stop at semantic conflicts or concurrent remote changes. Push one verified layer at a time, retain exact partial-publication receipts, and never claim atomicity or blindly retry.

## Read-only existing-manager discovery

```bash
gh stack view --json
```

Preserve existing manager order and metadata. Supported GitHub read-only stack APIs are an alternative; malformed, denied or incomplete discovery remains uncertainty. No manager working-tree mutation is required or permitted.

## Final merge only under explicit stack-land

For native topology, after all current-head readiness gates:

```bash
gh pr merge <verified-bottom-most-open-settled-URL> --squash --match-head-commit <verified-head>
```

For existing externally managed membership, retain the verified server-side ownership protocol where supported without workspace mutations:

```bash
gh stack merge <bottom-most-open-settled-PR> --yes --squash
```

Never substitute these protocols for each other. Under `target`/`stack-ready`, only print the appropriate command. After an authorized actual MERGED result (not enqueue), use `stack.md`'s native scoped retarget/rebase/push transaction; never `gh stack sync`. A failed merge performs no synchronization. Verify each remaining layer's graph, PR bases and exact remote heads; preserve/report incomplete synchronization or publication.
