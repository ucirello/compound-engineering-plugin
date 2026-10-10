# Determining the reviewed diff and scope

Read this at Stage 1. It defines how to resolve scope on every invocation path and how to compute the deterministic scope signals that Stage 3 (Select reviewers) uses.

### Stage 1: Determine scope

Compute the diff range, file list, and diff. Minimize permission prompts by combining into as few commands as possible.

Resolve the target's absolute `workspace_root` with `jj workspace root`, then run all repository operations with that root as cwd, never `jj -R`. In every shell call containing repository-scoped `gh`, use `(cd "$workspace_root" && export GIT_DIR=$(jj git root) && gh ...)`, or export it once within the same root-scoped shell block for all subsequent gh calls there. JJ references are bookmarks (`main@origin`, not `origin/main`), revisions are commit IDs, and `@` is the reviewed working copy. An empty `@` over the verified pushed head is aligned; do not confuse it with absent review work. Read-only backend Git is reserved for unsupported raw/numstat formatting or targeted line-history operations. Native command guidance: https://docs.jj-vcs.dev/latest/git-command-table/ and https://docs.jj-vcs.dev/latest/cli-reference/ .

**If `base:` argument is provided (fast path):**

The caller supplies the base candidate. Skip automatic base-bookmark discovery and remote resolution; verify the candidate and resolve its unique common ancestor with the reviewed tree:

```
BASE_ARG="{base_arg}"
BASE=$(cd "$workspace_root" && jj log --no-graph -r "heads(common_ancestors(@, $BASE_ARG))" -T 'commit_id ++ "\n"')
```

Then produce the same output as the other paths:

```
(cd "$workspace_root" && jj diff --from "$BASE" --to @ --name-only && jj diff --from "$BASE" --to @ --git --context 10)
```

Require exactly one verified common ancestor; on ambiguity or failure stop rather than guess. This path accepts a commit ID, `main@origin`, or bookmark. Label the resulting repo-relative files and diff as `BASE:`, `FILES:`, and `DIFF:` and inventory untracked paths separately below. **Do not combine `base:` with a PR number or branch target.** If both are present, stop with an error: "Cannot use `base:` with a PR number or branch target — `base:` implies the current checkout is already the correct branch. Pass `base:` alone, or pass the target alone and let scope detection resolve the base."

**If a PR number or GitHub URL is provided as an argument:**

Do **not** check out the PR branch. Scope comes from GitHub read APIs plus optional local alignment when HEAD already matches the PR head branch.

**Skip-condition pre-check.** Before scope detection, run a PR-state probe:

Before any lightweight scope subagent, discover OpenCode configuration sources for the absolute current project location via the authenticated `/api/config?location%5Bdirectory%5D=<encoded-root>` capability, inspect the top-level source array and actual precedence for `experimental.subagent_depth`, and compare the current session's known nesting level. Do not change config or assume the shipped depth is effective in a consuming project. Delegation, optional model-selection permission, nesting, and concurrency remain separate; use actual errors to distinguish them. Never retry denial or evade depth. This scope-only judgment permits inline fallback and does not claim independent review coverage.

```
(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view <number-or-url> --json state,title,body,files)
```

Apply skip rules in order:

- `state` is `CLOSED` or `MERGED` -> stop with reason `PR is closed/merged; not reviewing.`
- **Trivial-PR judgment**: this skill requests a native lightweight subagent; use the cheapest capable model only when model-selection permission allows it, otherwise inherit. Respect unconditional delegation prohibition or missing capacity: perform this scope judgment inline rather than falsely declaring an independent review. Give it the PR title, body, and changed paths. Ask whether this is an automated/trivial PR (dependency-only bumps, automated release/version increments with no substantive code). When in doubt answer no; skipping a needed review is worse than extra review. If yes, return `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current branch, or pass base:<ref> if review is intended.`

When any skip rule applies, stop without dispatching reviewers. **Default mode:** emit the reason as plain text. **`mode:agent`:** emit JSON only — `{"status":"skipped","reason":"<same message>"}` — so programmatic callers can parse the outcome. **Standalone**, **`base:`**, and **branch-remote** paths are unaffected. **Draft PRs are reviewed normally.**

