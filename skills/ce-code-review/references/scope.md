# Determining the reviewed diff and scope

Read this at Stage 1. It defines how to resolve scope on every invocation path and how to compute the deterministic scope signals that Stage 3 (Select reviewers) uses.

### Stage 1: Determine scope

Run JJ commands from the absolute target workspace root (`jj workspace root`).
Before repository-scoped `gh`, set `GIT_DIR=$(jj git root)` there and check
that resolution succeeded. Never change the working-copy revision for review.

**Capture endpoints once.** Resolve every candidate to a full immutable commit ID
with `jj log --no-graph -r "$REV" -T 'commit_id ++ "\n"'`; require exactly one.
For the local head, resolve `@` once with normal snapshotting so it includes
local edits. After that, use `--ignore-working-copy` and the captured IDs for
all reads. JJ includes newly auto-tracked files in that snapshot; ignored or
otherwise unsnapshotted files are not reviewed. Record known exclusions and
snapshot warnings under `UNTRACKED:` and in Coverage. Do not add them by hand.
Identify the current bookmark from `@`, or from `@-` when `@` is empty, and
verified ancestor bookmarks as needed; do not guess among competing bookmarks.

**`base:` fast path.** Resolve the supplied revision only: no PR, remote
discovery, or implicit merge base. Compare that exact base to the captured
local head. Reject combinations of `base:` with a PR or branch token. A remote
bookmark is written `main@origin`, not `origin/main`.

**PR number or URL.** From the workspace root:

```bash
GIT_DIR=$(jj git root) && export GIT_DIR &&
gh pr view "$PR" --json state,title,body,number,url,baseRefName,headRefName,headRefOid,headRepository,headRepositoryOwner,isCrossRepository,changedFiles,files,reviews,comments
```

- Closed or merged: stop with `PR is closed/merged; not reviewing.` Draft PRs
  are reviewed normally. Before a full review, use the cheapest capable native
  subagent (`references/subagent-model.md`) to judge whether the title, body,
  and paths are clearly trivial (lock-file-only bump, release automation, or
  version increment with no substantive changes). If that returns yes, stop
  with `PR appears to be a trivial automated PR; not reviewing. Run without a PR argument to review the current branch, or pass base:<ref> if review is intended.`
  Unavailable judgment, permission denial, or doubt does not authorize a skip.
  Output a plain reason by default, or `{"status":"skipped","reason":"<same message>"}` in `mode:agent`.
- Get the exact base/head pair from
  `GIT_DIR=$(jj git root) gh api "repos/$OWNER/$REPO/pulls/$NUMBER"` (`.base.sha`,
  `.head.sha`), using the owner/repo from the verified PR URL. Require the
  head, repository and branch identities to agree with the metadata above.
  If they differ, re-read once as a pair; stop rather than combine snapshots.
- Use `local-aligned` only if the workspace's verified bookmark is the PR's
  `headRefName`, the PR is not cross-repository, and `headRefOid` is an ancestor
  of the captured `@` (`<headRefOid> & ::<captured-head>` resolves to the PR
  head alone). Use the verified PR base tip and the captured local head; do
  not append remote hunks. Carry PR metadata and whether it contains review
  comments or a nontrivial review (an empty approval does not count).
- Otherwise use `pr-remote`. Keep `BASE:` as the logical `pr:<number-or-url>`
  marker and record the immutable endpoint IDs separately. Resolve the exact
  advertised base/head objects where available; if needed, use
  `jj git fetch --remote <verified-configured-remote> --branch <exact-pattern>`
  without checkout. Bind the actual head repository for forks; never equate
  a matching branch name with the captured SHA. Use the captured objects
  only, even if a fetched bookmark moved. For a local JJ diff compute the
  unique common ancestor as below, and set `PR_BASE_REF` to it, not the
  moving base tip. Pass `<pr-scope-mode>pr-remote</pr-scope-mode>` and
  `<pr-head-ref>` / `<pr-base-ref>` when those objects are inspectable locally.
