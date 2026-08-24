# Managed stacks: posture, discovery, transitions, upstack maintenance, landing

## Posture

Hold exactly one posture for the run. Carrier: `posture:target|stack-ready|stack-land`, distinct from watch mode and duration. Re-state it on every managed-stack `--continue-invocation` transition with the existing budget fields.

| Posture | Behavior |
| --- | --- |
| `target` | Only the named PR. Stop at looks-ready. May offer stack-wide once when a confirmed multi-layer managed stack needs work. Never merges. |
| `stack-ready` | When the active layer is quiescent, continue to the next open non-draft upstack layer needing work. Lower layers remain probed and the lowest reopened layer pulls the walk back. Never merges. |
| `stack-land` | Traverse as `stack-ready`. Selecting it authorizes landing the bottom-most open settled prefix through the provider after the full readiness gate. |

Quiescent means zero actionable feedback/CI, no standing residual, no open or claimed currency item, and no delegate in flight. Settled remains the stricter Step 3 gate. Named one PR defaults to `target`; intent to own the stack selects `stack-ready`; intent to land selects `stack-land`. In `mode:pipeline`, use only supplied scope and never ask.

## Discovery And Continuation

Classify every target from a fresh snapshot. Accept managed membership only when `gh stack view --json` contains that PR or the read-only GraphQL fallback positively confirms it. Manual dependency chains and `probe-error` remain target-local and mutation-conservative. Discovery never imports a stack, changes the working copy, moves a bookmark, or writes remote state.

For confirmed membership, inspect provider order before semantic work. Under `target`, offer stack-wide scope once when an unsettled downstack layer exists or when the requested layer settles and an immediate open upstack layer needs work. Under stack-wide posture, begin at the lowest unsettled in-scope non-draft layer and proceed upward without asking again. Never skip or enter an out-of-scope draft, advance past a human-blocked layer, or continue after manager confirmation is lost.

Keep one active target, one Jujutsu workspace, and one watcher. At each transition, stop the old watcher, revalidate provider order, prepare a clean empty working-copy change on the next PR's tracked remote bookmark, and initialize that PR's state with `--continue-invocation`, the same invocation ID/start/budget, the prior layer's `invocation_dead_time_seconds`, and the same posture. One budget covers the traversal.

## Pre-Push Baseline

Before a delegate may push a confirmed managed target, record the manager-ordered open bookmarks at or above it and each bookmark's local and remote target commit IDs on the selected Jujutsu remote. Require an empty conflict-free working-copy change based on the target bookmark and still-confirmed membership. Failure is a true stop: do not delegate, tick, or re-arm; report the residual and resume invocation. Jujutsu lease-checks each bookmark push, so always fetch and re-probe instead of assuming a multi-bookmark transaction.

## Upstack Maintenance

After an authorized target push, retain the pushed commit ID and re-run `gh stack view --json`. Require the same target and order, then fetch the target and every open dependent bookmark with `jj git fetch`. The target's local and remote bookmarks must both equal the pushed commit ID; movement or conflict becomes a residual and is never overwritten.

Select the first open dependent immediately above the target. If none exists, no cascade is needed. Otherwise use `jj rebase --branch <first-dependent-bookmark> --onto <target-bookmark>` so Jujutsu moves the dependent layer's ancestors not already in the destination as well as its descendants, while advancing attached bookmarks. Record the exact operation ID created by that owned rebase before any later operation. Before any push, require the target bookmark to remain unchanged and the rewritten range to contain no conflicts. On conflict, use `jj undo` only after proving the owned rebase is still the latest operation and no concurrent operation needs preservation. Otherwise use `jj op revert <owned-operation-id>`; if safe reversal cannot be established, stop and surface that operation ID in a recoverable `needs-human` residual.

Push every rewritten dependent bookmark explicitly with `jj git push --remote <tracking-remote> --bookmark <bookmark>`. Never use `--all` or bypass a lease rejection. After every success or rejection, fetch and compare the target and all open dependents with the baseline and expected rewritten tips. Treat already-updated remote bookmarks as observed progress and name the first rejected or divergent layer precisely. Recipes are in `references/stack-commands.md`.

## Watch And Layer Transitions

Arm one watcher with `--downstack-pr <N>` for every open lower layer. On `downstack-actionable`, finish any in-flight delegate, stop the watcher, and return to the lowest reopened in-scope non-draft layer. Recheck order and downstack quiescence at every transition, before mutation, and at readiness. Never mutate two layers concurrently.

Under `stack-ready`, advance from a quiescent layer after a fresh manager/downstack check, even while CI or settle time continues under the probe. Under `stack-land`, a quiescent layer may be traversed but the bottom-most open layer is landed only when settled. A `needs-human` layer remains active while independent streams continue.

When `stack-land` is authorized and the bottom-most open prefix satisfies the interactive settle or pipeline success gate, use the provider-owned `gh stack merge <PR> --yes --squash` and `gh stack sync --remote <tracking-remote>` recipes. Re-probe because merge queues can leave the PR open after enqueue. Advance only after the landed PR is actually `MERGED`; a merge/sync failure becomes a residual and never falls back to `gh pr merge`. Provider landing does not replace Jujutsu local fetch, bookmark, rebase, or push semantics.