If no skip rule applies, fetch PR metadata **without checkout**:

```
(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view <number-or-url> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments --jq '{title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, files: [.files[].path], hasPriorComments: ((.reviews | map(select(.state != "APPROVED" or .body != "")) | length) > 0 or (.comments | length) > 0)}')
```

Set `BASE:` to `pr:<number-or-url>` (logical marker, not a revision). Inventory `UNTRACKED:` in the current workspace as described below, without staging or adding files.

**PR scope mode.** Classify as **`local-aligned`** only when **all** of these hold; otherwise use **`pr-remote`**. A matching branch name alone is not enough — a fork PR or a stale local branch can share a name with the PR head while pointing at unrelated code, and trusting the name would diff and inspect the wrong tree.

1. An unambiguous local/remote bookmark association for `@` or its empty-tip parent matches `headRefName` and the verified PR repository/remote.
2. The PR is **not** cross-repository (`isCrossRepository` is false).
3. `(cd "$workspace_root" && jj log --no-graph -r '<headRefOid> & ancestors(@)' -T 'commit_id ++ "\n"')` yields exactly the metadata head ID. This allows unpushed local fixes above the verified PR head, never an unrelated same-named bookmark.

- **`local-aligned`** — all three checks pass. Local Read/Grep/git blame against workspace files are valid for PR changed paths.
- **`pr-remote`** — any check fails. The working tree is **not** the PR head; workspace file contents for changed paths may be stale or unrelated.

**Diff by scope mode** (do not mix remote and local diffs — contradictory hunks cause false positives):

- **`local-aligned`:** Resolve the PR repository's verified base bookmark (fetch via root-scoped `jj git fetch --remote "<verified-remote>" --bookmark "<baseRefName>"` when needed). Resolve exactly one `heads(common_ancestors(@, <resolved-base-ref>))` and use the root-scoped native diff/file-list command above, including all local tracked work. Do not append `gh pr diff`; the local tree is canonical. Note `scope: local-aligned (PR; local tree diff)`.
- **`pr-remote`:** Set `FILES:` from the PR `files` array. Set `DIFF:` from `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr diff <number-or-url> --color=never)`. Failure stops with an actionable error, never checkout fallback.

When **`pr-remote`**, before Stage 4:

1. Best-effort fetch the head bookmark from the verified PR-head repository remote without checkout: `(cd "$workspace_root" && jj git fetch --remote "<verified-head-remote>" --bookmark "<headRefName>")`. If no configured remote belongs to the fork, do not guess origin; use supplied hunks.
2. Resolve its commit ID with root-scoped `jj log --no-graph -r '<headRefName>@<verified-head-remote>' -T 'commit_id ++ "\n"'`. Set `PR_HEAD_REF` only when exactly one ID equals metadata `headRefOid`; moving PRs, fetch failures, and mismatches use hunks only with a Coverage note.
3. Best-effort fetch the base bookmark from the verified base repository remote using the same native fetch pattern. Resolve exactly one concrete commit ID as `PR_BASE_REF`; omit it and disclose the gap on failure. File-level native diffs use this real revision, never the logical PR marker or an assumed main branch.
4. Include `<pr-scope-mode>pr-remote</pr-scope-mode>` and, when set, `<pr-head-ref>...</pr-head-ref>` and `<pr-base-ref>...</pr-base-ref>` in the Stage 4 review context bundle.

Reviewers and validators in **`pr-remote`** must not Read/Grep workspace changed files. Use `(cd "$workspace_root" && jj file show -r "$PR_HEAD_REF" "<repo-relative-path>")`, otherwise only supplied hunks. Local-aligned permits workspace inspection.

**If a branch name is provided as an argument:**

Substitute the provided branch name as `<branch>`. Do **not** check out `<branch>`.

If the verified bookmark association of `@` (or its empty-tip parent) matches `<branch>` unambiguously, use the standalone path; otherwise use remote-only scope.

Otherwise diff the remote/local ref **without checkout**:

