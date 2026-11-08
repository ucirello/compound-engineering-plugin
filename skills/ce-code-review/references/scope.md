# Determining the reviewed diff and scope

Read this at Stage 1. It defines how to resolve scope on every invocation path and how to compute the deterministic scope signals that Stage 3 (Select reviewers) uses.

### Stage 1: Determine scope

Compute the diff range, file list, and diff. Minimize permission prompts by combining into as few commands as possible.

**If `base:` argument is provided (fast path):**

The caller already knows the diff base. Skip all base-branch detection, remote resolution, and merge-base computation. Use the provided value directly:

```
BASE_ARG="{base_arg}"
BASE=$(jj log --no-graph -r "$BASE_ARG" -T 'commit_id') # require exactly one revision
HEAD=$(jj log --no-graph -r @ -T 'commit_id')
```

Then produce the same output as the other paths:

```
echo "BASE:$BASE" && echo "FILES:" && jj diff --from "$BASE" --to "$HEAD" --name-only && echo "DIFF:" && jj diff --from "$BASE" --to "$HEAD" --git --context 10 && echo "STATUS:" && jj status
```

This path works with any uniquely resolved JJ revision — a commit ID, `main@origin`, or bookmark. Never replace an explicit base with a merge base. Run all commands from the absolute target workspace root (`cwd=workspace_root`, not `-R` alone). Before repository-scoped GitHub commands export `GIT_DIR=$(jj git root)` there. Callers reviewing the current workspace should pass explicit `base:` when auto-detection is unnecessary. **Do not combine `base:` with a PR number or bookmark target.** If both are present, stop with an actionable error.

**If a PR number or GitHub URL is provided as an argument:**

Do **not** check out the PR branch. Scope comes from GitHub read APIs plus optional local alignment when HEAD already matches the PR head branch.

**Skip-condition pre-check.** Before scope detection, run a PR-state probe:

```
gh pr view <number-or-url> --json state,title,body,files
```

Apply skip rules in order:

- `state` is `CLOSED` or `MERGED` -> stop with reason `PR is closed/merged; not reviewing.`
- **Trivial-PR judgment**: spawn a lightweight sub-agent on the platform's cheapest capable model when a known override exists; otherwise omit the model override and inherit. Read `references/subagent-model.md` before this spawn; in Codex it replaces this tier. Give it the PR title, body, and changed file paths. The agent's task: "Is this an automated or trivial PR that does not warrant a code review? Consider: dependency lock-file or manifest-only bumps, automated release commits, chore version increments with no substantive code changes. When in doubt, answer no — false negatives (skipped reviews that should have run) are more costly than false positives (unnecessary reviews)." If the judgment returns yes: stop with reason `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current branch, or pass base:<ref> if review is intended.`

Follow `subagent-model.md` at this launch: distinguish skill-requested delegation from model-override permission and effective depth. A configured/project model is intent, not permission to pass a forbidden model argument; use a suitable inherited reviewer and disclose unmet requirements. Never retry a denial or claim missing different-model coverage completed.

When any skip rule applies, stop without dispatching reviewers. **Default mode:** emit the reason as plain text. **`mode:agent`:** emit JSON only — `{"status":"skipped","reason":"<same message>"}` — so programmatic callers can parse the outcome. **Standalone**, **`base:`**, and **branch-remote** paths are unaffected. **Draft PRs are reviewed normally.**

If no skip rule applies, fetch PR metadata **without checkout**:

```
gh pr view <number-or-url> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments --jq '{title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, files: [.files[].path], hasPriorComments: ((.reviews | map(select(.state != "APPROVED" or .body != "")) | length) > 0 or (.comments | length) > 0)}'
```

Set `BASE:` to `pr:<number-or-url>` (logical marker, not a revision). Inventory `UNTRACKED:` on the current workspace by comparing a non-following local filesystem inventory with `jj file list`; exclude `.jj`, colocated `.git`, and this run's owned `.tmp` artifacts, and retain ignored/excluded classification. Never use Git ignore checks.

**PR scope mode.** Classify as **`local-aligned`** only when **all** of these hold; otherwise use **`pr-remote`**. A matching branch name alone is not enough — a fork PR or a stale local branch can share a name with the PR head while pointing at unrelated code, and trusting the name would diff and inspect the wrong tree.

1. Verify the local/remote bookmark corresponding to `headRefName` using `jj bookmark list`; do not infer a current branch from JJ's working copy.
2. The PR is **not** cross-repository (`isCrossRepository` is false).
3. Resolve exactly one metadata head commit and prove it is in `::@` with `jj log --no-graph -r '<headRefOid> & ::@' -T commit_id`. Empty `@` directly above that head is aligned; unpushed descendants are allowed. Require a nonempty exact match, not merely command success.

