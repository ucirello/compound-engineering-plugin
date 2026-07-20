# Cross-model Adversarial Pass

Run the adversarial brief in a separate read-only provider process. The pass uses the same `references/personas/adversarial-reviewer.md` brief and `findings-schema.json` contract, then folds into Stage 5 as `adversarial-independent`. It is non-blocking: a missing provider, timeout, or malformed return produces no artifact and never fails the review.

## Gates

Run only when `adversarial-reviewer` was selected and the working copy is the reviewed change (`local-aligned`, standalone, or `base:`). Skip `pr-remote` and `branch-remote` scopes.

## Provider Mapping

Select the provider from the runtime environment. In default interactive mode, announce the selected peer provider with the reviewer team; in `mode:agent`, keep the response JSON-only:

```bash
if [ -n "${CURSOR_AGENT:-}${CURSOR_CONVERSATION_ID:-}" ]; then REVIEW_PROVIDER=codex
elif [ "${CLAUDECODE:-}" = "1" ]; then REVIEW_PROVIDER=codex
elif [ -n "${CODEX_SANDBOX:-}${CODEX_SANDBOX_NETWORK_DISABLED:-}${CODEX_SESSION_ID:-}${CODEX_THREAD_ID:-}${CODEX_CI:-}" ]; then REVIEW_PROVIDER=claude
else REVIEW_PROVIDER=""; fi
```

An empty mapping skips silently. The script validates the selected CLI again.

## Run

Launch the script in parallel with persona reviewers and collect it before Stage 5. Resolve it from this skill's directory:

```bash
SKILL_DIR="<absolute path of the directory containing the ce-code-review SKILL.md you read>"
bash "$SKILL_DIR/scripts/cross-model-adversarial-review.sh" "<provider>" "<base-revision>" "<run-dir>"
```

- `<provider>` is the mapped provider.
- `<base-revision>` is Stage 1's resolved JJ base revision.
- `<run-dir>` is under `$(jj workspace root)/.tmp/rocketclaw/ce-code-review/<run-id>/`, or `$PWD/.tmp/rocketclaw/ce-code-review/<run-id>/` outside a JJ workspace.

Use a Bash-tool timeout of 660000 ms. If background execution is unavailable, run inline before awaiting reviewers.

## Fold Into Stage 5

- Read `<run-dir>/adversarial-independent.json` when present and treat it like another reviewer return.
- Missing file means the pass did not run; note only `independent adversarial pass: not run` in Coverage.
- Empty findings means no additional issues.
- A shared fingerprint with the in-process adversarial persona qualifies for normal independent-reviewer promotion.
