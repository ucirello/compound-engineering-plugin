# Managed stacks: posture, discovery, native JJ maintenance, and landing

Use `references/stack-commands.md` for the native JJ topology/rebase/push and scoped GitHub metadata/merge transaction. No Git-backed stack extension is needed or permitted. All JJ calls run at the target absolute workspace root; repository `gh` calls run there with `GIT_DIR=$(jj git root)`. Keep receipts and recovery evidence in workspace-local `.tmp`.

## Posture

Hold one `posture:target|stack-ready|stack-land` per run, independent of watch/checkpoint/pipeline mode and duration. Restate it at every transition.

| Posture | Behavior |
| --- | --- |
| `target` | Only the named PR. Stop at looks-ready; offer stack-wide continuation once for a confirmed managed stack. Never merge. Authorized dependent propagation after this target's push still applies. |
| `stack-ready` | After the active layer is quiescent, automatically continue to the next open non-draft layer needing work, even if CI/settle is pending. Lower layers stay under the downstack probe. Never merge. |
| `stack-land` | Same traversal; selecting this posture is run-level land authorization. Land the bottom-most open settled layer through the scoped GitHub merge/queue API, synchronize remaining layers with native JJ, then continue. Never merge an upper layer while lower layers remain open. |

Quiescent means zero actionable thread/comment/CI backlog, no open needs-human or blocked-failing residual, no stack blocker, no open/claimed currency item, and no delegate in flight. Quiescent is not settled: landing requires the full interactive Step 3 readiness/settle gate or pipeline success gate.

One PR without stack intent defaults to `target`; offer once to carry the confirmed stack. Own/finish the stack means `stack-ready`; explicit land/merge intent means `stack-land`. A request to babysit the whole managed stack already selects stack-wide authority, so do not ask redundantly. Pipeline never asks or expands supplied scope.

## Discovery and continuation

Every snapshot classifies membership through scoped remote GraphQL metadata. Accept only positive membership containing the target and a verified ordered chain. A successful null stack means `absent`; a stack-field schema-unavailable response means `absent` only after a separate successful default-branch lookup. Auth, transport, rate-limit, malformed responses, and failed default-branch lookup mean `probe-error`. Ordinary base/head relationships can identify a manual dependency chain but cannot confer managed membership. Discovery never switches workspaces/bookmarks or changes remote state.

Only fresh `manager_status == "confirmed"` permits managed continuation. Manual chains and probe errors remain target-local and mutation-conservative. Keep remote PR IDs, bookmark/repository identities, parent edges, and recovery receipts authoritative; do not recreate or import a guessed chain.

Before semantic work, inspect ordered entries. Under `target`, when a requested middle layer has unsettled downstack work, offer once to start at the lowest unsettled non-draft layer with `stack-ready`; do not silently redirect. When stack-wide authority is already granted, start at that lowest layer without asking, or at the requested layer if all below are settled. At a target-local ready stop, offer once to continue to the immediate open non-draft upstack layer needing work. Declining leaves a target-local stop. Pipeline returns an out-of-scope next candidate as a residual.

Use one active mutated target and one watcher. Before a layer transition, revalidate membership/order/downstack state, finish in-flight work, stop the old watcher, and align to the exact verified head using the native recipe. Preserve clean empty `@` above that head; dirty/conflicted/ignored/untracked work is never discarded. Initialize the layer state with `--continue-invocation --invocation-id "$RUN_INVOCATION_ID" --session-started-at "$RUN_STARTED_AT" --invocation-budget-seconds "$RUN_BUDGET_SECONDS" --continue-dead-time-seconds <prior-layer-invocation_dead_time_seconds>` and restate posture. Never renew the budget. Stop at a draft outside explicit scope, a human-blocked layer, end of stack, budget, user stop, or lost membership confirmation.

## Pre-push baseline