- If exact objects are unavailable, get the merge-base ID from the repository
  comparison API using the captured base-tip and head IDs, then request a
  Git-format diff of **that immutable merge-base and head** via
  `GIT_DIR=$(jj git root) gh api -H 'Accept: application/vnd.github.diff' "repos/$OWNER/$REPO/compare/$MERGE_BASE...$HEAD"`.
  Check the command exit status before filtering and verify the returned file
  inventory against the PR inventory (including the total and previous names
  where applicable). A truncated, mismatched, or unavailable patch is a scope
  failure, not permission to read the checkout or an unverified live PR diff.
  When only the pinned patch is inspectable, use its hunks, leave unavailable
  file-inspection refs unset, and report that limitation. Do not guess `main`.

**Branch argument.** A verified match with the current workspace bookmark
uses standalone scope. Otherwise prefer an associated PR (query with
`GIT_DIR=$(jj git root) gh pr view "$BRANCH" --json number,url` from the root);
absent a PR, resolve a verified `bookmark@remote` or explicit local bookmark,
fetching the exact branch from its verified remote if necessary. Do not switch
to it. Use `branch-remote`, pass `<branch-head-ref>` with the captured head ID,
and never inspect matching workspace paths.

**Standalone and branch-remote base selection.** Prefer the associated PR's
captured base tip if applicable, then the verified default branch bookmark
from the target repository/remote. Use verified repository metadata (for
example `GIT_DIR=$(jj git root) gh repo view "$OWNER/$REPO" --json nameWithOwner,defaultBranchRef`)
or verified local default/trunk configuration; do not infer the default from a
similarly named ref on another remote. If no base is resolvable, stop: a
working-copy-only diff would omit committed changes. For PR and branch
comparisons compute `heads(::<base-tip> & ::<review-head>)` in JJ and require
exactly one commit. Do not silently choose among multiple merge bases.

**Materialize the reviewed range.** Put the inventory and patch under the
private run directory (creation below; create it before saving any output,
including failures). Use the **same two captured endpoints** throughout:

```bash
jj --ignore-working-copy diff --from "$DIFF_A" --to "$DIFF_B" -T 'json({"path" => path, "source" => source.path(), "status" => status}) ++ "\n"'
jj --ignore-working-copy diff --from "$DIFF_A" --to "$DIFF_B" --git --context 10 --config diff.git.show-path-prefix=true
```

