# Determining the reviewed diff and scope

Read this at Stage 1. It owns scope resolution for every invocation path and the deterministic scope signals Stage 3 consumes.

### Stage 1: Determine scope

Compute the diff range, file list, and diff. Minimize permission prompts by combining into as few commands as possible.

**If `base:` argument is provided (fast path):**

The caller already knows the diff base. Skip all trunk detection and remote resolution. Resolve the fork point between the provided revision and the working-copy commit:

```
jj log -r 'exactly(fork_point(@ | <base-revision>), 1)' --no-graph -T 'commit_id ++ "\n"'
```

Set `BASE` to the returned commit ID. If the command cannot resolve one unique fork point, set `BASE` to the provided revision exactly as before.

Then set `FILES:` and `DIFF:` from these commands:

```
jj diff --from "$BASE" --to @ --name-only
jj diff --from "$BASE" --to @ --git --context 10
```

This path works with any unambiguous JJ revision expression, including a commit ID, change ID, bookmark, or remote bookmark. Callers reviewing the current workspace should pass explicit `base:` when auto-detection is unnecessary. **Do not combine `base:` with a PR number or bookmark target.** If both are present, stop with an error: "Cannot use `base:` with a PR number or bookmark target — `base:` implies the current workspace is already on the correct line of work. Pass `base:` alone, or pass the target alone and let scope detection resolve the base."

**If a PR number or GitHub URL is provided as an argument:**

Do **not** edit the PR head revision. Scope comes from GitHub read APIs plus optional local alignment when the working-copy commit `@` already descends from the PR head.

**Skip-condition pre-check.** Before scope detection, run a PR-state probe:

```
gh pr view <number-or-url> --json state,title,body,files
```

Apply skip rules in order:

- `state` is `CLOSED` or `MERGED` -> stop with reason `PR is closed/merged; not reviewing.`
- **Trivial-PR judgment**: spawn a lightweight sub-agent on the platform's cheapest capable model when a known override exists; otherwise omit the model override and inherit. Give it the PR title, body, and changed file paths. The agent's task: "Is this an automated or trivial PR that does not warrant a code review? Consider: dependency lock-file or manifest-only bumps, automated release commits, chore version increments with no substantive code changes. When in doubt, answer no — false negatives (skipped reviews that should have run) are more costly than false positives (unnecessary reviews)." If the judgment returns yes: stop with reason `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current workspace, or pass base:<revision> if review is intended.`

When any skip rule fires, stop without dispatching reviewers. **Default mode:** emit the reason as plain text. **`mode:agent`:** emit JSON only — `{"status":"skipped","reason":"<same message>"}` — so programmatic callers can parse the outcome. **Standalone**, **`base:`**, and **bookmark-remote** paths are unaffected. **Draft PRs are reviewed normally.**

If no skip rule fires, fetch PR metadata **without changing the working-copy commit**:

```
gh pr view <number-or-url> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments --jq '{title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, files: [.files[].path], hasPriorComments: ((.reviews | map(select(.state != "APPROVED" or .body != "")) | length) > 0 or (.comments | length) > 0)}'
```

Set `BASE:` to `pr:<number-or-url>` (logical marker, not a JJ revision). Set `EXCLUDED:` to any paths JJ reports as untracked while snapshotting the **current** workspace (usually empty during PR-remote review).

**PR scope mode.** Classify as **`local-aligned`** only when **all** of these hold; otherwise use **`pr-remote`**. A matching bookmark name alone is not enough — a fork PR or stale local bookmark can share a name with the PR head while pointing at unrelated code, and trusting the name would diff and inspect the wrong tree.

1. A local bookmark named `headRefName` targets an ancestor of `@`; test the intersection `bookmarks(exact:"<headRefName>") & ::@` and require exactly one revision.
2. The PR is **not** cross-repository (`isCrossRepository` is false).
3. The GitHub `headRefOid` resolves to exactly one JJ commit in `::@`; test `exactly(commit_id(<headRefOid>) & ::@, 1)`. This confirms the working-copy commit actually carries the PR head (allowing unpushed local fixes layered on top) rather than an unrelated same-named bookmark.

