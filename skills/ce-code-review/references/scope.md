# Determining the reviewed diff and scope

Read this at Stage 1. It owns scope resolution for every invocation path and the deterministic scope signals Stage 3 consumes.

### Stage 1: Determine scope

Compute the diff range, file list, and diff. Minimize permission prompts by combining into as few commands as possible.

**If `base:` argument is provided (fast path):**

The caller already knows the diff base. Skip default-bookmark detection and remote resolution. Resolve the common ancestor with the provided value directly:

```
BASE_ARG="{base_arg}"
BASE=$(jj log -r "heads(::$BASE_ARG & ::@)" --no-graph -T 'commit_id ++ "\n"')
```

Then produce the same output as the other paths:

```
printf 'BASE:%s\nFILES:\n' "$BASE"; jj diff --from "$BASE" --name-only; printf 'DIFF:\n'; jj diff --from "$BASE" --context 10
```

This path works with any JJ revision, including a change ID, commit ID, local bookmark, or remote bookmark. Callers reviewing the current workspace should pass explicit `base:` when auto-detection is unnecessary. **Do not combine `base:` with a PR number or bookmark target.** If both are present, stop with an error: "Cannot use `base:` with a PR number or bookmark target -- `base:` implies the current workspace is already correct. Pass `base:` alone, or pass the target alone and let scope detection resolve the base."

**If a PR number or GitHub URL is provided as an argument:**

Do **not** change the working-copy revision. Scope comes from GitHub read APIs plus optional local alignment when the current JJ change descends from the PR head revision.

**Skip-condition pre-check.** Before scope detection, run a PR-state probe:

```
gh pr view <number-or-url> --json state,title,body,files
```

Apply skip rules in order:

- `state` is `CLOSED` or `MERGED` -> stop with reason `PR is closed/merged; not reviewing.`
- **Trivial-PR judgment**: spawn a lightweight AI Assistant on the platform's cheapest capable model when a known override exists; otherwise inherit. Give it the PR title, body, and changed paths. Ask whether this is an automated or trivial PR with no substantive code change. When uncertain, answer no. If the judgment returns yes, explain how to review the current workspace or pass `base:<revision>` explicitly.

When any skip rule fires, stop without dispatching reviewers. **Default mode:** emit the reason as plain text. **`mode:agent`:** emit JSON only — `{"status":"skipped","reason":"<same message>"}` — so programmatic callers can parse the outcome. **Standalone**, **`base:`**, and **branch-remote** paths are unaffected. **Draft PRs are reviewed normally.**

If no skip rule fires, fetch PR metadata **without changing the working-copy revision**:

```
gh pr view <number-or-url> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments --jq '{title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, files: [.files[].path], hasPriorComments: ((.reviews | map(select(.state != "APPROVED" or .body != "")) | length) > 0 or (.comments | length) > 0)}'
```

Set `BASE:` to `pr:<number-or-url>` as a logical marker. JJ snapshots non-ignored workspace files into the working-copy change and has no index partition to report.

**PR scope mode.** Classify as **`local-aligned`** only when all checks hold; otherwise use **`pr-remote`**. A matching bookmark name alone is not enough because a fork PR or stale bookmark can point at unrelated code.

1. `jj bookmark list -r @` contains `headRefName`.
2. The PR is **not** cross-repository (`isCrossRepository` is false).
3. `jj log -r "<headRefOid>::@" --no-graph` contains `@`. This confirms the working copy descends from the PR head, allowing local changes on top, rather than merely sharing a bookmark name.

- **`local-aligned`** -- all three checks pass. Local Read/Grep and `jj file annotate` against workspace files are valid for PR changed paths.
- **`pr-remote`** -- any check fails. The working copy is **not** the PR head revision; workspace file contents for changed paths may be stale or unrelated.

**Diff by scope mode** (do not mix remote and local diffs — contradictory hunks cause false positives):

- **`local-aligned`:** Resolve `<resolved-base-ref>` from `baseRefName` with `jj git fetch --branch <baseRefName>` when needed. Resolve `BASE` as the sole result of `jj log -r "heads(::<resolved-base-ref> & ::@)" --no-graph -T 'commit_id ++ "\n"'`, then set `FILES:` from `jj diff --from "$BASE" --name-only` and `DIFF:` from `jj diff --from "$BASE" --context 10`. Do **not** call `gh pr diff` or append remote hunks because the local workspace is canonical. Note in Coverage: `scope: local-aligned (PR; local workspace diff)`.
- **`pr-remote`:** Set `FILES:` from the PR `files` array. Set `DIFF:` from `gh pr diff <number-or-url> --color=never`. If `gh pr diff` fails, stop with an actionable error — do not fall back to checkout.

