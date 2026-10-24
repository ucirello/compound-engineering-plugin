# Determining the reviewed diff and scope

## Stage 1: Capture exact review endpoints

Run every JJ command with cwd set to the target workspace's absolute root, not
`jj -R`. First resolve that root with `jj workspace root`. All repository-scoped
GitHub commands use `(cd "$workspace_root" && GIT_DIR=$(jj git root) gh ...)`.
Never invoke the Git executable. See https://docs.jj-vcs.dev/latest/cli-reference/
and https://docs.jj-vcs.dev/latest/git-command-table/.

**Explicit `base:` fast path:** resolve the supplied revision to exactly one full
commit ID with `jj log --no-graph -r "$BASE_ARG" -T 'commit_id ++ "\n"'`.
Use that exact base, not its merge base. Capture `@` as the full head ID after
JJ snapshots the working tree. Reject invalid/ambiguous endpoints. Do not combine
`base:` with a PR or branch target; report the conflicting arguments and stop.

**PR target (never checkout):** use scoped `gh pr view <target> --json
state,title,body,files` first. Closed/merged PRs stop with the existing skipped
reason. A permitted lightweight native subagent judges manifest/lock-only bumps,
automated releases and trivial version changes from this metadata; doubt means
review. Follow dispatch-reviewers.md's delegation/model/depth rules, inheriting
when overrides are not permitted. A denied/unavailable triviality agent is not
evidence to skip substantive review. Drafts are reviewed normally. In mode:agent
emit only `{"status":"skipped","reason":"<reason>"}` for actual skips.

Fetch metadata with scoped `gh pr view <target> --json
title,body,baseRefName,headRefName,headRefOid,isCrossRepository,url,files,reviews,comments`.
Retain prior-comment presence for reviewer selection. Verify head repository and
remote URL, not only branch name. Local-aligned requires a non-fork PR, matching
verified source bookmark, and the metadata head being an ancestor of `@`:
`jj log --no-graph -r '<headRefOid> & ::@' -T commit_id` must return that exact ID.
An empty `@` above it is aligned; unpushed fixes above it remain in local scope.
Otherwise use pr-remote and never inspect unrelated workspace changed-file bodies.

For local-aligned scope resolve the verified PR base bookmark, fetching it if
needed with `jj git fetch --remote <verified-remote> --branch <baseRefName>`.
Require one common ancestor via
`jj log --no-graph -r 'heads(::<base-ref> & ::<head-ref>)' -T 'commit_id ++ "\n"'`.
Capture that base and the current `@` full ID exactly once. Do not append remote
hunks to the canonical local diff.

For pr-remote, scoped `gh pr diff <target> --color=never` supplies the saved
canonical diff and metadata supplies the file inventory. Stop on diff failure,
never checkout. Best-effort `jj git fetch` the exact source branch from the
verified head repository remote and the base branch from the verified base
remote, without editing the workspace. Set PR_HEAD_REF only after the fetched
commit ID equals headRefOid; movement or wrong-repository heads are coverage
gaps, not permission to substitute. Capture PR_BASE_REF as the unique common
ancestor of verified base and head. Missing or ambiguous refs stay absent and
mechanical scope fails closed; reviewers use only supplied hunks where head
content is unavailable. Keep `BASE:pr:<target>` as a logical marker, separate
from actual captured diff endpoints. Pass pr-scope-mode, pr-head-ref and
pr-base-ref to reviewers/validators when verified.

**Branch target:** a verified bookmark containing the current local head uses
the standalone path. Otherwise prefer its PR metadata, or resolve the exact
local/remote bookmark (fetch only the verified branch/remote with `jj git fetch`).
Determine the default base from repository metadata/project instructions, not a
guessed main. Capture the unique common ancestor and requested branch head.
Unresolvable targets stop; do not switch trees. Use branch-remote scope and pass
branch-head-ref; workspace bodies are not reviewed-head bodies.

**Standalone:** resolve the actual current task's base from its PR metadata or
verified repository default, require a unique common ancestor with the captured
`@` head, then capture both full IDs. An empty working-copy tip does not erase
committed changes below it. If base cannot be resolved, stop rather than falling
back to a parent-only diff that misses committed work.

For every verified local/branch range save the file inventory using
`jj diff --from "$BASE" --to "$HEAD" --name-only` and the complete diff using
`jj diff --from "$BASE" --to "$HEAD" --git --context 10`. Always use these same
captured IDs for mechanics, reviewers, validators and peer; never re-resolve a
moving bookmark or replace a reviewed range with parent-relative statistics.
Keep the complete diff for mechanics. Create a presentation copy omitting deleted
bodies (preserving headers) using
`awk '/^diff --git /{del=0} del && !/^index /{next} /^deleted file mode /{del=1} {print}'`
after checking the diff producer succeeded. Read deleted bodies on demand with
`jj file show -r <captured-base> <path>`.

JJ snapshots nonignored tracked/auto-trackable files into `@`. Inspect `jj status`
and ignored/untracked paths without adding them merely for review. Excluded paths
remain out of scope and are listed in Coverage; do not block or prompt. Capture
head after the intended snapshot and preserve unrelated ignored/untracked work.