1. Try `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view <branch> --json baseRefName,url,headRefName)` — if a PR exists, prefer the PR path above.
2. Else resolve `<branch>@<verified-remote>` or a verified local bookmark after root-scoped `jj git fetch --remote "<verified-remote>" --bookmark "<branch>"` when needed.
3. Resolve the default base bookmark from PR/repository metadata. Resolve exactly one `heads(common_ancestors(<base-ref>, <branch-ref>))` via root-scoped `jj log`, then use the native remote-endpoint diff below.
4. If `<branch-ref>` cannot be resolved locally, stop: "Cannot diff branch `<branch>` without checkout. Check out that branch, pass its open PR URL/number, or review the current branch with `base:`."

On success set **branch-remote scope** and pass `<pr-scope-mode>branch-remote</pr-scope-mode>` plus `<branch-head-ref><branch-ref></branch-head-ref>`. Reviewers/validators must not inspect local changed-file paths: use root-scoped `jj file show -r '<branch-ref>' '<path>'` or supplied hunks.

Produce:

```
(cd "$workspace_root" && jj diff --from "$BASE" --to "<branch-ref>" --name-only && jj diff --from "$BASE" --to "<branch-ref>" --git --context 10)
```

**If no argument (standalone on current branch):**

Apply the same base-detection logic using the verified current bookmark association, including the empty-tip parent, with explicit `gh pr view <bookmark>` under the root/GIT_DIR preamble above. Do not rely on a detached Git HEAD to infer the current PR.

Resolve the current PR explicitly by verified bookmark when gh cannot infer it from JJ's detached backend. Otherwise resolve the verified repository default branch from gh metadata, fetch its bookmark natively if needed, and compute exactly one common ancestor with `@`. If no base resolves, stop; `jj diff` alone would silently miss committed work above the branch base.

On success, produce the diff:

```
(cd "$workspace_root" && jj diff --from "$BASE" --to @ --name-only && jj diff --from "$BASE" --to @ --git --context 10)
```

The explicit base-to-`@` diff includes all tracked local work plus committed changes above the base. JJ has no staged/unstaged distinction.

