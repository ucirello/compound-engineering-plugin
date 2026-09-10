# Determining the reviewed diff and scope

Read this at Stage 1. It owns scope resolution for every invocation path and the deterministic scope signals Stage 3 consumes.

### Stage 1: Determine scope

Compute the diff range, file list, and diff. Minimize permission prompts by combining into as few commands as possible. Run every `jj` and `gh` invocation with cwd at the workspace root (`WS_ROOT=$(jj workspace root)`). Pair every `gh` call with `GIT_DIR=$(jj git root)`.

**If `base:` argument is provided (fast path):**

The caller already knows the diff base. Skip all base-bookmark detection, remote resolution, and merge-base computation. Use the provided value directly:

```
WS_ROOT=$(jj workspace root)
BASE_ARG="{base_arg}"
BASE=$(cd "$WS_ROOT" && jj log -r "heads(::@ & ::$BASE_ARG)" -T commit_id --no-graph --no-pager 2>/dev/null | awk 'NF{c++; v=$0} END{if(c==1) print v}')
[ -n "$BASE" ] || BASE="$BASE_ARG"
```

Then produce the same output as the other paths:

```
echo "BASE:$BASE" && echo "FILES:" && (cd "$WS_ROOT" && jj diff --from $BASE --name-only --no-pager) && echo "DIFF:" && (cd "$WS_ROOT" && jj diff --from $BASE --git --no-pager) && echo "UNTRACKED:"
```

This path works with any rev — a change/commit id, a bookmark, `main@origin`. Callers reviewing the current workspace should pass explicit `base:` when auto-detection is unnecessary. **Do not combine `base:` with a PR number or branch target.** If both are present, stop with an error: "Cannot use `base:` with a PR number or branch target — `base:` implies the current workspace is already the correct bookmark. Pass `base:` alone, or pass the target alone and let scope detection resolve the base."

**If a PR number or GitHub URL is provided as an argument:**

Do **not** edit the working-copy revision onto the PR bookmark. Scope comes from GitHub read APIs plus optional local alignment when the working copy already matches the PR head bookmark.

**Skip-condition pre-check.** Before scope detection, run a PR-state probe:

```
WS_ROOT=$(jj workspace root)
(cd "$WS_ROOT" && GIT_DIR=$(jj git root) gh pr view <number-or-url> --json state,title,body,files)
```

Apply skip rules in order:

- `state` is `CLOSED` or `MERGED` -> stop with reason `PR is closed/merged; not reviewing.`
- **Trivial-PR judgment**: spawn a lightweight sub-agent on the platform's cheapest capable model when a known override exists; otherwise omit the model override and inherit. Give it the PR title, body, and changed file paths. The agent's task: "Is this an automated or trivial PR that does not warrant a code review? Consider: dependency lock-file or manifest-only bumps, automated release commits, chore version increments with no substantive code changes. When in doubt, answer no — false negatives (skipped reviews that should have run) are more costly than false positives (unnecessary reviews)." If the judgment returns yes: stop with reason `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current branch, or pass base:<ref> if review is intended.`

When any skip rule fires, stop without dispatching reviewers. **Default mode:** emit the reason as plain text. **`mode:agent`:** emit JSON only — `{"status":"skipped","reason":"<same message>"}` — so programmatic callers can parse the outcome. **Standalone**, **`base:`**, and **branch-remote** paths are unaffected. **Draft PRs are reviewed normally.**

If no skip rule fires, fetch PR metadata **without changing the working-copy revision**:

```
WS_ROOT=$(jj workspace root)
(cd "$WS_ROOT" && GIT_DIR=$(jj git root) gh pr view <number-or-url> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments --jq '{title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, files: [.files[].path], hasPriorComments: ((.reviews | map(select(.state != "APPROVED" or .body != "")) | length) > 0 or (.comments | length) > 0)}')
```

Set `BASE:` to `pr:<number-or-url>` (logical marker — not a commit id). JJ snapshots the working copy, so there is no git-index untracked listing; emit `UNTRACKED:` empty. Ignored files stay out of `jj diff`.

**PR scope mode.** Classify as **`local-aligned`** only when **all** of these hold; otherwise use **`pr-remote`**. A matching bookmark name alone is not enough — a fork PR or a stale local bookmark can share a name with the PR head while pointing at unrelated code, and trusting the name would diff and inspect the wrong tree.