- **`local-aligned`** — all three checks pass. Local Read/Grep/`jj file annotate` against workspace files are valid for PR changed paths.
- **`pr-remote`** — any check fails. The working-copy commit is **not** aligned with the PR head; workspace file contents for changed paths may be stale or unrelated.

**Diff by scope mode** (do not mix remote and local diffs — contradictory hunks cause false positives):

- **`local-aligned`:** Resolve `<resolved-base-revision>` from the GitHub `baseRefName` as `<baseRefName>@origin` (run `jj git fetch --remote origin --branch <baseRefName>` if needed). Compute `BASE` as the single revision selected by `fork_point(@ | <resolved-base-revision>)`, then set `FILES:` from `jj diff --from "$BASE" --to @ --name-only` and `DIFF:` from `jj diff --from "$BASE" --to @ --git --context 10`. This includes all snapshotted changes from the fork point through the working-copy commit; JJ has no staging area, and new non-ignored files are tracked automatically by default. Do **not** call `gh pr diff` or append remote hunks — when unpushed fixes exist, the local workspace is canonical. Note in Coverage: `scope: local-aligned (PR; local workspace diff)`.
- **`pr-remote`:** Set `FILES:` from the PR `files` array. Set `DIFF:` from `gh pr diff <number-or-url> --color=never`. If `gh pr diff` fails, stop with an actionable error — do not fall back to changing `@`.

When **`pr-remote`**, before Stage 4:

1. Best-effort fetch the PR head without editing it: `jj git fetch --remote origin --branch <headRefName>`.
2. When fetch succeeds and `<headRefName>@origin` resolves to exactly one revision, set `PR_HEAD_REF=<headRefName>@origin` for reviewers and validators. When fetch or resolution fails, omit `PR_HEAD_REF` and note in Coverage — reviewers must rely on diff hunks only.
3. Best-effort fetch the PR base without editing it: `jj git fetch --remote origin --branch <baseRefName>`. When it succeeds and `<baseRefName>@origin` resolves to exactly one revision, set `PR_BASE_REF=<baseRefName>@origin` — a real JJ revision reviewers and validators use for file-level diffs (e.g. `jj diff --from <PR_BASE_REF> --to <PR_HEAD_REF> -- db/schema.rb` or `structure.sql`). The `pr:<number-or-url>` logical marker in `BASE:` stays the scope marker; `PR_BASE_REF` is the diffable base. When fetch or resolution fails, omit `PR_BASE_REF` and note in Coverage — schema-drift and other JJ diff checks fall back to diff hunks only and must **not** assume `main`.
4. Include `<pr-scope-mode>pr-remote</pr-scope-mode>` and, when set, `<pr-head-ref>...</pr-head-ref>` and `<pr-base-ref>...</pr-base-ref>` in the Stage 4 review context bundle.

Reviewers and Stage 5b validators in **`pr-remote`** mode must **not** Read/Grep workspace paths for files in `FILES:`. Inspect via `jj file show -r <PR_HEAD_REF> <path>` when `PR_HEAD_REF` is set, and compare revisions via `jj diff --from <PR_BASE_REF> --to <PR_HEAD_REF> -- <path>` when both endpoints are set; otherwise use only the provided diff hunks. **`local-aligned`** uses normal workspace inspection.

**If a bookmark name is provided as an argument:**

Substitute the provided bookmark name as `<bookmark>`. Do **not** edit `<bookmark>`.

If `<bookmark>` is one of the closest local bookmarks in the ancestry of `@` (the revset `heads(::@ & bookmarks())`), use the **standalone (current workspace)** path below — same line of work, explicit bookmark name; do not use remote-only diff.

Otherwise diff the remote/local bookmark revision **without editing it**:

