# Determining the reviewed diff and scope

Read this at Stage 1. It defines how to resolve scope on every invocation path and how to compute the deterministic scope signals that Stage 3 (Select reviewers) uses.

### Stage 1: Determine scope

Compute the diff range, file list, and diff. Minimize permission prompts by combining into as few commands as possible.

Resolve `workspace_root` to the absolute `jj workspace root` once, then run every repository command from that root with shell `cd` or subprocess `cwd`. Snapshot and capture one full working-copy commit ID with `jj log --no-graph -r @ -T commit_id` as `HEAD`; resolve every provided endpoint to exactly one full commit ID too. Stop on missing/ambiguous endpoints. All later patches, helper counts, reviewer prompts, and receipts reuse those captured endpoints. Export `GIT_DIR=$(jj git root)` from that root before repository-scoped `gh`, including every inline example below. No direct Git execution and no unrelated-directory `jj -R` calls.

**If `base:` argument is provided (fast path):**

The caller already knows the diff base. Skip all base-branch detection, remote resolution, and merge-base computation. Use the provided value directly:

```
BASE_ARG="{base_arg}"
BASE="$BASE_ARG" # Resolve to one concrete commit ID with jj log; never recompute its merge base.
```

Then produce the same output as the other paths:

```
(cd "$workspace_root" && jj diff --from "$BASE" --to "$HEAD" --name-only && jj diff --from "$BASE" --to "$HEAD" --git --context 10 && jj status)
```

This path works with any ref — a SHA, `origin/main`, a branch name. Callers reviewing the current checkout should pass explicit `base:` when auto-detection is unnecessary. **Do not combine `base:` with a PR number or branch target.** If both are present, stop with an error: "Cannot use `base:` with a PR number or branch target — `base:` implies the current checkout is already the correct branch. Pass `base:` alone, or pass the target alone and let scope detection resolve the base."

**If a PR number or GitHub URL is provided as an argument:**

Do **not** check out the PR branch. Scope comes from GitHub read APIs plus optional local alignment when HEAD already matches the PR head branch.

**Skip-condition pre-check.** Before scope detection, run a PR-state probe:

```
(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view <number-or-url> --json state,title,body,files)
```

Apply skip rules in order:

- `state` is `CLOSED` or `MERGED` -> stop with reason `PR is closed/merged; not reviewing.`
- **Trivial-PR judgment**: spawn a lightweight sub-agent on the platform's cheapest capable model when a known override exists; otherwise omit the model override and inherit. Give it the PR title, body, and changed file paths. The agent's task: "Is this an automated or trivial PR that does not warrant a code review? Consider: dependency lock-file or manifest-only bumps, automated release commits, chore version increments with no substantive code changes. When in doubt, answer no — false negatives (skipped reviews that should have run) are more costly than false positives (unnecessary reviews)." If the judgment returns yes: stop with reason `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current branch, or pass base:<ref> if review is intended.`

Resolve requested/configured tiers with `opencode.models` only when model selection is permitted. This skill explicitly requests the lightweight reviewer under a user-or-skill delegation rule; respect genuine prohibitions. If user model authorization is required but absent, omit the model argument and use a suitable inherited model. Check remaining nesting depth separately and classify actual failures; never evade a prohibition or depth limit through shell. If no permitted reviewer is available, conservatively continue reviewing rather than assert that the PR is trivial.

When any skip rule applies, stop without dispatching reviewers. **Default mode:** emit the reason as plain text. **`mode:agent`:** emit JSON only — `{"status":"skipped","reason":"<same message>"}` — so programmatic callers can parse the outcome. **Standalone**, **`base:`**, and **branch-remote** paths are unaffected. **Draft PRs are reviewed normally.**

If no skip rule applies, fetch PR metadata **without checkout**:

```
(cd "$workspace_root" && GIT_DIR=$(jj git root) gh pr view <number-or-url> --json title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments --jq '{title, body, baseRefName, headRefName, headRefOid, isCrossRepository, url, files: [.files[].path], hasPriorComments: ((.reviews | map(select(.state != "APPROVED" or .body != "")) | length) > 0 or (.comments | length) > 0)}')
```

Set `BASE:` to `pr:<number-or-url>` (logical marker, not a revision). Set `UNTRACKED:` from `jj status` on the current workspace; JJ automatically tracks eligible files, so explicitly list ignored or untracked exclusions separately without staging or changing tracking policy.