1. Current working-copy bookmarks include `headRefName`: `(cd "$WS_ROOT" && jj log -r @ -T 'bookmarks.join("\n")' --no-graph --no-pager)` lists `headRefName`.
2. The PR is **not** cross-repository (`isCrossRepository` is false).
3. The PR head commit is contained in the local working copy: `(cd "$WS_ROOT" && jj log -r '<headRefOid> & ::@' -n 1 --no-graph --no-pager)` exits 0 and prints an id. This confirms the working tree actually carries the PR head (allowing unpushed local fixes layered on top) rather than an unrelated same-named bookmark.

- **`local-aligned`** — all three checks pass. Local Read/Grep/`jj file annotate` against workspace files are valid for PR changed paths.
- **`pr-remote`** — any check fails. The working tree is **not** the PR head; workspace file contents for changed paths may be stale or unrelated.

**Diff by scope mode** (do not mix remote and local diffs — contradictory hunks cause false positives):

- **`local-aligned`:** Resolve `<resolved-base-ref>` from `baseRefName` (fetch if needed). Compute `BASE=$(cd "$WS_ROOT" && jj log -r "heads(::@ & ::<resolved-base-ref>)" -T commit_id --no-graph --no-pager | awk 'NF{c++; v=$0} END{if(c==1) print v}')`, then set `FILES:` from `(cd "$WS_ROOT" && jj diff --from $BASE --name-only --no-pager)` and `DIFF:` from `(cd "$WS_ROOT" && jj diff --from $BASE --git --no-pager)` (includes working-copy changes on the PR bookmark). Do **not** call `gh pr diff` or append remote hunks — when unpushed fixes exist, the local tree is canonical. Note in Coverage: `scope: local-aligned (PR; local tree diff)`.
- **`pr-remote`:** Set `FILES:` from the PR `files` array. Set `DIFF:` from `(cd "$WS_ROOT" && GIT_DIR=$(jj git root) gh pr diff <number-or-url> --color=never)`. If `gh pr diff` fails, stop with an actionable error — do not fall back to changing the working-copy revision.

When **`pr-remote`**, before Stage 4:

1. Best-effort fetch PR head without changing the working-copy revision: `(cd "$WS_ROOT" && jj git fetch --remote origin --branch <headRefName>)` (substitute PR number from metadata).
2. When fetch succeeds, set `PR_HEAD_REF=<headRefName>@origin` for reviewers and validators. When fetch fails, omit `PR_HEAD_REF` and note in Coverage — reviewers must rely on diff hunks only.
3. Best-effort fetch the PR base without changing the working-copy revision: `(cd "$WS_ROOT" && jj git fetch --remote origin --branch <baseRefName>)`. When it succeeds, resolve a concrete rev with `(cd "$WS_ROOT" && jj log -r '<baseRefName>@origin' -n 1 -T commit_id --no-graph --no-pager)` and set `PR_BASE_REF` to that commit id — a **real JJ base rev** reviewers and validators use for file-level diffs (e.g. `data-migration-reviewer` runs `jj diff --from <PR_BASE_REF> -- db/schema.rb`/`structure.sql`). The `pr:<number-or-url>` logical marker in `BASE:` stays the scope marker; `PR_BASE_REF` is the diffable base. When the fetch fails, omit `PR_BASE_REF` and note in Coverage — schema-drift and other diff checks fall back to diff hunks only and must **not** assume `main`.
4. Include `<pr-scope-mode>pr-remote</pr-scope-mode>` and, when set, `<pr-head-ref>...</pr-head-ref>` and `<pr-base-ref>...</pr-base-ref>` in the Stage 4 review context bundle.

Reviewers and Stage 5b validators in **`pr-remote`** mode must **not** Read/Grep workspace paths for files in `FILES:`. Inspect via `jj file show -r <PR_HEAD_REF> <path>` when `PR_HEAD_REF` is set, otherwise use only the provided diff hunks. **`local-aligned`** uses normal workspace inspection.

**If a branch name is provided as an argument:**

Substitute the provided branch name as `<branch>`. Do **not** edit the working-copy revision onto `<branch>`.

