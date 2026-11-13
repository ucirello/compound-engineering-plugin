# Managed-stack native recipes

Use only after the snapshot confirms server-owned manager membership and complete order. Do not invoke the `gh stack` extension: even its local view/checkout paths may launch Git. Read manager membership through the snapshot's GraphQL API route; unsupported schema with a verified default branch means absent, while denied/malformed/truncated probes mean probe-error, not completed stack coverage. Never infer managed membership from topology.

Run JJ at the absolute target workspace root. Scope every `gh` API command with `GIT_DIR=$(jj git root)` there. Keep explicit host, repository, bookmark and remote identities; never assume `origin`. Use https://docs.jj-vcs.dev/latest/cli-reference/ for native operations.

## Discover, capture and align

Re-run the snapshot's complete manager query before each transaction, retaining manager ID, ordered PR numbers, head/base names, exact head OIDs, draft/closed state and trunk. Read the exact head repository and branch for each affected PR. Fetch each branch with `jj git fetch --remote "<verified-remote>" --branch "exact:<bookmark>"`; resolve its remote bookmark to a full OID and compare against the fresh API head.

Require a clean workspace and no unrelated tracked, ignored, untracked or conflicted content before alignment or propagation. An empty `@` directly above the exact head is already aligned. Otherwise use `jj new "<verified-head>"` only in a clean authorized workspace, without repeat approval. Preserve push-target identity explicitly; JJ has no checked-out branch to infer it from. Keep the existing isolation and lifecycle rules in `intake.md`.

Before a delegate pushes, capture every open affected layer's remote OID and its old immediate parent OID under recovery bookmarks. Preserve this baseline outside any disposable isolation. Missing parent identity, uncertain membership or a moved remote is a precise residual, never guessed topology.

## After an owned push (open dependents)

The active target is excluded from rebasing. Revalidate its head against the delegate-reported pushed SHA and its exact remote. For each open dependent in the confirmed order, from the first dependent upward:

1. Preserve its recorded old tip and old immediate parent under recovery bookmarks. Require the remote tip still equals its recorded baseline.
2. Select only that layer's own commits, `"<old-parent>..<old-tip>"`. Verify this set excludes all lower layers and unrelated descendants. Rebase this exact set with `jj rebase --revisions "<verified-layer-revset>" --destination "<new-immediate-parent>"` in authorized clean isolation. Never rebase the target or rebase a layer onto trunk opportunistically.
3. On conflict, retain recovery/evidence, restore no unrelated work, and park a stack-sync residual with the first blocked layer. Do not push conflicted or unvalidated tips. For clean results, read the exact before/after interdiff and verify the new tip contains its new immediate parent.
4. Move only the layer's head bookmark to its validated new tip; push with `jj git push --remote "<verified-remote>" --bookmark "<layer-bookmark>"`. Its remote-tracking lease must still represent the captured old tip. Never force over unexpected remote movement. If rejected, fetch/re-probe and report observed partial progress and the first divergent/rejected layer.
5. Re-probe the API head and fetched remote bookmark after each push. Use the verified new tip as the next layer's parent. Keep the active target unchanged at the delegate's pushed SHA throughout.

Do not assume atomic multi-ref pushes. Report all updated layers and remaining residuals truthfully. The native transaction preserves the server's existing PR/base relationships and manager identity; it does not create/import a stack or edit its structure. If the manager exposes a separate required registration operation, use only its documented API-native capability; unavailable external registration is incomplete maintenance, not successful sync.

## Land one settled prefix (only `posture:stack-land`)

The endpoint must be the bottom-most open settled member; all lower entries must already be merged. Thus this transaction's open prefix is exactly one PR, never several unreviewed open layers. Revalidate membership, target repository, base/head identities, settled gates and expected head SHA. Use GitHub's server merge API for that one verified endpoint:

```bash
(cd "$workspace_root" && GIT_DIR=$(jj git root) gh api --hostname "<host>" --method PUT \
  "repos/<owner>/<repo>/pulls/<bottom-most-open-settled-N>/merge" \
  -f sha="<verified-head-sha>" -f merge_method=squash)
```

Do not supply a fixed commit title/body: repository merge policy owns server-generated messages. A rejected expected SHA, permission/policy failure, or a required manager-specific atomic operation that this endpoint cannot satisfy is a residual, never a fallback to another merge mode. Never merge an upstack member with open downstack entries; never invoke `gh pr merge` or a Git-backed stack extension.

API success is not proof of actual landing. Re-probe PR state and queue status; while OPEN/queued, keep watching or return a queued pipeline residual. Only actual `MERGED` authorizes synchronization and transition.

After actual merge, fetch the verified trunk/base head, re-probe manager order and each surviving PR's base relationship. Propagate only surviving layers' recorded own-commit ranges from their recorded old parents onto the verified post-merge immediate parent using the native dependent transaction above, preserving recovery and lease checks. Require the server's base relationships/manager registration to agree; if required server-side synchronization cannot be performed through a documented API, name that genuine external capability as incomplete, not done. Never sync after failed or queued-only merge.

After successful synchronization, stop the old watcher and continue the next eligible non-draft layer with the same posture, invocation tuple and spent budget. A merge performed by this run is a layer transition, not a terminal run stop. Under `target`/`stack-ready`, print the explicit API merge command as a pending user action but never execute it.