- **`local-aligned`** — all three checks pass. Local Read/Grep/JJ annotation against workspace files are valid for PR changed paths.
- **`pr-remote`** — any check fails. The working tree is **not** the PR head; workspace file contents for changed paths may be stale or unrelated.

**Diff by scope mode** (do not mix remote and local diffs — contradictory hunks cause false positives):

- **`local-aligned`:** Resolve the verified base bookmark (fetch through `jj git fetch --remote <verified-remote> --branch <baseRefName>` if needed). Resolve exactly one `heads(::<resolved-base-ref> & ::@)` as `BASE`, and capture `@`'s commit ID as `HEAD`. Set `FILES:` from `jj diff --from "$BASE" --to "$HEAD" --name-only` and `DIFF:` from `jj diff --from "$BASE" --to "$HEAD" --git --context 10`. This includes committed and working-copy edits. Do not mix in remote hunks. Record local-aligned scope in Coverage.
- **`pr-remote`:** Set `FILES:` from the PR `files` array. Set `DIFF:` from `gh pr diff <number-or-url> --color=never`. If `gh pr diff` fails, stop with an actionable error — do not fall back to checkout. Then drop deleted-file bodies from that saved output the way `--irreversible-delete` does on the local paths, with `awk '/^diff --git /{del=0} del && !/^index /{next} /^deleted file mode /{del=1} {print}'`; never pipe `gh pr diff` straight into the filter, because the pipe hides its failure.

When **`pr-remote`**, before Stage 4:

1. Best-effort fetch the head with `jj git fetch --remote <verified-head-repository-remote> --branch <headRefName>`, without changing `@`. Verify the repository against PR metadata first; never guess that origin is a fork's head repository.
2. Resolve the fetched bookmark with `jj log --no-graph -r '<headRefName>@<verified-remote>' -T commit_id`. Set `PR_HEAD_REF` only when the unique full ID equals metadata `headRefOid`. Failure or mismatch means diff-hunk-only inspection and a named Coverage gap.
3. Fetch the verified base remote/bookmark with `jj git fetch`, then capture exactly one merge base of that revision and the verified PR head as `PR_BASE_REF`. Keep the logical `BASE:` marker separate. On failure omit the concrete base, report the gap, and use supplied hunks only; never assume `main` or substitute a local tree.
4. Include `<pr-scope-mode>pr-remote</pr-scope-mode>` and, when set, `<pr-head-ref>...</pr-head-ref>` and `<pr-base-ref>...</pr-base-ref>` in the Stage 4 review context bundle.

Reviewers and Stage 5b validators in **`pr-remote`** mode must **not** Read/Grep workspace paths for files in `FILES:`. Inspect via `jj file show -r <PR_HEAD_REF> <path>` when available, otherwise supplied hunks only. **`local-aligned`** uses workspace inspection.

**If a branch name is provided as an argument:**

Substitute the provided branch name as `<branch>`. Do **not** check out `<branch>`.

If verified bookmark identity and ancestry prove the target is the current workspace's lineage, use the standalone path; a name alone proves nothing.

Otherwise diff the remote/local ref **without checkout**:

1. Try `gh pr view <branch> --json baseRefName,url,headRefName` — if a PR exists, prefer the **PR number/URL path** above (same remote diff rules).
2. Else resolve `<branch>` as `<branch>@<verified-remote>` or its exact local bookmark after `jj git fetch --remote <verified-remote> --branch <branch>` when needed.
3. Resolve the default base bookmark from verified repository metadata. Capture exactly one `heads(::<base-ref> & ::<branch-ref>)` as `BASE` and the branch's full commit ID as `HEAD`. Diff those captured endpoints with `jj diff --from "$BASE" --to "$HEAD" --git --context 10`.
4. If `<branch-ref>` cannot be resolved locally, stop: "Cannot diff branch `<branch>` without checkout. Check out that branch, pass its open PR URL/number, or review the current branch with `base:`."

On success set **branch-remote scope** and include `<pr-scope-mode>branch-remote</pr-scope-mode>` and `<branch-head-ref><branch-ref></branch-head-ref>` in the context. Reviewers and validators must not inspect workspace paths in scope. Use `jj file show -r <branch-ref> <path>` or supplied hunks only.

Produce:

```
echo "BASE:$BASE" && echo "FILES:" && jj diff --from "$BASE" --to "$HEAD" --name-only && echo "DIFF:" && jj diff --from "$BASE" --to "$HEAD" --git --context 10 && echo "STATUS:" && jj status
```

**If no argument (standalone on current branch):**

Apply the same base-detection logic as branch mode above, using the current branch (i.e., `gh pr view --json baseRefName,url` with no argument defaults to the current branch).

If no base or unique common ancestor can be verified, **stop**. Never fall back to `jj diff -r @`: that silently omits earlier committed work.

On success, produce the diff:

```
echo "BASE:$BASE" && echo "FILES:" && jj diff --from "$BASE" --to "$HEAD" --name-only && echo "DIFF:" && jj diff --from "$BASE" --to "$HEAD" --git --context 10 && echo "STATUS:" && jj status
```

Capture `HEAD` from `@` after JJ snapshots the workspace; the exact base/head diff includes committed and working-copy edits. Pass these same endpoints throughout review, never parent-relative per-commit statistics.

**Whole-file deletions carry no body in reviewer context.** Keep the complete saved diff for mechanical counts, then filter deleted bodies from the context copy with the same saved-output filter described above. Keep deletion headers and paths. Read old bodies only when needed from the captured base with `jj file show`.

**Untracked file handling:** Inspect the local inventory difference described above. JJ automatically snapshots eligible new files, so they are in scope when present in the captured head. Explicitly untracked and ignored files remain excluded; list exclusions in Coverage and continue without prompting.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic facts once with `scripts/review-scope.py` from this skill's directory. The helper validates the endpoints, counts changed lines, derives path classes, and reports floors. It never awards lite. Do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and set `DIFF_A`/`DIFF_B` to its two endpoints:
- **`local-aligned` / standalone / `base:`** — `DIFF_A="$BASE"`, `DIFF_B="$HEAD"` (the captured full IDs), with `--local-scope` to retain local config facts.
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

Remote scope always passes both endpoint flags, even when best-effort retrieval left one empty; the helper fails closed rather than inspecting the unrelated local tree. Counts are added PLUS deleted lines across the exact captured endpoints, never parent-relative per-commit statistics. Production and tests remain separate. `hard_block_full` covers named hard-block classes, binary/uncounted files and the 200 executable non-test line floor. Below the floor, consequence still decides; size never awards lite. Whole-file deletions stay out of executable size-floor counts, appear in `deleted_files`, and have separate `deleted_exec_nontest_lines` / `deleted_band` inspection cues; their deleted lines remain part of total `changed_lines`. Renames retain destination path classification; executable-mode files count as code even without a known suffix, including mode-only zero-line changes. Binary deletions also remain uncounted and force full.

`silent_pass_classes` names guards for consequence assessment, not depth floors. `signals`, `test_files_changed`, `agent_surface` and `has_learnings_corpus` are reviewer-selection inputs, not automatic decisions. Apply the depth gate before later references. Stage 3 still judges auth, payments, mutation, external I/O, concurrency and process-execution risks. `declared_packs` is a local RocketClaw config-only fact (nothing resolves; `pack_roots` is 0). The catalog decides full-spine learnings selection and depth-paths governs lite/focused use. Remote scope reports null without running the resolver; local null requires reading the config's packs key manually.

### Stage 1c: Map criteria files to changed paths

**Goal:** the mapping that pairs each criteria file governing this change with the changed files it governs. Paths, not contents. Both depth paths consume it: the lite path checks the diff against it in context, and Stage 3b decides the `project-standards` dispatch from it.

Enumerate the candidates from **the tree under review**, never from whichever tree happens to be checked out: the workspace only in `local-aligned` scope, and the reviewed head ref in `pr-remote` and `branch-remote` (Stage 1 resolved which). A criteria file that exists only in the reviewed tree must appear, and one deleted there must not, or the review enforces criteria the change never had.

Candidates are `CODING_STANDARDS.md`, `CLAUDE.md`, and `AGENTS.md` at any depth. Keep those whose directory is an ancestor of a changed file — a root-level file governs the whole checkout, `skills/AGENTS.md` only what is under `skills/`.

`CODING_STANDARDS.md` is the designated criteria source, so an instruction file supplies criteria only for changed files that no `CODING_STANDARDS.md` governs, and no file is graded against both kinds. Every governing `CODING_STANDARDS.md` still applies together. Declared Compound Packs are not a criteria kind here. On the full spine they select `learnings-researcher`, which grades them; on the lite and focused paths they are graded in context. Either way they are graded separately from criteria files, so a line that violates a standards rule and a pack rule yields one finding per source.

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
