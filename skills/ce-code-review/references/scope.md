# Determining the reviewed diff and scope

Read this at Stage 1. It defines how to resolve scope on every invocation path and how to compute the deterministic scope signals that Stage 3 (Select reviewers) uses.

### Stage 1: Determine scope

Compute the diff range, file list, and diff. Minimize permission prompts by combining into as few commands as possible.

Resolve absolute `workspace_root` with `jj workspace root`. Every command in
this skill runs with cwd set to that target root: shell
`(cd "$workspace_root" && jj ...)`, Python `cwd=workspace_root`.
Every repository-scoped `gh` example uses
`(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`, including examples
abbreviated as `gh ...`. Never invoke the Git executable, even for fallback,
history or transport. See https://docs.jj-vcs.dev/latest/git-command-table/
and https://docs.jj-vcs.dev/latest/cli-reference/ .
Validate command status and exactly one resolved commit for each endpoint;
stop on ambiguity instead of guessing.

**If `base:` argument is provided (fast path):**

The caller already knows the diff base. Skip all base-branch detection, remote resolution, and merge-base computation. Use the provided value directly:

```
BASE_ARG="{base_arg}"
BASE=$(jj log --no-graph -r "$BASE_ARG" -T 'commit_id ++ "\n"')
```

Then produce the same output as the other paths:

```
HEAD=$(jj log --no-graph -r @ -T 'commit_id ++ "\n"')
jj diff --from "$BASE" --to "$HEAD" --name-only
jj diff --from "$BASE" --to "$HEAD" --git --context 10
jj status
```

This path accepts any single verified JJ revision, commit ID or bookmark (`main@origin`, for example). Preserve that exact supplied base, without merge-base substitution. **Do not combine `base:` with a PR number or branch target.** If both are present, stop with the existing conflicting-target error.

**If a PR number or GitHub URL is provided as an argument:**

Do **not** check out the PR branch. Scope comes from GitHub read APIs plus optional local alignment when HEAD already matches the PR head branch.

**Skip-condition pre-check.** Before scope detection, run a PR-state probe:

```
GIT_DIR=$(jj git root) gh pr view <number-or-url> --json state,title,body,files
```

Apply skip rules in order:

- `state` is `CLOSED` or `MERGED` -> stop with reason `PR is closed/merged; not reviewing.`
- **Trivial-PR judgment**: spawn a lightweight sub-agent on the platform's cheapest capable model when a known override exists; otherwise omit the model override and inherit. Read `references/subagent-model.md` before this spawn; in Codex it replaces this tier. Give it the PR title, body, and changed file paths. The agent's task: "Is this an automated or trivial PR that does not warrant a code review? Consider: dependency lock-file or manifest-only bumps, automated release commits, chore version increments with no substantive code changes. When in doubt, answer no — false negatives (skipped reviews that should have run) are more costly than false positives (unnecessary reviews)." If the judgment returns yes: stop with reason `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current branch, or pass base:<ref> if review is intended.`

Treat user/project role models and role configuration as desired intent, not permission to override the host. Apply `subagent-model.md`: under a user-OR-skill rule this skill requests the trivial-PR check, omit forbidden model arguments, classify actual depth/denial/capacity/model errors, and if no check can run do not assume the PR is trivial.

When any skip rule applies, stop without dispatching reviewers. **Default mode:** emit the reason as plain text. **`mode:agent`:** emit JSON only — `{"status":"skipped","reason":"<same message>"}` — so programmatic callers can parse the outcome. **Standalone**, **`base:`**, and **branch-remote** paths are unaffected. **Draft PRs are reviewed normally.**

If no skip rule applies, fetch PR metadata **without checkout**:

```
GIT_DIR=$(jj git root) gh pr view <number-or-url> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments --jq '{title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, files: [.files[].path], hasPriorComments: ((.reviews | map(select(.state != "APPROVED" or .body != "")) | length) > 0 or (.comments | length) > 0)}'
```

Set `BASE:` to `pr:<number-or-url>` (logical marker, not a revision). Obtain untracked paths from `jj status` on the current workspace; never auto-track excluded files.

