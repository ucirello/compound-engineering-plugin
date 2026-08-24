# Pipeline Mode (Non-Interactive)

Loaded when `ce-debug` is invoked with `mode:pipeline` by an orchestrator (`ce-babysit-pr`, `lfg`). The skill runs to completion without ever asking the user and returns a structured result the caller composes. The investigation rigor is unchanged — only the interaction and the fix-authority boundary change.

## Authority: you act under the orchestrator's inherited scope

Being invoked by an orchestrator is **not** itself authorization. You mutate under the **inherited** scope the orchestrator holds from the user: **actions** = fix, describe the fix change, move or create its publication bookmark, and publish it with `jj git push`; **exclusions** = merge revisions, rebase unrelated revisions, abandon unrelated changes, rewrite another publication bookmark, or approve a gated CI run. That envelope is fixed: you may narrow it by deferring a fix, but never broaden it. If making CI green requires an excluded graph or external action, defer as `needs-human` with a `decision_context`. A content-convergent fix can still be out of envelope because of the mechanism it would require.

## Non-interactive overrides (per phase)

- **Phase 0 (triage):** If an issue fetch fails, do not ask the user to paste content — proceed with the input you have and note the gap in the return. Do not ask "what have you tried"; infer prior attempts from the input.
- **Phase 2 (root cause + fix gate):** There is no "Fix it now / Diagnosis only" question. The caller invoked this skill to fix, so **fix by default — but only convergent fixes** (see the boundary below). A divergent fix is deferred, not applied.
- **Phase 3 (working-copy change):** Operate on `@`; the orchestrator owns the change and bookmark context, so never prompt to start another change or about pre-existing content. Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. Repository-local active instructions and syntax observed at runtime always win. Apply compatible Go guidance only to message quality, clarity, and structure; do not impose fixed syntax, examples, or templates. Preserve dynamic tracker tokens and other placeholders required by the active provider. Describe the fix change, create or move only its publication bookmark, and publish it with `jj git push`. Never weaken, skip, or mock a failing assertion to make it pass; repair the real issue or defer.
- **Phase 4 (handoff):** No prompt. Emit the structured return below. Skip the compound offer.
- **Quality tail (simplify/review):** Skip in pipeline to bound cost and nesting depth; the orchestrator scopes review at its own level. Keep the Phase 3 tests.

## The fix-authority boundary: convergent vs divergent

Apply a fix only when it **converges to intended behavior** — it repairs the real defect so the code meets its planned/tested intent (a genuine bug: null deref, off-by-one, a broken call, a regression against a test that encodes intended behavior).

**Defer** (do not apply) any fix that would **diverge from intended behavior**: it would change a deliberate contract, API shape, default, or product/UX decision rather than repair a bug; the failure is a test asserting a deliberate behavior that the fix would reverse; or making CI green would require a product/design call. This boundary is evidence-gated and rare, never a reason to dodge a real fix. When genuinely unsure whether a failure is a bug or a deliberate-behavior conflict, prefer deferring with a crisp `decision_context` over guessing.

### Emergent trade-offs (when the caller passes a `trajectory`)

Some divergence isn't visible in one pass — it emerges across rounds as **ping-pong**: your fix for A surfaces B, the fix for B brings A back. When the orchestrator supplies a trajectory of recurring checks and revisions since progress, reason over it before fixing again and hold the anti-cry-wolf line:

- **Progressive failure migration** — A fixed, B appears *once*, you fix B, done — is ordinary multi-step repair. **Keep fixing.** Do not park it.
- **Oscillation** — the *same* check/invariant returns after a fix aimed at it, defects cycle, or each fix trades one failure for another — means A and B can't both hold without a larger change. That larger change is a **product/design decision**, so **defer**: apply nothing this round and return `needs-human`, with a `decision_context` that names the two failures in tension, why they can't be reconciled without a divergent change, the options, and your lean.
- **Moving-target guard:** if the recurrence traces to an external cause (an updated trunk bookmark, a dependency bump, or flaky infrastructure) rather than your fixes fighting each other, it is *not* an emergent trade-off. Keep fixing and note the external cause. Recurrence is only meaningful when your own fixes oscillate.

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
  "change_id": "<Jujutsu change ID of the fix, when fixed-and-pushed or fixed-not-pushed>",
  "commit_id": "<current commit ID of that change, when fixed-and-pushed or fixed-not-pushed>",
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

- `fixed-and-pushed` — a convergent fix was applied, tests pass, its change is described, and `jj git push` published its bookmark.
- `fixed-not-pushed` — the same fix is applied and described locally, but publication did not happen because no suitable remote exists, access or authority is absent, or `jj git push` was rejected. Return both local IDs and put the reason in the first residual. Never report this as `fixed-and-pushed`, because the remote bookmark did not move, or as `diagnosed-no-fix`, because the fix is applied.
- `flaky-infra` — a flake or infrastructure failure, not a code defect (the caller may retry).
- `needs-human` — the failure requires a divergent/product decision; nothing applied; see `residuals`.
- `diagnosed-no-fix` — root cause found but no safe convergent fix available this run; see `residuals`.