When **`pr-remote`**, before Stage 4:

1. Best-effort fetch the PR head with `jj git fetch --remote origin --branch <headRefName>`.
2. When the fetched remote bookmark resolves to `headRefOid`, set `PR_HEAD_REF=<headRefName>@origin` for reviewers and validators. When it does not, omit `PR_HEAD_REF` and note in Coverage; reviewers rely on diff hunks only.
3. Best-effort fetch the PR base with `jj git fetch --remote origin --branch <baseRefName>`. When `<baseRefName>@origin` resolves, set `PR_BASE_REF=<baseRefName>@origin`; reviewers and validators use it for file-level JJ diffs. The `pr:<number-or-url>` marker remains the scope marker. When fetch fails, omit `PR_BASE_REF` and note in Coverage; checks fall back to diff hunks and must not assume `main`.
4. Include `<pr-scope-mode>pr-remote</pr-scope-mode>` and, when set, `<pr-head-ref>...</pr-head-ref>` and `<pr-base-ref>...</pr-base-ref>` in the Stage 4 review context bundle.

Reviewers and Stage 5b validators in **`pr-remote`** mode must **not** Read/Grep workspace paths for files in `FILES:`. Inspect via `jj file show -r <PR_HEAD_REF> <path>` when `PR_HEAD_REF` is set, otherwise use only the provided diff hunks. **`local-aligned`** uses normal workspace inspection.

**If a bookmark name is provided as an argument:**

Substitute the provided name as `<bookmark>`. Do **not** change the working-copy revision.

If `jj bookmark list -r @` contains `<bookmark>`, use the **standalone (current bookmark)** path below; do not use a remote-only diff.

Otherwise diff the remote or local bookmark **without changing the working-copy revision**:

1. Try `gh pr view <bookmark> --json baseRefName,url,headRefName`; if a PR exists, prefer the **PR number/URL path** above.
2. Otherwise resolve `<bookmark-ref>` as `<bookmark>@origin` or `<bookmark>`, using `jj git fetch --remote origin --branch <bookmark>` when needed.
3. Resolve the default base bookmark as in standalone mode. Resolve `BASE` with `jj log -r "heads(::<base-ref> & ::<bookmark-ref>)" --no-graph -T 'commit_id ++ "\n"'` and produce `jj diff --from "$BASE" --to <bookmark-ref> --context 10`.
4. If `<bookmark-ref>` cannot be resolved, stop: "Cannot diff bookmark `<bookmark>` without changing the working copy. Pass its open PR URL/number, or review the current workspace with `base:`."

On success for a remote bookmark diff, set **branch-remote scope**. The working copy is **not** `<bookmark>`. Include `<pr-scope-mode>branch-remote</pr-scope-mode>` and `<branch-head-ref><bookmark-ref></branch-head-ref>` in the Stage 4 review context bundle. Reviewers and Stage 5b validators must **not** inspect workspace paths for files in `FILES:`. Use `jj file show -r <bookmark-ref> <path>` or diff hunks only.

Produce:

```
printf 'BASE:%s\nFILES:\n' "$BASE"; jj diff --from "$BASE" --to <bookmark-ref> --name-only; printf 'DIFF:\n'; jj diff --from "$BASE" --to <bookmark-ref> --context 10
```

**If no argument (standalone in the current workspace):**

Apply the same base-detection logic as bookmark mode, using bookmarks that point to `@`; `gh pr view --json baseRefName,url` may provide the associated GitHub base.

If no base can be resolved, **stop**. Do not fall back to `jj diff`; a standalone review without the base would show only the current change and could silently miss earlier changes in the stack.

On success, produce the diff:

```
printf 'BASE:%s\nFILES:\n' "$BASE"; jj diff --from "$BASE" --name-only; printf 'DIFF:\n'; jj diff --from "$BASE" --context 10
```

`jj diff --from "$BASE"` compares the common ancestor to the working-copy change and therefore includes the whole local stack through `@`. JJ has no index; non-ignored files are snapshotted automatically.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic signals once with `scripts/review-scope.py` from this skill's directory. The helper owns endpoint validation, executable-line counting, changed-path signals, and the fail-closed lite eligibility calculation; do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and set `DIFF_A`/`DIFF_B` to its two endpoints:
- **`local-aligned` / standalone / `base:`** -- `DIFF_A="$BASE"` (a JJ revision), `DIFF_B` empty (diffs base vs working copy).
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