**PR scope mode.** Classify as **`local-aligned`** only when **all** of these hold; otherwise use **`pr-remote`**. A matching branch name alone is not enough — a fork PR or a stale local branch can share a name with the PR head while pointing at unrelated code, and trusting the name would diff and inspect the wrong tree.

1. A verified local JJ bookmark for the current ancestry matches `headRefName` (inspect `jj bookmark list` and `jj log`); no guessed current branch.
2. The PR is **not** cross-repository (`isCrossRepository` is false).
3. `jj log --no-graph -r '<headRefOid> & ::@' -T 'commit_id ++ "\n"'` returns exactly the verified PR head. This allows local fixes and an empty `@` above that head, but excludes unrelated same-named bookmarks.

- **`local-aligned`** — all three checks pass. Local Read/Grep/JJ annotation against workspace files are valid for PR changed paths.
- **`pr-remote`** — any check fails. The working tree is **not** the PR head; workspace file contents for changed paths may be stale or unrelated.

**Diff by scope mode** (do not mix remote and local diffs — contradictory hunks cause false positives):

- **`local-aligned`:** Resolve the verified base bookmark, fetching with `jj git fetch --remote <verified-base-remote> --branch <baseRefName>` if needed. Resolve exactly one `heads(::@ & ::<resolved-base-ref>)` as BASE, then capture `@` as HEAD. Use `jj diff --from "$BASE" --to "$HEAD" --name-only` and `jj diff --from "$BASE" --to "$HEAD" --git --context 10`. Do not mix remote hunks with this canonical local tree diff. Note `scope: local-aligned (PR; local tree diff)` in Coverage.
- **`pr-remote`:** Set `FILES:` from the PR `files` array. Set `DIFF:` from `gh pr diff <number-or-url> --color=never`. If `gh pr diff` fails, stop with an actionable error — do not fall back to checkout. Then drop deleted-file bodies from that saved output the way `--irreversible-delete` does on the local paths, with `awk '/^diff --git /{del=0} del && !/^index /{next} /^deleted file mode /{del=1} {print}'`; never pipe `gh pr diff` straight into the filter, because the pipe hides its failure.

When **`pr-remote`**, before Stage 4:

1. Resolve the actual head repository and a verified remote; fetch with `jj git fetch --remote <head-remote> --branch <headRefName>` without editing the working copy. Do not assume origin owns a fork's head.
2. Resolve the fetched remote bookmark to one commit ID with `jj log --no-graph -r '<headRefName>@<head-remote>' -T 'commit_id ++ "\n"'`. Set `PR_HEAD_REF` only if it equals metadata `headRefOid`; otherwise omit it and record diff-hunks-only coverage.
3. Fetch the verified base repository/bookmark with `jj git fetch`. Resolve the unique common ancestor of the fetched base and verified head as `PR_BASE_REF`, retaining the PR's exact range. If unavailable or ambiguous, omit it and report degraded mechanics; never guess main, use a different ref, or compare to the local tree. `BASE:` remains the logical PR marker.
4. Include `<pr-scope-mode>pr-remote</pr-scope-mode>` and, when set, `<pr-head-ref>...</pr-head-ref>` and `<pr-base-ref>...</pr-base-ref>` in the Stage 4 review context bundle.

Reviewers and validators in remote scope must not Read/Grep workspace paths for changed files. Use `jj file show -r <verified-head> <path>` or provided hunks; local-aligned uses normal workspace inspection.

**If a branch name is provided as an argument:**

Substitute the provided branch name as `<branch>`. Do **not** check out `<branch>`.

If the verified bookmark target is in current ancestry and represents this working copy's task, use standalone; a matching name alone is insufficient.

Otherwise diff the remote/local ref **without checkout**:

1. Try `gh pr view <branch> --json baseRefName,url,headRefName` — if a PR exists, prefer the **PR number/URL path** above (same remote diff rules).
2. Else resolve the verified remote bookmark `<branch>@<remote>` or local bookmark, fetching with `jj git fetch --remote <remote> --branch <branch>` when needed.
3. Resolve the actual default base from repository/PR metadata. Capture the unique `heads(::<base-ref> & ::<branch-ref>)` as BASE and the verified branch commit as HEAD. Compare those exact IDs with `jj diff --from "$BASE" --to "$HEAD" --git --context 10`.
4. If `<branch-ref>` cannot be resolved locally, stop: "Cannot diff branch `<branch>` without checkout. Check out that branch, pass its open PR URL/number, or review the current branch with `base:`."