1. Try `gh pr view <bookmark> --json baseRefName,url,headRefName` — if a PR exists, prefer the **PR number/URL path** above (same remote diff rules).
2. Else run `jj git fetch --remote origin --branch <bookmark>` when needed, then resolve `<bookmark-ref>` as `<bookmark>@origin` or the local `<bookmark>`, in that order.
3. Resolve the default base revision with the same logic as standalone. Compute `BASE` as the single revision selected by `fork_point(<base-revision> | <bookmark-ref>)` and diff from `BASE` to `<bookmark-ref>`.
4. If `<bookmark-ref>` cannot be resolved to exactly one revision, stop: "Cannot diff bookmark `<bookmark>` without editing it. Edit that bookmark, pass its open PR URL/number, or review the current workspace with `base:`."

On success for a remote bookmark diff, set **`bookmark-remote` scope**. The working-copy commit is **not** `<bookmark-ref>`. Include `<pr-scope-mode>bookmark-remote</pr-scope-mode>` and `<bookmark-head-ref><bookmark-ref></bookmark-head-ref>` in the Stage 4 review context bundle. Reviewers and Stage 5b validators must **not** Read/Grep workspace paths for files in `FILES:`. Inspect via `jj file show -r <bookmark-ref> <path>` or diff hunks only.

Produce:

```
jj diff --from "$BASE" --to <bookmark-ref> --name-only
jj diff --from "$BASE" --to <bookmark-ref> --git --context 10
```

Treat these outputs as `FILES:` and `DIFF:` respectively.

**If no argument (standalone in the current workspace):**

Resolve `<base-revision>` from `gh pr view --json baseRefName,url` when GitHub identifies a PR for the current line of work; fetch and use `<baseRefName>@origin`. Otherwise use `trunk()` only when it resolves to exactly one non-root revision. Set `BASE` to the single revision selected by `fork_point(<base-revision> | @)`. This is the same base-resolution policy used by bookmark mode.

If no base can be resolved, **stop**. Do not fall back to `jj diff -r @` — a standalone review without the base would show only the working-copy commit's own changes and silently miss earlier commits in the line of work.

On success, produce the diff:

```
jj diff --from "$BASE" --to @ --name-only
jj diff --from "$BASE" --to @ --git --context 10
```

Treat these outputs as `FILES:` and `DIFF:` respectively. Using `jj diff --from "$BASE" --to @` compares the fork point with the snapshotted working-copy commit, so it includes the complete committed stack plus current working-copy changes. JJ has no staging-area split.

**Untracked path handling:** JJ automatically tracks new non-ignored files by default, so they appear in the `@` diff without a staging step. Paths JJ leaves untracked because of `snapshot.auto-track` or size limits are out of scope, as are untracked ignored paths. When JJ reports untracked paths during snapshotting, record them in `EXCLUDED:`, list them in Coverage, and continue on tracked changes only — never stop, prompt, or run `jj file track`.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic signals once with `scripts/review-scope.py` from this skill's directory. The helper owns endpoint validation, executable-line counting, changed-path signals, and the fail-closed lite eligibility calculation; do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and set `DIFF_A`/`DIFF_B` to its two endpoints:
- **`local-aligned` / standalone / `base:`** — `DIFF_A="$BASE"` (a resolvable JJ revision), `DIFF_B` empty (diffs base vs working-copy commit).
- **`pr-remote` / `bookmark-remote`** — `DIFF_A=<PR_BASE_REF>`, `DIFF_B=<PR_HEAD_REF>` (or `<bookmark-head-ref>`) — the fetched remote-bookmark revisions from Stage 1.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
if [ "$SCOPE_MODE" = "pr-remote" ] || [ "$SCOPE_MODE" = "bookmark-remote" ]; then
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --docs-root "<root>";
else
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --docs-root "<root>";
fi
```

Remote scope always passes both endpoint flags, even when a best-effort fetch left one value empty; the helper then fails closed instead of comparing the fetched base to the unrelated working-copy commit. Load the JSON result. `exec_lines: null`, any `uncounted_files > 0`, or helper failure disqualifies the lite path. `signals` are path heuristics, not selection decisions. Stage 3 still judges content-based risk such as auth, payments, mutation, external I/O, concurrency, and process execution. Use `test_files_changed`, `agent_surface`, and `has_learnings_corpus` as inputs to the generic reviewer gates, not as automatic spawn decisions.