Use the actual paths for `FILES:` / `files.txt`, keeping the source path for a
rename. Preserve binary, rename, and mode headers. For the staged review
`DIFF:` / `full.diff`, strip the bodies of whole-file deletions after saving
the full range output successfully: keep `diff --git`, `deleted file mode`,
and `index` in those sections, omit the old body, and leave all other sections
untouched. Count those lines separately in Stage 1b. Inspect a deleted body
only at the captured base, as `references/diff-scope.md` describes.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic facts once with `scripts/review-scope.py` from this skill's directory. The helper validates the endpoints, counts changed lines, derives path classes, and reports floors. It never awards lite. Do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and pass both captured endpoints in
every mode. The helper does not recompute a merge base or snapshot a moving head.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
if [ "$SCOPE_MODE" = "pr-remote" ] || [ "$SCOPE_MODE" = "branch-remote" ]; then
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --docs-root "<root>";
else
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --head "$DIFF_B" --local-scope --docs-root "<root>";
fi
```

If the verified PR patch came from the API but its exact objects are unavailable
locally, the helper returns unknown scope facts: continue on the full spine
with that verified patch, disclose unavailable line counts, and never substitute
the local working copy. `hard_block_full` forces full for named hard-block
classes, uncounted files (including binary), or at least 200 executable
non-test added-plus-deleted lines. Smaller counts do not award lite.
Whole-file deletions count toward overall changed lines but have their own
`deleted_files`, `deleted_exec_nontest_lines`, and `deleted_band`; their size
is not the production execution floor. `silent_pass_classes` and `signals`
are inspection cues, not roster decisions. Apply the depth gate next. Stage 3
still judges semantic risk. Use `test_files_changed`, `agent_surface`,
`has_learnings_corpus`, and `declared_packs` as inputs to persona selection.
`declared_packs` is a config-only fact in local scope (`pack_roots` is 0);
in remote scope it is `null` and no pack resolver runs. If unknown in local
scope, inspect both config layers' `packs:` keys. The local `has_learnings_corpus`
hint is also `null` remotely; inspect the captured tree for a corpus if
available, never the unrelated filesystem.

### Stage 1c: Map criteria files to changed paths

**Goal:** the mapping that pairs each criteria file governing this change with the changed files it governs. Paths, not contents. Both depth paths consume it: the lite path checks the diff against it in context, and Stage 3b decides the `project-standards` dispatch from it.

Enumerate candidates from **the captured tree under review** with `jj --ignore-working-copy file list -r "$DIFF_B"` and read at that ID. A criteria file that exists only there must appear, and one deleted there must not. If the remote tree is unavailable, record discovery as limited to the pinned patch and any exact-ID API reads; do not use the workspace's version.

Candidates are `CODING_STANDARDS.md`, `CLAUDE.md`, and `AGENTS.md` at any depth. Keep those whose directory is an ancestor of a changed file — a root-level file governs the whole checkout, `skills/AGENTS.md` only what is under `skills/`.

`CODING_STANDARDS.md` is the designated criteria source, so an instruction file supplies criteria only for changed files that no `CODING_STANDARDS.md` governs, and no file is graded against both kinds. Every governing `CODING_STANDARDS.md` applies cumulatively. When two of them state rules that cannot both hold for the same changed file, the one whose directory is nearer that file decides it, so a nested file's rule wins only for changed files under its directory. Declared Compound Packs are not a criteria kind here. On the full spine they select `learnings-researcher`, which grades them; on the lite and focused paths they are graded in context. Either way they are graded separately from criteria files, so a line that violates a standards rule and a pack rule yields one finding per source.

**Done** when no changed file could be graded against two kinds of criteria. A changed file that no criteria file governs is a complete result, not a gap. A search failure or uncertain scope is recorded as exactly that, never as an empty result; the Review depth gate and Stage 3b each state what it means for them.

Create the review run directory before staging the diff or any other
artifacts; Stage 1c reuses it. Verify `.tmp/` in that workspace is ignored
and not tracked. Do not add an ignore rule to the reviewer's project diff.
If private, ignored local scratch is unavailable, stop and report the
blocker instead of using a global temp location:

```bash
SCRATCH_ROOT="$WORKSPACE_ROOT/.tmp/rocketclaw/ce-code-review"
for path in "$WORKSPACE_ROOT/.tmp" "$WORKSPACE_ROOT/.tmp/rocketclaw" "$SCRATCH_ROOT"; do
  [ ! -L "$path" ] && (umask 077; mkdir -p "$path") &&
    [ ! -L "$path" ] && [ -O "$path" ] || exit 1
done
chmod 700 "$SCRATCH_ROOT" || exit 1
RUN_DIR=$(umask 077; mktemp -d "$SCRATCH_ROOT/run.XXXXXXXX") || exit 1
RUN_ID=${RUN_DIR##*/}
printf '%s\n' "$RUN_DIR"
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
- **Inspection.** Use `jj --ignore-working-copy file list -r "$DIFF_A"` and `jj --ignore-working-copy file show -r "$DIFF_A"` from the workspace root. If the base cannot be inspected, record policy discovery as incomplete rather than assuming there is no policy.
- **Includes.** In the root file, a line holding only `@<path>` stands for that file, read from the same ref, one level deep. Skip an include of a file this review already reads as criteria, such as `@CODING_STANDARDS.md`.

Write what you read to `<run-dir>/review-policy.md`, each file under a heading that names its path and the paths it governs. No policy file at the base is a complete result: write nothing. A policy file you found but could not read is recorded for Coverage as unread, never treated as absent.

## Task Visibility

For the multi-agent path, once the review scope is resolved, use the platform's task-tracking capability when available to show a short user-facing view derived from the execution spine. Track review outcomes, not individual personas, setup mechanics, or tool calls; add conditional work only when its condition is met, and update the view at meaningful transitions. If no task-tracking capability is available, continue with the normal progress and final report without simulating a task list in chat.