### Stage 1b: Compute scope signals (cheap, deterministic)

Derive deterministic facts once with `scripts/review-scope.py` from this skill's directory. The helper validates the endpoints, counts changed lines, derives path classes, and reports floors. It never awards lite. Do not reproduce those mechanics in prose or estimate them from diff hunks. The invocation below is the helper's contract: run it directly rather than inspecting the script or probing its `--help`, unless it actually fails with an incompatibility.

Set `SCOPE_MODE` to the Stage 1 scope mode and set `DIFF_A`/`DIFF_B` to its two endpoints:
- **`local-aligned` / standalone / `base:`** — `DIFF_A="$BASE"`, `DIFF_B="$HEAD"`, both captured full commit IDs after the intended working-copy snapshot. Never leave the local head empty or recompute a merge base inside the helper.
- **`pr-remote` / `branch-remote`** — `DIFF_A=<PR_BASE_REF>`, `DIFF_B=<PR_HEAD_REF>` (or `<branch-head-ref>`) — the fetched refs from Stage 1.

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just read>";
cd "$workspace_root" || exit 1;
PY="$(for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c '' >/dev/null 2>&1 && { echo "$c"; break; }; done)"; [ -n "$PY" ] || { echo "no working Python 3 interpreter on PATH" >&2; exit 1; };
if [ "$SCOPE_MODE" = "pr-remote" ] || [ "$SCOPE_MODE" = "branch-remote" ]; then
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "${DIFF_A:-}" --head "${DIFF_B:-}" --docs-root "<root>";
else
  "$PY" "$SKILL_DIR/scripts/review-scope.py" --base "$DIFF_A" --head "$DIFF_B" --local-scope --docs-root "<root>";
fi
```

Remote scope always passes both endpoint flags, even when a best-effort fetch left one value empty; the helper then refuses to compute rather than comparing the fetched base to the unrelated local worktree. Load the JSON result. `hard_block_full` is a floor for the Review depth gate in `references/modes-and-output.md`; it covers the named hard-block classes, uncounted files, and a `size_band` of `large` (executable non-test changed lines at the full floor). `silent_pass_classes` names guards the gate may never send to lite. Neither awards lite, and a count below the floor decides nothing on its own. Whole-file deletions are not in any of the line counts above: the helper lists them in `deleted_files`, counts their executable non-test lines in `deleted_exec_nontest_lines`, and bands that count in `deleted_band` (`none`, `small`, or `large`), which the gate reads. `signals` are path heuristics, not selection decisions and not a lite block. After this stage, apply that gate before reading any later reference. On the full spine, Stage 3 still judges content-based risk such as auth, payments, mutation, external I/O, concurrency, and process execution. Use `test_files_changed`, `agent_surface`, `has_learnings_corpus`, and `declared_packs` as inputs to the conditions that select generic reviewers, not as automatic spawn decisions. `declared_packs` reports whether the local RocketClaw config names any Compound Pack, read from the config alone (nothing is resolved, so `pack_roots` is always 0); the learnings selection rule in `references/persona-catalog.md` decides what that fact selects. It describes the local checkout, so the helper evaluates it only in local scope: in remote scope it is `null` and no resolver runs. In local scope, `null` means the helper could not tell; read the config's `packs:` key yourself.

### Stage 1c: Map criteria files to changed paths

**Goal:** the mapping that pairs each criteria file governing this change with the changed files it governs. Paths, not contents. Both depth paths consume it: the lite path checks the diff against it in context, and Stage 3b decides the `project-standards` dispatch from it.

Enumerate the candidates from **the tree under review**, never from whichever tree happens to be checked out: the workspace only in `local-aligned` scope, and the reviewed head ref in `pr-remote` and `branch-remote` (Stage 1 resolved which). A criteria file that exists only in the reviewed tree must appear, and one deleted there must not, or the review enforces criteria the change never had.

Candidates are `CODING_STANDARDS.md`, `CLAUDE.md`, and `AGENTS.md` at any depth. Keep those whose directory is an ancestor of a changed file — a root-level file governs the whole checkout, `skills/AGENTS.md` only what is under `skills/`.

`CODING_STANDARDS.md` is the designated criteria source, so an instruction file supplies criteria only for changed files that no `CODING_STANDARDS.md` governs, and no file is graded against both kinds. Every governing `CODING_STANDARDS.md` still applies together. Declared Compound Packs are not a criteria kind here: they select `learnings-researcher` on the full spine and are graded by it independently, so a line that violates a standards rule and a pack rule yields one finding per source.

**Done** when no changed file could be graded against two kinds of criteria. A changed file that no criteria file governs is a complete result, not a gap. A search failure or uncertain scope is recorded as exactly that, never as an empty result; the Review depth gate and Stage 3b each state what it means for them.

Create the review run directory now. Every path, lite or full, writes its artifacts there:

```bash
SCRATCH_ROOT="$workspace_root/.tmp/rocketclaw";
[ ! -L "$SCRATCH_ROOT" ] || { echo "unsafe scratch root" >&2; exit 1; };
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
