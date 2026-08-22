# ce-debug pipeline mode

Run without questions under the orchestrator's inherited scope: fix, describe, and push the current working-copy change and bookmark. Merge, rebase, bypassed safety, and gated-run approval remain excluded. Narrow or defer; never broaden.

## Overrides

- Failed issue fetch: proceed with available input and report the gap.
- Root-cause gate: fix convergent defects; defer divergent behavior or product decisions.
- Workspace: use the orchestrator-owned working-copy change and bookmark stack without prompting. Never weaken an assertion to make it pass.
- Handoff: emit the structured return below and skip interactive quality and learning offers.

Based on https://go.dev/wiki/CommitMessage and on past commit messages that you can see in `git log`, compose commit messages adherent to the present standards. The project's active instructions and the description syntax observed at runtime in `jj log` win. Apply compatible Go guidance only to quality, clarity, and structure; it does not prescribe imperative mood, casing, punctuation, line wrapping, subject/body shape, or any fixed syntax.

## Fix Authority

Apply only a bounded fix that converges to intended behavior. Defer a change that reverses a deliberate contract, API, default, UX decision, or intended test expectation. When uncertain, return `needs-human` with decision context.

When a supplied trajectory shows the same invariant recurring because this workflow's fixes trade failures back and forth, defer the larger product/design decision. A new failure appearing once, or recurrence from an external base/dependency/infrastructure change, remains ordinary repair.

## Residuals

Never write a PR-body section. Keep matching review threads open and attach decision context when replying is in scope; otherwise return one typed residual owning every represented source. Preserve all source IDs, thread URLs, quoted constraint, investigation, options, tradeoffs, and nullable recommendation.

## Structured Return

```json
{
  "status": "fixed-and-pushed | fixed-not-pushed | diagnosed-no-fix | flaky-infra | needs-human",
  "summary": "<one line>",
  "root_cause": "<brief causal chain>",
  "changed_files": ["..."],
  "change_id": "<Jujutsu change ID when fixed>",
  "commit_id": "<Jujutsu commit ID when fixed>",
  "residuals": [
    {
      "type": "needs-human",
      "sources": [{ "id": "<stable source ID>", "kind": "check | thread | comment | review" }],
      "decision_context": {
        "quoted_feedback": "<failure or constraint>",
        "investigation": "<what was inspected>",
        "decision_reason": "<why no bounded convergent fix is safe>",
        "options": [{ "option": "<choice>", "tradeoff": "<gain and loss>" }],
        "recommendation": "<lean and why, or null>"
      },
      "thread_urls": []
    }
  ]
}
```

- `fixed-and-pushed`: convergent fix applied, tests pass, described, and pushed.
- `fixed-not-pushed`: fix is described locally but publication failed or was excluded; include IDs and the reason residual.
- `flaky-infra`: failure is infrastructure, not code.
- `needs-human`: no fix applied because a divergent decision is required.
- `diagnosed-no-fix`: root cause found but no safe convergent fix was available.