Before a delegate may push, read fresh remote topology and exact fetched JJ bookmark OIDs for the target and all open dependents. Record each remote/repository/bookmark, local and remote tip, parent boundary, intended revision set, invocation, and recovery bookmark in a read-back receipt. Require clean state and exact target alignment (including the empty-`@` parent case), known push authority, and still-confirmed membership. Failure here is a true stop in every mode: no delegate, further tick, or watcher rearm; report the residual and resume invocation. Do not require atomic multi-ref push support; use per-layer expected remote OIDs and verified progress instead.

## Step 7: authorized upstack propagation

After the delegate's authorized target push, maintaining the confirmed linear chain is implicit babysit authority, even under `target`; it does not grant semantic review/CI work on another PR. Re-read topology and fetch exact head bookmarks. Verify the target's local and remote tips equal the reported pushed OID. This intentional target change is not dependent divergence. No dependents means no cascade.

Starting with the immediate open dependent, follow the detailed native transaction: isolate its recorded old-parent-to-tip revision set, rebase only that set onto its new immediate parent with `jj rebase --revisions ... --destination ...`, inspect conflicts/diffs/topology, move only its authorized bookmark, and `jj git push --remote ... --bookmark ...` with JJ's tracked expectation. Continue bottom-up using each preceding rewritten tip. **Exclude the active target and all lower-layer revisions; never rebase onto trunk.** Recheck the unchanged target invariant throughout. No broad descendant selection, unconditional force push, bookmark deletion, or unrequested topology change.

For every layer, preserve old/new OIDs, old/new parent, operation/change IDs, expected remote OID, push result, and independently observed remote tip. Re-probe after success or rejection; do not assume all-or-none. Already-updated dependent remotes are progress. Stop at the first conflict, moved remote, unknown authority, topology change, or failed verification; preserve recovery bookmarks and the conflicted local rewrite without pushing it, and report that exact layer and safe resume point. Never broadly undo other work. Do not claim readiness while any open dependent diverges. A later retry first reconciles receipts and remote truth rather than restarting or overwriting completed layers.

Arm the single watcher with `--downstack-pr <N>` for every open lower layer. On `downstack-actionable`, wait for any current delegate, stop the watcher, and return to the lowest reopened eligible layer under the same invocation; handle it, propagate, then walk back up. Recheck order/downstack quiescence at every transition, before target mutation, and at looks-ready. Loss of positive membership ends continuation with a classification residual.

## Layer stops and landing

Under `stack-ready`, quiescence triggers advancement; report the layer in one line, revalidate order/downstack, and continue without another approval. Pass already-quiescent non-draft layers only after fresh confirmation. Report each layer's settled/quiescent state from fresh probes. A standing residual keeps that layer active while independent streams continue; never advance past it or a draft outside scope.

Under `stack-land`, land a settled bottom-most open layer **before** ordinary advancement. A merely quiescent bottom layer may be walked past but not merged. Use the head-guarded scoped GitHub merge API (or supported expected-head queue mutation) and native JJ synchronization in `stack-commands.md`; this step remains caller-owned, not delegated. Verify actual `MERGED`: enqueue or request success while OPEN is not completion. Interactive watches continue observing the queue; pipeline returns a queued residual, never success. A rejected merge does not trigger sync. After actual merge, preserve premerge boundaries and recovery references, verify the surviving base, retarget the immediate dependent's PR base through scoped metadata API, rebase only its unmerged revisions onto that base, and propagate higher dependents with the same lease/conflict/receipt rules.

Merge/sync failures return precise recoverable residuals including partial remote progress; do not weaken head guards, bypass queue policy, or merge another layer before synchronization completes. A layer this run actually merged and synchronized is a transition: stop its watcher, refresh topology, and continue the next eligible open layer with unchanged budget/posture. Externally observed MERGED/CLOSED on a layer this run did not land remains a true terminal stop. Pipeline must complete actual merge and synchronization before advancing or reporting success. Under `target`/`stack-ready`, only print the resolved, unexecuted final-merge API option and required subsequent synchronization; readiness is not merge authorization.
