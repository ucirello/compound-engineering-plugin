# Stack scope, traversal and native maintenance

## One posture per run

| Posture | Authority and stop |
|---|---|
| `target` | Named PR only; stop at looks-ready. Offer stack-wide once only for a positively confirmed multi-layer stack needing work. Decline preserves target-local scope. Never merge. |
| `stack-ready` | Carry the confirmed stack bottom-up. A layer with zero actionable backlog and no standing residual is quiescent and may be passed while CI still runs; keep lower layers probed. Never merge. |
| `stack-land` | Same traversal plus explicit run-level land authority. Land the bottom-most open layer only after full settle/pipeline green, then verify MERGED and synchronize native topology before advancing. Quiescence alone never authorizes landing. |

Named PR without stack intent defaults to `target`; explicit whole-stack work means `stack-ready`, explicit landing intent means `stack-land`. Prefer actual intent over keyword matching. Pipeline uses supplied scope only and never asks. Restate `posture:target|stack-ready|stack-land` at each transition; posture is separate from watch/checkpoint/pipeline/duration.

## Classification and scope

The helper reads authoritative host stack GraphQL metadata directly, without a Git-backed CLI. `manager_status == "confirmed"` requires positive membership of the actual target. A successful null stack means absent; schema-unavailable means absent only with a successful independent default-branch lookup. Auth/transport/rate-limit/malformed/other GraphQL/default-branch failures stay `probe-error`. When host membership is absent, an explicitly authorized native stack handoff may prove membership through exact live PR identities/parent links and fetched JJ ancestry per `stack-commands.md`; it cannot override host metadata or probe errors. Without either confirmation, manual chains and uncertainty remain target-local. Do not silently import, adopt, change metadata or infer managed membership from topology alone.

Inspect ordered entries before semantic work. Under `target`, when a requested middle layer has unsettled downstack, offer once to begin at the lowest unsettled eligible layer and continue upward, or retain target-only. When the original target settles, the same one-time scope decision may offer its immediate open upstack layer if needed; never repeat an already answered offer. Explicit whole-stack intent already authorizes traversal. Under stack-wide scope, begin at the lowest unsettled non-draft downstack layer, or the requested layer when all lower layers are settled. This never authorizes creating/adopting a stack. In pipeline, unsupplied scope expansion is a residual.

## Mutation and recovery

Read `references/stack-commands.md` for the mandatory native JJ/bookmark + direct gh lifecycle: exact remote/head/parent verification, recoverable pre-push baseline, bounded first-dependent-upward rebases, guarded per-bookmark pushes, conflict/lease-rejection recovery, partial-progress accounting and host metadata preservation. No Git-backed stack dispatcher is an active route. Before a delegate may push, require clean work and verified membership; failed preconditions stop the invocation in all modes before delegate/tick/re-arm, with residual and resume invocation. Do not require unsupported atomic multi-ref proof; always inspect partial results.

After a delegate pushes, retain its SHA and preserve only the verified upstack, never rewrite the target or trunk. Re-probe every intended layer after success or rejection. A missing metadata-preserving native capability is `stack-blocked`, not permission to omit maintenance or report readiness. Upstack propagation is implicit in authorized babysitting of a managed target, but review/CI mutation of another PR requires stack-wide scope. Only this coordinator owns propagation and landing; target delegates cannot broaden into rebase/force/merge. Unknown or pre-existing target staleness is a stack-sync residual, not ordinary base currency work.

## Single-writer traversal

Keep one mutated target and one watcher. Arm repeated `--downstack-pr <N>` for every open lower layer; `downstack-actionable` returns to the lowest re-opened eligible layer. Wait for in-flight target delegates before moving. Re-probe order, membership and downstack quiescence at each transition, immediately before mutation and at looks-ready. Loss of confirmation ends continuation with a classification residual, not manual-chain fallback.

Stop the old watcher before each transition; align the clean JJ workspace to the exact verified next PR head per setup.md, without another approval. Pass `--continue-invocation` with the same `--invocation-id`, `--session-started-at`, `--invocation-budget-seconds`, plus `--continue-dead-time-seconds <prior-layer-invocation_dead_time_seconds>` and the same posture. No layer renews the budget or recounts excluded suspended time.

Never skip a draft outside explicit scope or pass a layer with standing `needs-human`/red/blocking residuals. Under interactive mode keep driving independent streams of the active human-blocked layer; pipeline returns the canonical residual set once autonomous work ends. Otherwise stop at end of stack, budget or user stop. A quiescent layer may advance under `stack-ready`; freshly verify every already-quiescent layer passed and report each layer's actual settled/quiescent state, not whole-stack readiness by implication.

## Land before plain advance

Under `stack-land`, when the bottom-most open layer settles (or passes pipeline green), execute the native land/synchronize procedure in `stack-commands.md` before any plain advance; never walk past an eligible settled open prefix without landing it. A merely quiescent bottom layer may be walked past but not merged. Queue acceptance is not MERGED; watch it or return a queued pipeline residual. Verify actual merge and metadata-preserving retarget/restack before transitioning. Partial land/sync failure stays a precise recoverable residual, not success. This run's completed merge is a layer transition; externally observed MERGED/CLOSED remains a true terminal stop. Pipeline cannot return success until authorized land+sync is complete, then continues its original bound on the next eligible layer. Under `target`/`stack-ready`, readiness leaves the final merge decision with the human.