If `(cd "$WS_ROOT" && jj log -r @ -T 'bookmarks.join("\n")' --no-graph --no-pager)` lists `<branch>`, use the **standalone (current branch)** path below — same tree, explicit bookmark name; do not use remote-only diff.

Otherwise diff the remote/local rev **without changing the working-copy revision**:

1. Try `(cd "$WS_ROOT" && GIT_DIR=$(jj git root) gh pr view <branch> --json baseRefName,url,headRefName)` — if a PR exists, prefer the **PR number/URL path** above (same remote diff rules).
2. Else resolve `<branch>` as `<branch>@origin` or `<branch>` after `(cd "$WS_ROOT" && jj git fetch --remote origin --branch <branch>)` when needed.
3. Resolve default base bookmark (same logic as standalone). Compute `BASE=$(cd "$WS_ROOT" && jj log -r "heads(::<base-ref> & ::<branch-ref>)" -T commit_id --no-graph --no-pager | awk 'NF{c++; v=$0} END{if(c==1) print v}')` and `(cd "$WS_ROOT" && jj diff --from $BASE --to <branch-ref> --git --no-pager)`.
4. If `<branch-ref>` cannot be resolved locally, stop: "Cannot diff branch `<branch>` without changing the working-copy revision. Edit that bookmark, pass its open PR URL/number, or review the current bookmark with `base:`."

On success for remote branch diff, set **branch-remote scope**. The working tree is **not** `<branch>`. Include `<pr-scope-mode>branch-remote</pr-scope-mode>` and `<branch-head-ref><branch-ref></branch-head-ref>` in the Stage 4 review context bundle. Reviewers and Stage 5b validators must **not** Read/Grep workspace paths for files in `FILES:`. Inspect via `jj file show -r <branch-ref> <path>` or diff hunks only.

Produce:

```
echo "BASE:$BASE" && echo "FILES:" && (cd "$WS_ROOT" && jj diff --from $BASE --to <branch-ref> --name-only --no-pager) && echo "DIFF:" && (cd "$WS_ROOT" && jj diff --from $BASE --to <branch-ref> --git --no-pager) && echo "UNTRACKED:"
```

**If no argument (standalone on current branch):**

Apply the same base-detection logic as branch mode above, using the current bookmark (i.e., `(cd "$WS_ROOT" && GIT_DIR=$(jj git root) gh pr view --json baseRefName,url)` with no argument defaults to the current bookmark).

If no base can be resolved, **stop**. Do not fall back to `jj diff` (working-copy vs parents) — a standalone review without the base would only show the working-copy change and silently miss all committed work on the bookmark.

On success, produce the diff:

```
echo "BASE:$BASE" && echo "FILES:" && (cd "$WS_ROOT" && jj diff --from $BASE --name-only --no-pager) && echo "DIFF:" && (cd "$WS_ROOT" && jj diff --from $BASE --git --no-pager) && echo "UNTRACKED:"
```

Using `jj diff --from $BASE` (no `--to`) diffs the merge-base against the working copy, which includes all working-copy changes together. JJ has no index.

**Untracked file handling:** JJ snapshots the working copy. Non-ignored files appear in `jj diff`; ignored files stay out of scope. `UNTRACKED:` is empty. Never stop or prompt.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic signals once with `scripts/review-scope.py` from this skill's directory. The helper owns endpoint validation, executable-line counting, changed-path signals, and the fail-closed lite eligibility calculation; do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and set `DIFF_A`/`DIFF_B` to its two endpoints:
- **`local-aligned` / standalone / `base:`** — `DIFF_A="$BASE"` (a real SHA/ref), `DIFF_B` empty (diffs base vs working tree).
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

Remote scope always passes both endpoint flags, even when a best-effort fetch left one value empty; the helper then fails closed instead of comparing the fetched base to the unrelated local worktree. Load the JSON result. `exec_lines: null`, any `uncounted_files > 0`, or helper failure disqualifies the lite path. `signals` are path heuristics, not selection decisions. Stage 3 still judges content-based risk such as auth, payments, mutation, external I/O, concurrency, and process execution. Use `test_files_changed`, `agent_surface`, and `has_learnings_corpus` as inputs to the generic reviewer gates, not as automatic spawn decisions.