**PR scope mode.** Classify as **`local-aligned`** only when **all** of these hold; otherwise use **`pr-remote`**. A matching branch name alone is not enough — a fork PR or a stale local branch can share a name with the PR head while pointing at unrelated code, and trusting the name would diff and inspect the wrong tree.

1. The verified source bookmark associated with the captured working-copy head equals `headRefName`; inspect `jj bookmark list` and its targets rather than infer a checked-out branch.
2. The PR is **not** cross-repository (`isCrossRepository` is false).
3. `jj log --no-graph -r '<headRefOid> & ::<captured-head>' -T commit_id` returns exactly the verified PR head. This proves ancestry, allowing local fixes above it, rather than trusting a same-named bookmark.

- **`local-aligned`** — all three checks pass. Local Read/Grep and targeted `jj file annotate` are valid for PR changed paths.
- **`pr-remote`** — any check fails. The working tree is **not** the PR head; workspace file contents for changed paths may be stale or unrelated.

**Diff by scope mode** (do not mix remote and local diffs — contradictory hunks cause false positives):

- **`local-aligned`:** Resolve the base bookmark (fetch with `jj git fetch --remote <verified-remote> --branch <baseRefName>` if needed). Resolve exactly one common ancestor with `jj log --no-graph -r 'heads(::<captured-head> & ::<resolved-base-ref>)' -T 'commit_id ++ "\n"'`; ambiguity is a blocker. Capture that ID as `BASE`, file names with `jj diff --from "$BASE" --to "$HEAD" --name-only`, and the exact patch with `jj diff --from "$BASE" --to "$HEAD" --git --context 10`. Do not append remote hunks. Note `scope: local-aligned (PR; local tree diff)`.
- **`pr-remote`:** Set `FILES:` from the PR `files` array. Set `DIFF:` from `gh pr diff <number-or-url> --color=never`. If `gh pr diff` fails, stop with an actionable error — do not fall back to checkout. Then drop deleted-file bodies from that saved output the way `--irreversible-delete` does on the local paths, with `awk '/^diff --git /{del=0} del && !/^index /{next} /^deleted file mode /{del=1} {print}'`; never pipe `gh pr diff` straight into the filter, because the pipe hides its failure.

When **`pr-remote`**, before Stage 4:

1. Best-effort fetch the PR head without changing the working copy using `jj git fetch --remote <verified-head-remote> --branch <headRefName>`. Verify the remote's repository identity, especially for forks; never assume origin contains the PR head.
2. Resolve the fetched bookmark to a full `commit_id` with `jj log`. Set `PR_HEAD_REF` only if it equals metadata `headRefOid`. Fetch success or a matching name is insufficient; mismatch/failure means hunks-only inspection and explicit Coverage.
3. Fetch the verified base remote/bookmark with `jj git fetch`, then capture exactly one common ancestor of the verified base and head as `PR_BASE_REF`. Use that exact base/head pair for file-level `jj diff --from <PR_BASE_REF> --to <PR_HEAD_REF> -- <path>`. The logical `BASE: pr:...` marker remains separate. Missing endpoints mean hunks-only, unknown mechanical scope, and explicit degraded Coverage; never substitute main or the local tree.
4. Include `<pr-scope-mode>pr-remote</pr-scope-mode>` and, when set, `<pr-head-ref>...</pr-head-ref>` and `<pr-base-ref>...</pr-base-ref>` in the Stage 4 review context bundle.

Reviewers and Stage 5b validators in **`pr-remote`** mode must **not** Read/Grep workspace paths for files in `FILES:`. Inspect via `jj file show -r <PR_HEAD_REF> <path>` when set, otherwise only supplied diff hunks. **`local-aligned`** uses normal workspace inspection.

**If a branch name is provided as an argument:**

Substitute the provided branch name as `<branch>`. Do **not** check out `<branch>`.

If the verified source bookmark and captured local head identify `<branch>`, use the **standalone** path below; do not infer identity from a same-named remote bookmark alone.

Otherwise diff the remote/local ref **without checkout**:

1. Try `gh pr view <branch> --json baseRefName,url,headRefName` — if a PR exists, prefer the **PR number/URL path** above (same remote diff rules).
2. Else resolve `<branch>` as `<branch>@<verified-remote>` or the verified local bookmark after `jj git fetch --remote <verified-remote> --branch <branch>` when needed.
3. Resolve the default base (same logic as standalone), capture exactly one `heads(::<base-ref> & ::<branch-ref>)` commit ID as `BASE`, and capture the branch head ID as `HEAD`. Generate `jj diff --from "$BASE" --to "$HEAD" --git --context 10`.
4. If `<branch-ref>` cannot be resolved locally, stop: "Cannot diff branch `<branch>` without checkout. Check out that branch, pass its open PR URL/number, or review the current branch with `base:`."

On success set **branch-remote scope**, with `<pr-scope-mode>branch-remote</pr-scope-mode>` and `<branch-head-ref>` holding the captured head ID. Reviewers and validators must not inspect workspace paths; use `jj file show -r <captured-head> <path>` or supplied hunks only.

Produce:

```
(cd "$workspace_root" && jj diff --from "$BASE" --to "$HEAD" --name-only && jj diff --from "$BASE" --to "$HEAD" --git --context 10 && jj status)
```

**If no argument (standalone on current branch):**

Resolve the verified source bookmark (inspect `@-` as well when `@` is empty). Query its associated PR explicitly with scoped `gh pr view <verified-bookmark> --json baseRefName,url`; never depend on Git's current-branch inference. If absent, resolve the verified repository's default branch with scoped `gh repo view --json defaultBranchRef`, then the corresponding verified remote bookmark. Fetch if required and capture exactly one common ancestor of it and the captured head. Never assume main/master or a different remote.

If no base can be resolved, **stop**. Do not fall back to a parent-relative diff that silently misses committed work.

On success, produce the diff:

```
(cd "$workspace_root" && jj diff --from "$BASE" --to "$HEAD" --name-only && jj diff --from "$BASE" --to "$HEAD" --git --context 10 && jj status)
```

Capture the working-copy `commit_id` after its snapshot; the exact base-to-head range includes all eligible working-copy changes and committed work. JJ has no staging area. Every JJ command runs from the absolute target root, never via `-R` from an unrelated directory. Export `GIT_DIR=$(jj git root)` there before **every** repository-scoped `gh` call in this reference, including inline examples. Verify repository/bookmark/remote identity; never infer a current branch from Git state. See https://docs.jj-vcs.dev/latest/cli-reference/.

**Whole-file deletions carry no body in reviewer context.** Save the complete exact-range patch for mechanical counting first, then filter a separate reviewer copy with `awk '/^diff --git /{del=0} del && !/^index /{next} /^deleted file mode /{del=1} {print}'`. Keep deletion headers and paths; read old bodies from the captured base only when evidence needs them.

**Untracked file handling:** Inspect `jj status` and tracking/ignore state. JJ automatically tracks eligible files; those captured in the reviewed revision are in scope. Files explicitly untracked or ignored remain excluded: list them in Coverage and continue without changing tracking policy, staging, or prompting. Ignored files are not protected by JJ snapshots.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic facts once with `scripts/review-scope.py` from this skill's directory. The helper validates the endpoints, counts changed lines, derives path classes, and reports floors. It never awards lite. Do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and set `DIFF_A`/`DIFF_B` to its two endpoints:
- **`local-aligned` / standalone / `base:`** — `DIFF_A="$BASE"`, `DIFF_B="$HEAD"` (captured full local commit IDs).
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

Remote scope always passes both endpoint flags, including empty values after failed fetches; the helper fails closed rather than substituting the local tree. Load the JSON. `hard_block_full` is the depth gate's floor: named hard-block classes, uncounted files, and `large` executable non-test added-plus-deleted line counts (200 or more). `silent_pass_classes` forbids lite but does not force full. Neither a small count nor a signal awards lite. Whole-file deletions are separately listed and counted in `deleted_files`, `deleted_exec_nontest_lines`, and `deleted_band` (`none`, `small`, `large`); they do not raise the executable full-review floor. `changed_lines` includes their deleted lines. Apply `modes-and-output.md`'s gate before reading later references. Stage 3 still judges auth, payments, mutation, external I/O, concurrency, and process risks. `signals`, `test_files_changed`, `agent_surface`, and `has_learnings_corpus` inform selection, never automatically dispatch. `declared_packs` is a local configuration fact: declared Compound Packs select learnings under `persona-catalog.md` on full and are handled under `depth-paths.md` otherwise. Parse-only means `pack_roots` is always 0. Remote scope reports `declared_packs: null` without running the resolver; local null means unknown and requires reading `packs:` yourself.

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
