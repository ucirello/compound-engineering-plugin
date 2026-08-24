# Managed stacks: posture, discovery, transitions, upstack maintenance, landing

## Posture

Hold exactly one posture for the run. Carrier: `posture:target|stack-ready|stack-land`, distinct from sustain mode and duration. Re-state it on every managed-stack `--continue-invocation` transition.

| Posture | Behavior |
| --- | --- |
| `target` | Only the named PR. Stop at looks-ready. May offer stack-wide once when a confirmed multi-layer managed stack needs work. Never merges. |
| `stack-ready` | When the active layer is quiescent, continue to the next open non-draft upstack layer needing work. Lower layers remain probed and the lowest re-opened layer regains the writer lane. Never merges. |
| `stack-land` | Traverse as `stack-ready`. Selecting it authorizes landing the bottom-most open settled prefix with `gh stack merge` and `gh stack sync`. |

Quiescent means zero actionable feedback/CI, no delegate in flight, no current decision, no terminal red check, no stack blocker, and no open or claimed currency item. Landing requires the full settled gate, not quiescence.

Named PR without stack intent defaults to `target`; intent to own the stack selects `stack-ready`; intent to land it selects `stack-land`. Under `target`, ask once before expanding semantic scope across a confirmed stack. `mode:pipeline` uses only supplied scope and never asks.

## Discovery And Continuation

Classify the PR chain automatically. Run `jj git export` before the read-only `gh stack view --json` probe so the manager sees current JJ bookmarks. Accept local manager output only when it contains the target PR. If the manager cannot identify an exported bookmark without changing the working copy, skip that local probe and use the read-only GraphQL fallback. A successful null stack is `manager_status == "absent"`; auth, transport, malformed, rate-limit, or uncertain schema/default-branch evidence is `probe-error`. Ordinary open-PR base/head relationships distinguish an independent PR from a manual dependency chain when no manager is confirmed.

Only `manager_status == "confirmed"` from a fresh probe activates stack-wide continuation or manager-owned upstack maintenance. Manual chains and probe errors stay target-local and mutation-conservative.

For a confirmed stack, orient from manager order. Under accepted stack-wide posture, begin at the lowest unsettled in-scope non-draft layer, proceed upward, and never skip a human-blocked layer. Keep one active target and one watcher. At a transition, stop the old watcher, run `jj git fetch --remote <layer-remote>`, verify `<bookmark>@<layer-remote>` against the PR head OID, and create or edit a dedicated JJ working-copy change with `jj new <bookmark>@<layer-remote>` or `jj edit <change>`. JJ has no current bookmark. Refuse to replace unrelated content in `@`.

Initialize the layer state with `--continue-invocation`, the original `--invocation-id`, `--session-started-at`, and `--invocation-budget-seconds`, plus `--continue-dead-time-seconds <prior-layer-dead-time>`, and re-state the posture. One fixed budget covers the traversal. Reconfirm manager membership before every cross-PR transition; loss of confirmation ends continuation.

## Pre-Push Baseline

Before a delegate may push a confirmed managed target, fetch the stack remote, export JJ bookmarks, and obtain a fresh manager view. Record every open bookmark at or above the target and each corresponding remote bookmark's commit ID. Require `@` to contain no unrelated content, every involved bookmark to be unconflicted, and target membership to remain confirmed. Failure is a true stop for this invocation. Do not assume `gh stack push` updates multiple refs atomically; always fetch and re-probe afterward.

## Upstack Maintenance

After an authorized target push, retain the pushed commit ID, fetch the remote, and require both local and remote target bookmarks to equal it. Save the current JJ change ID and require its diff to be empty. Select the first open dependent above the target; no dependent means no cascade.

For a cascade, use the interop transaction in `references/stack-commands.md`: export bookmarks, let `gh stack` rebase and push dependents, import the resulting refs, fetch, and restore the saved JJ working-copy change. The manager owns this bounded rewrite; it does not authorize changing stack structure or rebasing the active target. After success or rejection, compare every open dependent's local and remote bookmark commits with the baseline and expected imported tips. Keep observed partial progress, name the first rejected, conflicted, or divergent dependent, and leave a recoverable residual. Never bypass JJ's bookmark conflict or remote-lease safeguards.

Arm one watcher with repeated `--downstack-pr <N>` flags for open lower layers. A lower layer that gains work returns the single writer lane to the lowest reopened non-draft layer after any in-flight delegate finishes. Recheck downstack quiescence before mutation, transition, and readiness.

## Layer Transitions And Landing

Under `stack-ready`, quiescence advances the walk even while checks or settle time continue; the downstack probe guards earlier layers. Under `stack-land`, land the bottom-most open settled prefix before advancing. Stop before an out-of-scope draft and keep a `needs-human` layer active.

For landing, identify the bottom-most open settled PR and run the JJ interop recipe in `references/stack-commands.md`. Re-probe GitHub after `gh stack merge`: merge queue acceptance may leave the PR open, so continue watching or return a queued residual until it is actually `MERGED`. A merge performed by this run is a layer transition, not a run-level terminal stop. On merge, sync, import, bookmark-conflict, or fetch failure, surface a residual and never fall back to `gh pr merge`. In `mode:pipeline`, success requires the authorized prefix to reach `MERGED` and the imported JJ bookmark state to be verified.
