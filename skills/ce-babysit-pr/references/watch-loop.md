# Watch loop: scheduling, state, dedup, edge cases

Read this before acting on the first tick. `SKILL.md` owns ordering; this file owns scheduling, durable state, claim/act/confirm, and re-entry.

## Sustain The Watch

`pr-snapshot watch` is a deterministic background detector. It polls GitHub, prints one `BABYSIT_WAKE` JSON line when work or a stop condition appears, then exits. Background it and wait with the runtime's background-and-wake capability. One wake causes one agent tick and one re-arm. Never replace that reasoning loop with a shell script.

Watcher ownership is latest-valid-watcher-wins. A replacement preflights before superseding the active watcher. Wakes carry `watch_generation`; compare it with a fresh snapshot and discard stale or already-cleared wakes. `invocation-superseded` ends the old loop without acting.

When no background-and-wake capability exists, checkpoint mode runs one tick, persists, reports that monitoring is paused, and prints one host-rendered resume invocation. A foreground sleep or detached process is not a substitute.

For resume syntax, default to `/ce-babysit-pr <url>` and append non-target posture. Use `$ce-babysit-pr ...` only on a runtime that documents that form. Render one inline invocation.

State lives at `<jj-workspace-root>/.tmp/ce-babysit-pr/<host>-<owner>-<repo>-<pr>/state.json`. If `jj workspace root` fails, use `<current-directory>/.tmp/...`. All transient and durable watcher files resolve under that path. Ensure `.tmp/` is ignored before another JJ command snapshots the working copy. The host component prevents public GitHub and Enterprise PRs with the same owner/repo/number from sharing state. The helper locks all state access and writes replacement files in that same directory.

The in-session watch is session-bound. A durable scheduler must start from the same workspace so it resolves the same `.tmp` state. Re-set `SKILL_DIR`, `WORKSPACE_ROOT`, and `STATE_DIR` in every shell call.

## Cadence

- Poll about every 150 seconds while active; widen only when quiet and no short review drain is active.
- Leave the ordinary `--settle-seconds` unset so the helper's 300-second default applies. Set it only after the review-signal judgment rejects a candidate wake.
- Set `--blocked-external-drain-seconds` only after an approval-gate wake.
- Every re-arm carries the same invocation ID, start, and budget. Only the first snapshot starts an invocation; only a layer transition continues it.
- After a mutation, snapshot at the start of the next tick, not midway through the current tick.
- Honor GitHub rate limits.

## Pipeline Bound

`mode:pipeline` runs synchronous ticks until one condition decides:

- Success requires checks present and green, zero actionable backlog, no current human decision, certain `MERGEABLE`/`CLEAN` state, and null base, stack, currency, and unrequested-merge blockers.
- A non-empty canonical decision set with no independent autonomous work returns `needs-human` immediately.
- Otherwise stop at the supplied round/time budget with precise residuals. Never wait for human review, approval, or the interactive settle window.

Use a native non-blocking wait for CI. If none exists, return control to the orchestrator after one tick rather than sleeping or spinning.

## Non-Convergence

The helper emits trajectory facts; it never declares non-convergence. When a trigger in `tick.md` fires, pass those facts to `ce-debug` or `ce-resolve-pr-feedback`. The delegate must either identify bounded progress or return one typed decision covering the whole blocked stream.

Progressive migration from one fixed failure to a new independent failure is normal. Recurrence, cycling failure sets, one unsatisfied invariant moving across sites, or superlinear fix growth may indicate oscillation. Correct equivalent findings across sites route to the resolver for a bounded-class assessment; the babysitter does not infer semantic equivalence from counters.

External base movement, dependency updates, flaky infrastructure, and changed bot rules are moving targets, not proof of non-convergence. Contradictory conclusions from review and CI become one cross-stream decision. A current decision blocks readiness until answered or until its frozen source observations change.

## State Contract

The state records PR identity, head OID, invocation clock, watcher ownership, check/thread/comment observations, dispatched work, canonical human decisions and answers, review lifecycle, merge identity, branch currency, chain classification, settle activity, and trajectory. `pr-snapshot` owns the schema and migration.

