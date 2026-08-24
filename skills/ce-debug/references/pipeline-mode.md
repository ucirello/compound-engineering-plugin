# Pipeline mode (non-interactive)

Loaded when `ce-debug` is invoked with `mode:pipeline` by an orchestrator (`ce-babysit-pr`, `lfg`). The skill runs to completion without asking the user and returns a structured result the caller composes. Investigation rigor is unchanged; only interaction and fix authority change.

## Authority: you act under the orchestrator's inherited scope

Being invoked by an orchestrator is **not** itself authorization. Mutate under the inherited scope the orchestrator holds from the user: **actions** = fix, describe the current working-copy change, move or create its publication bookmark, and push that bookmark; **exclusions** = merge, rebase, bypass Jujutsu push safety, or approve a gated CI run. Narrow or defer this envelope, never broaden it. If completion requires an excluded operation, return `needs-human` with `decision_context`.

## Non-interactive overrides (per phase)

- **Phase 0 (triage):** If an issue fetch fails, do not ask the user to paste content — proceed with the input you have and note the gap in the return. Do not ask "what have you tried"; infer prior attempts from the input.
- **Phase 2 (root cause + fix gate):** There is no "Fix it now / Diagnosis only" question. The caller invoked this skill to fix, so **fix by default — but only convergent fixes** (see the boundary below). A divergent fix is deferred, not applied.
- **Phase 3 (workspace/change):** Operate in the orchestrator-owned workspace and working-copy change without prompting. Record `@`'s change ID and commit ID, describe the fix, and point the intended publication bookmark at that revision with `jj bookmark set <bookmark> -r <fix-revision>`. Resolve `<publication-remote>` as the unique writable, PR-capable remote by reconciling the bookmark's tracked remote bookmarks with the provider repository; never default to `origin`. If those signals identify multiple remotes or disagree, stop publication and return `fixed-not-pushed` with the ambiguity as the first residual. Otherwise fetch `<publication-remote>`, inspect exactly `<bookmark>@<publication-remote>..<bookmark>`, and publish only that bookmark with `jj git push --remote <publication-remote> --bookmark <bookmark>`. Confirm that remote bookmark moved before returning `fixed-and-pushed`. Never weaken, skip, or mock a failing assertion to make it pass; repair the real issue or defer.
- **Phase 4 (handoff):** No prompt. Emit the structured return below. Skip the compound offer.
- **Quality tail (simplify/review):** Skip in pipeline to bound cost and nesting depth; the orchestrator scopes review at its own level. Keep the Phase 3 tests.

## The fix-authority boundary: convergent vs divergent

Apply a fix only when it **converges to intended behavior** — it repairs the real defect so the code meets its planned/tested intent (a genuine bug: null deref, off-by-one, a broken call, a regression against a test that encodes intended behavior).

**Defer** (do not apply) any fix that would **diverge from intended behavior**: it would change a deliberate contract, API shape, default, or product/UX decision rather than repair a bug; or the "failure" is a test asserting a deliberate behavior that the fix would reverse; or making CI green would require a product/design call. This mirrors the `ce-resolve-pr-feedback` intent-conflict tripwire — evidence-gated and rare, never a reason to dodge a real fix. When genuinely unsure whether a failure is a bug or a deliberate-behavior conflict, prefer deferring with a crisp `decision_context` over guessing.

### Emergent trade-offs (when the caller passes a `trajectory`)

Some divergence isn't visible in one pass — it emerges across rounds as **ping-pong**: your fix for A surfaces B, the fix for B brings A back. When the orchestrator seeds you with a `trajectory` (`recurring_checks`, `check_recur_max`, `changes_since_progress`), reason over it before fixing again — and hold the anti-cry-wolf line:

- **Progressive failure migration** — A fixed, B appears *once*, you fix B, done — is ordinary multi-step repair. **Keep fixing.** Do not park it.
- **Oscillation** — the *same* check/invariant returns after a fix aimed at it, defects cycle, or each fix trades one failure for another — means A and B can't both hold without a larger change. That larger change is a **product/design decision**, so **defer**: apply nothing this round and return `needs-human`, with a `decision_context` that names the two failures in tension, why they can't be reconciled without a divergent change, the options, and your lean.
- **Moving-target guard:** if the recurrence traces to an external cause (a trunk update, a dependency bump, flaky infrastructure) rather than your fixes fighting each other, it is *not* an emergent trade-off — keep fixing, and note the external cause. Recurrence is only meaningful when your own fixes are what oscillate.

To defer, name the invariant the fix would need to satisfy and why no bounded convergent change satisfies it. If unsure it's genuine oscillation vs one more real bug, prefer one more convergent attempt over a premature park.

## Surfacing a deferred (divergent / needs-human) item

Never write a PR-body section. Never block. Surface it so the human sees it after the run:

- If it maps to an **open review thread**, leave that thread open (and attach the `decision_context` as a reply when a thread reply is in scope).
- Otherwise, **return it in the `residuals` list** for the caller to place in its single run-report comment. For a bare `ce-debug` invocation with no orchestrator and no PR, file it as a ticket in the project's tracker (detected in Phase 1.4) with enough background to action it standalone; when no tracker is reachable, return it in the structured result and say plainly that nothing else recorded it.

Return each decision in the shared typed residual contract. Its `sources` enumerate every item the decision owns: each failing check key with `kind: "check"`, plus the stable ID and kind of every open review thread, comment, or review body represented by the same decision. `decision_context` contains the quoted failure, investigation, decision reason, options with tradeoffs, and nullable recommendation. `thread_urls` includes every owned open thread and is empty only when no source is a thread. The caller persists and invalidates the complete source set as one unit, so never split, omit, or summarize source ownership.

## Structured return

The skill's final output in pipeline mode is machine-readable (the caller parses it):

```json
{
  "status": "fixed-and-pushed | fixed-not-pushed | diagnosed-no-fix | flaky-infra | needs-human",
  "summary": "<one line: what happened>",
  "root_cause": "<causal chain, brief>",
  "changed_files": ["..."],
  "change_id": "<Jujutsu change ID when fixed>",
  "commit_id": "<Jujutsu commit ID when fixed>",
  "residuals": [
    {
      "type": "needs-human",
      "sources": [
        { "id": "<failing-check-key>", "kind": "check" },
        { "id": "<owned-open-thread-id, when any>", "kind": "thread" }
      ],
      "decision_context": {
        "quoted_feedback": "<the failure or constraint in tension>",
        "investigation": "<what was inspected and found>",
        "decision_reason": "<why no bounded convergent fix is safe>",
        "options": [ { "option": "<choice>", "tradeoff": "<gain and loss>" } ],
        "recommendation": "<lean and why, or null>"
      },
      "thread_urls": ["<URL for every owned open thread, or empty when none>"]
    }
  ]
}
```

- `fixed-and-pushed` — a convergent fix was applied, tests pass, the change was described, its bookmark was pushed, and remote state confirms the move.
- `fixed-not-pushed` — the same fix is described locally, but the bookmark was not pushed because no suitable remote/bookmark exists, access is unavailable, the envelope excludes publication, or Jujutsu rejected the push. Include both IDs and make the first residual explain why. Never report this as `fixed-and-pushed` when the remote bookmark did not move, or as `diagnosed-no-fix` when the fix exists locally.
- `flaky-infra` — a flake or infrastructure failure, not a code defect (the caller may retry).
- `needs-human` — the failure requires a divergent/product decision; nothing applied; see `residuals`.
- `diagnosed-no-fix` — root cause found but no safe convergent fix available this run; see `residuals`.