On success set branch-remote scope, passing the verified head in `<branch-head-ref>` and mode in `<pr-scope-mode>`. Reviewers and validators use `jj file show -r <branch-ref> <path>` or diff hunks, never changed workspace paths.

Produce:

```
jj diff --from "$BASE" --to "$HEAD" --name-only
jj diff --from "$BASE" --to "$HEAD" --git --context 10
jj status
```

**If no argument (standalone on current branch):**

Apply branch-mode base detection using the verified task bookmark/PR identity,
not the Git backend's current branch. Call repository-scoped
`GIT_DIR=$(jj git root) gh pr view <verified-task-bookmark> --json baseRefName,url`
from the absolute root, or use explicit task/repository default-base metadata.
An empty `@` above the pushed task head still belongs to that task when the
bookmark/ancestry is verified. If task identity is ambiguous, do not guess a
backend HEAD or default main.

If no unique verified base can be resolved, **stop**. Do not fall back to `jj diff -r @`: it would miss committed task work.

On success, produce the diff:

```
jj diff --from "$BASE" --to "$HEAD" --name-only
jj diff --from "$BASE" --to "$HEAD" --git --context 10
jj status
```

Capture `@` to HEAD after snapshotting, so the exact base-to-working-copy range includes committed and current tracked task changes. Record both IDs and reuse them throughout review.

**Whole-file deletions carry no body in the reviewer prompt.** Save the full exact diff for mechanical facts, then omit deleted hunk bodies from the presentation copy (retain headers/path/mode). The awk filter above applies to saved JJ Git-format output too. Never use the filtered copy for line counts. Read needed old bodies from the captured base with `jj file show`.