Every snapshot emits the attention set plus merge, base, chain, currency, review, budget, and trajectory facts. Persisted-state age is not invocation elapsed time. A new head clears head-scoped CI dispatch but does not erase unrelated durable decisions unless their source observations changed.

## Claim, Act, Confirm

Observation alone never marks work handled.

- Review threads remain actionable until a successful resolver pass is marked or remote truth resolves them. Later reviewer activity reopens dispatched threads.
- Non-thread feedback remains actionable until classified and marked. A new comment has a new identity; routine bot edits do not reopen an already dispatched status comment.
- Failing checks remain actionable until marked for the current head. A new head invalidates those marks.
- Typed decisions are the sole coverage layer for their exact source observations. Remote activity invalidates a decision but never counts as the user's answer.
- Branch-currency mutation requires an atomic exact-item claim. Re-entry to a claimed item is reconciliation-only. Retry once only after conclusive no-mutation evidence; ambiguous evidence parks.

For conflict evidence, preview in a dedicated JJ workspace under `.tmp`. Fingerprint sorted conflicted paths and JJ conflict-term identities, excluding the base OID. Changed evidence reopens attention; unchanged evidence remains parked.

## Merge Identity And Currency

GitHub supplies mergeability, but readiness requires binding it to the current base and head. The helper compares `baseRef.target.oid` with an independent exact-ref read and checks generated merge parents. The REST Git-ref endpoint is primary. Non-interactive Git transport authenticated by `gh auth git-credential` is the required fallback only when REST returns 404; it is a read-only remote probe, not a local Git workflow.

Branch currency is separate from mergeability. Only the exact emitted item permits maintenance. Managed stacks and uncertain manager/relationship probes are excluded from ordinary currency repair.

- `BEHIND` uses GitHub's update-branch endpoint with the observed head precondition, then `jj git fetch` and JJ ancestry verification.
- `DIRTY` uses the exact-base JJ merge-change workflow in `branch-currency.md`. JJ records conflicts as first-class change state and has no interrupted merge/continue protocol.
- Manual dependency repair never mutates dependent bookmarks.
- A host or remote head move requires fresh fetch and reconciliation, never an unsafe overwrite.

## Managed Stacks

Managed continuation requires a fresh positive manager probe. Before local manager reads, run `jj git export` so `gh stack` sees JJ bookmarks. Semantic work uses dedicated JJ changes and tracked bookmarks; JJ has no current bookmark.

After an owned target push, preserve dependents through the bounded interop recipe in `stack-commands.md`: save the empty JJ working-copy change, export, let `gh stack` perform its manager-owned operation, import, fetch, inspect for divergent changes or conflicted bookmarks, then restore the saved change. Never invoke raw Git, bypass JJ push safety, or assume a multi-ref push was atomic.

One watcher probes downstack. A lower layer reopening returns the one writer lane to the lowest affected layer after any current delegate completes. Manual chains never enter managed continuation.

## Readiness And Re-Entry

Use GitHub's certain `MERGEABLE`/`CLEAN` result only after current base/head identity is proven, then require chain and currency blockers clear. A managed target is ready only as the next PR; a manual dependency is ready only relative to its parent.

The settle clock moves on check, feedback, head, review, merge, or signal changes. A live or previously observed incomplete review lifecycle follows `settle.md`; silence alone proves nothing.

On re-entry:

- Run `jj git fetch` before comparing local and remote bookmarks.
- Inspect `jj status`, `jj log`, bookmark conflicts, and the exact saved change ID.
- A persisted conflicted JJ change is resumable state, not an interrupted operation. Resume or abandon only that known change; never layer a second attempt over it.
- No push access, a conflicted bookmark, an unexpected remote move, or uncertain fork routing parks rather than overwrites.
- Closed or externally merged PRs exit cleanly; a merge performed by this run under `stack-land` is a layer transition.
- Rate limits back off to the reset time.

Interactive mode keeps watching around standing residuals until a true stop. Pipeline mode returns the canonical decision set once independent work is exhausted. Checkpoint mode ends after its report and resume path.