**Untracked file handling:** Inspect `jj status` from the root and compare an owned non-mutating filesystem inventory to `jj file list -r @`, honoring ignore rules and excluding repository metadata/scratch. JJ normally auto-tracks eligible new files; review those in `@`. Explicitly untracked/ignored files stay out of scope unless authorized as input. List excluded paths in Coverage and continue, never add them or prompt.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic facts once with `scripts/review-scope.py` from this skill's directory. The helper validates the endpoints, counts changed lines, derives path classes, and reports floors. It never awards lite. Do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and set `DIFF_A`/`DIFF_B` to its two endpoints:
- **`local-aligned` / standalone / `base:`** — `DIFF_A="$BASE"` (a real SHA/ref), `DIFF_B` empty (diffs base vs working tree).
- **`pr-remote` / `branch-remote`** — `DIFF_A=<PR_BASE_REF>`, `DIFF_B=<PR_HEAD_REF>` (or `<branch-head-ref>`) — the fetched refs from Stage 1.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
if [ "$SCOPE_MODE" = "pr-remote" ] || [ "$SCOPE_MODE" = "branch-remote" ]; then
  (cd "$workspace_root" && "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --docs-root "<root>");
else
  (cd "$workspace_root" && "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --docs-root "<root>");
fi
```

Remote scope always passes both endpoint flags, even when a best-effort fetch left one empty; the helper refuses to compare to an unrelated local tree. Load its JSON. `hard_block_full` is a floor for the depth gate: named hard-block classes, uncounted files, and `size_band: large` (executable non-test lines at the full floor). `silent_pass_classes` names guards never sent to lite. Neither awards lite; a below-floor count decides nothing alone. `signals` are path heuristics, not selection decisions or lite blocks. Apply the gate before later references. Stage 3 still judges auth, payments, mutation, external I/O, concurrency, and process execution. `test_files_changed`, `agent_surface`, `has_learnings_corpus`, and `declared_packs` feed generic selection conditions, not automatic spawns. `declared_packs` reads local config only, resolves nothing (`pack_roots: 0`), and follows the persona-catalog learnings rule. It is `null` in remote scope with no resolver; local `null` requires reading `packs:` yourself.

### Stage 1c: Map criteria files to changed paths

**Goal:** the mapping that pairs each criteria file governing this change with the changed files it governs. Paths, not contents. Both depth paths consume it: the lite path checks the diff against it in context, and Stage 3b decides the `project-standards` dispatch from it.

Enumerate the candidates from **the tree under review**, never from whichever tree happens to be checked out: the workspace only in `local-aligned` scope, and the reviewed head ref in `pr-remote` and `branch-remote` (Stage 1 resolved which). A criteria file that exists only in the reviewed tree must appear, and one deleted there must not, or the review enforces criteria the change never had.

Candidates are `CODING_STANDARDS.md`, `CLAUDE.md`, and `AGENTS.md` at any depth. Keep those whose directory is an ancestor of a changed file — a root-level file governs the whole checkout, `skills/AGENTS.md` only what is under `skills/`.

`CODING_STANDARDS.md` is the designated criteria source, so an instruction file supplies criteria only for changed files that no `CODING_STANDARDS.md` governs, and no file is graded against both kinds. Every governing `CODING_STANDARDS.md` still applies together. Declared Compound Packs are not a criteria kind here: they select `learnings-researcher` on the full spine and are graded by it independently, so a line that violates a standards rule and a pack rule yields one finding per source.

**Done** when no changed file could be graded against two kinds of criteria. A changed file that no criteria file governs is a complete result, not a gap. A search failure or uncertain scope is recorded as exactly that, never as an empty result; the Review depth gate and Stage 3b each state what it means for them.

Create the review run directory now. Every path, lite or full, writes its artifacts there:

Keep `.tmp/` ignored in the project and verify the chosen scratch root stays inside the absolute workspace after resolving every ancestor. Reject symlinked `.tmp` or escaped/unowned scratch directories; a failure has no OS-global temporary fallback. Do not store review content in the shared pack cache.

```bash
SCRATCH_ROOT="$workspace_root/.tmp/rocketclaw";
if [ -L "$SCRATCH_ROOT" ]; then echo "unsafe scratch root symlink: $SCRATCH_ROOT" >&2; exit 1; fi;
(umask 077; mkdir -p "$SCRATCH_ROOT") || exit 1;
if [ -L "$SCRATCH_ROOT" ] || [ ! -O "$SCRATCH_ROOT" ]; then echo "scratch root is not owned by the current user: $SCRATCH_ROOT" >&2; exit 1; fi;
chmod 700 "$SCRATCH_ROOT" || exit 1;
RUN_ID=$(date +%Y%m%d-%H%M%S)-$(head -c4 /dev/urandom | od -An -tx1 | tr -d ' ');
RUN_DIR="$SCRATCH_ROOT/ce-code-review/$RUN_ID";
(umask 077; mkdir -p "$RUN_DIR") || exit 1; chmod 700 "$RUN_DIR" || exit 1;
echo "$RUN_DIR";
```

### Stage log

Every run records what each stage cost, so the thresholds this skill uses can be set from measured runs. The record is `<run-dir>/stages.jsonl`, written only by the bundled script below; the receipt writer folds it into `metadata.json` at the end (`summarize`, named where each path writes its receipt). Open the scope stage now, in the same shell call that printed the run directory when you can:

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
"$PY" "$SKILL_DIR/scripts/run-log.py" event --run-dir "$RUN_DIR" --start scope
```

Every later boundary is the same call with `--end <stage> --start <stage>` in one invocation, and `--reviewers`, `--candidates`, `--tokens` (only when the host handed you a count), or `--fact key=value` for what that stage learned. The stage names are fixed: `scope`, then `review` and `receipt` on lite and focused (with `peer` overlapping `review` on focused), or `select`, `dispatch`, `validate`, `merge`, and `report` on the full spine (with `peer` overlapping `dispatch`). Fold the call into a shell call the step already makes wherever one exists; a boundary is never its own turn.

## Task Visibility

For the multi-agent path, once the review scope is resolved, use the platform's task-tracking capability when available to show a short user-facing view derived from the execution spine. Track review outcomes, not individual personas, setup mechanics, or tool calls; add conditional work only when its condition is met, and update the view at meaningful transitions. If no task-tracking capability is available, continue with the normal progress and final report without simulating a task list in chat.
