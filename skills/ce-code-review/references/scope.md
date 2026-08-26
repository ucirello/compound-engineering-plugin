# Determining the reviewed diff and scope

Read this at Stage 1. It owns scope resolution for every invocation path and the deterministic scope signals Stage 3 consumes.

### Stage 1: Determine scope

Compute the diff range, file list, and diff. Minimize permission prompts by combining into as few commands as possible.

**If `base:` argument is provided (fast path):**

The caller already knows the diff base. Skip all base-bookmark detection, remote resolution, and common-ancestor computation. Use the provided value directly:

```
BASE_ARG="{base_arg}"
BASE=$(jj log -r "heads(::$BASE_ARG & ::@)" --no-graph -T 'commit_id ++ "\n"')
[ "$(printf '%s\n' "$BASE" | sed '/^$/d' | wc -l | tr -d ' ')" = 1 ] || BASE="$BASE_ARG"
```

Then produce the same output as the other paths:

```
echo "BASE:$BASE" && echo "FILES:" && jj diff --from "$BASE" --name-only && echo "DIFF:" && jj diff --from "$BASE" --git && echo "UNTRACKED:"
```

This path works with any ref — a commit ID, `main@origin`, or a bookmark name. Callers reviewing the current working copy should pass explicit `base:` when auto-detection is unnecessary. **Do not combine `base:` with a PR number or bookmark target.** If both are present, stop with an error: "Cannot use `base:` with a PR number or bookmark target — `base:` implies the current working copy is already the intended revision. Pass `base:` alone, or pass the target alone and let scope detection resolve the base."

**If a PR number or GitHub URL is provided as an argument:**

Do **not** move the working-copy revision to the PR head. Scope comes from GitHub read APIs plus optional local alignment when `@` contains the PR head commit.

**Skip-condition pre-check.** Before scope detection, run a PR-state probe:

```
gh pr view <number-or-url> --json state,title,body,files
```

Apply skip rules in order:

- `state` is `CLOSED` or `MERGED` -> stop with reason `PR is closed/merged; not reviewing.`
- **Trivial-PR judgment**: spawn a lightweight sub-agent on the platform's cheapest capable model when a known override exists; otherwise omit the model override and inherit. Give it the PR title, body, and changed file paths. The agent's task: "Is this an automated or trivial PR that does not warrant a code review? Consider: dependency lock-file or manifest-only bumps, automated release commits, chore version increments with no substantive code changes. When in doubt, answer no — false negatives (skipped reviews that should have run) are more costly than false positives (unnecessary reviews)." If the judgment returns yes: stop with reason `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current working copy, or pass base:<ref> if review is intended.`

When any skip rule fires, stop without dispatching reviewers. **Default mode:** emit the reason as plain text. **`mode:agent`:** emit JSON only — `{"status":"skipped","reason":"<same message>"}` — so programmatic callers can parse the outcome. **Standalone**, **`base:`**, and **branch-remote** paths are unaffected. **Draft PRs are reviewed normally.**

If no skip rule fires, fetch PR metadata **without moving the working-copy revision**:

```
gh pr view <number-or-url> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments --jq '{title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, files: [.files[].path], hasPriorComments: ((.reviews | map(select(.state != "APPROVED" or .body != "")) | length) > 0 or (.comments | length) > 0)}'
```

Set `BASE:` to `pr:<number-or-url>` as a logical marker, not a JJ revision. Set `UNTRACKED:` empty; JJ snapshots non-ignored working-copy files automatically.

**PR scope mode.** Classify as **`local-aligned`** only when **all** of these hold; otherwise use **`pr-remote`**. A matching branch name alone is not enough — a fork PR or a stale local branch can share a name with the PR head while pointing at unrelated code, and trusting the name would diff and inspect the wrong tree.

1. `headRefName` is a local bookmark on `@`.
2. The PR is **not** cross-repository (`isCrossRepository` is false).
3. `jj log -r '<headRefOid>::@' --no-graph -T 'commit_id ++ "\n"'` includes `@`. This confirms the working copy carries the PR head while allowing local changes layered on top.

- **`local-aligned`** — all three checks pass. Local file inspection and `jj file annotate` against workspace files are valid for PR changed paths.
- **`pr-remote`** — any check fails. The working copy is **not** the PR head; workspace file contents for changed paths may be stale or unrelated.

**Diff by scope mode** (do not mix remote and local diffs — contradictory hunks cause false positives):

- **`local-aligned`:** Resolve `<resolved-base-ref>` from `baseRefName` with `jj git fetch --branch <baseRefName>` when needed. Resolve the unique common ancestor with `heads(::<resolved-base-ref> & ::@)`, then set `FILES:` and `DIFF:` with `jj diff --from "$BASE" --name-only` and `jj diff --from "$BASE" --git`. Do not append remote hunks; the local working copy is canonical. Note in Coverage: `scope: local-aligned (PR; local working-copy diff)`.
- **`pr-remote`:** Set `FILES:` from the PR `files` array. Set `DIFF:` from `gh pr diff <number-or-url> --color=never`. If `gh pr diff` fails, stop with an actionable error — do not move the workspace to the PR revision.

When **`pr-remote`**, before Stage 4:

1. Best-effort fetch the PR head bookmark with `jj git fetch --branch <headRefName>`.
2. When fetch succeeds, set `PR_HEAD_REF=<headRefName>@origin` for reviewers and validators. When fetch fails, omit `PR_HEAD_REF` and note in Coverage; reviewers rely on diff hunks only.
3. Best-effort fetch the PR base bookmark with `jj git fetch --branch <baseRefName>`. When it succeeds, set `PR_BASE_REF=<baseRefName>@origin`, a real JJ revision reviewers and validators use for file-level diffs. Keep the `pr:<number-or-url>` logical marker in `BASE:`. When fetch fails, omit `PR_BASE_REF` and note in Coverage; do not assume `main`.
4. Include `<pr-scope-mode>pr-remote</pr-scope-mode>` and, when set, `<pr-head-ref>...</pr-head-ref>` and `<pr-base-ref>...</pr-base-ref>` in the Stage 4 review context bundle.

Reviewers and Stage 5b validators in **`pr-remote`** mode must not inspect workspace paths for files in `FILES:`. Use `jj file show -r <PR_HEAD_REF> <path>` when `PR_HEAD_REF` is set, otherwise use only the provided diff hunks. **`local-aligned`** uses normal workspace inspection.

**If a branch name is provided as an argument:**

Substitute the provided branch name as `<branch>`. Do **not** check out `<branch>`.

If `<branch>` is a local bookmark on `@`, use the **standalone (current bookmark)** path below; do not use remote-only diff.

Otherwise diff the remote/local ref **without moving the working-copy revision**:

1. Try `gh pr view <branch> --json baseRefName,url,headRefName` — if a PR exists, prefer the **PR number/URL path** above (same remote diff rules).
2. Otherwise resolve `<branch>` as `<branch>@origin` or `<branch>` after `jj git fetch --branch <branch>` when needed.
3. Resolve the default base bookmark using the standalone logic. Resolve `BASE` as the unique `heads(::<base-ref> & ::<branch-ref>)`, then run `jj diff --from "$BASE" --to <branch-ref> --git`.
4. If `<branch-ref>` cannot be resolved locally, stop: "Cannot diff bookmark `<branch>` without moving the working-copy revision. Pass its open PR URL/number, enter a workspace at that bookmark, or review the current working copy with `base:`."

On success for remote bookmark diff, set **branch-remote scope**. The working copy is not `<branch>`. Include `<pr-scope-mode>branch-remote</pr-scope-mode>` and `<branch-head-ref><branch-ref></branch-head-ref>` in the Stage 4 review context bundle. Reviewers and validators must use `jj file show -r <branch-ref> <path>` or diff hunks only.

Produce:

```
echo "BASE:$BASE" && echo "FILES:" && jj diff --from "$BASE" --to <branch-ref> --name-only && echo "DIFF:" && jj diff --from "$BASE" --to <branch-ref> --git && echo "UNTRACKED:"
```

**If no argument (standalone on the current working copy):**

Apply the same base-detection logic as bookmark mode above. When one local bookmark points at `@`, pass that bookmark explicitly to `gh pr view --json baseRefName,url`; otherwise resolve the default base bookmark without relying on implicit Git branch state.

If no base can be resolved, stop. Do not fall back to `jj diff`; a standalone review without the base would silently miss earlier changes on the bookmark.

On success, produce the diff:

```
echo "BASE:$BASE" && echo "FILES:" && jj diff --from "$BASE" --name-only && echo "DIFF:" && jj diff --from "$BASE" --git && echo "UNTRACKED:"
```

`jj diff --from "$BASE"` compares the base revision with the current working-copy revision, including all snapshotted working-copy changes.

**Compatibility marker:** Keep `UNTRACKED:` empty. JJ snapshots every non-ignored working-copy file, so those files are already represented in `FILES:` and `DIFF:`; ignored files remain out of scope.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic signals once with `scripts/review-scope.py` from this skill's directory. The helper owns endpoint validation, executable-line counting, changed-path signals, and the fail-closed lite eligibility calculation; do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and set `DIFF_A`/`DIFF_B` to its two endpoints:
- **`local-aligned` / standalone / `base:`** — `DIFF_A="$BASE"` (a real commit ID/ref), `DIFF_B` empty (diffs base vs working copy).
- **`pr-remote` / `branch-remote`** — `DIFF_A=<PR_BASE_REF>`, `DIFF_B=<PR_HEAD_REF>` (or `<branch-head-ref>`) — the fetched refs from Stage 1.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
if [ "$SCOPE_MODE" = "pr-remote" ] || [ "$SCOPE_MODE" = "branch-remote" ]; then
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --docs-root "<root>";
else
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --docs-root "<root>";
fi
```

Remote scope always passes both endpoint flags, even when a best-effort fetch left one value empty; the helper then fails closed instead of comparing the fetched base to the unrelated local working copy. Load the JSON result. `exec_lines: null`, any `uncounted_files > 0`, or helper failure disqualifies the lite path. `signals` are path heuristics, not selection decisions. Stage 3 still judges content-based risk such as auth, payments, mutation, external I/O, concurrency, and process execution. Use `test_files_changed`, `agent_surface`, and `has_learnings_corpus` as inputs to the generic reviewer gates, not as automatic spawn decisions.