**Untracked file handling:** Always inspect `UNTRACKED:`. Untracked paths are out of scope unless staged. When non-empty, list excluded files in Coverage and continue on tracked changes only — never stop or prompt.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic facts once with `scripts/review-scope.py` from this skill's directory. The helper validates the endpoints, counts changed lines, derives path classes, and reports floors. It never awards lite. Do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and set `DIFF_A`/`DIFF_B` to its two endpoints:
- **`local-aligned` / standalone / `base:`** — `DIFF_A="$BASE"`, `DIFF_B="$HEAD"` (both captured commit IDs, including snapshotted working-copy changes).
- **`pr-remote` / `branch-remote`** — `DIFF_A=<PR_BASE_REF>`, `DIFF_B=<PR_HEAD_REF>` (or `<branch-head-ref>`) — the fetched refs from Stage 1.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
if [ "$SCOPE_MODE" = "pr-remote" ] || [ "$SCOPE_MODE" = "branch-remote" ]; then
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --docs-root "<root>";
else
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --head "$DIFF_B" --local-scope --docs-root "<root>";
fi
```

Remote scope always passes both endpoint flags, even when a best-effort fetch left one value empty; the helper then refuses to compute rather than comparing the fetched base to the unrelated local worktree. Load the JSON result. `hard_block_full` is a floor for the Review depth gate in `references/modes-and-output.md`; it covers the named hard-block classes, uncounted files, and a `size_band` of `large` (executable non-test changed lines at the full floor). `silent_pass_classes` names guards for consequence assessment under that gate, not a depth floor. Neither awards lite, and a count below the floor decides nothing on its own. Whole-file deletions are not in any of the line counts above: the helper lists them in `deleted_files`, counts their executable non-test lines in `deleted_exec_nontest_lines`, and bands that count in `deleted_band` (`none`, `small`, or `large`), which the gate reads. `signals` are path heuristics, not selection decisions and not a lite block. After this stage, apply that gate before reading any later reference. On the full spine, Stage 3 still judges content-based risk such as auth, payments, mutation, external I/O, concurrency, and process execution. Use `test_files_changed`, `agent_surface`, `has_learnings_corpus`, and `declared_packs` as inputs to the conditions that select generic reviewers, not as automatic spawn decisions. `declared_packs` reports whether the local RocketClaw config names any Compound Pack, read from the config alone (nothing is resolved, so `pack_roots` is always 0); the learnings selection rule in `references/persona-catalog.md` decides what that fact selects on the full spine, and `references/depth-paths.md` decides how the lite and focused paths use it. It describes the local checkout, so the helper evaluates it only in local scope: in remote scope it is `null` and no resolver runs. In local scope, `null` means the helper could not tell; read the config's `packs:` key yourself.

### Stage 1c: Map criteria files to changed paths

**Goal:** the mapping that pairs each criteria file governing this change with the changed files it governs. Paths, not contents. Both depth paths consume it: the lite path checks the diff against it in context, and Stage 3b decides the `project-standards` dispatch from it.

Enumerate the candidates from **the tree under review**, never from whichever tree happens to be checked out: the workspace only in `local-aligned` scope, and the reviewed head ref in `pr-remote` and `branch-remote` (Stage 1 resolved which). A criteria file that exists only in the reviewed tree must appear, and one deleted there must not, or the review enforces criteria the change never had.

Candidates are `CODING_STANDARDS.md`, `CLAUDE.md`, and `AGENTS.md` at any depth. Keep those whose directory is an ancestor of a changed file — a root-level file governs the whole checkout, `skills/AGENTS.md` only what is under `skills/`.

`CODING_STANDARDS.md` is the designated criteria source, so an instruction file supplies criteria only for changed files that no `CODING_STANDARDS.md` governs, and no file is graded against both kinds. Every governing `CODING_STANDARDS.md` applies cumulatively. When two of them state rules that cannot both hold for the same changed file, the one whose directory is nearer that file decides it, so a nested file's rule wins only for changed files under its directory. Declared Compound Packs are not a criteria kind here. On the full spine they select `learnings-researcher`, which grades them; on the lite and focused paths they are graded in context. Either way they are graded separately from criteria files, so a line that violates a standards rule and a pack rule yields one finding per source.

**Done** when no changed file could be graded against two kinds of criteria. A changed file that no criteria file governs is a complete result, not a gap. A search failure or uncertain scope is recorded as exactly that, never as an empty result; the Review depth gate and Stage 3b each state what it means for them.

Create the review run directory now. Every path, lite or full, writes its artifacts there:

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

### Stage 1d: Stage the review policy

**Goal:** the repository's review policy, read from a copy the change under review cannot have edited, staged where every later reader finds it.

A review policy is a `REVIEW.md` file: instructions for how review behaves in this repository, such as what each severity means here, paths or classes of finding to skip, a cap on minor findings, the evidence a class of finding needs, or checks to run on every change. Claude Code Review reads the same file. It is not a criteria file: it neither supplies criteria nor displaces them, so Stage 1c's precedence ignores it.

- **Which files.** The root `REVIEW.md` governs the whole change. A `REVIEW.md` in a directory that is an ancestor of a changed file adds to the root file for the paths under it.
- **Which copy.** Read each file from the Stage 1 base (`BASE:`, or `PR_BASE_REF` in `pr-remote`), never from the reviewed tree, because a change must not be reviewed under policy it wrote itself. When the diff adds, edits, or deletes a policy file, the base copy applies (none for a new file), and Coverage says the change's version was not applied.
- **Includes.** In the root file, a line holding only `@<path>` stands for that file, read from the same ref, one level deep. Skip an include of a file this review already reads as criteria, such as `@CODING_STANDARDS.md`.

Write what you read to `<run-dir>/review-policy.md`, each file under a heading that names its path and the paths it governs. No policy file at the base is a complete result: write nothing. A policy file you found but could not read is recorded for Coverage as unread, never treated as absent.

## Task Visibility

For the multi-agent path, once the review scope is resolved, use the platform's task-tracking capability when available to show a short user-facing view derived from the execution spine. Track review outcomes, not individual personas, setup mechanics, or tool calls; add conditional work only when its condition is met, and update the view at meaningful transitions. If no task-tracking capability is available, continue with the normal progress and final report without simulating a task list in chat.
