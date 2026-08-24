# Determining the reviewed diff and scope

Read this at Stage 1. It owns scope resolution for every invocation path and the deterministic scope signals Stage 3 consumes.

### Stage 1: Determine scope

Compute the diff range, file list, and diff with native Jujutsu commands. Minimize permission prompts by combining into as few commands as possible.

**If `base:` argument is provided (fast path):**

The caller already knows the diff base. Skip all base-bookmark detection and remote resolution. Resolve the closest common ancestor when it is unique; otherwise use the provided value directly:

```
BASE_ARG="{base_arg}"
BASE=$(jj log --no-graph -r "heads(::@ & ::$BASE_ARG)" -T 'commit_id ++ "\n"') || BASE="$BASE_ARG"
```

Then produce the same output as the other paths:

```
echo "BASE:$BASE" && echo "FILES:" && jj diff --from "$BASE" --name-only && echo "DIFF:" && jj diff --from "$BASE" --context 10 --git
```

This path works with any Jujutsu revision, including a change ID, commit ID, local bookmark, or remote bookmark such as `main@origin`. Callers reviewing the current workspace should pass explicit `base:` when auto-detection is unnecessary. **Do not combine `base:` with a PR number or bookmark target.** If both are present, stop with an error: "Cannot use `base:` with a PR number or bookmark target — `base:` implies the current workspace is already correct. Pass `base:` alone, or pass the target alone and let scope detection resolve the base."

**If a PR number or GitHub URL is provided as an argument:**

Do **not** switch to the PR bookmark. Scope comes from GitHub read APIs plus optional local alignment when the working-copy revision already contains the PR head.

**Skip-condition pre-check.** Before scope detection, run a PR-state probe:

```
gh pr view <number-or-url> --json state,title,body,files
```

Apply skip rules in order:

- `state` is `CLOSED` or `MERGED` -> stop with reason `PR is closed/merged; not reviewing.`
- **Trivial-PR judgment**: spawn a lightweight sub-agent using a low-cost supported tier when an explicit selector exists; otherwise inherit. Give it the PR title, body, and changed file paths. Its task is to decide whether this is an automated or trivial PR that does not warrant code review, with false negatives treated as more costly than unnecessary reviews. If it returns yes, stop with reason `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current bookmark, or pass base:<revision> if review is intended.`

When any skip rule fires, stop without dispatching reviewers. **Default mode:** emit the reason as plain text. **`mode:agent`:** emit JSON only — `{"status":"skipped","reason":"<same message>"}` — so programmatic callers can parse the outcome. **Standalone**, **`base:`**, and **bookmark-remote** paths are unaffected. **Draft PRs are reviewed normally.**

If no skip rule fires, fetch PR metadata **without changing the workspace**:

```
gh pr view <number-or-url> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments --jq '{title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, files: [.files[].path], hasPriorComments: ((.reviews | map(select(.state != "APPROVED" or .body != "")) | length) > 0 or (.comments | length) > 0)}'
```

Set `BASE:` to `pr:<number-or-url>` as a logical marker, not a revision. Jujutsu automatically snapshots non-ignored working-copy files, so there is no staging-area or untracked-file list to append.

**PR scope mode.** Classify as **`local-aligned`** only when **all** of these hold; otherwise use **`pr-remote`**. A matching bookmark name alone is not enough; a fork PR or stale local bookmark can share a name with the PR head while pointing at unrelated code.

1. The closest local bookmark in `heads(::@ & bookmarks())` is `headRefName`.
2. The PR is **not** cross-repository (`isCrossRepository` is false).
3. `jj log --no-graph -r '<headRefOid>::@' -T 'commit_id ++ "\n"'` includes `@`. This confirms the working copy actually carries the PR head, allowing local fixes layered on top rather than trusting an unrelated same-named bookmark.

- **`local-aligned`** — all three checks pass. Local Read/Grep/`jj file annotate` against workspace files are valid for PR changed paths.
- **`pr-remote`** — any check fails. The working copy is **not** the PR head; workspace file contents for changed paths may be stale or unrelated.

**Diff by scope mode** (do not mix remote and local diffs — contradictory hunks cause false positives):

- **`local-aligned`:** Resolve `<resolved-base-ref>` from `baseRefName` (fetch if needed). Resolve `BASE` as the unique `heads(::<resolved-base-ref> & ::@)` revision, then set `FILES:` from `jj diff --from "$BASE" --name-only` and `DIFF:` from `jj diff --from "$BASE" --context 10 --git`. This includes every local change through the working-copy commit. Do **not** call `gh pr diff` or append remote hunks; when local fixes exist, the workspace is canonical. Note in Coverage: `scope: local-aligned (PR; local workspace diff)`.
- **`pr-remote`:** Set `FILES:` from the PR `files` array. Set `DIFF:` from `gh pr diff <number-or-url> --color=never`. If `gh pr diff` fails, stop with an actionable error — do not fall back to checkout.

When **`pr-remote`**, before Stage 4:

1. Resolve and retain `<remote>` by matching the configured JJ remotes to the PR base repository identity. For a same-repository PR, best-effort fetch its bookmarks without changing the workspace: `jj git fetch --remote <remote> --branch <headRefName> --branch <baseRefName>`. This is Git interoperability owned by Jujutsu. Do not fetch the head for a cross-repository PR whose repository identity does not match `<remote>`.
2. When the head fetch succeeds and `headRefOid` resolves in Jujutsu, set `PR_HEAD_REF=<headRefOid>` for reviewers and validators. Otherwise omit `PR_HEAD_REF` and note in Coverage; reviewers must rely on diff hunks only.
3. When `<baseRefName>@<remote>` resolves, set `PR_BASE_REF=<baseRefName>@<remote>`. This is the diffable base reviewers use for file-level `jj diff --from <PR_BASE_REF> --to <PR_HEAD_REF> <path>` checks. The `pr:<number-or-url>` marker in `BASE:` remains logical. When the base or applicable remote cannot be resolved uniquely, omit `PR_BASE_REF` and note in Coverage; schema-drift checks fall back to diff hunks and must not assume a base bookmark.
4. Include `<pr-scope-mode>pr-remote</pr-scope-mode>` and, when set, `<pr-head-ref>...</pr-head-ref>` and `<pr-base-ref>...</pr-base-ref>` in the Stage 4 review context bundle.

Reviewers and Stage 5b validators in **`pr-remote`** mode must **not** Read/Grep workspace paths for files in `FILES:`. Inspect via `jj file show -r <PR_HEAD_REF> <path>` when `PR_HEAD_REF` is set, otherwise use only the provided diff hunks. **`local-aligned`** uses normal workspace inspection.

**If a bookmark name is provided as an argument:**

Substitute the provided name as `<bookmark>`. Do **not** edit `<bookmark>`.

If the closest local bookmark in `heads(::@ & bookmarks())` is `<bookmark>`, use the **standalone (current bookmark)** path below; do not use remote-only diff.

Otherwise diff the remote/local bookmark **without changing the workspace**:

1. Try `gh pr view <bookmark> --json baseRefName,url,headRefName`; if a PR exists, prefer the **PR number/URL path** above.
2. Else resolve and retain `<remote>` by matching the configured JJ remotes to the repository identity selected by the provider, then resolve `<bookmark-ref>` as `<bookmark>@<remote>` after `jj git fetch --remote <remote> --branch <bookmark>` when needed. Use the local `<bookmark>` only when no applicable remote bookmark is required.
3. Resolve the default base bookmark. Resolve `BASE` as the unique `heads(::<base-ref> & ::<bookmark-ref>)` revision and run `jj diff --from "$BASE" --to <bookmark-ref> --context 10 --git`.
4. If `<bookmark-ref>` cannot be resolved, stop: "Cannot diff bookmark `<bookmark>` without changing the workspace. Pass its open PR URL/number, or review the current bookmark with `base:`."

On success for a remote bookmark diff, set **`bookmark-remote` scope**. The working copy is **not** `<bookmark>`. Include `<pr-scope-mode>bookmark-remote</pr-scope-mode>` and `<bookmark-head-ref><bookmark-ref></bookmark-head-ref>` in the Stage 4 review context bundle. Reviewers and Stage 5b validators must **not** Read/Grep workspace paths for files in `FILES:`. Inspect via `jj file show -r <bookmark-ref> <path>` or diff hunks only.

Produce:

```
echo "BASE:$BASE" && echo "FILES:" && jj diff --from "$BASE" --to <bookmark-ref> --name-only && echo "DIFF:" && jj diff --from "$BASE" --to <bookmark-ref> --context 10 --git
```

**If no argument (standalone on the current workspace):**

Apply the same base-detection logic as bookmark mode above, using the closest local bookmark. Pass that bookmark explicitly to `gh pr view <bookmark> --json baseRefName,url`; do not rely on implicit branch detection.

If no base can be resolved, **stop**. Do not fall back to `jj diff`; a standalone review without the base would show only the working-copy change and silently miss earlier changes in the stack.

On success, produce the diff:

```
echo "BASE:$BASE" && echo "FILES:" && jj diff --from "$BASE" --name-only && echo "DIFF:" && jj diff --from "$BASE" --context 10 --git
```

`jj diff --from "$BASE"` compares the resolved base with the working-copy commit, which already snapshots all non-ignored workspace changes without a staging area.

**Ignored file handling:** Jujutsu snapshots non-ignored files automatically. Ignored files remain out of scope unless explicitly tracked; do not manufacture a Git-style staged/untracked distinction.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic signals once with `scripts/review-scope.py` from this skill's directory. The helper owns endpoint validation, executable-line counting, changed-path signals, and the fail-closed lite eligibility calculation; do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and set `DIFF_A`/`DIFF_B` to its two endpoints:
- **`local-aligned` / standalone / `base:`** — `DIFF_A="$BASE"` (a Jujutsu revision), `DIFF_B` empty (diffs base vs working-copy commit).
- **`pr-remote` / `bookmark-remote`** — `DIFF_A=<PR_BASE_REF>`, `DIFF_B=<PR_HEAD_REF>` (or `<bookmark-head-ref>`) — the resolved revisions from Stage 1.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
if [ "$SCOPE_MODE" = "pr-remote" ] || [ "$SCOPE_MODE" = "bookmark-remote" ]; then
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --docs-root "<root>";
else
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --docs-root "<root>";
fi
```

Remote scope always passes both endpoint flags, even when a best-effort fetch left one value empty; the helper then fails closed instead of comparing the fetched base to the unrelated local working-copy change. Load the JSON result. `exec_lines: null`, any `uncounted_files > 0`, or helper failure disqualifies the lite path. `signals` are path heuristics, not selection decisions. Stage 3 still judges content-based risk such as auth, payments, mutation, external I/O, concurrency, and process execution. Use `test_files_changed`, `agent_surface`, and `has_learnings_corpus` as inputs to the generic reviewer gates, not as automatic spawn decisions.
